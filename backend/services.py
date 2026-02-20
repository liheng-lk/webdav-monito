import requests
import xmltodict
import logging
import json
import os
import time
import urllib3
import concurrent.futures
import threading
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin, unquote, urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("webdav-services")

class WebDAVService:
    @staticmethod
    def test_connection(url, username, password):
        target_urls = [url.rstrip('/'), url.rstrip('/') + '/']
        auth_methods = [HTTPBasicAuth(username, password), HTTPDigestAuth(username, password)]
        
        headers = {
            'Depth': '0',
            'User-Agent': 'WebDAV-Monitor-Premium',
            'Content-Type': 'application/xml; charset="utf-8"'
        }
        
        last_error = "Unknown Error"
        
        for target_url in target_urls:
            for auth in auth_methods:
                try:
                    logger.info(f"Testing WebDAV ({type(auth).__name__}): {target_url}")
                    resp = requests.request('PROPFIND', target_url, auth=auth, headers=headers, timeout=10, verify=False)
                    
                    if resp.status_code in [200, 207]:
                        return True, "Success"
                    
                    if resp.status_code == 401:
                        last_error = "Authentication Failed: Check username/password"
                        continue
                    
                    if resp.status_code == 405:
                        get_resp = requests.get(target_url, auth=auth, timeout=10, verify=False)
                        if get_resp.status_code < 400:
                            return True, "Success (GET fallback)"
                        last_error = f"HTTP {get_resp.status_code}: GET failed"
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.reason}"
                        if resp.text:
                            last_error += f" ({resp.text[:50]}...)"
                            
                except requests.exceptions.RequestException as e:
                    logger.error(f"WebDAV Test Attempt Failed: {e}")
                    last_error = str(e)
                    
        return False, last_error

    @staticmethod
    def _list_dir_worker(session, url, username, password, path):
        results = {}
        subdirs = []
        
        base_url = url if url.endswith('/') else url + '/'
        
        if path.startswith('http'):
            target_url = path
        else:
            joined = urljoin(base_url, path)
            if not joined.startswith(base_url.rstrip('/')):
                target_url = base_url + path.lstrip('/')
            else:
                target_url = joined
        
        # Determine auth mechanism (basic vs digest)
        # Optimization: We can't easily guess, so we try Basic first.
        # Ideally, main thread detects auth type once and passes it down.
        # But for robustness, we keep try-catch or assume Basic if not specified.
        # Since session keeps connection alive, maybe auth header is cached?
        # Requests Session handles cookies but not Basic Auth unless set on session.auth
        # We'll set auth on session if possible, or pass it.
        
        # To avoid overhead of testing auth every time, we rely on passed params
        # But requests require auth per request if not set on session.
        
        headers = {
            'Depth': '1',
            'User-Agent': 'WebDAV-Monitor-Premium',
            'Accept': 'application/xml, text/xml'
        }
        
        # Try passed auth (Basic)
        # If session has auth set, we don't need to pass it.
        # But we don't know if it's Basic or Digest.
        # We will assume Basic for speed, fallback to Digest if 401.
        
        try:
            # We use session.request
            resp = session.request('PROPFIND', target_url, auth=HTTPBasicAuth(username, password), headers=headers, timeout=60, verify=False)
            if resp.status_code == 401:
                # Fallback to Digest
                resp = session.request('PROPFIND', target_url, auth=HTTPDigestAuth(username, password), headers=headers, timeout=60, verify=False)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"WebDAV scan error for {path}: {e}")
            raise e
        
        try:
            content = xmltodict.parse(resp.content.decode('utf-8'))
        except Exception as e:
             logger.error(f"XML Parse error for {path}: {e}")
             return {}, []

        multistatus = content.get('D:multistatus', {}) or content.get('multistatus', {})
        responses = multistatus.get('D:response', []) or multistatus.get('response', [])
        
        if isinstance(responses, dict):
            responses = [responses]
            
        for res in responses:
            href = unquote(res.get('D:href', '') or res.get('href', ''))
            clean_href = href.rstrip('/')
            
            propstat = res.get('D:propstat', {}) or res.get('propstat', {})
            if isinstance(propstat, list):
                propstat = propstat[0]
            prop = propstat.get('D:prop', {}) or propstat.get('prop', {})
            
            resourcetype = prop.get('D:resourcetype', {}) or prop.get('resourcetype', {})
            is_dir = 'D:collection' in resourcetype or 'collection' in resourcetype if resourcetype else False
            
            is_self = False
            if clean_href.rstrip('/') == path.rstrip('/'):
                is_self = True
            elif clean_href.endswith(path.rstrip('/')) and (len(clean_href) == len(path.rstrip('/')) or clean_href[-(len(path.rstrip('/'))+1)] == '/'):
                is_self = True

            mtime = prop.get('D:getlastmodified', '') or prop.get('getlastmodified', '')
            etag = prop.get('D:getetag', '') or prop.get('getetag', '')
            size = prop.get('D:getcontentlength', '0') or prop.get('getcontentlength', '0')

            entry = {"size": size, "mtime": mtime, "etag": etag, "is_dir": is_dir}
            
            if is_self:
                results[clean_href] = entry
                continue

            results[clean_href] = entry
            
            if is_dir:
                sub_path = href
                if href.startswith('http'):
                    try:
                        sub_path = urlparse(href).path
                    except:
                        sub_path = href.split(url.rstrip('/'))[-1]
                subdirs.append(sub_path)
                
        return results, subdirs

    @staticmethod
    def list_recursive(url, username, password, path, old_state=None, smart_scan=True, concurrency=10):
        mode_str = "Smart" if smart_scan else "Deep"
        logger.info(f"Starting {mode_str} WebDAV scan for {path} (Threads: {concurrency})")
        start_time = time.time()
        
        all_results = {}
        visited = set()
        visited_lock = threading.Lock()
        
        visited.add(path)
        
        # Init Session with Connection Pooling
        session = requests.Session()
        max_workers = concurrency
        adapter = HTTPAdapter(pool_connections=max_workers, pool_maxsize=max_workers, max_retries=3)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        futures = {}
        
        # Initial task
        f = executor.submit(WebDAVService._list_dir_worker, session, url, username, password, path)
        futures[f] = (path, 0)
        
        # Smart scan helper: Function to copy descendants
        def copy_descendants_from_old_state(skip_path):
            count = 0
            if not old_state: return 0
            
            # Simple prefix match (can be optimized if needed, but acceptable for now)
            prefix = skip_path + "/"
            for k, v in old_state.items():
                if k == skip_path: continue
                if k.startswith(prefix):
                    all_results[k] = v
                    count += 1
            return count
        
        try:
            while futures:
                done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                
                for fut in done:
                    p, depth = futures.pop(fut)
                    try:
                        res, subdirs = fut.result()
                        
                        # Add current dir results
                        all_results.update(res)
                        
                        # Logic for subdirs
                        if depth < 50: 
                            for sd_raw in subdirs:
                                sd_clean = sd_raw.rstrip('/')
                                
                                # Check lock
                                should_process = False
                                with visited_lock:
                                    if sd_clean not in visited:
                                        visited.add(sd_clean)
                                        should_process = True
                                
                                if should_process:
                                    # SMART SCAN LOGIC
                                    should_recurse = True
                                    
                                    if smart_scan and old_state and sd_clean in old_state and sd_clean in res:
                                        # Check if modified
                                        current_entry = res[sd_clean]
                                        old_entry = old_state[sd_clean]
                                        
                                        # Compare mtime
                                        cur_mtime = current_entry.get('mtime')
                                        old_mtime = old_entry.get('mtime')
                                        
                                        if cur_mtime and old_mtime and cur_mtime == old_mtime:
                                            # Match! Skip recursion
                                            logger.debug(f"SmartScan: Skipping unchanged {sd_clean}")
                                            should_recurse = False
                                            # We must copy descendants!
                                            # This happens in main thread, safe.
                                            copied = copy_descendants_from_old_state(sd_clean)
                                            # logger.debug(f"  -> Copied {copied} items")

                                    if should_recurse:
                                        # Submit new task
                                        new_f = executor.submit(WebDAVService._list_dir_worker, session, url, username, password, sd_raw)
                                        futures[new_f] = (sd_raw, depth + 1)
                                    
                    except Exception as e:
                        logger.error(f"Failed to scan {p}: {e}")
                        
        finally:
            executor.shutdown(wait=False)
            session.close()
            
        logger.info(f"WebDAV Scan finished in {time.time() - start_time:.2f}s. Scanned {len(visited)} dirs. Total: {len(all_results)}")
        return all_results

    @staticmethod
    def list_directory(url, username, password, path):
        # Keep this for the file picker UI (simple single-level list)
        base_url = url if url.endswith('/') else url + '/'
        
        joined = urljoin(base_url, path)
        if not joined.startswith(base_url.rstrip('/')):
            target_url = base_url + path.lstrip('/')
        else:
            target_url = joined
            
        if not target_url.endswith('/'): target_url += '/'
        
        auth_methods = [HTTPBasicAuth(username, password), HTTPDigestAuth(username, password)]
        headers = {'Depth': '1', 'User-Agent': 'WebDAV-Monitor-Premium'}
        
        for auth in auth_methods:
            try:
                resp = requests.request('PROPFIND', target_url, auth=auth, headers=headers, timeout=15, verify=False)
                if resp.status_code == 401: continue
                resp.raise_for_status()
                
                content = xmltodict.parse(resp.content.decode('utf-8'))
                multistatus = content.get('D:multistatus', {}) or content.get('multistatus', {})
                responses = multistatus.get('D:response', []) or multistatus.get('response', [])
                
                if isinstance(responses, dict):
                    responses = [responses]
                    
                items = []
                for res in responses:
                    href = unquote(res.get('D:href', '') or res.get('href', ''))
                    clean_href = href.rstrip('/')
                    
                    if clean_href.rstrip('/') == path.rstrip('/'): continue
                    if clean_href.endswith(path.rstrip('/')) and (len(clean_href) == len(path.rstrip('/')) or clean_href[-(len(path.rstrip('/'))+1)] == '/'):
                         continue

                    name = os.path.basename(clean_href) or clean_href
                    
                    propstat = res.get('D:propstat', {}) or res.get('propstat', {})
                    if isinstance(propstat, list): propstat = propstat[0]
                    prop = propstat.get('D:prop', {}) or propstat.get('prop', {})
                    resourcetype = prop.get('D:resourcetype', {}) or prop.get('resourcetype', {})
                    is_dir = 'D:collection' in resourcetype or 'collection' in resourcetype if resourcetype else False
                    
                    items.append({"name": name, "is_dir": is_dir, "path": clean_href})
                return items
            except:
                continue
        return []

