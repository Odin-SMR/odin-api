# pylint: skip-file
from datetime import datetime
import pytest
from pg import DB
from odinapi.test.testdefs import system
from odinapi.views.level1b_scanlogdata_exporter import(
    ScanInfoExporter,
    scan_data_is_valid,
)


class DatabaseConnector(DB):
    def __init__(self):
        DB.__init__(
            self,
            dbname='odin',
            user='odinop',
            host='localhost',
        )


@pytest.fixture(scope="session")
def scan_info_exporter():
    db_connection = DatabaseConnector()
    return ScanInfoExporter(
        'AC1', 2, db_connection)


@pytest.fixture
def scan_log_sample_data():
    return {
        'mjd': [54321.0, 54321.1],
        'latitude': [10.5, 11.5],
        'longitude': [12.5, 13.5],
        'altitude': [7e3, 65e3],
        'sunzd': [110.0, 110.0],
        'freqmode': [2],
        'quality': [0],
    }


@system
@pytest.mark.usefixtures('dockercompose')
class TestScanInfoExporter():

    def test_get_scanids(self, scan_info_exporter):
        stw_min = 7014769646
        stw_max = 7014785316
        scanids = scan_info_exporter.get_scanids(
            stw_min, stw_max)
        assert len(scanids) == 10
        assert scanids[0] == stw_min
        assert scanids[-1] == stw_max

    def test_extract_scan_log(self, scan_info_exporter):
        scan_log = scan_info_exporter.extract_scan_log(
            7014785316)
        assert scan_log['AltEnd'] == pytest.approx(
            81062.6, abs=1e-3)
        assert scan_log['AltStart'] == pytest.approx(
            22603.8, abs=1e-3)
        assert scan_log['DateTime'] == datetime(
            2015, 1, 12, 0, 17, 12, 315840)
        assert scan_log['FreqMode'] == 2
        assert scan_log['LatEnd'] == pytest.approx(
            29.42, abs=1e-3)
        assert scan_log['LatStart'] == pytest.approx(
            25.5651, abs=1e-3)
        assert scan_log['LonEnd'] == pytest.approx(
            271.474, abs=1e-3)
        assert scan_log['LonStart'] == pytest.approx(
            271.879, abs=1e-3)
        assert scan_log['MJDEnd'] == pytest.approx(
            57034.012428, abs=1e-3)
        assert scan_log['MJDStart'] == pytest.approx(
            57034.0114682, abs=1e-3)
        assert scan_log['NumSpec'] == 21
        assert scan_log['Quality'] == 0
        assert scan_log['ScanID'] == 7014785316
        assert scan_log['SunZD'] == pytest.approx(
            103.17699, abs=1e-3)

    def test_get_log_of_scans(self, scan_info_exporter):
        scanids = [7014769646, 7014785316, 7037412634]
        log_of_scans = scan_info_exporter.get_log_of_scans(
            datetime(2015, 1, 12),
            datetime(2015, 1, 13),
            scanids)
        assert len(log_of_scans) == 2
        assert log_of_scans[0]['ScanID'] == 7014769646
        assert log_of_scans[-1]['ScanID'] == 7014785316

    def test_scan_data_is_valid(self, scan_log_sample_data):
        assert scan_data_is_valid(scan_log_sample_data)

    def test_scan_data_is_unvalid_1(self, scan_log_sample_data):
        del(scan_log_sample_data['mjd'])
        assert not scan_data_is_valid(scan_log_sample_data)

    def test_scan_data_is_unvalid_2(self, scan_log_sample_data):
        scan_log_sample_data['mjd'][0] = None
        assert not scan_data_is_valid(scan_log_sample_data)
