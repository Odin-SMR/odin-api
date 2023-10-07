import os
from datetime import datetime

import h5py  # type: ignore
import numpy as np
import s3fs  # type: ignore


def read_sageIII_file(filename, date, species, event_type):
    """Convenience function for getting all data from a Sage III file"""
    # Handle case of species -- special case for OClO:
    species = species.upper()
    if species == "OCLO":
        species = "OClO"

    # Construct filename:
    versions = {"lunar": "v03", "solar": "v04"}

    sageIII_datapath = "s3://odin-vds-data/Meteor3M_SAGEIII_Level2/"

    year = date[0:4]
    month = date[5:7]
    sageIII_datapath = os.path.join(sageIII_datapath, year, month, versions[event_type])
    sageIII_file = os.path.join(sageIII_datapath, filename)

    # Open correct file object:
    dataObject = {"lunar": Sage3Lunar, "solar": Sage3Solar}

    data_dict = {}
    with dataObject[event_type](sageIII_file) as data:
        # Generate data dict
        data_dict["FileName"] = filename
        data_dict["Instrument"] = "Meteor-3M SAGE III"
        data_dict["EventType"] = event_type
        data_dict["MJDStart"] = data.datetimes_mjd.tolist()[0]
        data_dict["MJDEnd"] = data.datetimes_mjd.tolist()[1]
        data_dict["LatStart"] = data.latitudes.tolist()[0]
        data_dict["LatEnd"] = data.latitudes.tolist()[1]
        data_dict["LongStart"] = data.longitudes.tolist()[0]
        data_dict["LongEnd"] = data.longitudes.tolist()[1]
        data_dict["Pressure"] = data.pressure.tolist()
        data_dict["Temperature"] = data.temperature.tolist()
        data_dict[species] = data.speciesData[species].tolist()

    # Return data
    return data_dict


def nanitize(f):
    """A decorator function for replacing undefined values in returned
    nd-arrays with nan.
    """

    def _decoration(self):
        data = f(self)
        if data.dtype == np.int32:
            maximum = np.iinfo(np.int32).max
        else:
            maximum = np.finfo(np.float32).max

        return np.where(data == maximum, np.nan, data)

    return _decoration


class Sage3Data:
    def __init__(self, filename):
        self.s3 = s3fs.S3FileSystem()
        self.f = self.s3.open(filename)
        self._hfile = h5py.File(self.f)
        self.speciesData = {"O3": self.ozone, "NO2": self.nitrogen_dioxide}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._hfile.close()
        self.f.close()

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
        for n in range(timestamps.shape[0]):
            if np.isnan(timestamps[n]).any():
                datetimes.append(np.nan)
            else:
                datetimes.append(self._parse_timestamp(timestamps[n]))
        return datetimes

    @property
    @nanitize
    def raw_timestamps(self):
        timestamps = np.array(
            [[x[0][0], x[0][1]] for x in self._getSpaceTimeCoordinates()]
        )
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
        return np.array(
            [[x[0], x[1], x[4]] for x in self._getNitrogenDioxideProfiles()]
        )

    def _getGroundTrackSpaceTimeCoordinates(self):
        """Get ground track times, longitudes and latitudes for the event in
        the file.
        """
        key = (
            "Section 4.0 - Event Identification/"
            "Section 4.3 - Ground Track Data Over This Event/"
            "Section 4.3 - Ground Track Data Over This Event"
        )
        data = self._hfile[key]
        if type(data) == h5py.Dataset:
            return list(data)
        return []

    def _getSpaceTimeCoordinates(self):
        """Get measurement times, longitudes and latitudes for the event in
        the file.
        """
        key1 = (
            "Section 4.0 - Event Identification/"
            "Section 4.1 - Science Data Start Information/"
            "Section 4.1 - Science Data Start Information"
        )
        key2 = (
            "Section 4.0 - Event Identification/"
            "Section 4.2 - Science Data End Information/"
            "Section 4.2 - Science Data End Information"
        )
        data1 = self._hfile[key1]
        data2 = self._hfile[key2]

        if (type(data1) == h5py.Dataset) and (type(data2) == h5py.Dataset):
            return list(data1), list(data2)
        return []

    def _getTempAndPressureProfiles(self):
        key = (
            "Section 5.0 - Altitude-based Data/"
            "Section 5.1 - Temperature_pressure profiles/"
            "Temperature_pressure profiles"
        )
        data = self._hfile[key]
        if type(data) == h5py.Dataset:
            return list(data)
        return []

    def _getOzoneProfiles(self):
        key = (
            "Section 5.0 - Altitude-based Data/"
            "Section 5.2A - Mesospheric Ozone profiles/"
            "Mesospheric Ozone profiles"
        )
        data = self._hfile[key]
        if type(data) == h5py.Dataset:
            return list(data)
        return []

    def _getNitrogenDioxideProfiles(self):
        key = (
            "Section 5.0 - Altitude-based Data/"
            "Section 5.4 - Nitrogen Dioxide profiles/"
            "Nitrogen Dioxide profiles"
        )
        data = self._hfile[key]
        if type(data) == h5py.Dataset:
            return list(data)
        return []

    def _parse_timestamp(self, timestamp):
        date = str(timestamp.astype(int)[0])
        year = int(date[0:4])
        month = int(date[4:6])
        day = int(date[6:8])

        time = timestamp.astype(int)[1]
        hour = time // 10000
        minute = (time - hour * 10000) // 100
        second = time - hour * 10000 - minute * 100

        return datetime(year, month, day, hour, minute, second)


