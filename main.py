import os
import time
import json
import logging
import requests
import xmltodict
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("webdav-monitor")

# Configuration from Environment Variables
WEBDAV_URL = os.getenv("WEBDAV_URL")
WEBDAV_USER = os.getenv("WEBDAV_USER")
WEBDAV_PASS = os.getenv("WEBDAV_PASS")

ALIST_URL = os.getenv("ALIST_URL")
ALIST_USER = os.getenv("ALIST_USER")
ALIST_PASS = os.getenv("ALIST_PASS")
ALIST_TOKEN = os.getenv("ALIST_TOKEN") # Optional: can provide token directly

# Format: JSON array of paths to monitor, e.g., ["/storage1", "/storage2/sub"]
MONITOR_PATHS = json.loads(os.getenv("MONITOR_PATHS", '["/"]'))
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 300)) # Default 5 minutes

# State File Path
STATE_FILE = "webdav_state.json"

class AlistClient:
    def __init__(self, url, user=None, password=None, token=None):
        self.url = url.rstrip('/')
        self.user = user
        self.password = password
        self.token = token
        
    def login(self):
        if self.token:
            return True
        
        logger.info(f"Logging in to Alist at {self.url}...")
        try:
            resp = requests.post(f"{self.url}/api/auth/login", json={
                "username": self.user,
                "password": self.password
            })
            resp.raise_for_status()
            data = resp.json()
            if data['code'] == 200:
                self.token = data['data']['token']
                logger.info("Login successful")
                return True
            else:
                logger.error(f"Login failed: {data['message']}")
        except Exception as e:
            logger.error(f"Error during Alist login: {e}")
        return False

    def refresh_path(self, path):
        if not self.token and not self.login():
            return False
            
        logger.info(f"Triggering refresh for Alist path: {path}")
        headers = {"Authorization": self.token}
        try:
            # Alist refresh is triggered by listing the directory with refresh=true
            resp = requests.post(f"{self.url}/api/fs/list", 
                headers=headers,
                json={
                    "path": path,
                    "refresh": True,
                    "page": 1,
                    "per_page": 1
                }
            )
            resp.raise_for_status()
            data = resp.json()
            if data['code'] == 200:
                logger.info(f"Successfully refreshed {path}")
                return True
            else:
                logger.error(f"Refresh failed for {path}: {data['message']}")
        except Exception as e:
            logger.error(f"Error refreshing Alist path {path}: {e}")
        return False

class WebDAVScanner:
    def __init__(self, url, user, password):
        self.url = url.rstrip('/')
        self.auth = (user, password)
        
    def _list_recursive(self, path):
        """Recursively list files and directories to detect changes."""
        results = {}
        try:
            # WebDAV PROPFIND request
            headers = {'Depth': '1'}
            resp = requests.request('PROPFIND', f"{self.url}{path}", auth=self.auth, headers=headers)
            resp.raise_for_status()
            
            content = xmltodict.parse(resp.text)
            responses = content.get('D:multistatus', {}).get('D:response', [])
            
            if isinstance(responses, dict):
                responses = [responses]
                
            for res in responses:
                href = res['D:href']
                # Decode URL encoded paths if necessary
                # Simplified check for directory vs file
                prop = res['D:propstat']['D:prop'] if isinstance(res['D:propstat'], dict) else res['D:propstat'][0]['D:prop']
                
                is_dir = 'D:collection' in prop.get('D:resourcetype', {}) if prop.get('D:resourcetype') else False
                
                # We skip the path itself in the listing if it's the root of the current call
                current_href = href.rstrip('/')
                base_path_href = path.rstrip('/')
                # Hacky check to see if it's the current directory
                if current_href.endswith(base_path_href):
                    continue

                if is_dir:
                    # Recursive call
                    sub_results = self._list_recursive(href[len(self.url):] if href.startswith(self.url) else href)
                    results.update(sub_results)
                else:
                    # It's a file
                    size = prop.get('D:getcontentlength', '0')
                    mtime = prop.get('D:getlastmodified', '')
                    results[href] = {"size": size, "mtime": mtime}
                    
        except Exception as e:
            logger.error(f"Error scanning WebDAV path {path}: {e}")
            
        return results

    def get_file_state(self, paths):
        all_files = {}
        for path in paths:
            logger.info(f"Scanning WebDAV path: {path}")
            all_files.update(self._list_recursive(path))
        return all_files

def run_job():
    logger.info("Starting scheduled scan...")
    
    # Load previous state
    old_state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                old_state = json.load(f)
        except:
            pass

    scanner = WebDAVScanner(WEBDAV_URL, WEBDAV_USER, WEBDAV_PASS)
    new_state = scanner.get_file_state(MONITOR_PATHS)
    
    # Check for changes
    has_changes = False
    
    # 1. New or modified files
    for file, info in new_state.items():
        if file not in old_state or old_state[file] != info:
            logger.info(f"Change detected: {file}")
            has_changes = True
            break
            
    # 2. Deleted files
    if not has_changes:
        for file in old_state:
            if file not in new_state:
                logger.info(f"File deleted: {file}")
                has_changes = True
                break
                
    if has_changes:
        logger.info("Changes detected on WebDAV. Triggering Alist refresh.")
        alist = AlistClient(ALIST_URL, ALIST_USER, ALIST_PASS, ALIST_TOKEN)
        for path in MONITOR_PATHS:
            alist.refresh_path(path)
            
        # Save new state
        with open(STATE_FILE, 'w') as f:
            json.dump(new_state, f)
    else:
        logger.info("No changes detected.")

if __name__ == "__main__":
    logger.info("WebDAV Monitor started")
    logger.info(f"Monitoring paths: {MONITOR_PATHS}")
    logger.info(f"Scan interval: {SCAN_INTERVAL} seconds")
    
    # Run once immediately
    run_job()
    
    # Schedule
    scheduler = BlockingScheduler()
    scheduler.add_job(run_job, 'interval', seconds=SCAN_INTERVAL)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
