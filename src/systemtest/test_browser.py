from time import sleep
import requests
import pytest

from selenium import webdriver
from selenium.webdriver.support.ui import Select

from odinapi.utils import encrypt_util
from .level2_test_data import WRITE_URL, VERSION, get_test_data

PROJECT_NAME = 'testproject'


@pytest.fixture(scope='session')
def chrome():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = './node_modules/chromium/lib/chromium/chrome-linux/chrome'
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome('./node_modules/chromedriver/bin/chromedriver', options=chrome_options)
    yield driver
    driver.quit()


class TestBrowser:
    def test_main_page_is_up(self, odinapi_service, chrome):
        """Test that main page is up"""
        driver = chrome
        driver.get(odinapi_service)
        assert "Odin/SMR" in driver.title


@pytest.fixture
def lvl2data(odinapi_service):
    import_level2data(odinapi_service)
    yield
    delete_level2data(odinapi_service)


@pytest.fixture
def lvl2data_withoffset(odinapi_service):
    import_level2data(odinapi_service, offset=-1)
    yield
    delete_level2data(odinapi_service, offset=-1)


class TestLevel2Browser:
    '''test of level2 browser'''

    def get_lvl2page(self, driver, baseurl):
        driver.get("{}/level2".format(baseurl))
        return driver

    def test_main_page_is_up(self, odinapi_service, chrome, lvl2data):
        """Test that main page is up"""
        driver = self.get_lvl2page(chrome, odinapi_service)
        assert "Odin/SMR" in driver.title

    def test_selectors_displayed(self, odinapi_service, chrome, lvl2data):
        """test that project and freqmode selectors
           are displayed"""
        driver = self.get_lvl2page(chrome, odinapi_service)
        assert driver.find_element_by_id('select-project').is_displayed()
        assert driver.find_element_by_id('select-freqmode').is_displayed()

    def test_project_is_selectable(self, odinapi_service, chrome, lvl2data):
        """test that a project can be selected"""
        driver = self.get_lvl2page(chrome, odinapi_service)
        select = Select(driver.find_element_by_id('select-project'))
        options = []
        for option in select.options:
            options.append(option.get_attribute('value'))
        assert 'Choose project' in options
        assert 'development/testproject' in options

    def test_freqmode_is_selectable(self, odinapi_service, chrome, lvl2data):
        """test that when a project is selected freqmode is displayed
           and can also be selected"""
        driver = self.get_lvl2page(chrome, odinapi_service)
        select = Select(driver.find_element_by_id('select-project'))
        select.select_by_visible_text('development/testproject')
        assert driver.find_element_by_id('select-freqmode').is_displayed()
        select = Select(driver.find_element_by_id('select-freqmode'))
        options = []
        for option in select.options:
            options.append(option.get_attribute('value'))
        assert 'Choose freqmode' in options
        assert '1' in options

    def test_scan_get_selected(
        self, odinapi_service, chrome, lvl2data, lvl2data_withoffset,
    ):
        """test that a scan show up in the search table
           when doing a selection and that a plot of a level2 scan
           is shown if a link is clicked
           """
        driver = self.get_lvl2page(chrome, odinapi_service)
        select = Select(driver.find_element_by_id('select-project'))
        select.select_by_visible_text('development/testproject')
        select = Select(driver.find_element_by_id('select-freqmode'))
        select.select_by_visible_text('1')
        driver.find_element_by_name('start_date').send_keys('2015-01-12')
        driver.find_element_by_name('end_date').send_keys('2015-01-13')
        driver.find_element_by_name('offset').send_keys('1')
        driver.find_element_by_class_name('search-form-table').submit()
        assert (driver.find_element_by_id(
            'search-results').find_elements_by_tag_name(
                name='td')[0].text == '7014791071')
        test_ref = '/level2/development/testproject/1/7014791071'
        href = driver.find_element_by_id(
            'search-results').find_elements_by_xpath(
                "//a[@href='{0}']".format(test_ref))[0]
        href.click()
        driver.get("{}{}".format(odinapi_service, test_ref))
        sleep(1)
        header = driver.find_element_by_class_name('page-header')
        assert (
            header.text
            == 'Title: development, Project: testproject, Freqmode: 1, Scanid: 7014791071'  # noqa
        )
        plotsection = driver.find_element_by_id('alt-cross-section-plots')
        plottitles = set(
            plot.find_element_by_class_name('product-name').text for plot
            in plotsection.find_elements_by_class_name(
                'alt-cross-section-plot-product',
            )
        )
        assert plottitles == {
         'O3 / 501 GHz / 20 to 50 km',
         'N2O / 502 GHz / 20 to 50 km',
         'ClO / 501 GHz / 20 to 50 km',
        }

    def test_freqmode_list(self, odinapi_service, chrome):
        driver = self.get_lvl2page(chrome, odinapi_service)
        freqmode_div = driver.find_element_by_id('freqmodeInfoTable')
        assert freqmode_div is not None
        assert freqmode_div.find_elements_by_tag_name('table')


def import_level2data(host, offset=0):
    '''import level2 data'''
    data = get_test_data()
    data['L2I']['ScanID'] = data['L2I']['ScanID'] + offset
    datastring = encrypt_util.encode_level2_target_parameter(
        data['L2I']['ScanID'],
        data['L2I']['FreqMode'],
        PROJECT_NAME)
    url = WRITE_URL.format(host=host, version=VERSION, d=datastring)
    requests.delete(url)
    requests.post(url, json=data)


def delete_level2data(host, offset=0):
    '''delete level2 data'''
    data = get_test_data()
    data['L2I']['ScanID'] = data['L2I']['ScanID'] + offset
    datastring = encrypt_util.encode_level2_target_parameter(
        data['L2I']['ScanID'],
        data['L2I']['FreqMode'],
        PROJECT_NAME)
    url = WRITE_URL.format(host=host, version=VERSION, d=datastring)
    requests.delete(url)