class Sage3Solar(Sage3Data):
    def __init__(self, filename):
        super(Sage3Solar, self).__init__(filename)
        self.speciesData = {
            "O3": self.ozone,
            "H2O": self.water_vapour,
            "NO2": self.nitrogen_dioxide,
        }

    @property
    @nanitize
    def water_vapour(self):
        """Water vapour concentration in cm ** -3"""
        return np.array([[x[0], x[1], x[2]] for x in self._getWaterProfiles()])

    def _getWaterProfiles(self):
        key = (
            "Section 5.0 - Altitude-based Data/"
            "Section 5.3 - Water Vapor profiles/"
            "Water Vapor profiles"
        )
        data = self._hfile[key]
        if type(data) == h5py.Dataset:
            return list(data)
        return []


class Sage3Lunar(Sage3Data):
    def __init__(self, filename):
        super(Sage3Lunar, self).__init__(filename)
        self.speciesData = {
            "O3": self.ozone,
            "NO2": self.nitrogen_dioxide,
            "NO3": self.nitrogen_trioxide,
            "OClO": self.chlorine_dioxide,
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
        return np.array(
            [[x[0], x[1], x[2]] for x in self._getNitrogenTrioxideProfiles()]
        )

    @property
    @nanitize
    def chlorine_dioxide(self):
        """Chlorine Dioxide concentration in cm ** -3"""
        return np.array(
            [[x[0], x[1], x[2]] for x in self._getChlorineDioxideProfiles()]
        )

    def _getTempAndPressureProfiles(self):
        key = (
            "Section 6.1 - Temperature_pressure profiles/"
            "Temperature_pressure profiles"
        )
        data = self._hfile[key]
        if type(data) == h5py.Dataset:
            return list(data)
        return []

    def _getOzoneProfiles(self):
        key = "Section 6.2 - Ozone profiles /" "Ozone profiles"
        key_opt = "Section 6.2 - Ozone profiles/" "Ozone profiles"
        if key in self._hfile.keys():
            data = self._hfile[key]
        else:
            data = self._hfile[key_opt]
        if type(data) == h5py.Dataset:
            return list(data)
        return []

    def _getNitrogenDioxideProfiles(self):
        key = "Section 6.3 - Nitrogen Dioxide profiles/" "Nitrogen Dioxide profiles"
        data = self._hfile[key]
        if type(data) == h5py.Dataset:
            return list(data)
        return []

    def _getNitrogenTrioxideProfiles(self):
        key = "Section 6.4 - Nitrogen Trioxide profiles/" "Nitrogen Dioxide profiles"
        data = self._hfile[key]
        if type(data) == h5py.Dataset:
            return list(data)
        return []

    def _getChlorineDioxideProfiles(self):
        key = "Section 6.5 - OClO profiles/" "OClO profiles"
        data = self._hfile[key]
        if type(data) == h5py.Dataset:
            return list(data)
        return []
