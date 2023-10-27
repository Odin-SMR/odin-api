import pytest
import pyarrow as pa  # type: ignore
from odinapi.views.read_ptz import prefix_names, get_ptz


class TestPTZ:
    def test_prefix_pseudo(self):
        # This is a psuedo test that confirms theories assumed in implementation.

        # prev_file_in_bucket = "s3://odin-zpt/ac1/341/341fcd5c.ac1.parquet"
        # file_in_bucket = "s3://odin-zpt/ac1/342/342009ec.ac1.parquet"
        # next_file_in_bucket = "s3://odin-zpt/ac1/342/34206025.ac1.parquet"
        first_scanid_in_file = 13992239357
        last_scanid_in_file = 13992591241
        prev_stw_accordin_to_prev_file_name = 0x341FCD5C << 4
        first_stw_according_to_file_name = 0x342009EC << 4
        last_stw_according_to_next_file_name = 0x34206025 << 4
        assert first_scanid_in_file > first_stw_according_to_file_name
        assert last_scanid_in_file > first_stw_according_to_file_name
        assert first_scanid_in_file < last_stw_according_to_next_file_name
        assert last_scanid_in_file < last_stw_according_to_next_file_name

    def test_prefix(self):
        scanid = 13992239357
        [this_prefix, prev_prefix] = prefix_names(scanid)
        assert this_prefix == "342"
        assert prev_prefix == "341"

    def test_ptz_cannot_find_data(self, mocker):
        dataset_mock = mocker.patch("odinapi.views.read_ptz.ds.dataset")
        dataset_mock.side_effect = FileNotFoundError
        ptz = get_ptz("AC1", 0, 0, 0, 0)
        assert ptz is None

    @pytest.fixture
    def ptz(self):
        t = pa.array([1e-3, 100 + 1e-3, 2 + 1e-4])
        z = pa.array([1, 2, 3])
        p = pa.array([1000 + 1e-10, 500 + 1e-11, 1e-10])
        names = ["t", "z", "p"]
        return pa.Table.from_arrays([t, z, p], names=names)

    def test_ptz(self, ptz, mocker):
        table = mocker.Mock()
        table.to_table.return_value = ptz
        dataset = mocker.patch("odinapi.views.read_ptz.ds.dataset")
        dataset.return_value = table
        ptz = get_ptz("AC1", 0, 1, 2, 3)
        if ptz:
            assert ptz["Temperature"] == [1e-3, 100 + 1e-3, 2], "3 fractional digits"
            assert ptz["Altitude"] == [1000, 2000, 3000], "scaling from km to m"
            assert ptz["Pressure"] == [
                100000 + 1e-8,
                50000,
                1e-8,
            ], "scaling to hPa, 8 fractional digits"
            assert ptz["MJD"] == 1
            assert ptz["Latitude"] == 2
            assert ptz["Longitude"] == 3
        else:
            assert False

    @pytest.fixture
    def empty_ptz(self):
        obj = [{"t": [], "p": [], "z": []}]
        return pa.Table.from_pylist(obj).filter([False])

    def test_no_match(self, empty_ptz, mocker):
        table = mocker.Mock()
        table.to_table.return_value = empty_ptz
        dataset = mocker.patch("odinapi.views.read_ptz.ds.dataset")
        dataset.return_value = table
        ptz = get_ptz("AC1", 0, 1, 2, 3)
        assert ptz is None
