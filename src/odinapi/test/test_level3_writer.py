# pylint: skip-file
import unittest
import numpy as np
from numpy.testing import assert_almost_equal
from netCDF4 import Dataset
from scripts.smrl3filewriter import(
    get_zonal_average_of_l2_data,
    get_representative_time_of_data,
    get_l2_median,
    get_l2_error,
    get_l2_std,
    get_mean_measurement_response,
    get_number_of_measurements,
    get_quartiles,
    get_average_latitude,
    get_length_of_dimensions,
    read_odin_l2_file,
)


L2_DATA = {
    "time": np.linspace(40200, 40201, 11),
    "latitude": np.linspace(-85, 85, 11),
    "l2_value": np.array(
        [scale * ones for scale, ones in
         enumerate(np.ones(shape=(11, 55)))]),
    "measurement_response": np.ones(shape=(11, 55)),
}


def mk_test_l2_file():
    dataset = Dataset(
        "odin_l2_file", "w", fomat="NETCFD4", diskless=True)
    dataset.createDimension("time", L2_DATA["time"].shape[0])
    dataset.createDimension("level", L2_DATA["l2_value"].shape[1])
    group = dataset.createGroup("Geolocation")
    time = group.createVariable("time", "f8", ("time"))
    time[:] = L2_DATA["time"]
    latitude = group.createVariable("latitude", "f4", ("time"))
    latitude[:] = L2_DATA["latitude"]
    group = dataset.createGroup("Retrieval_results")
    l2_value = group.createVariable(
        "l2_value", "f4", ("time", "level"))
    l2_value[:] = L2_DATA["l2_value"]
    group = dataset.createGroup("Specific_data_for_selection")
    measurement_response = group.createVariable(
        "measurement_response", "f4", ("time", "level"))
    measurement_response[:] = L2_DATA["measurement_response"]
    return dataset


class TestLevel3Writer(unittest.TestCase):

    def test_read_odin_l2_file(self):
        l2_data = read_odin_l2_file(
            mk_test_l2_file())
        self.assertTrue(
            np.all(L2_DATA["time"] == l2_data["time"]))
        self.assertTrue(
            np.all(L2_DATA["latitude"] == l2_data["latitude"]))
        self.assertTrue(
            np.all(L2_DATA["l2_value"] == l2_data["l2_value"]))
        self.assertTrue(
            np.all(
                L2_DATA["measurement_response"] ==
                l2_data["measurement_response"]))

    def test_get_length_of_dimensions(self):
        length_of_dimensions = get_length_of_dimensions(
            [L2_DATA])
        self.assertTrue(length_of_dimensions["time"] == 1)
        self.assertTrue(length_of_dimensions["quartile"] == 3)

    def test_get_zonal_average(self):
        data = get_zonal_average_of_l2_data([L2_DATA])
        self.assertTrue(data["l2_median"].shape == (1, 55, 18))

    def test_get_representative_time(self):
        time = get_representative_time_of_data(L2_DATA["time"])
        self.assertTrue(time == 40191)

    def test_get_l2_median(self):
        data = get_l2_median(L2_DATA["l2_value"])
        self.assertTrue(np.all(data == np.full((55, ), 5.0)))

    def test_get_l2_error(self):
        data = get_l2_error(L2_DATA["l2_value"])
        assert_almost_equal(data, np.full((55, ), 0.95346259))

    def test_get_l2_std(self):
        data = get_l2_std(L2_DATA["l2_value"])
        assert_almost_equal(data, np.full((55, ), 3.16227766))

    def test_get_measurement_response(self):
        data = get_mean_measurement_response(
            L2_DATA["measurement_response"])
        self.assertTrue(np.all(data == np.full((55, ), 1.0)))

    def test_get_number_of_measurements(self):
        data = get_number_of_measurements(L2_DATA["l2_value"])
        self.assertTrue(data == 11)

    def test_get_quartiles(self):
        data = get_quartiles(L2_DATA["l2_value"])
        self.assertTrue(np.all(data[0] == np.array([2.5, 5., 7.5])))
        self.assertTrue(np.all(data[54] == np.array([2.5, 5., 7.5])))

    def test_get_average_latitude(self):
        data = get_average_latitude(L2_DATA["latitude"])
        self.assertTrue(data == 0)
