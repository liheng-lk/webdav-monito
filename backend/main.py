from fastapi import FastAPI, HTTPException, Body, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from backend.models import load_config, save_config, Account, MonitorTask, pwd_context
from backend.services import WebDAVService, AlistService
from backend.scheduler import init_scheduler, update_task_job, run_task
from backend.watcher import WatcherManager
import os
import uuid
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, List
import collections
import logging
import jwt

os.environ['TZ'] = 'Asia/Shanghai'
try:
    time.tzset()
except AttributeError:
    pass

class LogBufferHandler(logging.Handler):
    def __init__(self, capacity=100):
        super().__init__()
        self.buffer = collections.deque(maxlen=capacity)

    def emit(self, record):
        msg = self.format(record)
        timestamp = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
        self.buffer.append({"time": timestamp, "level": record.levelname, "msg": msg})

log_handler = LogBufferHandler()
log_handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))

logging.basicConfig(level=logging.INFO, handlers=[
    logging.StreamHandler(),
    log_handler
])
logger = logging.getLogger("main")

notifications = collections.deque(maxlen=50)

def add_notification(title, message, ntype="info"):
    notifications.appendleft({
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "message": message,
        "type": ntype,
        "time": datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%m-%d %H:%M"),
        "read": False
    })

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    if SECRET_KEY:
        logger.warning("JWT_SECRET is too short (minimum 32 characters). Generating a random one for security.")
    import secrets
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.info("A random 32-byte JWT secret has been generated.")
    if not os.getenv("JWT_SECRET"):
        logger.warning("Note: Sessions will be invalidated on container restart unless you provide a persistent JWT_SECRET.")

logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

ALGORITHM = "HS256"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Monitor Service...")
    init_scheduler()
    WatcherManager.update_watchers()
    yield
    logger.info("Shutting down...")

