import unittest
import numpy as np
from numpy.testing import assert_almost_equal
from odinapi.views.get_ancillary_data import (
    get_orbit,
    get_theta,
    get_solartime,
    get_sza_at_retrieval_position,
)


class TestGetAncillaryData(unittest.TestCase):

    def test_get_theta(self):
        pressure = np.array([1e5, 1e4])
        temperature = np.array([300.0, 200.0])
        theta = get_theta(pressure, temperature)
        assert_almost_equal(theta[0], 300.0, decimal=3)
        assert_almost_equal(theta[1], 386.407, decimal=3)

    def test_get_solartime(self):
        mjd = 55000
        longitudes = [-15, 0, 15]
        expected_solar_times = [22.983, 23.983, 0.983]
        for longitude, expected_solar_time in zip(
                longitudes, expected_solar_times):
            solartime = get_solartime(mjd, longitude)
            assert_almost_equal(
                solartime, expected_solar_time, decimal=3)

    def test_get_sza_at_retrieval_position(self):
        """test that nearest neighbour interpolation works,
           along a path across the meridian"""
        latitude_reference = np.linspace(83, 87, 9)
        longitude_reference = np.linspace(5, -5, 9)
        sza_reference = np.linspace(90, 95, 9)
        indexes = [2, 4, 6]
        latitude_retrieval_pos = latitude_reference[indexes]
        longiude_retrieval_pos = longitude_reference[indexes]
        sza_at_retrieval_pos = get_sza_at_retrieval_position(
            latitude_retrieval_pos,
            longiude_retrieval_pos,
            latitude_reference,
            longitude_reference,
            sza_reference)
        self.assertTrue(np.all(
            sza_at_retrieval_pos == sza_reference[indexes]))

    def test_get_orbit(self):
        orbit = get_orbit(
            np.linspace(55000, 55001, 100))
        self.assertTrue(orbit == 55000)
