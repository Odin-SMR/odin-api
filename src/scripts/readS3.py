import h5py
import numpy as np
from datetime import datetime


def nanitize(f):
    """A decorator function for replacing undefined values in returned
    nd-arrays with nan."""

    maximum = 2**31 - 1

    def _decoration(self):
        data = f(self)
        return np.where(data >= maximum, np.nan, data)

    return _decoration


class Sage3Data(object):
    def __init__(self, filename):
        self._hfile = h5py.File(filename)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._hfile.close()

    @property
    def datetimes_iso(self):
        iso = []
        for dt in self.datetimes:
            try:
                iso.append(dt.isoformat())
            except AttributeError:
                iso.append(dt)
        return iso

    @property
    def datetimes_mjd(self):
        mjd0 = datetime(1858, 11, 17)
        sec_per_day = 24 * 60 * 60
        day_per_sec = 1.0 / sec_per_day
        mjds = []
        for dt in self.datetimes:
            try:
                mjd = dt - mjd0
                mjds.append(mjd.total_seconds() * day_per_sec)
            except TypeError:
                mjds.append(dt)
        return np.array(mjds)

    @property
    def datetimes(self):
        timestamps = self.raw_timestamps
        datetimes = []
        for n in xrange(timestamps.shape[0]):
            if np.isnan(timestamps[n]).any():
                datetimes.append(np.nan)
            else:
                datetimes.append(self._parse_timestamp(timestamps[n]))
        return datetimes

    @property
    @nanitize
    def raw_timestamps(self):
        timestamps = np.array([[x[0], x[1]] for x in
                               self._getSpaceTimeCoordinates()])
        return timestamps

    @property
    @nanitize
    def latitudes(self):
        """Tangential latitudes for scan in degrees"""
        return np.array([x[2] for x in self._getSpaceTimeCoordinates()])

    @property
    @nanitize
    def longitudes(self):
        """Tangential longitudes for scan in degrees"""
        return np.array([x[3] for x in self._getSpaceTimeCoordinates()])

    @property
    @nanitize
    def temperature(self):
        return np.array([x[0] for x in self._getTempAndPressureProfiles()])

    @property
    @nanitize
    def pressure(self):
        return np.array([x[2] for x in self._getTempAndPressureProfiles()])

    @property
    @nanitize
    def ozone(self):
        """Ozone concentration in cm ** -3"""
        return np.array([x[0] for x in self._getOzoneProfiles()])

    @property
    @nanitize
    def nitrogen_dioxide(self):
        """Nitrogen Dioxide concentration in cm ** -3"""
        return np.array([x[0] for x in self._getNitrogenDioxideProfiles()])

    def _getSpaceTimeCoordinates(self):
        """Get times, longitudes and latitudes for the event in the file."""
        return (self._hfile['Section 4.0 - Event Identification']
                ['Section 4.3 - Ground Track Data Over This Event']
                ['Section 4.3 - Ground Track Data Over This Event'].value)

    def _getTempAndPressureProfiles(self):
        return (self._hfile['Section 5.0 - Altitude-based Data']
                ['Section 5.1 - Temperature_pressure profiles']
                ['Temperature_pressure profiles'].value)

    def _getOzoneProfiles(self):
        return (self._hfile['Section 5.0 - Altitude-based Data']
                ['Section 5.2A - Mesospheric Ozone profiles']
                ['Mesospheric Ozone profiles'].value)

    def _getNitrogenDioxideProfiles(self):
        return (self._hfile['Section 5.0 - Altitude-based Data']
                ['Section 5.4 - Nitrogen Dioxide profiles']
                ['Nitrogen Dioxide profiles'].value)

    def _parse_timestamp(self, timestamp):
        date = str(timestamp.astype(np.int)[0])
        year = int(date[0: 4])
        month = int(date[4: 6])
        day = int(date[6: 8])

        time = str(timestamp.astype(np.int)[1])
        hour = int(time[0: 2])
        minute = int(time[2: 4])
        second = int(time[4: 6])

        return datetime(year, month, day, hour, minute, second)


class Sage3Solar(Sage3Data):
    @property
    @nanitize
    def water_vapour(self):
        """Water vapour concentration in cm ** -3"""
        return np.array([x[0] for x in self._getWaterProfiles()])

    def _getWaterProfiles(self):
        return (self._hfile['Section 5.0 - Altitude-based Data']
                ['Section 5.3 - Water Vapor profiles']
                ['Water Vapor profiles'].value)


class Sage3Lunar(Sage3Data):
    @property
    @nanitize
    def chlorine_dioxide(self):
        """Chlorine Dioxide concentration in cm ** -3"""
        return np.array([x[0] for x in self._getChlorineDioxideProfiles()])

    @property
    @nanitize
    def nitrogen_trioxide(self):
        """Nitrogen Trioxide concentration in cm ** -3"""
        return np.array([x[0] for x in self._getNitrogenTrioxideProfiles()])

    def _getTempAndPressureProfiles(self):
        return (self._hfile['Section 6.1 - Temperature_pressure profiles']
                ['Temperature_pressure profiles'].value)

    def _getOzoneProfiles(self):
        try:
            return (self._hfile['Section 6.2 - Ozone profiles ']
                    ['Ozone profiles'].value)
        except KeyError:
            return (self._hfile['Section 6.2 - Ozone profiles']
                    ['Ozone profiles'].value)

    def _getNitrogenDioxideProfiles(self):
        return (self._hfile['Section 6.3 - Nitrogen Dioxide profiles']
                ['Nitrogen Dioxide profiles'].value)

    def _getNitrogenTrioxideProfiles(self):
        return (self._hfile['Section 6.4 - Nitrogen Trioxide profiles']
                ['Nitrogen Dioxide profiles'].value)

    def _getChlorineDioxideProfiles(self):
        return (self._hfile['Section 6.5 - OClO profiles']
                ['OClO profiles'].value)
