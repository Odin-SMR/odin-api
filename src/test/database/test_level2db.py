# pylint: disable=no-self-use,redefined-outer-name,invalid-name,no-init
import pytest

from odinapi.database.level2db import Level2DB

FREQMODE = 42


@pytest.fixture
def level2db(mongodb):
    level2db = Level2DB('projectfoo', mongodb['level2testdb'])
    mongodb['level2testdb']['L2i_projectfoo'].insert_many([
        {
            'ScanID': 1234, 'FreqMode': FREQMODE, 'ProcessingError': False,
            'Comments': ["Foo", "Bar"]
        },
        {
            'ScanID': 1235, 'FreqMode': FREQMODE, 'ProcessingError': False,
            'Comments': ["Foo", "Baz"]
        },
        {
            'ScanID': 4321, 'FreqMode': FREQMODE, 'ProcessingError': True,
            'Comments': ["Foo", "Error"]
        },
        {
            'ScanID': 4322, 'FreqMode': FREQMODE, 'ProcessingError': True,
            'Comments': ["Foo", "Error"]
        },
        {
            'ScanID': 1236, 'FreqMode': FREQMODE + 1, 'ProcessingError': False,
            'Comments': ["Not", "Me"]
        },
        {
            'ScanID': 4323, 'FreqMode': FREQMODE + 1, 'ProcessingError': True,
            'Comments': ["Or", "Me"]
        },
    ])
    return level2db


class TestGetComments(object):

    def test_get_all_comments(self, level2db):
        expected = ["Bar", "Baz", "Error", "Foo"]
        assert list(level2db.get_comments(FREQMODE)) == expected

    def test_get_comments_with_limit(self, level2db):
        expected = ["Bar", "Baz"]
        assert list(level2db.get_comments(FREQMODE, limit=2)) == expected

    def test_get_comments_with_offset(self, level2db):
        expected = ["Error", "Foo"]
        assert list(level2db.get_comments(FREQMODE, offset=2)) == expected

    def test_count_comments(self, level2db):
        assert level2db.count_comments(FREQMODE) == 4


class TestGetScans(object):

    def test_get_all_scans(self, level2db):
        scans = level2db.get_scans(FREQMODE)
        assert set(scan['ScanID'] for scan in scans) == set([1234, 1235])

    def test_get_scans_with_limit(self, level2db):
        scans = level2db.get_scans(FREQMODE, limit=1)
        assert set(scan['ScanID'] for scan in scans) == set([1234])

    def test_get_scans_with_offset(self, level2db):
        scans = level2db.get_scans(FREQMODE, offset=1)
        assert set(scan['ScanID'] for scan in scans) == set([1235])

    def test_count_scans(self, level2db):
        assert level2db.count_scans(FREQMODE) == 2


class TestGetFailedScans(object):

    def test_get_all_failed_scans(self, level2db):
        scans = level2db.get_failed_scans(FREQMODE)
        assert set(scan['ScanID'] for scan in scans) == set([4321, 4322])

    def test_get_failed_scans_vith_limit(self, level2db):
        scans = level2db.get_failed_scans(FREQMODE, limit=1)
        assert set(scan['ScanID'] for scan in scans) == set([4321])

    def test_get_failed_scans_with_offset(self, level2db):
        scans = level2db.get_failed_scans(FREQMODE, offset=1)
        assert set(scan['ScanID'] for scan in scans) == set([4322])

    def test_count_failed_scans(self, level2db):
        assert level2db.count_scans(FREQMODE) == 2
