from apscheduler.schedulers.background import BackgroundScheduler
from backend.models import load_config, save_config, MonitorTask
from backend.services import WebDAVService, AlistService
import logging
import json
import os
import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Set
import gzip

logger = logging.getLogger("scheduler")

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
running_tasks: Set[str] = set()

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
    if not task or not task.enabled:
        return

    if task_id in running_tasks:
        logger.warning(f"Task {task_id} is already running. Skipping this trigger.")
        return
    
    running_tasks.add(task_id)
    try:
        logger.info(f"Running task: {task.name}")
        task.status = "running"
        save_config(config)

        src_acc = next((a for a in config.accounts if a.id == task.src_account_id), None)
        dst_acc = next((a for a in config.accounts if a.id == task.dst_account_id), None)
        
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

        logger.info(f"Scanning {src_acc.name}:{task.src_path}...")
        scan_error = None
        if src_acc.type == "webdav":
            try:
                new_state = WebDAVService.list_recursive(src_acc.url, src_acc.username, src_acc.password, task.src_path, old_state=old_state, smart_scan=task.smart_scan)
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
                new_state = AlistService.list_recursive_rich(src_acc.url, token, task.src_path, old_state=old_state, refresh=refresh, smart_scan=task.smart_scan)
            except Exception as scan_ex:
                scan_error = str(scan_ex)
                new_state = {}
        else:
            new_state = {}
        
        if scan_error and not new_state:
            raise Exception(f"Scan failed: {scan_error}")
        
        if not new_state and not old_state:
            logger.warning(f"Scan returned 0 items for {src_acc.name}:{task.src_path}. Source may be empty or unreachable.")
        
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
                        AlistService.refresh_path(dst_acc.url, dst_token, refresh_path)
        
        
        try:
            with gzip.open(state_path, "wt", encoding="utf-8") as f:
                json.dump(new_state, f)
            
            
            if os.path.exists(legacy_path):
                os.remove(legacy_path)
                logger.info(f"Migrated legacy state file to compressed format for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to save state file: {e}")
        
        task.last_run = datetime.datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
        task.status = "idle"
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
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        task.status = f"error: {str(e)}"
        try:
            from backend.main import add_notification
            add_notification(f"任务失败: {task.name}", str(e), "error")
        except: pass
    finally:
        running_tasks.discard(task_id)
        save_config(config)

def init_scheduler():
    scheduler.start()
    config = load_config()
    for task in config.tasks:
        if task.enabled:
            update_task_job(task)

def update_task_job(task: MonitorTask):
    # Local tasks rely on Watchdog, no polling needed
    if getattr(task, 'src_type', 'webdav') == 'local':
        if scheduler.get_job(task.id):
            scheduler.remove_job(task.id)
        return

    if task.enabled:
        scheduler.add_job(
            run_task, 
            'interval', 
            seconds=task.interval, 
            id=task.id, 
            args=[task.id],
            replace_existing=True
        )
    else:
        if scheduler.get_job(task.id):
            scheduler.remove_job(task.id)