class AlistService:
    @staticmethod
    def test_connection(url, username=None, password=None, token=None):
        try:
            base_url = url.rstrip('/')
            
            if not token:
                if not username or not password:
                    return False, "Username/Password required for login"
                
                logger.info(f"Logging in to Alist: {base_url}")
                resp = requests.post(f"{base_url}/api/auth/login", json={
                    "username": username,
                    "password": password
                }, timeout=15, verify=False)
                
                if resp.status_code == 404:
                    return False, f"API Not Found (404) at {base_url}. Check URL."
                
                resp.raise_for_status()
                data = resp.json()
                if data.get('code') != 200:
                    return False, f"Login Error: {data.get('message', 'Check credentials')}"
                token = data['data']['token']
            
            logger.info(f"Verifying Alist connectivity: {base_url}")
            headers = {"Authorization": token, "User-Agent": "WebDAV-Monitor-Premium"}
            resp = requests.post(f"{base_url}/api/fs/list", 
                headers=headers,
                json={"path": "/", "page": 1, "per_page": 1},
                timeout=15, verify=False
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 200:
                    return True, "Success"
                return False, f"Alist API Error ({data.get('code')}): {data.get('message')}"
            
            return False, f"Connectivity failed: HTTP {resp.status_code} {resp.reason}"
            
        except requests.exceptions.ConnectionError:
            return False, f"Connection Failed: Could not reach {url}"
        except Exception as e:
            logger.error(f"Alist Test Exception: {e}")
            return False, str(e)

    @staticmethod
    def get_token(url, username, password):
        try:
            resp = requests.post(f"{url.rstrip('/')}/api/auth/login", json={
                "username": username,
                "password": password
            }, timeout=10, verify=False)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 200:
                    return data['data']['token']
        except:
            pass
        return None

    @staticmethod
    def refresh_path(url, token, path):
        try:
            logger.info(f"Triggering Alist refresh for: {path}")
            resp = requests.post(f"{url.rstrip('/')}/api/fs/list", 
                headers={"Authorization": token, "User-Agent": "WebDAV-Monitor-Premium"},
                json={
                    "path": path,
                    "refresh": True,
                    "page": 1,
                    "per_page": 1
                }, timeout=60, verify=False
            )
            data = resp.json()
            return data.get('code') == 200
        except Exception as e:
            logger.error(f"Refresh failed for {path}: {e}")
            return False

    @staticmethod
    def list_directory(url, token, path):
        try:
            headers = {"Authorization": token, "User-Agent": "WebDAV-Monitor-Premium"}
            resp = requests.post(f"{url.rstrip('/')}/api/fs/list", 
                headers=headers,
                json={"path": path, "page": 1, "per_page": 200},
                timeout=15, verify=False
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 200:
                    files = data['data'].get('content') or []
                    return [{"name": f['name'], "is_dir": f['is_dir'], "path": os.path.join(path, f['name']), "size": f.get('size'), "mtime": f.get('modified')} for f in files]
        except Exception as e:
            logger.error(f"Alist list_directory failed: {e}")
        return []

    @staticmethod
    def _list_dir_rich_worker(session, url, token, path, refresh=False):
        results = {}
        subdirs = []
        headers = {"Authorization": token, "User-Agent": "WebDAV-Monitor-Premium"}
        
        page = 1
        while True:
            try:
                # Use session
                resp = session.post(f"{url.rstrip('/')}/api/fs/list", 
                    headers=headers,
                    json={"path": path, "page": page, "per_page": 200, "refresh": refresh},
                    timeout=60, verify=False
                )
                if resp.status_code != 200: break
                
                data = resp.json()
                if data.get('code') != 200:
                    # Log but don't break immediately if page 1 failed? 
                    # If page 1 fails, we raise.
                    if page == 1:
                        raise Exception(f"Alist API error: {data.get('message', 'Unknown')}")
                    break
                    
                content = data['data'].get('content') or []
                if not content: break
                
                for f in content:
                    full_path = os.path.join(path, f['name'])
                    mtime = f.get('modified')
                    sign = f.get('sign') or f.get('hash')
                    size = f.get('size')
                    is_dir = f['is_dir']
                    
                    results[full_path] = {"size": size, "mtime": mtime, "sign": sign, "is_dir": is_dir}
                    
                    if is_dir:
                        subdirs.append(full_path)
                
                total = data['data'].get('total', 0)
                if page * 200 >= total: break
                page += 1
            except Exception as e:
                logger.error(f"Error listing Alist path {path}: {e}")
                raise e
            
        return results, subdirs

    @staticmethod
    def list_recursive_rich(url, token, path, old_state=None, refresh=False, smart_scan=True, concurrency=10):
        mode_str = "Smart" if smart_scan else "Deep"
        logger.info(f"Starting {mode_str} Alist scan for {path} (Threads: {concurrency})")
        start_time = time.time()
        
        all_results = {}
        visited = set()
        visited_lock = threading.Lock()
        visited.add(path)
        
        # Init Session
        session = requests.Session()
        max_workers = concurrency
        adapter = HTTPAdapter(pool_connections=max_workers, pool_maxsize=max_workers, max_retries=3)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        futures = {}
        
        f = executor.submit(AlistService._list_dir_rich_worker, session, url, token, path, refresh)
        futures[f] = (path, 0)
        
        def copy_descendants_from_old_state(skip_path):
            count = 0
            if not old_state: return 0
            prefix = skip_path + "/"
            for k, v in old_state.items():
                if k == skip_path: continue
                if k.startswith(prefix):
                    all_results[k] = v
                    count += 1
            return count
        
        try:
            while futures:
                done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                for fut in done:
                    p, depth = futures.pop(fut)
                    try:
                        res, subdirs = fut.result()
                        all_results.update(res)
                        
                        if depth < 20:
                            for sd in subdirs:
                                
                                should_process = False
                                with visited_lock:
                                    if sd not in visited:
                                        visited.add(sd)
                                        should_process = True
                                        
                                if should_process:
                                    # SMART Logic
                                    should_recurse = True
                                    if smart_scan and old_state and sd in old_state and sd in res:
                                        cur_mtime = res[sd].get('mtime')
                                        old_mtime = old_state[sd].get('mtime')
                                        if cur_mtime and old_mtime and cur_mtime == old_mtime:
                                            logger.info(f"SmartScan: Skipping {sd} (Matches old state)")
                                            should_recurse = False
                                            copied = copy_descendants_from_old_state(sd)
                                            logger.info(f"SmartScan: Copied {copied} items for {sd}")
                                    
                                    if should_recurse:
                                        new_f = executor.submit(AlistService._list_dir_rich_worker, session, url, token, sd, refresh)
                                        futures[new_f] = (sd, depth + 1)
                    except Exception as e:
                        logger.error(f"Failed to scan {p}: {e}")
        finally:
            executor.shutdown(wait=False)
            session.close()
            
        logger.info(f"Alist Scan finished in {time.time() - start_time:.2f}s. Scanned {len(visited)} dirs. Total: {len(all_results)}")
        return all_results
