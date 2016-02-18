import os
import h5py
import numpy as np
from datetime import datetime


def read_sageIII_file(filename, date, species, event_type):
    """Convenience function for getting all data from a Sage III file"""
    # Handle case of species -- special case for OClO:
    species = species.upper()
    if species == "OCLO":
        species = "OClO"

    # Construct filename:
    versions = {'lunar': 'v03', 'solar': 'v04'}

    sageIII_datapath = '/vds-data/Meteor3M_SAGEIII_Level2/'

    year = date[0:4]
    month = date[5:7]
    sageIII_datapath = os.path.join(sageIII_datapath, year, month,
                                    versions[event_type])
    sageIII_file = os.path.join(sageIII_datapath, filename)

    # Open correct file object:
    dataObject = {'lunar': Sage3Lunar, 'solar': Sage3Solar}

    data_dict = {}
    with dataObject[event_type](sageIII_file) as data:
        # Generate data dict
        data_dict['FileName'] = filename
        data_dict['Instrument'] = "Meteor-3M SAGE III"
        data_dict['EventType'] = event_type
        data_dict['MJD'] = data.datetimes_mjd.tolist()
        data_dict['Latitudes'] = data.latitudes.tolist()
        data_dict['Longitudes'] = data.longitudes.tolist()
        data_dict['Pressure'] = data.pressure.tolist()
        data_dict['Temperature'] = data.temperature.tolist()
        data_dict[species] = data.speciesData[species].tolist()

    # Return data
    return data_dict


def nanitize(f):
    """A decorator function for replacing undefined values in returned
    nd-arrays with nan."""

    def _decoration(self):
        data = f(self)
        if data.dtype == np.int32:
            maximum = np.iinfo(np.int32).max
        else:
            maximum = np.finfo(np.float32).max

        return np.where(data == maximum, np.nan, data)

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
        timestamps = np.array([[x[0][0], x[0][1]] for x in
                               self._getSpaceTimeCoordinates()])
        return timestamps

    @property
    @nanitize
    def latitudes(self):
        """Tangential latitudes for scan in degrees"""
        return np.array([x[0][2] for x in self._getSpaceTimeCoordinates()])

    @property
    @nanitize
    def longitudes(self):
        """Tangential longitudes for scan in degrees"""
        return np.array([x[0][3] for x in self._getSpaceTimeCoordinates()])

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
        return np.array([[x[0], x[1], x[4]] for x in self._getOzoneProfiles()])

    @property
    @nanitize
    def nitrogen_dioxide(self):
        """Nitrogen Dioxide concentration in cm ** -3"""
        return np.array([[x[0], x[1], x[4]] for x in
                         self._getNitrogenDioxideProfiles()])

    def _getGroundTrackSpaceTimeCoordinates(self):
        """Get ground track times, longitudes and latitudes for the event in
        the file."""
        return (self._hfile['Section 4.0 - Event Identification']
                ['Section 4.3 - Ground Track Data Over This Event']
                ['Section 4.3 - Ground Track Data Over This Event'].value)

    def _getSpaceTimeCoordinates(self):
        """Get measurement times, longitudes and latitudes for the event in
        the file."""
        return (self._hfile['Section 4.0 - Event Identification']
                ['Section 4.1 - Science Data Start Information']
                ['Section 4.1 - Science Data Start Information'].value,
                self._hfile['Section 4.0 - Event Identification']
                ['Section 4.2 - Science Data End Information']
                ['Section 4.2 - Science Data End Information'].value)

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

        time = timestamp.astype(np.int)[1]
        hour = time / 10000
        minute = (time - hour * 10000) / 100
        second = time - hour * 10000 - minute * 100

        return datetime(year, month, day, hour, minute, second)


class Sage3Solar(Sage3Data):
    def __init__(self):
        super(Sage3Solar, self).__init__()
        self.speciesData = {
            'O3': self.ozone,
            'H2O': self.water_vapour,
            'NO2': self.nitrogen_dioxide
            }

    @property
    @nanitize
    def water_vapour(self):
        """Water vapour concentration in cm ** -3"""
        return np.array([[x[0], x[1], x[2]] for x in self._getWaterProfiles()])

    def _getWaterProfiles(self):
        return (self._hfile['Section 5.0 - Altitude-based Data']
                ['Section 5.3 - Water Vapor profiles']
                ['Water Vapor profiles'].value)


class Sage3Lunar(Sage3Data):
    def __init__(self):
        super(Sage3Lunar, self).__init__()
        self.speciesData = {
            'O3': self.ozone,
            'NO2': self.nitrogen_dioxide,
            'NO3': self.nitroge_trioxide,
            'OClO': self.chlorine_dioxide
            }

    @property
    @nanitize
    def ozone(self):
        """Ozone concentration in cm ** -3"""
        return np.array([[x[0], x[1], x[2]] for x in self._getOzoneProfiles()])

    @property
    @nanitize
    def nitrogen_trioxide(self):
        """Nitrogen Trioxide concentration in cm ** -3"""
        return np.array([[x[0], x[1], x[2]] for x in
                         self._getNitrogenTrioxideProfiles()])

    @property
    @nanitize
    def chlorine_dioxide(self):
        """Chlorine Dioxide concentration in cm ** -3"""
        return np.array([[x[0], x[1], x[2]] for x in
                         self._getChlorineDioxideProfiles()])

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
