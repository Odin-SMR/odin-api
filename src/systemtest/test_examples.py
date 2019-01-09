"""Tests for example scripts for API interaction"""
import unittest

import pytest
import requests

from examples import get_l1b_for_period, filter_spectra


@pytest.mark.usefixtures('dockercompose')
class TestLevel1Examples(unittest.TestCase):
    """Tests for Level1 API interaction example scripts"""
    API_ROOT = "http://localhost:5000/rest_api/v5"

    def test_get_scans_for_period(self):
        """Test getting scans for a frequency mode and period"""
        # V5
        scans = get_l1b_for_period.get_scans_for_period(
            1, "2015-12-30", None, self.API_ROOT)
        assert len(scans) == 322
        scans = get_l1b_for_period.get_scans_for_period(
            1, "2015-12-31", None, self.API_ROOT)
        assert len(scans) == 463
        scans = get_l1b_for_period.get_scans_for_period(
            1, "2015-12-30", "2015-12-31", self.API_ROOT)
        assert len(scans) == 785
        scans = get_l1b_for_period.get_scans_for_period(
            1, "2015-12-30", "2016-01-01", self.API_ROOT)
        assert len(scans) == 785
        with self.assertRaises(ValueError):
            get_l1b_for_period.get_scans_for_period(
                1, "2016-01-01", "2015-12-30", self.API_ROOT)

    @pytest.mark.slow
    def test_get_spectra_for_period(self):
        """Test getting spectra for a frequency mode and period"""
        # V5
        spectra = get_l1b_for_period.get_spectra_for_period(
            1, "2015-01-12", None, self.API_ROOT)
        assert len(spectra) == 34
        assert len(spectra["Spectrum"]) == 8935
        with self.assertRaises(ValueError):
            get_l1b_for_period.get_scans_for_period(
                1, "2016-01-01", "2015-12-30", self.API_ROOT)

    @pytest.mark.slow
    def test_break_postgresql(self):
        """This test used to break psql because 2015-01-13 has no spectra"""
        # V5
        spectra = get_l1b_for_period.get_spectra_for_period(
            1, "2015-01-12", "2015-01-13", self.API_ROOT)
        assert len(spectra) == 34
        assert len(spectra["Spectrum"]) == 8935

    def test_filter_by_param(self):
        """Test filtering by parameter range"""
        # V5
        request = requests.get(
            "{}/level1/1/7015305914/L1b/".format(self.API_ROOT))
        spectra = request.json()
        assert len(spectra) == 3
        assert len(spectra["Data"]) == 35
        assert len(spectra["Data"]["Spectrum"]) == 21
        filter_spectra.filter_by_param(spectra, 50000, 70000, "Altitude")
        assert len(spectra["Data"]["Spectrum"]) == 4
        with self.assertRaises(ValueError):
            filter_spectra.filter_by_param(spectra, 70000, 50000, "Altitude")

    def test_filter_by_quality(self):
        """Test filtering by parameter quality flags"""
        # V5
        request = requests.get(
            "{}/level1/1/7015305914/L1b/".format(self.API_ROOT))
        spectra = request.json()
        assert len(spectra) == 3
        assert len(spectra["Data"]) == 35
        assert len(spectra["Data"]["Spectrum"]) == 21
        filter_spectra.filter_by_quality(spectra, 0x80, 0x08)
        assert len(spectra["Data"]["Spectrum"]) == 16
        with self.assertRaises(ValueError):
            filter_spectra.filter_by_quality(spectra, 0x80, 0x88)
