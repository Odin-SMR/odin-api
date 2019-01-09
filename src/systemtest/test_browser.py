'''test of browser'''
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
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        './dependencies/chromedriver',
        options=chrome_options
    )
    yield driver
    driver.quit()


@pytest.mark.usefixtures("dockercompose")
class TestBrowser():
    def test_main_page_is_up(self, chrome):
        """Test that main page is up"""
        driver = chrome
        driver.get("http://localhost:5000")
        assert "Odin/SMR" in driver.title


@pytest.fixture
def lvl2data():
    import_level2data()
    yield
    delete_level2data()


@pytest.fixture
def lvl2data_withoffset():
    import_level2data(offset=-1)
    yield
    delete_level2data(offset=-1)


@pytest.mark.usefixtures("dockercompose")
class TestLevel2Browser():
    '''test of level2 browser'''

    def test_main_page_is_up(self, chrome, lvl2data):
        """Test that main page is up"""
        driver = chrome
        driver.get("http://localhost:5000/level2")
        assert "Odin/SMR" in driver.title

    def test_selectors_displayed(self, chrome, lvl2data):
        """test that project and freqmode selectors
           are displayed"""
        driver = chrome
        driver.get("http://localhost:5000/level2")
        assert driver.find_element_by_id('select-project').is_displayed()
        assert driver.find_element_by_id('select-freqmode').is_displayed()

    def test_project_is_selectable(self, chrome, lvl2data):
        """test that a project can be selected"""
        driver = chrome
        driver.get("http://localhost:5000/level2")
        select = Select(driver.find_element_by_id('select-project'))
        options = []
        for option in select.options:
            options.append(option.get_attribute('value'))
        assert 'Choose project' in options
        assert 'development/testproject' in options

    def test_freqmode_is_selectable(self, chrome, lvl2data):
        """test that when a project is selected freqmode is displayed
           and can also be selected"""
        driver = chrome
        driver.get("http://localhost:5000/level2")
        select = Select(driver.find_element_by_id('select-project'))
        select.select_by_visible_text('development/testproject')
        assert driver.find_element_by_id('select-freqmode').is_displayed()
        select = Select(driver.find_element_by_id('select-freqmode'))
        options = []
        for option in select.options:
            options.append(option.get_attribute('value'))
        assert 'Choose freqmode' in options
        assert '1' in options

    def test_scan_get_selected(self, chrome, lvl2data, lvl2data_withoffset):
        """test that a scan show up in the search table
           when doing a selection and that a plot of a level2 scan
           is shown if a link is clicked
           """
        driver = chrome
        driver.get("http://localhost:5000/level2")
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
        driver.get("http://localhost:5000{0}".format(test_ref))
        sleep(1)
        assert (driver.find_elements_by_id(
            'alt-cross-section-plots')[0].find_elements_by_class_name(
                'product-name')[0].text == 'O3 / 501 GHz / 20 to 50 km')


def import_level2data(offset=0):
    '''import level2 data'''
    data = get_test_data()
    data['L2I']['ScanID'] = data['L2I']['ScanID'] + offset
    datastring = encrypt_util.encode_level2_target_parameter(
        data['L2I']['ScanID'],
        data['L2I']['FreqMode'],
        PROJECT_NAME)
    url = WRITE_URL.format(version=VERSION, d=datastring)
    requests.delete(url)
    requests.post(url, json=data)


def delete_level2data(offset=0):
    '''delete level2 data'''
    data = get_test_data()
    data['L2I']['ScanID'] = data['L2I']['ScanID'] + offset
    datastring = encrypt_util.encode_level2_target_parameter(
        data['L2I']['ScanID'],
        data['L2I']['FreqMode'],
        PROJECT_NAME)
    url = WRITE_URL.format(version=VERSION, d=datastring)
    requests.delete(url)
