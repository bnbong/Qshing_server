# --------------------------------------------------------------------------
# HTML loader module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging
import time

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup  # type: ignore

from src.qshing_server.core.exceptions import BackendExceptions


logger = logging.getLogger("main")


class HTMLLoader:
    def __init__(self, url: str, timeout: int = 30):
        self.url = url
        self.timeout = timeout

    def __attach_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # No GUI
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )
        logger.info("Driver attached")
        return driver

    def __load_url(self, url: str):
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
            raise
        except Exception as e:
            logger.error(f"Error loading URL {url}: {e}")
            raise

    def _load(self):
        self.driver = self.__attach_driver()
        try:
            final_url = self.__load_url(self.url)
            time.sleep(2)  # wait for page rendering

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            urls = [final_url]
            html_content = str(soup)

            logger.info("HTML loaded successfully")
            return urls, html_content

        except Exception as e:
            logger.error(f"Error in _load: {e}")
            raise BackendExceptions(e)
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver closed")

    @staticmethod
    def load(url: str):
        try:
            loader = HTMLLoader(url)
            return loader._load()
        except Exception as e:
            logger.error(f"Error loading HTML: {e}")
            raise BackendExceptions(e)
