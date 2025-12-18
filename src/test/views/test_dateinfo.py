"""Tests for DateInfo views before BaseView refactoring"""

from http.client import OK
from unittest.mock import MagicMock, patch


class TestDateInfo:
    """Test DateInfo view that uses BaseView"""

    @patch("odinapi.views.views.db.session.execute")
    def test_dateinfo_v4(self, mock_execute, test_client):
        """Test DateInfo GET request for v4 API"""
        # Mock database result
        mock_row1 = MagicMock()
        mock_row1.backend = "AC1"
        mock_row1.freqmode = 1
        mock_row1.count = 10

        mock_row2 = MagicMock()
        mock_row2.backend = "AC2"
        mock_row2.freqmode = 2
        mock_row2.count = 20

        mock_execute.return_value = [mock_row1, mock_row2]

        # Make request
        resp = test_client.get("/rest_api/v4/freqmode_raw/2023-01-15/")

        assert resp.status_code == OK
        data = resp.json
        assert "Date" in data
        assert data["Date"] == "2023-01-15"
        assert "Info" in data
        assert len(data["Info"]) == 2
        assert data["Info"][0]["Backend"] == "AC1"
        assert data["Info"][0]["FreqMode"] == 1
        assert data["Info"][0]["NumScan"] == 10
        assert "URL" in data["Info"][0]

    @patch("odinapi.views.views.db.session.execute")
    def test_dateinfo_v5(self, mock_execute, test_client):
        """Test DateInfo GET request for v5 API"""
        # Mock database result
        mock_row = MagicMock()
        mock_row.backend = "AC1"
        mock_row.freqmode = 1
        mock_row.count = 10

        mock_execute.return_value = [mock_row]

        # Make request
        resp = test_client.get("/rest_api/v5/freqmode_raw/2023-01-15/")

        assert resp.status_code == OK
        data = resp.json
        assert "Date" in data
        assert data["Date"] == "2023-01-15"
        assert "Data" in data
        assert "Type" in data
        assert data["Type"] == "freqmode_info"
        assert "Count" in data
        assert data["Count"] == 1

    def test_dateinfo_invalid_date(self, test_client):
        """Test DateInfo with invalid date format"""
        resp = test_client.get("/rest_api/v4/freqmode_raw/invalid-date/")
        assert resp.status_code == 404


class TestDateBackendInfo:
    """Test DateBackendInfo view that uses BaseView"""

    @patch("odinapi.views.views.db.session.execute")
    def test_datebackendinfo_v4(self, mock_execute, test_client):
        """Test DateBackendInfo GET request for v4 API"""
        # Mock database result
        mock_row = MagicMock()
        mock_row.backend = "AC1"
        mock_row.freqmode = 1
        mock_row.count = 10

        mock_execute.return_value = [mock_row]

        # Make request
        resp = test_client.get("/rest_api/v4/freqmode_raw/2023-01-15/AC1/")

        assert resp.status_code == OK
        data = resp.json
        assert "Date" in data
        assert data["Date"] == "2023-01-15"
        assert "Info" in data
        assert len(data["Info"]) == 1
        assert data["Info"][0]["Backend"] == "AC1"

    def test_datebackendinfo_unsupported_version(self, test_client):
        """Test DateBackendInfo with v5 (unsupported)"""
        resp = test_client.get("/rest_api/v5/freqmode_raw/2023-01-15/AC1/")
        assert resp.status_code == 404
