import requests
import xmltodict
import logging
import json
import os
import time
import urllib3
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

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
    def list_recursive(url, username, password, path, old_state=None, visited=None, depth=0):
        if visited is None: visited = set()
        
        if depth > 20:
            logger.warning(f"Max depth reached at {path}. Stopping recursion.")
            return {}
            
        if path in visited:
            logger.warning(f"Circular reference detected at {path}. Skipping.")
            return {}
        visited.add(path)

        from urllib.parse import urljoin, unquote
        results = {}
        
        base_url = url if url.endswith('/') else url + '/'
        
        if path.startswith('http'):
            target_url = path
        else:
            joined = urljoin(base_url, path)
            if not joined.startswith(base_url.rstrip('/')):
                target_url = base_url + path.lstrip('/')
            else:
                target_url = joined
        
        auth = (username, password)
        headers = {
            'Depth': '1',
            'User-Agent': 'WebDAV-Monitor-Premium',
            'Accept': 'application/xml, text/xml'
        }
        
        try:
            resp = requests.request('PROPFIND', target_url, auth=auth, headers=headers, timeout=30, verify=False)
            if resp.status_code == 401:
                resp = requests.request('PROPFIND', target_url, auth=HTTPDigestAuth(username, password), headers=headers, timeout=30, verify=False)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"WebDAV scan error for {path}: {e}")
            if depth == 0:
                raise Exception(f"WebDAV connection failed: {e}")
            return {}
        
        content = xmltodict.parse(resp.content.decode('utf-8'))
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

            if is_dir:
                should_recurse = True
                
                if old_state and clean_href in old_state:
                    old_entry = old_state[clean_href]
                    old_mtime = old_entry.get('mtime')
                    old_etag = old_entry.get('etag')
                    
                    match = False
                    if mtime and old_mtime and mtime == old_mtime:
                        match = True
                    
                    if match:
                        logger.info(f"  [SmartScan] Skipping unchanged dir: {clean_href} (mtime: {mtime})")
                        should_recurse = False
                        
                        count = 0
                        prefix = clean_href + "/"
                        results[clean_href] = entry
                        
                        for k, v in old_state.items():
                            if k == clean_href: continue
                            if k.startswith(prefix):
                                results[k] = v
                                count += 1

                if should_recurse:
                    sub_path = href
                    if href.startswith('http'):
                        try:
                            from urllib.parse import urlparse
                            sub_path = urlparse(href).path
                        except:
                            sub_path = href.split(url.rstrip('/'))[-1]
                    
                    if sub_path.rstrip('/') == path.rstrip('/'):
                         continue

                    logger.info(f"  [WebDAV] -> Dir: {sub_path}")
                    time.sleep(0.05)
                    results.update(WebDAVService.list_recursive(url, username, password, sub_path, old_state, visited, depth + 1))
            else:
                results[clean_href] = entry
                    
        return results

    @staticmethod
    def list_directory(url, username, password, path):
        from urllib.parse import urljoin, unquote
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
                }, timeout=30, verify=False
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
    def list_recursive_rich(url, token, path, old_state=None, visited=None, depth=0, refresh=False):
        if visited is None: visited = set()
        
        if depth > 20:
            logger.warning(f"Max depth reached at {path}. Stopping recursion.")
            return {}
            
        if path in visited:
            logger.warning(f"Circular reference detected at {path}. Skipping.")
            return {}
        visited.add(path)

        results = {}
        headers = {"Authorization": token, "User-Agent": "WebDAV-Monitor-Premium"}
        
        if refresh:
            logger.info(f"Force refreshing source path: {path}")

        page = 1
        while True:
            resp = requests.post(f"{url.rstrip('/')}/api/fs/list", 
                headers=headers,
                json={"path": path, "page": page, "per_page": 200, "refresh": refresh},
                timeout=30, verify=False
            )
            if resp.status_code != 200:
                break
                
            data = resp.json()
            if data.get('code') != 200:
                if depth == 0:
                    raise Exception(f"Alist API error: {data.get('message', 'Unknown')}")
                break
                
            content = data['data'].get('content') or []
            if not content:
                break
                
            for f in content:
                full_path = os.path.join(path, f['name'])
                
                mtime = f.get('modified')
                sign = f.get('sign') or f.get('hash')
                size = f.get('size')
                is_dir = f['is_dir']
                
                entry = {"size": size, "mtime": mtime, "sign": sign, "is_dir": is_dir}
                results[full_path] = entry
                
                if is_dir:
                    should_recurse = True
                    if old_state and full_path in old_state:
                        old_entry = old_state[full_path]
                        old_mtime = old_entry.get('mtime')
                        if mtime and old_mtime and mtime == old_mtime:
                            logger.info(f"  [SmartScan] Skipping unchanged dir: {full_path} (mtime: {mtime})")
                            should_recurse = False
                            
                            count = 0
                            prefix = full_path + "/"
                            for k, v in old_state.items():
                                if k == full_path: continue
                                if k.startswith(prefix):
                                    results[k] = v
                                    count += 1
                    
                    if should_recurse:
                        logger.info(f"  [Alist] -> Dir: {full_path}")
                        time.sleep(0.05)
                        results.update(AlistService.list_recursive_rich(url, token, full_path, old_state, visited, depth + 1, refresh))
                
            
            total = data['data'].get('total', 0)
            if page * 200 >= total:
                break
            page += 1
            
        return results
