"""Tests for example scripts for API interaction"""
import pytest
import requests

from examples import get_l1b_for_period, filter_spectra


class TestLevel1Examples:
    """Tests for Level1 API interaction example scripts"""
    def get_apiroot(self, baseurl):
        return "{}/rest_api/v5".format(baseurl)

    def test_get_scans_for_period(self, odinapi_service):
        """Test getting scans for a frequency mode and period"""
        # V5
        apiurl = self.get_apiroot(odinapi_service)
        scans = get_l1b_for_period.get_scans_for_period(
            1, "2015-12-30", None, apiurl)
        assert len(scans) == 322
        scans = get_l1b_for_period.get_scans_for_period(
            1, "2015-12-31", None, apiurl)
        assert len(scans) == 463
        scans = get_l1b_for_period.get_scans_for_period(
            1, "2015-12-30", "2015-12-31", apiurl)
        assert len(scans) == 785
        scans = get_l1b_for_period.get_scans_for_period(
            1, "2015-12-30", "2016-01-01", apiurl)
        assert len(scans) == 785
        with pytest.raises(ValueError):
            get_l1b_for_period.get_scans_for_period(
                1, "2016-01-01", "2015-12-30", apiurl)

    @pytest.mark.slow
    def test_get_spectra_for_period(self, odinapi_service):
        """Test getting spectra for a frequency mode and period"""
        # V5
        apiurl = self.get_apiroot(odinapi_service)
        spectra = get_l1b_for_period.get_spectra_for_period(
            1, "2015-01-12", None, apiurl)
        assert len(spectra) == 34
        assert len(spectra["Spectrum"]) == 8935
        with pytest.raises(ValueError):
            get_l1b_for_period.get_scans_for_period(
                1, "2016-01-01", "2015-12-30", apiurl)

    @pytest.mark.slow
    def test_break_postgresql(self, odinapi_service):
        """This test used to break psql because 2015-01-13 has no spectra"""
        # V5
        apiurl = self.get_apiroot(odinapi_service)
        spectra = get_l1b_for_period.get_spectra_for_period(
            1, "2015-01-12", "2015-01-13", apiurl)
        assert len(spectra) == 34
        assert len(spectra["Spectrum"]) == 8935

    def test_filter_by_param(self, odinapi_service):
        """Test filtering by parameter range"""
        # V5
        apiurl = self.get_apiroot(odinapi_service)
        request = requests.get("{}/level1/1/7015305914/L1b/".format(apiurl))
        spectra = request.json()
        assert len(spectra) == 3
        assert len(spectra["Data"]) == 35
        assert len(spectra["Data"]["Spectrum"]) == 21
        filter_spectra.filter_by_param(spectra, 50000, 70000, "Altitude")
        assert len(spectra["Data"]["Spectrum"]) == 4
        with pytest.raises(ValueError):
            filter_spectra.filter_by_param(spectra, 70000, 50000, "Altitude")

    def test_filter_by_quality(self, odinapi_service):
        """Test filtering by parameter quality flags"""
        # V5
        apiurl = self.get_apiroot(odinapi_service)
        request = requests.get("{}/level1/1/7015305914/L1b/".format(apiurl))
        spectra = request.json()
        assert len(spectra) == 3
        assert len(spectra["Data"]) == 35
        assert len(spectra["Data"]["Spectrum"]) == 21
        filter_spectra.filter_by_quality(spectra, 0x80, 0x08)
        assert len(spectra["Data"]["Spectrum"]) == 16
        with pytest.raises(ValueError):
            filter_spectra.filter_by_quality(spectra, 0x80, 0x88)
