'''test of browser'''
import unittest
from time import sleep
import requests
import pytest

from selenium import webdriver
from selenium.webdriver.support.ui import Select

from odinapi.utils import encrypt_util
from .level2_test_data import WRITE_URL, VERSION, get_test_data
from .testdefs import system


PROJECT_NAME = 'testproject'


@system
@pytest.mark.usefixtures("dockercompose")
class TestBrowser(unittest.TestCase):
    '''test of browser'''
    def setUp(self):
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()

    def test_main_page_is_up(self):
        """Test that main page is up"""
        driver = self.driver
        driver.get("http://localhost:5000")
        assert "Odin/SMR" in driver.title


@system
@pytest.mark.usefixtures("dockercompose")
class TestLevel2Browser(unittest.TestCase):
    '''test of level2 browser'''
    def setUp(self):
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()
        delete_level2data()
        delete_level2data(offset=-1)

    def test_main_page_is_up(self):
        """Test that main page is up"""
        driver = self.driver
        driver.get("http://localhost:5000/level2")
        assert "Odin/SMR" in driver.title

    def test_selectors_displayed(self):
        """test that project and freqmode selectors
           are displayed"""
        driver = self.driver
        driver.get("http://localhost:5000/level2")
        assert driver.find_element_by_id('select-project').is_displayed()
        assert driver.find_element_by_id('select-freqmode').is_displayed()

    def test_project_is_selectable(self):
        """test that a project can be selected"""
        import_level2data()
        driver = self.driver
        driver.get("http://localhost:5000/level2")
        select = Select(driver.find_element_by_id('select-project'))
        options = []
        for option in select.options:
            options.append(option.get_attribute('value'))
        assert 'Choose project' in options
        assert 'development/testproject' in options

    def test_freqmode_is_selectable(self):
        """test that when a project is selected freqmode is displayed
           and can also be selected"""
        import_level2data()
        driver = self.driver
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

    def test_scan_get_selected(self):
        """test that a scan show up in the search table
           when doing a selection and that a plot of a level2 scan
           is shown if a link is clicked
           """
        import_level2data(offset=-1)
        import_level2data()
        driver = self.driver
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
