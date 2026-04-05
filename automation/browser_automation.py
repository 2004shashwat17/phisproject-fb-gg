import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# automatically download matching chromedriver
from webdriver_manager.chrome import ChromeDriverManager

class BrowserAutomation:
    def __init__(self, headless=True, proxy=None, user_data_dir=None, profile_directory=None):
        self.headless = headless
        self.proxy = proxy
        self.user_data_dir = user_data_dir
        self.profile_directory = profile_directory
        self.driver = None
        self.wait = None

    def _build_options(self):
        options = Options()
        # headless
        if self.headless:
            options.add_argument('--headless=new')
        # user agent (example)
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/115.0.0.0 Safari/537.36'
        )
        # disable common automation flags
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        # hide webdriver switch
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        # proxy support
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
        # optionally use existing Chrome profile
        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
        if self.profile_directory:
            options.add_argument(f"--profile-directory={self.profile_directory}")
        return options

    def start(self):
        opts = self._build_options()
        # use webdriver_manager so we always have a matching driver version
        raw_path = ChromeDriverManager().install()
        # webdriver_manager sometimes returns path to LICENSE/THIRD_PARTY_NOTICES
        # instead of the binary; correct it manually if necessary.
        driver_path = raw_path
        if driver_path.endswith('THIRD_PARTY_NOTICES.chromedriver') or driver_path.endswith('LICENSE.chromedriver'):
            driver_path = os.path.join(os.path.dirname(driver_path), 'chromedriver')
        # debug output
        print(f"Using chromedriver binary at {driver_path}")
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=opts)
        # run a small script in every new page to hide webdriver and other tell‑tale signs
        try:
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        window.chrome = window.chrome || {};
                        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                        Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
                    """
                }
            )
        except Exception:
            pass
        # implicit wait might help
        self.driver.implicitly_wait(2)
        self.wait = WebDriverWait(self.driver, 10)
        return self

    def navigate(self, url):
        if not self.driver:
            raise RuntimeError('Driver is not initialized. Call start() first.')
        self.driver.get(url)
        # wait for document.readyState
        self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        return self

    def fill_input(self, selector, value):
        try:
            elem = self.wait_for_element(selector)
            elem.clear()
            elem.send_keys(value)
        except Exception as e:
            raise RuntimeError(f'Error filling input {selector}: {e}')
        return self

    def click(self, selector):
        try:
            elem = self.wait_for_element(selector)
            elem.click()
        except Exception as e:
            raise RuntimeError(f'Error clicking {selector}: {e}')
        return self

    def wait_for_element(self, selector, timeout=10):
        if not self.driver:
            raise RuntimeError('Driver is not initialized. Call start() first.')
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except Exception as e:
            raise RuntimeError(f'Element {selector} not found after {timeout}s: {e}')

    def get_page_source(self):
        return self.driver.page_source if self.driver else None

    def get_current_url(self):
        return self.driver.current_url if self.driver else None

    def get_cookies(self):
        return self.driver.get_cookies() if self.driver else []

    def load_cookies(self, cookies, url='https://www.google.com'):
        """Load provided cookie list into the browser after navigating to `url`.

        Cookies should be a list of dicts as returned by Selenium's
        `driver.get_cookies()`.  Some attributes may not be accepted by
        Selenium; the method will clean them if necessary.
        """
        if not self.driver:
            raise RuntimeError('Driver is not initialized. Call start() first.')
        # navigate to base domain so cookies can be set
        self.driver.get(url)
        for c in cookies:
            try:
                self.driver.add_cookie(c)
            except Exception:
                # try removing unexpected keys
                allowed = {'name','value','domain','path','expiry','secure','httpOnly'}
                small = {k:v for k,v in c.items() if k in allowed}
                try:
                    self.driver.add_cookie(small)
                except Exception:
                    pass
        return self

    def save_screenshot(self, filename):
        if self.driver:
            self.driver.save_screenshot(filename)
            return True
        return False

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            self.wait = None
