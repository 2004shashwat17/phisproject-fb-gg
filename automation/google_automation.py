from automation.browser_automation import BrowserAutomation
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class GoogleSeleniumManager:
    """Light wrapper around BrowserAutomation tailored for the 2026-style
    Google sign-in flow.  Methods are intentionally simple so that the upper
    layers (API endpoints) can orchestrate the multi-step process.

    The class keeps a reference to the underlying bot so callers can still
    perform arbitrary `bot.driver` operations if necessary (e.g. screenshots).
    """

    def __init__(self, headless: bool = True):
        self.bot = BrowserAutomation(headless=headless)
        self.wait: WebDriverWait | None = None

    def start(self):
        self.bot.start()
        self.wait = self.bot.wait
        return self

    def navigate_to_login(self):
        # some accounts flows redirect to /signin/v2/identifier automatically
        self.bot.navigate('https://accounts.google.com/signin')
        # ensure we have a fresh wait reference
        self.wait = self.bot.wait
        return self

    def enter_email(self, email: str):
        if not self.wait:
            raise RuntimeError('manager.start() must be called first')
        # field id is stable (identifierId)
        email_field = self.wait.until(EC.presence_of_element_located((By.ID, 'identifierId')))
        email_field.clear()
        email_field.send_keys(email)
        # click "Next"
        nxt = self.wait.until(EC.element_to_be_clickable((By.ID, 'identifierNext')))
        nxt.click()
        # after clicking Next, wait for the password input to appear (or just a URL change)
        try:
            self.wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        except Exception:
            # if it doesn't appear, it's fine; detect_google_page will handle unknown
            pass
        return self

    def enter_password(self, password: str):
        if not self.wait:
            raise RuntimeError('manager.start() must be called first')
        # wait for password input to appear (sometimes delayed)
        try:
            pwd = self.wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        except Exception:
            # fall back to generic selector
            pwd = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type=password]')))
        pwd.clear()
        pwd.send_keys(password)
        # click the continue button
        btn = self.wait.until(EC.element_to_be_clickable((By.ID, 'passwordNext')))
        btn.click()
        # after click wait for URL to change or password field disappear
        try:
            self.wait.until(lambda d: 'signin' not in d.current_url.lower())
        except Exception:
            pass
        return self

    def get_qr_code(self) -> str | None:
        """If a QR code is displayed (e.g. for authenticator setup) return a
        base64 screenshot of the first <img> element found.  Otherwise return
        None.  """
        try:
            img = self.bot.driver.find_element(By.TAG_NAME, 'img')
            return img.screenshot_as_base64
        except Exception:
            return None

    def submit_2fa(self, code: str):
        """Attempt to locate a 2‑step verification input and submit the code."""
        if not self.wait:
            raise RuntimeError('manager.start() must be called first')
        # there are multiple possible names/ids depending on the challenge type
        try:
            inp = self.wait.until(EC.presence_of_element_located((By.NAME, 'code')))
        except Exception:
            try:
                inp = self.wait.until(EC.presence_of_element_located((By.NAME, 'smsVerificationCode')))
            except Exception:
                inp = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'input')))
        inp.clear()
        inp.send_keys(code)
        # click continue/next button
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.ID, 'totpNext')))
        except Exception:
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH,
                "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'next') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'verify')]")))
        btn.click()
        return self

    def current_page(self) -> str:
        """Heuristic detection of what the Google login page is currently
        showing, returning one of: 'email','password','2fa','qr','success', or
        'unknown'.  """
        try:
            url = (self.bot.driver.current_url or '').lower()
            src = (self.bot.driver.page_source or '').lower()
        except Exception:
            return 'unknown'

        if 'signin/v2/challenge/pwd' in url or 'password' in src:
            return 'password'
        # various flavors of two‑factor challenges including SMS/code, push
        if ('challenge/selection' in url or '2sv' in url or
            'enter your code' in src or 'verify' in src or
            'open the gmail app' in src or 'notification to your' in src or
            'tap yes' in src):
            return '2fa'
        if 'qr' in src and 'scan' in src:
            return 'qr'
        if 'accounts.google.com/signin' not in url:
            return 'success'
        return 'unknown'

    def destroy_cookies(self):
        # reuse the generic cookie removal script imported from api; callers can
        # also call automation.api.destroy_all_cookie_popups directly
        from automation.api import cookie_js
        try:
            self.bot.driver.execute_script(cookie_js)
        except Exception:
            pass
        return self
