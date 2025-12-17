import json
import os

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from odinapi.utils import encrypt_util

from .level2_test_data import VERSION, get_test_data

pytestmark = pytest.mark.system
PROJECT_NAME = "testproject"
WRITE_URL = "{host}/rest_api/{version}/level2?d={d}"


@pytest.fixture(scope="session")
def chrome():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.path.abspath(
        "./node_modules/chromium/lib/chromium/chrome-linux/chrome"
    )
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    service = ChromeService(
        os.path.abspath("./node_modules/chromedriver/bin/chromedriver")
    )
    driver = webdriver.Chrome(
        service=service,
        options=chrome_options,
    )
    driver.implicitly_wait(4)
    yield driver
    driver.quit()


class TestBrowser:
    def test_main_page_is_up(self, selenium_app, chrome):
        """Test that main page is up"""
        driver = chrome
        driver.get(selenium_app)
        assert "Odin/SMR" in driver.title


@pytest.fixture
def lvl2data(selenium_app):
    import_level2data(selenium_app)
    yield
    delete_level2data(selenium_app)


@pytest.fixture
def lvl2data_withoffset(selenium_app):
    import_level2data(selenium_app, offset=-1)
    yield
    delete_level2data(selenium_app, offset=-1)


class TestLevel2Browser:
    """test of level2 browser"""

    def get_lvl2page(self, driver, baseurl):
        driver.get("{}/level2".format(baseurl))
        return driver

    def test_main_page_is_up(self, selenium_app, chrome, lvl2data):
        """Test that main page is up"""
        driver = self.get_lvl2page(chrome, selenium_app)
        assert "Odin/SMR" in driver.title

    def test_selectors_displayed(self, selenium_app, chrome, lvl2data):
        """test that project and freqmode selectors
        are displayed"""
        driver = self.get_lvl2page(chrome, selenium_app)
        assert driver.find_element(By.ID, "select-project").is_displayed()
        assert driver.find_element(By.ID, "select-freqmode").is_displayed()

    def test_project_is_selectable(self, selenium_app, chrome, lvl2data):
        """test that a project can be selected"""
        driver = self.get_lvl2page(chrome, selenium_app)
        select = Select(driver.find_element(By.ID, "select-project"))
        options = []
        for option in select.options:
            options.append(option.get_attribute("value"))
        assert "Choose project" in options
        assert "development/testproject" in options

    def test_freqmode_is_selectable(self, selenium_app, chrome, lvl2data):
        """test that when a project is selected freqmode is displayed
        and can also be selected"""
        driver = self.get_lvl2page(chrome, selenium_app)
        select = Select(driver.find_element(By.ID, "select-project"))
        select.select_by_visible_text("development/testproject")
        assert driver.find_element(By.ID, "select-freqmode").is_displayed()
        select = Select(driver.find_element(By.ID, "select-freqmode"))
        options = []
        for option in select.options:
            options.append(option.get_attribute("value"))
        assert "Choose freqmode" in options
        assert "1" in options

    def test_scan_get_selected(
        self,
        selenium_app,
        chrome,
        lvl2data,
        lvl2data_withoffset,
    ):
        """test that a scan show up in the search table
        when doing a selection and that a plot of a level2 scan
        is shown if a link is clicked
        """
        driver = self.get_lvl2page(chrome, selenium_app)
        select = Select(driver.find_element(By.ID, "select-project"))
        select.select_by_visible_text("development/testproject")
        select = Select(driver.find_element(By.ID, "select-freqmode"))
        select.select_by_visible_text("1")
        driver.find_element(By.NAME, "start_date").send_keys("2015-01-12")
        driver.find_element(By.NAME, "end_date").send_keys("2015-01-13")
        driver.find_element(By.NAME, "offset").send_keys("1")

        driver.find_element(By.CLASS_NAME, "search-form-table").submit()
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#search-results td")) > 0
        )
        search_results = driver.find_element(By.ID, "search-results")
        first_td = search_results.find_elements(By.TAG_NAME, "td")[0]
        assert first_td.text == "7014791071"

        test_ref = "/level2/development/testproject/1/7014791071"
        href = driver.find_element(By.ID, "search-results").find_elements(
            By.XPATH, "//a[@href='{0}']".format(test_ref)
        )[0]
        href.click()
        driver.get("{}{}".format(selenium_app, test_ref))
        header = driver.find_element(By.CLASS_NAME, "page-header")
        assert (
            header.text
            == "Title: development, Project: testproject, Freqmode: 1, Scanid: 7014791071"  # noqa
        )
        plotsection = driver.find_element(By.ID, "alt-cross-section-plots")
        plottitles = set(
            plot.find_element(By.CLASS_NAME, "product-name").text
            for plot in plotsection.find_elements(
                By.CLASS_NAME,
                "alt-cross-section-plot-product",
            )
        )
        assert plottitles == {
            "O3 / 501 GHz / 20 to 50 km",
            "N2O / 502 GHz / 20 to 50 km",
            "ClO / 501 GHz / 20 to 50 km",
        }

    def test_freqmode_list(self, selenium_app, chrome):
        driver = self.get_lvl2page(chrome, selenium_app)
        freqmode_div = driver.find_element(By.ID, "freqmodeInfoTable")
        assert freqmode_div is not None
        assert freqmode_div.find_elements(By.TAG_NAME, "table")


def import_level2data(host, offset=0):
    """import level2 data"""
    data = get_test_data()
    data["L2I"]["ScanID"] = data["L2I"]["ScanID"] + offset
    datastring = encrypt_util.encode_level2_target_parameter(
        data["L2I"]["ScanID"], data["L2I"]["FreqMode"], PROJECT_NAME
    )
    url = WRITE_URL.format(host=host, version=VERSION, d=datastring)
    requests.delete(url)
    requests.post(
        url,
        data=json.dumps(data, allow_nan=True),
        headers={"Content-Type": "application/json"},
    )


def delete_level2data(host, offset=0):
    """delete level2 data"""
    data = get_test_data()
    data["L2I"]["ScanID"] = data["L2I"]["ScanID"] + offset
    datastring = encrypt_util.encode_level2_target_parameter(
        data["L2I"]["ScanID"], data["L2I"]["FreqMode"], PROJECT_NAME
    )
    url = WRITE_URL.format(host=host, version=VERSION, d=datastring)
    requests.delete(url)
