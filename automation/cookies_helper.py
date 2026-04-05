import pickle
import json
import os
import re
import time

AUTH_COOKIE_NAMES = {'c_user', 'xs', 'fr', 'datr', 'sb', 'wd', 'spin', 'presence'}


def parse_cookies(selenium_cookies):
    """Convert Selenium cookies to serializable format

    Args:
        selenium_cookies: List from driver.get_cookies()

    Returns:
        List of dicts with name, value, domain, path, expiry, secure, httpOnly
    """
    parsed = []
    for c in selenium_cookies or []:
        parsed.append({
            'name': c.get('name'),
            'value': c.get('value'),
            'domain': c.get('domain'),
            'path': c.get('path'),
            'expiry': c.get('expiry'),
            'secure': c.get('secure', False),
            'httpOnly': c.get('httpOnly', False),
        })
    return parsed


def cookies_to_netscape(cookies):
    """Convert cookie dicts to Netscape format string for curl"""
    lines = ["# Netscape HTTP Cookie File"]
    for c in cookies:
        name = c.get('name', '')
        value = c.get('value', '')
        domain = c.get('domain', '')
        path = c.get('path', '/')
        secure = 'TRUE' if c.get('secure') else 'FALSE'
        expiry = str(int(c.get('expiry', 0))) if c.get('expiry') else '0'
        # domain field format: with leading dot if domain starts with
        host_only = 'FALSE' if domain.startswith('.') else 'TRUE'
        lines.append('\t'.join([domain, host_only, path, secure, expiry, name, value]))
    return '\n'.join(lines)


def save_cookies_to_file(cookies, filename):
    """Save cookies to file in multiple formats:
    - Pickle (.pkl) for Python
    - JSON (.json) for readability
    - Netscape format (.txt) for curl/wget
    """
    base, ext = os.path.splitext(filename)
    cookie_list = parse_cookies(cookies)

    def _write(path, data, mode='wb'):
        with open(path, mode) as f:
            f.write(data)

    if ext.lower() in ['.pkl', '.pickle']:
        _write(filename, pickle.dumps(cookie_list))
        return
    if ext.lower() == '.json':
        _write(filename, json.dumps(cookie_list, indent=2).encode('utf-8'))
        return
    if ext.lower() in ['.txt', '.netscape']:
        _write(filename, cookies_to_netscape(cookie_list).encode('utf-8'))
        return
    # no extension or unrecognized: save all three
    _write(base + '.pkl', pickle.dumps(cookie_list))
    _write(base + '.json', json.dumps(cookie_list, indent=2).encode('utf-8'))
    _write(base + '.txt', cookies_to_netscape(cookie_list).encode('utf-8'))


def load_cookies_from_file(filename):
    """Load cookies from file (auto-detect format)"""
    if not os.path.exists(filename):
        raise FileNotFoundError(filename)
    _, ext = os.path.splitext(filename)
    if ext.lower() in ['.pkl', '.pickle']:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    content = open(filename, 'r', encoding='utf-8').read()
    if ext.lower() == '.json':
        return json.loads(content)
    # assume netscape or plain text
    cookies = []
    for line in content.splitlines():
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) < 7:
            continue
        domain, host_only, path, secure, expiry, name, value = parts[:7]
        cookies.append({
            'domain': domain,
            'path': path,
            'secure': secure.upper() == 'TRUE',
            'expiry': int(expiry) if expiry.isdigit() else None,
            'name': name,
            'value': value,
        })
    return cookies


def extract_auth_cookies(cookies, domains=None):
    """Filter only authentication-relevant cookies
    (c_user, xs, fr, datr, etc.)
    """
    if domains is None:
        domains = ['.facebook.com', 'facebook.com']
    auth = []
    for c in cookies:
        name = c.get('name', '')
        domain = c.get('domain', '')
        if name in AUTH_COOKIE_NAMES and any(d in domain for d in domains):
            auth.append(c)
    return auth


def verify_google_cookies(filepath: str) -> dict:
    """Check whether cookies stored in `filepath` still log in to Google.

    Returns a dictionary with keys:
    - success: bool
    - logged_in: bool
    - url: current url
    - title: page title
    - error: optional error message
    """
    from automation.browser_automation import BrowserAutomation
    try:
        cookies = load_cookies_from_file(filepath)
    except Exception as e:
        return {"success": False, "error": f"could not read cookies: {e}"}

    manager = BrowserAutomation(headless=False)
    try:
        manager.start()
        manager.load_cookies(cookies, url='https://www.google.com')
        manager.navigate('https://myaccount.google.com/')
        # give the page some time to possibly redirect past the signin intermediary
        for _ in range(6):
            time.sleep(1)
            curr = manager.driver.current_url or ''
            # if we've been bounced to signin with continue query, allow further wait
            if 'signin' in curr.lower() and 'continue=' in curr.lower():
                continue
            break
        else:
            curr = manager.driver.current_url or ''
        title = manager.driver.title or ''
        # also inspect page text for account indicator
        src = manager.driver.page_source.lower() or ''
        logged_in = 'signin' not in curr.lower() or 'my account' in title.lower() or 'my account' in src
        return {"success": True, "logged_in": logged_in, "url": curr, "title": title}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try:
            manager.close()
        except Exception:
            pass


def verify_google_profile(user_data_dir: str, profile_directory: str = 'Default') -> dict:
    """Launch Chrome with a real profile and confirm login state.

    user_data_dir - path to Chrome/User Data folder (parent of 'Default', 'Profile 1', etc.)
    profile_directory - name of the profile subdirectory (Default by default).

    Returns same dictionary as verify_google_cookies.
    """
    from automation.browser_automation import BrowserAutomation
    result: dict = {"success": False}
    try:
        manager = BrowserAutomation(headless=False,
                                     user_data_dir=user_data_dir,
                                     profile_directory=profile_directory)
        manager.start()
        manager.navigate('https://myaccount.google.com/')
        time.sleep(2)
        curr = manager.driver.current_url or ''
        title = manager.driver.title or ''
        src = manager.driver.page_source.lower() or ''
        logged_in = 'signin' not in curr.lower() or 'my account' in title.lower() or 'my account' in src
        result = {"success": True, "logged_in": logged_in, "url": curr, "title": title}
    except Exception as e:
        result = {"success": False, "error": str(e)}
    finally:
        try:
            manager.close()
        except Exception:
            pass
    return result
