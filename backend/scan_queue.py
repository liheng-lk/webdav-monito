import time
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass, field
import threading
from collections import deque

logger = logging.getLogger("scan_queue")

@dataclass
class ScanJob:
    task_id: str
    path: str  # Source path (local or remote)
    job_type: str  # "FULL" or "PARTIAL"
    created_at: float = field(default_factory=time.time)

class ScanQueue:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.queue = deque()
        self.pending_tasks: Dict[str, float] = {}  # key -> timestamp
        self.lock = threading.Lock()
        
    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = ScanQueue()
        return cls._instance

    def add_job(self, task_id: str, path: str, job_type: str = "PARTIAL"):
        """
        Add a job to the queue with debounce logic.
        key: task_id + path
        """
        key = f"{task_id}:{path}:{job_type}"
        now = time.time()
        
        with self.lock:
            # Simple Debounce: If same job added within 2 seconds, ignore
            if key in self.pending_tasks:
                last_time = self.pending_tasks[key]
                if now - last_time < 2.0:
                    # logger.debug(f"Debounced job: {key}")
                    return
            
            self.pending_tasks[key] = now
            job = ScanJob(task_id=task_id, path=path, job_type=job_type)
            self.queue.append(job)
            logger.info(f"Queue Added: [{job_type}] {task_id} - {path} (Queue Size: {len(self.queue)})")

    def pop_job(self) -> Optional[ScanJob]:
        with self.lock:
            if not self.queue:
                return None
            
            job = self.queue.popleft()
            
            # Clean up pending_tasks (lazy cleanup)
            key = f"{job.task_id}:{job.path}:{job.job_type}"
            if key in self.pending_tasks:
                del self.pending_tasks[key]
                
            return job

    def size(self):
        with self.lock:
            return len(self.queue)
