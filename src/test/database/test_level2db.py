import pytest
import os
import json

from odinapi.database.level2db import (
    Level2DB,
    get_valid_collapsed_products,
    get_next_min_scanid,
)
from odinapi.database.mongo import get_collection, get_database

FREQMODE = 42


@pytest.fixture
def level2db(db_context):
    database = get_database("level2testdb")
    level2db = Level2DB("projectfoo", database)
    for prefix in ["L2", "L2i"]:
        get_collection("level2testdb", f"{prefix}_projectfoo").drop()
    collection = get_collection("level2testdb", "L2i_projectfoo")
    collection.insert_many(
        [
            {
                "ScanID": 1234,
                "FreqMode": FREQMODE,
                "ProcessingError": False,
                "Comments": ["Foo", "Bar"],
            },
            {
                "ScanID": 1235,
                "FreqMode": FREQMODE,
                "ProcessingError": False,
                "Comments": ["Foo", "Baz"],
            },
            {
                "ScanID": 4242,
                "FreqMode": FREQMODE,
                "ProcessingError": False,
                "Comments": ["Foo", "Fi"],
            },
            {
                "ScanID": 4321,
                "FreqMode": FREQMODE,
                "ProcessingError": True,
                "Comments": ["Foo", "Error"],
            },
            {
                "ScanID": 4322,
                "FreqMode": FREQMODE,
                "ProcessingError": True,
                "Comments": ["Foo", "Error"],
            },
            {
                "ScanID": 1236,
                "FreqMode": FREQMODE + 1,
                "ProcessingError": False,
                "Comments": ["Not", "Me"],
            },
            {
                "ScanID": 4323,
                "FreqMode": FREQMODE + 1,
                "ProcessingError": True,
                "Comments": ["Or", "Me"],
            },
        ]
    )
    return level2db


@pytest.fixture
def level2db_with_example_data(db_context):
    database = get_database("level2testdb")
    level2db = Level2DB("projectfoo", database)
    for prefix in ["L2", "L2i"]:
        get_collection("level2testdb", f"{prefix}_projectfoo").drop()
    file_example_data = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "systemtest",
        "testdata",
        "odin_result.json",
    )
    with open(file_example_data, "r") as the_file:
        data = json.load(the_file)
    L2 = data["L2"]
    L2i = data["L2I"]
    L2c = data["L2C"]
    level2db.store(L2, L2i, L2c)
    return level2db


class TestGetComments:
    @pytest.mark.slow
    def test_get_all_comments(self, level2db):
        expected = ["Bar", "Baz", "Error", "Fi", "Foo"]
        assert list(level2db.get_comments(FREQMODE)) == expected

    @pytest.mark.slow
    def test_get_comments_with_limit(self, level2db):
        expected = ["Bar", "Baz"]
        assert list(level2db.get_comments(FREQMODE, limit=2)) == expected

    @pytest.mark.slow
    def test_get_comments_with_offset(self, level2db):
        expected = ["Error", "Fi", "Foo"]
        assert list(level2db.get_comments(FREQMODE, offset=2)) == expected

    @pytest.mark.slow
    def test_count_comments(self, level2db):
        assert level2db.count_comments(FREQMODE) == 5


class TestGetScans:
    @pytest.mark.slow
    def test_get_all_scans(self, level2db):
        scans = level2db.get_scans(FREQMODE)
        assert set(scan["ScanID"] for scan in scans) == set([1234, 1235, 4242])

    @pytest.mark.slow
    def test_get_scans_with_limit(self, level2db):
        scans = level2db.get_scans(FREQMODE, limit=1)
        assert set(scan["ScanID"] for scan in scans) == set([1234])

    @pytest.mark.slow
    def test_get_scans_with_offset(self, level2db):
        scans = level2db.get_scans(FREQMODE, offset=1)
        assert set(scan["ScanID"] for scan in scans) == set([1235, 4242])

    @pytest.mark.slow
    def test_count_scans(self, level2db):
        assert level2db.count_scans(FREQMODE) == 3

    @pytest.mark.slow
    def test_count_scans_with_limit(self, level2db):
        assert level2db.count_scans(FREQMODE, limit=1) == 1

    @pytest.mark.slow
    def test_count_scans_with_offset(self, level2db):
        assert level2db.count_scans(FREQMODE, offset=1) == 2

    @pytest.mark.slow
    def test_get_l2i_of_scan(self, level2db):
        l2i, _, _ = level2db.get_scan(FREQMODE, 1234)
        assert set(l2i.keys()) == set(["ScanID", "FreqMode", "GenerationTime"])
        assert isinstance(l2i["GenerationTime"], str)

    @pytest.mark.slow
    def test_get_l2i(self, level2db):
        l2i = level2db.get_L2i(FREQMODE, 1234)
        assert set(l2i.keys()) == set(["ScanID", "FreqMode", "GenerationTime"])
        assert isinstance(l2i["GenerationTime"], str)


