# --------------------------------------------------------------------------
# HTML loader module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging
import time
import os
import uuid

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

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
        self.driver = None
        self.chromedriver_path = settings.CHROMEDRIVER_PATH
        self.timeout = settings.HTML_LOAD_TIMEOUT
        self.retries = settings.HTML_LOAD_RETRIES

    def _init_driver(self) -> bool:
        try:            
            # service = ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            service = webdriver.ChromeService(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            
            # User Agent 설정은 주석 처리 (안정성을 위해)
            # self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            #     "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            # })
            
            # 메모리 사용량 모니터링도 주석 처리 (안정성을 위해)
            # self.driver.execute_cdp_cmd('Memory.startSampling', {})
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False

    # TODO : 단축 url이나 리디렉션 url인 경우의 분기 처리

    def _normalize_url(self, url: str) -> str:
        if url.startswith("http://"):
            protocol = "http://"
            rest = url[7:]
        elif url.startswith("https://"):
            protocol = "https://"
            rest = url[8:]
        else:
            protocol = ""
            rest = url
        if not rest.startswith("www."):
            rest = "www." + rest
        if not rest.endswith("/") and ("?" not in rest and "#" not in rest):
            rest += "/"
        return protocol + rest

    def __load_url(self, url: str) -> str:
        url = self._normalize_url(url)
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
                
                time.sleep(1.5)
                return self.driver.page_source
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if self.driver:
                    try:
                        # 메모리 정리는 주석 처리 (안정성을 위해)
                        # self.driver.execute_cdp_cmd('Memory.forciblyPurgeJavaScriptMemory', {})
                        self.driver.quit()
                    except Exception:
                        pass
                    self.driver = None
                if attempt == self.retries - 1:
                    raise BackendExceptions(
                        f"Failed to load URL after {self.retries} attempts"
                    )
        return ""

    def __del__(self):
        if self.driver:
            try:
                # 메모리 정리는 주석 처리 (안정성을 위해)
                # self.driver.execute_cdp_cmd('Memory.forciblyPurgeJavaScriptMemory', {})
                self.driver.quit()
            except Exception:
                pass

    @staticmethod
    def get_instance():
        return HTMLLoader()
