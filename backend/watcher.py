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
        
        rel_path = src_path[len(self.base_path):]
        if rel_path.startswith(os.sep): rel_path = rel_path[1:]
        rel_path = rel_path.replace('\\', '/')
        
        logger.info(f"Local {event_type}: {src_path} -> Queued for logging")
        
        from backend.scan_queue import ScanQueue
        # Add a specifically flagged EVENT job instead of a scan request
        ScanQueue.get_instance().add_job(self.task.id, src_path, f"EVENT_{event_type.upper()}")

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
                
                # Get Dst Account (optional for Local monitoring only)
                dst_acc = next((a for a in config.accounts if a.id == task.dst_account_id), None)
                # We no longer strictly require dst_acc. The worker will handle Alist logic conditionally.
                
                # Select Observer based on config
                use_polling = getattr(task, 'use_polling', False)
                
                if use_polling:
                    try:
                        from watchdog.observers.polling import PollingObserver as ObserverClass
                        obs_type = "Polling"
                    except ImportError:
                        from watchdog.observers import Observer as ObserverClass
                        obs_type = "Native (Fallback)"
                else:
                    from watchdog.observers import Observer as ObserverClass
                    obs_type = "Native"

                logger.info(f"Starting watcher for local path: {task.src_path} (Mode: {obs_type})")
                handler = RefreshHandler(task, dst_acc)
                observer = ObserverClass()
                observer.schedule(handler, task.src_path, recursive=True)
                observer.start()
                WatcherManager._observers[task.id] = observer
                
        except Exception as e:
            logger.error(f"Error updating watchers: {e}")