class TestGetFailedScans:
    @pytest.mark.slow
    def test_get_all_failed_scans(self, level2db):
        scans = level2db.get_failed_scans(FREQMODE)
        assert set(scan["ScanID"] for scan in scans) == set([4321, 4322])

    @pytest.mark.slow
    def test_get_failed_scans_vith_limit(self, level2db):
        scans = level2db.get_failed_scans(FREQMODE, limit=1)
        assert set(scan["ScanID"] for scan in scans) == set([4321])

    @pytest.mark.slow
    def test_get_failed_scans_with_offset(self, level2db):
        scans = level2db.get_failed_scans(FREQMODE, offset=1)
        assert set(scan["ScanID"] for scan in scans) == set([4322])

    @pytest.mark.slow
    def test_count_failed_scans(self, level2db):
        assert level2db.count_failed_scans(FREQMODE) == 2

    @pytest.mark.slow
    def test_count_failed_scans_with_limit(self, level2db):
        assert level2db.count_failed_scans(FREQMODE, limit=1) == 1

    @pytest.mark.slow
    def test_count_failed_scans_with_offset(self, level2db):
        assert level2db.count_failed_scans(FREQMODE, offset=1) == 1


class TestGetMeasurements:
    @pytest.mark.parametrize(
        "min_scanid,limit,expect",
        (
            (7014791071, 50, 36),
            (7014791071, 5, 5),
            (7014791072, 20, 0),
        ),
    )
    def test_get_measurements_respect_offset_and_limit(
        self, level2db_with_example_data, min_scanid, limit, expect
    ):
        products = [
            "ClO / 501 GHz / 20 to 50 km",
            "O3 / 501 GHz / 20 to 50 km",
        ]
        measurements = level2db_with_example_data.get_measurements(
            products, limit, min_scanid=min_scanid
        )
        results = list(measurements)
        assert len(results) == expect

    @pytest.mark.parametrize(
        "min_scanid,limit,expect",
        (
            (7014791071, 37, 2),
            (7014791071, 36, 0),
        ),
    )
    def test_get_valid_collapsed_products(
        self, level2db_with_example_data, min_scanid, limit, expect
    ):
        products = [
            "ClO / 501 GHz / 20 to 50 km",
            "O3 / 501 GHz / 20 to 50 km",
        ]
        measurements = level2db_with_example_data.get_measurements(
            products, limit, min_scanid=min_scanid
        )
        results = list(measurements)
        collapsed_products, _ = get_valid_collapsed_products(results, limit)
        assert len(collapsed_products) == expect

    @pytest.mark.parametrize(
        "min_scanid,limit,expect",
        (
            (7014791071, 37, None),
            (7014791071, 36, 7014791071),
        ),
    )
    def test_get_valid_collapsed_products_returns_next(
        self, level2db_with_example_data, min_scanid, limit, expect
    ):
        products = [
            "ClO / 501 GHz / 20 to 50 km",
            "O3 / 501 GHz / 20 to 50 km",
        ]
        measurements = level2db_with_example_data.get_measurements(
            products, limit, min_scanid=min_scanid
        )
        results = list(measurements)
        _, next_scanid = get_valid_collapsed_products(results, limit)
        assert next_scanid == expect

    @pytest.mark.parametrize(
        "limit,expect",
        (
            (5, 11),
            (10, None),
        ),
    )
    def test_get_next_min_scanid(self, limit, expect):
        products = [
            {"ScanID": 4},
            {"ScanID": 4},
            {"ScanID": 7},
            {"ScanID": 7},
            {"ScanID": 11},
        ]
        assert get_next_min_scanid(products, limit) == expect
