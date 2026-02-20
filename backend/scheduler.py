from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.models import load_config, save_config, MonitorTask, TaskRunRecord
from backend.services import WebDAVService, AlistService
import logging
import json
import os
import datetime
import time
from datetime import timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Set
from backend.scan_queue import ScanQueue, ScanJob
import threading
import gzip
import traceback

logger = logging.getLogger("scheduler")

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
running_tasks: Set[str] = set()
retry_counts: Dict[str, int] = {}
MAX_HISTORY = 200

def get_state_path(task_id: str):
    return f"data/state_{task_id}.json.gz"

def get_legacy_state_path(task_id: str):
    return f"data/state_{task_id}.json"

def get_parent_path(file_href: str) -> str:
    parts = file_href.rstrip('/').split('/')
    if len(parts) <= 1:
        return "/"
    return "/".join(parts[:-1])

def run_task(task_id: str):
    config = load_config()
    task = next((t for t in config.tasks if t.id == task_id), None)
    if not task:
        return
    if not task.enabled:
        logger.info(f"Task {task_id} ({task.name}) is disabled, skipping.")
        return

    if task_id in running_tasks:
        logger.warning(f"Task {task_id} is already running. Skipping this trigger.")
        return
    
    running_tasks.add(task_id)
    start_time = time.time()
    start_iso = datetime.datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    run_new_files = 0
    run_modified = 0
    run_deleted = 0
    run_scanned = 0
    run_dirs_refreshed = 0
    try:
        logger.info(f"Running task: {task.name}")
        task.status = "running"
        save_config(config)

        is_local = getattr(task, 'src_type', 'webdav') == 'local'

        src_acc = None
        dst_acc = next((a for a in config.accounts if a.id == task.dst_account_id), None)

        if not is_local:
            src_acc = next((a for a in config.accounts if a.id == task.src_account_id), None)
            if not src_acc:
                task.enabled = False
                task.status = "error: Scanning account missing (disabled)"
                save_config(config)
                if scheduler.get_job(task_id):
                    scheduler.remove_job(task_id)
                raise Exception("Scanning account not found. Task has been disabled.")

        state_path = get_state_path(task_id)
        legacy_path = get_legacy_state_path(task_id)
        old_state = {}
        
        if os.path.exists(state_path):
            try:
                with gzip.open(state_path, "rt", encoding="utf-8") as f:
                    old_state = json.load(f)
                logger.info(f"Loaded previous state (compressed) with {len(old_state)} items.")
            except Exception as e:
                logger.warning(f"Failed to load compressed state: {e}, starting fresh.")
        elif os.path.exists(legacy_path):
            try:
                with open(legacy_path, "r", encoding="utf-8") as f:
                    old_state = json.load(f)
                logger.info(f"Loaded legacy state with {len(old_state)} items. Will migrate to compressed format.")
            except Exception as e:
                logger.warning(f"Failed to load legacy state: {e}, starting fresh.")
        else:
            logger.info("No previous state found, starting fresh scan.")

        scan_error = None
        new_state = {}

        if is_local:
            local_path = task.src_path.rstrip('/')
            logger.info(f"Scanning local path: {local_path} ...")
            if not os.path.exists(local_path):
                raise Exception(f"Local path not found: {local_path}")
            try:
                scanned_count = 0
                last_log_time = time.time()
                # Enable followlinks to support symlinked directories in Docker volumes
                for root, dirs, files in os.walk(local_path, followlinks=True):
                    scanned_count += 1
                    current_time = time.time()
                    if current_time - last_log_time > 10:
                        logger.info(f"Scanning local path... checked {scanned_count} directories, found {len(new_state)} items so far...")
                        last_log_time = current_time
                    
                    rel_root = root[len(local_path):]
                    if not rel_root.startswith('/'):
                        rel_root = '/' + rel_root
                    dir_key = task.src_path.rstrip('/') + rel_root.rstrip('/')
                    if dir_key:
                        new_state[dir_key + '/'] = {'is_dir': True, 'mtime': str(os.path.getmtime(root)), 'size': 0}
                    
                    for i, fname in enumerate(files):
                        fpath = os.path.join(root, fname)
                        try:
                            stat = os.stat(fpath)
                            file_key = dir_key.rstrip('/') + '/' + fname
                            new_state[file_key] = {
                                'is_dir': False,
                                'mtime': str(stat.st_mtime),
                                'size': stat.st_size
                            }
                            if len(new_state) <= 5:
                                logger.info(f"Found file: {fpath}")
                        except (PermissionError, OSError):
                            continue
                logger.info(f"Local scan found {len(new_state)} items. Scanned {scanned_count} directories.")
            except Exception as scan_ex:
                scan_error = str(scan_ex)
                new_state = {}
        else:
            src_name = src_acc.name if src_acc else "unknown"
            logger.info(f"Scanning {src_name}:{task.src_path}...")
            if src_acc.type == "webdav":
                try:
                    new_state = WebDAVService.list_recursive(src_acc.url, src_acc.username, src_acc.password, task.src_path, old_state=old_state, smart_scan=task.smart_scan, concurrency=task.concurrency)
                except Exception as scan_ex:
                    scan_error = str(scan_ex)
                    new_state = {}
            elif src_acc.type == "alist":
                old_token = src_acc.token
                token = src_acc.token or AlistService.get_token(src_acc.url, src_acc.username, src_acc.password)
                
                if not token:
                    raise Exception(f"Cannot get Alist token for account {src_acc.name}")
                
                if token and token != old_token:
                    logger.info(f"Updating cached Alist token for account {src_acc.name}")
                    src_acc.token = token
                    save_config(config)
                
                refresh = getattr(task, 'refresh_source', False)
                try:
                    new_state = AlistService.list_recursive_rich(src_acc.url, token, task.src_path, old_state=old_state, refresh=refresh, smart_scan=task.smart_scan, concurrency=task.concurrency)
                except Exception as scan_ex:
                    scan_error = str(scan_ex)
                    new_state = {}
        
        if scan_error and not new_state:
            raise Exception(f"Scan failed: {scan_error}")
        
        if not new_state and not old_state:
            src_label = task.src_path if is_local else f"{src_acc.name}:{task.src_path}"
            logger.warning(f"Scan returned 0 items for {src_label}. Source may be empty or unreachable.")
        
        logger.info(f"Scan completed. Found {len(new_state)} items (Files + Dirs).")

        changed_dirs: Set[str] = set()
        new_files = 0
        modified_files = 0
        deleted_files = 0
        
        for href, info in new_state.items():
            is_dir = info.get('is_dir', False)
            
            if href not in old_state:
                if is_dir:
                    logger.info(f"Change detected: [New Dir] {href}")
                    changed_dirs.add(get_parent_path(href))
                else:
                    logger.info(f"Change detected: [New File] {href}")
                    changed_dirs.add(get_parent_path(href))
                    new_files += 1
            elif old_state[href] != info:
                if not is_dir:
                    logger.info(f"Change detected: [Modified File] {href}")
                    changed_dirs.add(get_parent_path(href))
                    modified_files += 1
                
        for href, info_or_dict in old_state.items():
            if href not in new_state:
                is_dir = False
                if isinstance(info_or_dict, dict):
                    is_dir = info_or_dict.get('is_dir', False)
                
                # Double check if local file really deleted
                if is_local and os.path.exists(href):
                    new_state[href] = info_or_dict
                    continue

                if is_dir:
                    logger.info(f"Change detected: [Deleted Dir] {href}")
                else:
                    logger.info(f"Change detected: [Deleted File] {href}")
                    deleted_files += 1
                
                changed_dirs.add(get_parent_path(href))

        if changed_dirs:
            logger.info(f"Action: Refreshing {len(changed_dirs)} target directories due to changes.")
            
            if dst_acc and dst_acc.type == "alist":
                dst_old_token = dst_acc.token
                dst_token = dst_acc.token or AlistService.get_token(dst_acc.url, dst_acc.username, dst_acc.password)
                if dst_token:
                    if dst_token != dst_old_token:
                        dst_acc.token = dst_token
                        save_config(config)
                    
                    refresh_dst = getattr(task, 'refresh_destination', True)
                    if refresh_dst:
                        base_src_path = task.src_path.rstrip('/')
                        base_dst_path = task.dst_path.rstrip('/')
                        
                        for src_dir in changed_dirs:
                            rel_path = ""
                            if src_dir.startswith(base_src_path):
                                rel_path = src_dir[len(base_src_path):]
                            else:
                                idx = src_dir.find(base_src_path)
                                if idx != -1:
                                    rel_path = src_dir[idx + len(base_src_path):]
                            
                            refresh_path = base_dst_path + rel_path
                            try:
                                AlistService.refresh_path(dst_acc.url, dst_token, refresh_path)
                            except Exception as e:
                                logger.error(f"Failed to refresh Alist path {refresh_path}: {e}")
                    else:
                        logger.info(f"Skipping Alist refresh for task {task.name} (refresh_destination=False).")
        
        
        try:
            with gzip.open(state_path, "wt", encoding="utf-8") as f:
                json.dump(new_state, f)
            
            
            if os.path.exists(legacy_path):
                os.remove(legacy_path)
                logger.info(f"Migrated legacy state file to compressed format for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to save state file: {e}")
        
        run_new_files = new_files
        run_modified = modified_files
        run_deleted = deleted_files
        run_scanned = len(new_state)
        run_dirs_refreshed = len(changed_dirs)

        task.last_run = datetime.datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
        task.status = "idle"
        retry_counts.pop(task_id, None)
        try:
            from backend.main import add_notification
            if changed_dirs:
                parts = []
                if new_files: parts.append(f"{new_files} 新文件")
                if modified_files: parts.append(f"{modified_files} 修改")
                if deleted_files: parts.append(f"{deleted_files} 删除")
                detail = ", ".join(parts) if parts else f"{len(changed_dirs)} 个目录变更"
                add_notification(f"任务完成: {task.name}", f"检测到变更: {detail}，已刷新", "success")
            else:
                add_notification(f"任务完成: {task.name}", f"扫描了 {len(new_state)} 个项目，无变更", "info")
        except: pass

        record = TaskRunRecord(
            task_id=task_id, task_name=task.name,
            start_time=start_iso,
            end_time=datetime.datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
            duration_seconds=round(time.time() - start_time, 2),
            status="success", items_scanned=run_scanned,
            new_files=run_new_files, modified_files=run_modified,
            deleted_files=run_deleted, dirs_refreshed=run_dirs_refreshed
        )
        config.task_history.append(record)
        if len(config.task_history) > MAX_HISTORY:
            config.task_history = config.task_history[-MAX_HISTORY:]

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        task.status = f"error: {str(e)}"

        record = TaskRunRecord(
            task_id=task_id, task_name=task.name,
            start_time=start_iso,
            end_time=datetime.datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
            duration_seconds=round(time.time() - start_time, 2),
            status="error", error_message=str(e),
            items_scanned=run_scanned,
            new_files=run_new_files, modified_files=run_modified,
            deleted_files=run_deleted, dirs_refreshed=run_dirs_refreshed
        )
        config.task_history.append(record)
        if len(config.task_history) > MAX_HISTORY:
            config.task_history = config.task_history[-MAX_HISTORY:]

        max_r = getattr(task, 'max_retries', 0)
        if max_r > 0:
            count = retry_counts.get(task_id, 0)
            if count < max_r:
                retry_counts[task_id] = count + 1
                delay = getattr(task, 'retry_delay', 60)
                logger.warning(f"Retrying task {task.name} ({count+1}/{max_r}) in {delay}s")
                scheduler.add_job(
                    run_task, 'date',
                    run_date=datetime.datetime.now() + timedelta(seconds=delay),
                    args=[task_id], id=f"{task_id}_retry",
                    replace_existing=True
                )
            else:
                retry_counts.pop(task_id, None)
                logger.error(f"Task {task.name} failed after {max_r} retries.")

        try:
            from backend.main import add_notification
            add_notification(f"任务失败: {task.name}", str(e), "error")
        except: pass
    finally:
        running_tasks.discard(task_id)
        save_config(config)

