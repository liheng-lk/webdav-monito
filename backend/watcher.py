from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import logging
from backend.services import AlistService
from backend.models import load_config

logger = logging.getLogger("watcher")

class RefreshHandler(FileSystemEventHandler):
    def __init__(self, task, dst_acc):
        self.task = task
        self.dst_acc = dst_acc
        self.base_path = task.src_path.rstrip('/')
        self.last_refresh = 0
        
    def process(self, src_path, event_type):
        if not src_path.startswith(self.base_path): return
        
        # Debounce
        now = time.time()
        if now - self.last_refresh < 2: return
        self.last_refresh = now
        
        rel_path = src_path[len(self.base_path):]
        if rel_path.startswith(os.sep): rel_path = rel_path[1:]
        
        # Consistent slash
        rel_path = rel_path.replace('\\', '/')
        
        # Target Alist Path
        # Alist path starts with / usually
        dst_base = self.task.dst_path.rstrip('/')
        target_path = f"{dst_base}/{rel_path}"
        
        logger.info(f"Local {event_type}: {src_path} -> Refreshing Alist: {target_path}")
        
        # Get Token
        token = self.dst_acc.token
        if not token:
             token = AlistService.get_token(self.dst_acc.url, self.dst_acc.username, self.dst_acc.password)
             
        if token:
            try:
                # Refresh parent dir just in case
                parent = os.path.dirname(target_path)
                AlistService.refresh_path(self.dst_acc.url, token, parent)
            except Exception as e:
                logger.error(f"Failed to refresh Alist {parent}: {e}")

    def on_created(self, event):
        if event.is_directory: return
        self.process(event.src_path, "created")

    def on_deleted(self, event):
        if event.is_directory: return
        self.process(event.src_path, "deleted")

    def on_moved(self, event):
        if event.is_directory: return
        self.process(event.dest_path, "moved")

    def on_modified(self, event):
        if event.is_directory: return
        self.process(event.src_path, "modified")

class WatcherManager:
    _observers = {}
    
    @staticmethod
    def stop_all():
        for obs in WatcherManager._observers.values():
            obs.stop()
            obs.join()
        WatcherManager._observers.clear()
        
    @staticmethod
    def update_watchers():
        try:
            config = load_config()
            # Find active LOCAL tasks
            active_tasks = [t for t in config.tasks if t.enabled and getattr(t, 'src_type', 'webdav') == 'local']
            
            # Stop removed
            active_ids = {t.id for t in active_tasks}
            current_ids = list(WatcherManager._observers.keys())
            
            for tid in current_ids:
                if tid not in active_ids:
                    logger.info(f"Stopping watcher for task {tid}")
                    obs = WatcherManager._observers.pop(tid)
                    obs.stop()
                    obs.join()
            
            # Start new
            for task in active_tasks:
                if task.id in WatcherManager._observers: continue
                
                # Check path
                if not os.path.exists(task.src_path):
                    logger.warning(f"Watcher: Local path {task.src_path} not found. Skipping.")
                    continue
                
                # Get Dst Account
                dst_acc = next((a for a in config.accounts if a.id == task.dst_account_id), None)
                if not dst_acc: continue
                
                logger.info(f"Starting watcher for local path: {task.src_path}")
                handler = RefreshHandler(task, dst_acc)
                observer = Observer()
                observer.schedule(handler, task.src_path, recursive=True)
                observer.start()
                WatcherManager._observers[task.id] = observer
                
        except Exception as e:
            logger.error(f"Error updating watchers: {e}")
