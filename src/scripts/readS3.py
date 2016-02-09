import h5py
import numpy as np


class Sage3Data(object):
    def __init__(self, filename):
        self._hfile = h5py.File(filename)

    @property
    def times(self):
        dates = np.array([x[0] for x in self._getSpaceTime()])
        times = np.array([x[1] for x in self._getSpaceTime()])
        return dates, times  # Make a DT object or an iso formatted string!

    @property
    def latitudes(self):
        """Tangential latitudes for scan in degrees"""
        return np.array([x[2] for x in self._getSpaceTimeCoordinates()])

    @property
    def longitudes(self):
        """Tangential longitudes for scan in degrees"""
        return np.array([x[3] for x in self._getSpaceTimeCoordinates()])

    @property
    def temperatures(self):
        return np.array([x[0] for x in self._getTempAndPressureProfiles()])

    @property
    def pressure(self):
        return np.array([x[2] for x in self._getTempAndPressureProfiles()])

    @property
    def ozone(self):
        """Ozone concentration in cm ** -3"""
        return np.array([x[0] for x in self._getOzoneProfiles()])

    @property
    def water_vapour(self):
        """Water vapour concentration in cm ** -3"""
        return np.array([x[0] for x in self._getWaterProfiles()])

    @property
    def nitrogen_dioxide(self):
        """Nitrogen Dioxide concentration in cm ** -3"""
        return np.array([x[0] for x in self._getNitrogenDioxideProfiles()])

    def nanitaze(self, data):
        """Replace int and floating-point limit numbers with nan"""
        pass

    def _getSpaceTimeCoordinates(self):
        """Get times, longitudes and latitudes for the event in the file.

        The [1:] may not work for all files, and applying a sanity filter might
        be better practice in the future."""
        return (self.hfile['Section 4.0 - Event Identification']
                ['Section 4.3 - Ground Track Data Over This Event']
                ['Section 4.3 - Ground Track Data Over This Event'].value[1:])

    def _getTempAndPressureProfiles(self):
        return (self.hfile['Section 5.0 - Altitude-based Data']
                ['Section 5.1 - Temperature_pressure profiles']
                ['Temperature_pressure profiles'].value)

    def _getOzoneProfiles(self):
        return (self.hfile['Section 5.0 - Altitude-based Data']
                ['Section 5.2A - Mesospheric Ozone profiles']
                ['Mesospheric Ozone profiles'].value)

    def _getWaterProfiles(self):
        return (self.hfile['Section 5.0 - Altitude-based Data']
                ['Section 5.3 - Water Vapor profiles']
                ['Water Vapor profiles'].value)

    def _getNitrogenDioxideProfiles(self):
        return (self.hfile['Section 5.0 - Altitude-based Data']
                ['Section 5.4 - Nitrogen Dioxide profiles']
                ['Nitrogen Dioxide profiles'].value)
