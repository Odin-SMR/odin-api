import unittest

import pytest
from selenium import webdriver

from odinapi.test.testdefs import system


@system
@pytest.mark.usefixtures("dockercompose")
class TestBrowser(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()

    def test_main_page_is_up(self):
        """Test that main page is up"""
        driver = self.driver
        driver.get("http://localhost:5000")
        assert "Odin/SMR" in driver.title
