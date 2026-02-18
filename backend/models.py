from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import json
import os
from passlib.context import CryptContext

CONFIG_PATH = os.getenv("CONFIG_PATH", "data/config.json")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Account(BaseModel):
    id: Optional[str] = None
    type: str
    name: str
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None

class MonitorTask(BaseModel):
    id: Optional[str] = None
    name: str
    src_account_id: str
    dst_account_id: Optional[str] = ""
    src_path: str
    dst_path: Optional[str] = "/"
    interval: int = 600
    enabled: bool = True
    last_run: Optional[str] = None
    status: str = "idle"
    refresh_source: bool = False

class UserSettings(BaseModel):
    username: str = "admin"
    password_hash: str = ""
    language: str = "zh"
    avatar: str = ""

class Config(BaseModel):
    accounts: List[Account] = []
    tasks: List[MonitorTask] = []
    settings: UserSettings = UserSettings()

def load_config() -> Config:
    config_updated = False
    
    def get_default():
        default_hash = pwd_context.hash("admin")
        return Config(settings=UserSettings(password_hash=default_hash))

    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        config = get_default()
        save_config(config)
        return config
    
    try:
        with open(CONFIG_PATH, "r") as f:
            content = f.read()
            if not content.strip():
                raise ValueError("Empty file")
            data = json.loads(content)
    except (json.JSONDecodeError, ValueError, Exception) as e:
        print(f"Config corrupted, resetting to default: {e}")
        config = get_default()
        try:
            save_config(config)
        except Exception as save_err:
            print(f"Critical error: Could not reset config file: {save_err}")
        return config
        
    if "settings" not in data:
        data["settings"] = UserSettings(password_hash=pwd_context.hash("admin")).model_dump()
        config_updated = True
    elif "password_hash" not in data["settings"] or not data["settings"]["password_hash"]:
        data["settings"]["password_hash"] = pwd_context.hash("admin")
        config_updated = True
        
    if "tasks" in data and isinstance(data["tasks"], list):
        for t_data in data["tasks"]:
            if not isinstance(t_data, dict): continue
            if "account_id" in t_data:
                t_data["src_account_id"] = t_data.pop("account_id")
                config_updated = True
            if "alist_account_id" in t_data:
                t_data["dst_account_id"] = t_data.pop("alist_account_id")
                config_updated = True
            if "webdav_path" in t_data:
                t_data["src_path"] = t_data.pop("webdav_path")
                config_updated = True
            if "alist_path" in t_data:
                t_data["dst_path"] = t_data.pop("alist_path")
                config_updated = True
        
    try:
        config = Config(**data)
    except Exception as e:
        print(f"Config structure error: {e}. Attempting to recover...")
        if not isinstance(data, dict) or "accounts" not in data or "tasks" not in data:
            print("Critical sections missing or invalid format. Resetting.")
            config = get_default()
            try:
                save_config(config)
            except: pass
            return config
            
        settings_data = data.get("settings")
        if not isinstance(settings_data, dict):
            settings_obj = UserSettings(password_hash=pwd_context.hash("admin"))
        else:
            settings_obj = UserSettings(**settings_data)
            
        config = Config(
            accounts=data.get("accounts", []),
            tasks=data.get("tasks", []),
            settings=settings_obj
        )
        try:
            save_config(config)
        except: pass

    if config_updated:
        save_config(config)
    return config

def save_config(config: Config):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(CONFIG_PATH)), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding='utf-8') as f:
            data = config.model_dump() if hasattr(config, "model_dump") else config.dict()
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")