app = FastAPI(title="WebDAV Monitor Premium API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.PyJWTError:
        raise credentials_exception

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    config = load_config()
    logger.info(f"Login attempt for user: {form_data.username}")
    
    if form_data.username != config.settings.username:
        logger.warning(f"Login failed: Username mismatch. Expected {config.settings.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    if not pwd_context.verify(form_data.password, config.settings.password_hash):
        logger.warning(f"Login failed: Password mismatch for user {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    logger.info(f"Login successful for user: {form_data.username}")
    access_token = create_access_token(data={"sub": config.settings.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/config")
def get_config(current_user: str = Depends(get_current_user)):
    return load_config()

@app.get("/api/logs")
def get_logs(current_user: str = Depends(get_current_user)):
    return list(log_handler.buffer)

@app.get("/api/settings")
def get_settings(current_user: str = Depends(get_current_user)):
    config = load_config()
    return config.settings

@app.put("/api/settings")
def update_settings(settings: dict, current_user: str = Depends(get_current_user)):
    config = load_config()
    if "language" in settings:
        config.settings.language = settings["language"]
    if "password" in settings and settings["password"]:
        config.settings.password_hash = pwd_context.hash(settings["password"])
    save_config(config)
    return config.settings

@app.put("/api/avatar")
def update_avatar(data: dict, current_user: str = Depends(get_current_user)):
    config = load_config()
    avatar_data = data.get("avatar", "")
    if len(avatar_data) > 500000:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Image too large (max 500KB)")
    config.settings.avatar = avatar_data
    save_config(config)
    return {"avatar": config.settings.avatar}

@app.post("/api/accounts")
def add_account(account: Account, current_user: str = Depends(get_current_user)):
    config = load_config()
    if not account.id:
        account.id = str(uuid.uuid4())
    config.accounts.append(account)
    save_config(config)
    return account

@app.put("/api/accounts/{account_id}")
def update_account(account_id: str, account: Account, current_user: str = Depends(get_current_user)):
    config = load_config()
    for i, acc in enumerate(config.accounts):
        if acc.id == account_id:
            config.accounts[i] = account
            save_config(config)
            return account
    raise HTTPException(status_code=404, detail="Account not found")

@app.delete("/api/accounts/{account_id}")
def delete_account(account_id: str, current_user: str = Depends(get_current_user)):
    config = load_config()
    from backend.scheduler import scheduler
    tasks_to_remove = [t for t in config.tasks if t.src_account_id == account_id or t.dst_account_id == account_id]
    for task in tasks_to_remove:
        if scheduler.get_job(task.id):
            scheduler.remove_job(task.id)
    
    config.tasks = [t for t in config.tasks if t.src_account_id != account_id and t.dst_account_id != account_id]
    config.accounts = [a for a in config.accounts if a.id != account_id]
    
    save_config(config)
    WatcherManager.update_watchers()
    return {"message": "Deleted account and associated tasks"}

@app.post("/api/accounts/test")
def test_account(account: Account, current_user: str = Depends(get_current_user)):
    if account.type == "webdav":
        success, msg = WebDAVService.test_connection(account.url, account.username, account.password)
    else:
        success, msg = AlistService.test_connection(account.url, account.username, account.password, account.token)
    return {"success": success, "message": msg}

@app.post("/api/accounts/{account_id}/ls")
def list_account_dir(account_id: str, path: str = Body(..., embed=True), current_user: str = Depends(get_current_user)):
    config = load_config()
    account = next((a for a in config.accounts if a.id == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account.type == "webdav":
        return WebDAVService.list_directory(account.url, account.username, account.password, path)
    else:
        token = account.token or AlistService.get_token(account.url, account.username, account.password)
        if not token:
            raise HTTPException(status_code=400, detail="Could not get Alist token")
        return AlistService.list_directory(account.url, token, path)

@app.post("/api/local/list")
def list_local_dir(path: str = Body(..., embed=True), current_user: str = Depends(get_current_user)):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"Not a directory: {path}")
    
    items = []
    try:
        for entry in os.scandir(path):
            try:
                stat = entry.stat()
                items.append({
                    "name": entry.name,
                    "path": os.path.join(path, entry.name),
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size if entry.is_file() else 0,
                    "mtime": stat.st_mtime
                })
            except (PermissionError, OSError):
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")
    
    return items

@app.post("/api/tasks")
def add_task(task: MonitorTask, current_user: str = Depends(get_current_user)):
    config = load_config()
    if not task.id:
        task.id = str(uuid.uuid4())
    config.tasks.append(task)
    save_config(config)
    update_task_job(task)
    WatcherManager.update_watchers()
    return task

@app.put("/api/tasks/{task_id}")
def update_task(task_id: str, task: MonitorTask, current_user: str = Depends(get_current_user)):
    config = load_config()
    for i, t in enumerate(config.tasks):
        if t.id == task_id:
            config.tasks[i] = task
            save_config(config)
            update_task_job(task)
            WatcherManager.update_watchers()
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str, current_user: str = Depends(get_current_user)):
    config = load_config()
    config.tasks = [t for t in config.tasks if t.id != task_id]
    save_config(config)
    WatcherManager.update_watchers()
    from backend.scheduler import scheduler
    if scheduler.get_job(task_id):
        scheduler.remove_job(task_id)
    return {"message": "Deleted"}

@app.post("/api/tasks/{task_id}/run")
def trigger_task(task_id: str, background_tasks: BackgroundTasks, current_user: str = Depends(get_current_user)):
    background_tasks.add_task(run_task, task_id)
    return {"message": "Task triggered"}

@app.get("/api/wallpaper")
def get_wallpapers():
    import requests as req
    try:
        resp = req.get(
            "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8",
            timeout=10, verify=False
        )
        data = resp.json()
        images = [f"https://cn.bing.com{img['url']}" for img in data.get('images', [])]
        return {"images": images}
    except Exception as e:
        logger.error(f"Failed to fetch wallpapers: {e}")
        return {"images": []}

@app.get("/api/notifications")
def get_notifications(current_user: str = Depends(get_current_user)):
    return {"notifications": list(notifications), "unread": sum(1 for n in notifications if not n["read"])}

@app.put("/api/notifications/read")
def mark_notifications_read(current_user: str = Depends(get_current_user)):
    for n in notifications:
        n["read"] = True
    return {"message": "All marked as read"}

@app.delete("/api/notifications")
def clear_notifications(current_user: str = Depends(get_current_user)):
    notifications.clear()
    return {"message": "Cleared"}


if os.path.exists("frontend/dist"):
    app.mount("/static", StaticFiles(directory="frontend/dist/assets"), name="static")

@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    
    if full_path.startswith("assets/"):
        asset_path = os.path.join("frontend/dist", full_path)
        if os.path.exists(asset_path):
            return FileResponse(asset_path)
            
    dist_path = os.path.join("frontend/dist", "index.html")
    if os.path.exists(dist_path):
        return FileResponse(dist_path)
    return JSONResponse(status_code=404, content={"message": "Frontend not build yet."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