def process_scan_job(job: ScanJob):
    """
    Process a scan job from the queue.
    Watchdog now only triggers purely local EVENT jobs which are logged directly.
    """
    if job.job_type.startswith("EVENT_"):
        event_name = job.job_type.replace("EVENT_", "").lower()
        logger.info(f"[实时监控] 侦测到局部变更 | 事件: {event_name} | 路径: {job.path}")
        
        # Also notify via web UI
        try:
            from backend.main import add_notification
            add_notification("实时监控反馈", f"文件发生变动 ({event_name}): {job.path}", "info")
        except:
            pass
        return

    logger.info(f"Processing scan job for task {job.task_id} (Type: {job.job_type}, Path: {job.path})")
    run_task(job.task_id)

def worker_thread():
    queue = ScanQueue.get_instance()
    logger.info("Scan Worker Thread Started")
    while True:
        try:
            job = queue.pop_job()
            if job:
                process_scan_job(job)
            else:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Worker Loop Error: {e}")
            logger.error(traceback.format_exc())
            time.sleep(5)

def init_scheduler():
    scheduler.start()
    
    # Start Worker Thread
    t = threading.Thread(target=worker_thread, daemon=True)
    t.start()
    
    config = load_config()
    for task in config.tasks:
        if task.enabled:
            update_task_job(task)

def update_task_job(task: MonitorTask):
    # Allow local tasks to be scheduled as well (e.g. for safety/redundancy)
    # previously returned here if local -> removed to allow cron/interval
    
    if task.enabled:
        stype = getattr(task, 'schedule_type', 'interval')
        cron_expr = getattr(task, 'cron_expr', '')
        if stype == 'cron' and cron_expr.strip():
            try:
                trigger = CronTrigger.from_crontab(cron_expr.strip(), timezone='Asia/Shanghai')
                scheduler.add_job(
                    run_task, trigger,
                    id=task.id, args=[task.id],
                    replace_existing=True
                )
                logger.info(f"Task {task.name} scheduled with cron: {cron_expr}")
            except Exception as e:
                logger.error(f"Invalid cron expression '{cron_expr}' for task {task.name}: {e}. Falling back to interval.")
                scheduler.add_job(
                    run_task, 'interval',
                    seconds=task.interval, id=task.id,
                    args=[task.id], replace_existing=True
                )
        else:
            scheduler.add_job(
                run_task, 'interval',
                seconds=task.interval, id=task.id,
                args=[task.id], replace_existing=True
            )
    else:
        if scheduler.get_job(task.id):
            scheduler.remove_job(task.id)
