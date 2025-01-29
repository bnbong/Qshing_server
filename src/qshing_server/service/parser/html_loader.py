# --------------------------------------------------------------------------
# HTML loader module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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

    @staticmethod
    def load(url: str):
        try:
            loader = HTMLLoader(url)
            return loader._load()
        except Exception as e:
            logger.error(f"Error loading HTML: {e}")
            raise BackendExceptions(e)

    def _load(self):
        driver = self.__attach_driver()
        driver.get(self.url)
        driver.implicitly_wait(self.timeout)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        urls = [self.url]
        html_content = str(soup)

        # for a_tag in soup.find_all('a', href=True):
        #     urls.append(a_tag['href'])
        # for a_tag in soup.find_all('link', href=True):
        #     urls.append(a_tag['href'])

        logger.info("HTML loaded")
        driver.quit()

        return urls, html_content
