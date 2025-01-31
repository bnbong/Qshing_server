# --------------------------------------------------------------------------
# HTML loader module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.qshing_server.core.config import settings
from src.qshing_server.core.exceptions import BackendExceptions

logger = logging.getLogger("main")


class HTMLLoader:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--remote-debugging-port=9222")
        self.chrome_options.add_argument("--disable-software-rasterizer")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-background-networking")
        self.driver = None
        self.timeout = settings.HTML_LOAD_TIMEOUT
        self.retries = settings.HTML_LOAD_RETRIES

    def _init_driver(self) -> bool:
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.chrome_options,
            )
            self.driver.set_page_load_timeout(self.timeout)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False

    def __load_url(self, url: str) -> str:
        try:
            if not (url.startswith("http://") or url.startswith("https://")):
                # Try HTTP first
                try:
                    http_url = f"http://{url}"
                    self.driver.get(http_url)
                    return http_url
                except TimeoutException:
                    # If HTTP fails, try HTTPS
                    https_url = f"https://{url}"
                    self.driver.get(https_url)
                    return https_url
            else:
                self.driver.get(url)
                return url
        except TimeoutException:
            logger.error(f"Timeout while loading URL: {url}")
            raise BackendExceptions("Timeout while loading URL")
        except Exception as e:
            logger.error(f"Error loading URL {url}: {e}")
            raise BackendExceptions(e)

    def load(self, url: str) -> str | None:
        for attempt in range(self.retries):
            try:
                if not self.driver:
                    if not self._init_driver():
                        raise BackendExceptions("Failed to initialize WebDriver")

                url = self.__load_url(url)
                self.driver.get(url)
                time.sleep(3)
                return self.driver.page_source
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                if attempt == self.retries - 1:
                    raise BackendExceptions(
                        f"Failed to load URL after {self.retries} attempts"
                    )
        return ""

    def __del__(self):
        if self.driver:
            self.driver.quit()

    @staticmethod
    def get_instance():
        return HTMLLoader()
