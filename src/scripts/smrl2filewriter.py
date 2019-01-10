#! /usr/bin/env python
'''Functionality to generate Odin/SMR level2 netcdf files'''


import os
from argparse import ArgumentParser
import datetime as DT
import json

import numpy as np
import ephem
import requests as R
from dateutil.relativedelta import relativedelta
from netCDF4 import Dataset
import spacepy.coordinates as coord
from spacepy.time import Ticktock
from simpleflock import SimpleFlock
import pyproj

from odinapi.views.database import DatabaseConnector


PRESSURE_GRID_CCI = np.array([
    450, 400, 350, 300, 250, 200, 170, 150, 130, 115, 100,
    90, 80, 70, 50, 40, 30, 20, 15, 10, 7, 5, 4, 3, 2, 1.5,
    1.0, 0.7, 0.5, 0.4, 0.3, 0.2, 0.15, 0.1, 0.07, 0.05, 0.04,
    0.03, 0.02, 0.015, 0.01, 0.007, 0.005, 0.004, 0.003, 0.002,
    0.0015, 0.001, 0.0007, 0.0005, 0.0004, 0.0003, 0.0002,
    0.00015, 0.0001
])


class Smrl2filewriter(object):
    '''class derived to generate Odin/SMR level2 netcdf files'''
    def __init__(self, l2idata, l2data, project, dbcon,
                 use_pgrid_cci=False):
        self.l2item = l2data['Product'].split('-')[0].rstrip()
        self.project = project
        self.l2idata = l2idata
        self.l2data = l2data
        self.dbcon = dbcon
        self.use_pgrid_cci = use_pgrid_cci
        self.odinl2file = self.generate_filename()

    def generate_filename(self):
        '''generate product filename:
           currently:
           odin-l2-{project}-{product}-{pgridtype}-{year}-month}.nc
        '''
        l2datadir = os.path.join('/data/odin-l2-data', self.project)
        if not os.path.isdir(l2datadir):
            os.makedirs(l2datadir)
        mjd0 = DT.datetime(1858, 11, 17)
        datetime = mjd0 + DT.timedelta(self.l2data['MJD'])
        l2item = self.l2data['Product'].replace(' - ', '-').replace(' ', '-')
        if self.use_pgrid_cci:
            pgridtype = 'grid'
        else:
            pgridtype = 'std'
        l2filename = '''OdinSMR-L2-{0}-{1}-{2}-{3}-{4:02d}.nc'''.format(
            self.project,
            l2item,
            pgridtype,
            datetime.year,
            datetime.month
        )
        return os.path.join(l2datadir, l2filename)

    def add_scan_to_file(self, rootgrp):
        '''filter data to be included:
           currently only check if scan already is included
        '''
        ids_included = np.array(
            rootgrp['Satellite_specific_data']['scanID']
        )
        if np.any(ids_included == self.l2data['ScanID']):
            print '''scan {0} already included'''.format(self.l2data['ScanID'])
            return False
        return True

    def _open_file(self):
        if not os.path.isfile(self.odinl2file):
            #  create new file
            rootgrp = Dataset(self.odinl2file, 'w', format='NETCDF4')
            self.createnewfile = True
        else:
            #  open file to append data to existing file
            rootgrp = Dataset(self.odinl2file, 'a', format='NETCDF4')
            self.createnewfile = False
        return rootgrp

    def write_scan_to_file(self):
        '''apply the functions of the class to write data from
           one scan to file'''
        with SimpleFlock(self.odinl2file + '.lock', timeout=600):
            with self._open_file() as rootgrp:
                if self.createnewfile:
                    #  create dimensions
                    if self.use_pgrid_cci:
                        nlevels = np.array(PRESSURE_GRID_CCI).shape[0]
                    else:
                        nlevels = np.array(self.l2data['Pressure']).shape[0]
                    ntimes = None
                    self.create_dimensions(rootgrp, nlevels, ntimes)
                    index = 0
                    add_scan_to_file = True
                else:
                    #  get the number of scans already included in file
                    index = rootgrp['Geolocation']['time'].shape[0]
                    add_scan_to_file = self.add_scan_to_file(rootgrp)
                if add_scan_to_file:
                    #  write geolocation data
                    self.write_geolocation(rootgrp, index)
                    #  write retrieval results
                    self.write_retrieval_results(rootgrp, index)
                    #  write specific data for selection
                    self.write_data_for_selection(rootgrp, index)
                    #  write satellite specific data
                    self.write_satellite_specific_data(rootgrp, index)
                    #  write apriori data
                    self.write_apriori_data(rootgrp, index)
                    #  create/update attributes
                    self.write_global_netcdf_attributes(rootgrp)

    @staticmethod
    def create_dimensions(self, rootgrp, nlevels, ntimes):
        '''create time and level dimensions'''
        rootgrp.createDimension('level', nlevels)
        rootgrp.createDimension('time', ntimes)
        rootgrp.createDimension('range', 2)

    def write_geolocation(self, rootgrp, index):
        '''Common measurement geolocation:
           - time (from 01/01/1900)
           - latitude (-90 to +90)
           - longitude (from -180 to +180)
           - pressure (natural grid of the instrument)
        '''
        datagroup = 'Geolocation'
        if index == 0:
            #  create group and items
            datagrp = rootgrp.createGroup('Geolocation')
            times = datagrp.createVariable('time', 'f8', ('time',))
            latitudes = datagrp.createVariable('latitude', 'f4', ('time',))
            longitudes = datagrp.createVariable('longitude', 'f4', ('time',))
            pressures = datagrp.createVariable('pressure', 'f4', ('level',))
            if self.use_pgrid_cci:
                pressures[:] = PRESSURE_GRID_CCI
            else:
                pressures[:] = np.array(self.l2data['Pressure']) * 0.01
            times.units = 'days since 1900-01-01 00:00:00.0'
            latitudes.units = 'degrees north'
            longitudes.units = 'degrees east'
            pressures.units = 'hPa'
        else:
            #  get pointers to existing items (except pressure)
            times = rootgrp[datagroup]['time']
            latitudes = rootgrp[datagroup]['latitude']
            longitudes = rootgrp[datagroup]['longitude']
        #  fill in data to items
        times[index] = mjd2daysince19000101(self.l2data['MJD'])
        latitudes[index] = self.l2data['Lat1D']
        longitudes[index] = fix_longitude(self.l2data['Lon1D'])

    def write_retrieval_results(self, rootgrp, index):
        '''- concentration in vmr
           - concentration error in vmr
           - vertical resolution
        '''
        datagroup = 'Retrieval_results'
        if index == 0:
            #  create group and items
            datagrp = rootgrp.createGroup(datagroup)
            l2values = datagrp.createVariable(
                'l2_value', 'f4', ('time', 'level',)
            )
            l2errors = datagrp.createVariable(
                'l2_error', 'f4', ('time', 'level',)
            )
            resolutions = datagrp.createVariable(
                'vertical_resolution', 'f4', ('time', 'level',)
            )
            if self.l2data['Product'] == 'Temperature':
                l2values.units = 'K'
                l2errors.units = 'K'
            else:
                l2values.units = 'VMR'
                l2errors.units = 'VMR'
            resolutions.units = 'km'
        else:
            #  get pointers to existing items
            l2values = rootgrp[datagroup]['l2_value']
            l2errors = rootgrp[datagroup]['l2_error']
            resolutions = rootgrp[datagroup]['vertical_resolution']
        #  fill in data to items
        if self.use_pgrid_cci:
            #  interpolate to p_grid_cci
            if self.l2item == 'Temperature':
                l2values[index, :] = interpl2(
                    PRESSURE_GRID_CCI,
                    np.array(self.l2data['Pressure']) * 0.01,
                    self.l2data['Temperature']
                )
            else:
                l2values[index, :] = interpl2(
                    PRESSURE_GRID_CCI,
                    np.array(self.l2data['Pressure']) * 0.01,
                    self.l2data['VMR']
                )
            l2errors[index, :] = interpl2(
                PRESSURE_GRID_CCI,
                np.array(self.l2data['Pressure']) * 0.01,
                self.l2data['ErrorTotal']
            )
            resolutions[index, :] = interpl2(
                PRESSURE_GRID_CCI,
                np.array(self.l2data['Pressure']) * 0.01,
                get_resolution(
                    self.l2data['Altitude'], self.l2data['AVK']
                )
            )
        else:
            #  use the original retrieval grid data
            if self.l2item == 'Temperature':
                l2values[index, :] = self.l2data['Temperature']
            else:
                l2values[index, :] = self.l2data['VMR']
            l2errors[index, :] = self.l2data['ErrorTotal']
            resolutions[index, :] = get_resolution(
                self.l2data['Altitude'], self.l2data['AVK']
            )

    def write_data_for_selection(self, rootgrp, index):
        '''- quality flags
           - measurement response
           - averaging kernels
           - local time
           - magnetic coordinates (Donal has a Python routine called geomag
             to calculate that)
           - equivalent latitude (Not relevant for the Meso products, but would
             be good to include it in the final products. Should be discussed.)
           - valid vertical range
        '''
        datagroup = 'Specific_data_for_selection'
        if index == 0:
            #  create group and items
            datagrp = rootgrp.createGroup(datagroup)
            quals = datagrp.createVariable('quality', 'f4', ('time',))
            quals.units = '-'
            measr = datagrp.createVariable(
                'measurement_response', 'f4', ('time', 'level',)
            )
            measr.units = '-'
            if not self.use_pgrid_cci:
                #  only include these variables when using
                #  the original retrieval grid
                avks = datagrp.createVariable(
                    'averaging_kernel', 'f4', ('time', 'level', 'level',)
                )
                avks.units = '-'
            ltimes = datagrp.createVariable(
                'local_time', 'f4', ('time',)
            )
            ltimes.units = 'h'
            glats = datagrp.createVariable(
                'geomagnetic_latitude', 'f4', ('time',)
            )
            glats.units = 'degrees north'
            glons = datagrp.createVariable(
                'geomagnetic_longitude', 'f4', ('time',)
            )
            glons.units = 'degrees east'
            #  skip equivalent_latitude for now
            #  eqlats = datagrp.createVariable(
            #      'equivalent_latitude', 'f4', ('time',)
            #  )
            #  eqlats.units = '-'
            vertranges = datagrp.createVariable(
                'valid_vertical_range', 'f4', ('time', 'range',)
            )
            vertranges.units = 'hPa'
        else:
            #  get pointers to existing items
            quals = rootgrp[datagroup]['quality']
            measr = rootgrp[datagroup]['measurement_response']
            if not self.use_pgrid_cci:
                avks = rootgrp[datagroup]['averaging_kernel']
            ltimes = rootgrp[datagroup]['local_time']
            glats = rootgrp[datagroup]['geomagnetic_latitude']
            glons = rootgrp[datagroup]['geomagnetic_longitude']
            #  skip equivalent_latitude for now
            #  eqlats = rootgrp[datagroup]['equivalent_latitude']
            vertranges = rootgrp[datagroup]['valid_vertical_range']
        #  fill in data to items
        quals[index] = 0  # N.B change
        if self.use_pgrid_cci:
            #  interpolate to p_grid_cci
            measr[index, :] = interpl2(
                PRESSURE_GRID_CCI,
                np.array(self.l2data['Pressure']) * 0.01,
                self.l2data['MeasResponse']
            )
        else:
            #  use the original retrieval grid data
            measr[index, :] = self.l2data['MeasResponse']
        if not self.use_pgrid_cci:
            #  only include these variables when using
            #  the original retrieval grid
            avks[index, :, :] = self.l2data['AVK']
        ltimes[index] = solartime(self.l2data['MJD'], self.l2data['Lon1D'])
        coords = geotomag(
            np.mean(np.array(self.l2data['Altitude'])) * 0.001,
            np.float(self.l2data['Lat1D']),
            fix_longitude(np.float(self.l2data['Lon1D'])),
            mjd2datetime(self.l2data['MJD']).strftime("%Y%m%dT%H:%M:%S")
        )
        glats[index] = coords.lati
        glons[index] = coords.long
        #  eqlats[index] = 0  # N.B change
        vertranges[index] = get_valid_range(
            np.array(self.l2data['Pressure']) * 0.01,
            np.array(self.l2data['MeasResponse'])
        )

    def write_satellite_specific_data(self, rootgrp, index):
        '''- orbit number
           - scan ID
           - frequency mode
           - latitude at all measurement points
           - longitude at all measurement points
        '''
        datagroup = 'Satellite_specific_data'
        if index == 0:
            #  create group and items
            datagrp = rootgrp.createGroup(datagroup)
            orbitnumbers = datagrp.createVariable('orbit', 'u8', ('time',))
            orbitnumbers.units = '-'
            scanids = datagrp.createVariable('scanID', 'u8', ('time',))
            scanids.units = '-'
            freqmodes = datagrp.createVariable('freqmode', 'u8', ('time',))
            freqmodes.units = '-'
            if not self.use_pgrid_cci:
                #  only include these variables when using
                #  the original retrieval grid
                latitudes = datagrp.createVariable(
                    'latitude', 'f4', ('time', 'level',)
                )
                latitudes.units = 'degrees north'
                longitudes = datagrp.createVariable(
                    'longitude', 'f4', ('time', 'level',)
                )
                longitudes.units = 'degrees east'
        else:
            #  get pointers to existing items
            orbitnumbers = rootgrp[datagroup]['orbit']
            scanids = rootgrp[datagroup]['scanID']
            freqmodes = rootgrp[datagroup]['freqmode']
            if not self.use_pgrid_cci:
                #  only include these variables when using
                #  the original retrieval grid
                latitudes = rootgrp[datagroup]['latitude']
                longitudes = rootgrp[datagroup]['longitude']
        #  fill in data to items
        orbitnumbers[index] = get_orbit_from_scanid(
            self.dbcon, self.l2data['ScanID']
        )
        scanids[index] = self.l2data['ScanID']
        freqmodes[index] = self.l2idata['FreqMode']
        if not self.use_pgrid_cci:
            #  only include these variables when using
            #  the original retrieval grid
            latitudes[index, :] = self.l2data['Latitude']
            longitudes[index, :] = fix_longitude(self.l2data['Longitude'])

    def write_apriori_data(self, rootgrp, index):
        '''a priori data'''
        datagroup = 'Apriori'
        if index == 0:
            #  create group and items
            datagrp = rootgrp.createGroup(datagroup)
            l2aprioris = datagrp.createVariable(
                'l2_apriori', 'f4', ('time', 'level',)
            )
            if self.l2item == 'Temperature':
                l2aprioris.units = 'K'
            else:
                l2aprioris.units = 'VMR'
        else:
            #  get pointers to existing items
            l2aprioris = rootgrp[datagroup]['l2_apriori']
        #  fill in data to items
        if self.use_pgrid_cci:
            #  interpolate to p_grid_cci
            l2aprioris[index, :] = interpl2(
                PRESSURE_GRID_CCI,
                np.array(self.l2data['Pressure']) * 0.01,
                self.l2data['Apriori']
            )
        else:
            #  use the original retrieval grid data
            l2aprioris[index, :] = self.l2data['Apriori']

    def write_global_netcdf_attributes(
        self,
        rootgrp,
        prodversion='0001',
        l1version='8.0',
        l2version='3.0',
        file_vers_description='first version',
    ):
        '''- source file identification
           - instrument name
           - platform name
           - source data version
           - data version
           - file creation date
           - project name: ESA MesosphEO / ESA Odin reprocessing
           - responsible institute
           - name and email of the person responsible for the dataset
             within the project
        '''
        if not hasattr(rootgrp, 'title'):
            # write all attributes
            rootgrp.title = (
                'ESA MesosphEO / ESA Odin reprocessing ' +
                '{0} {1} product level 2'.format(*[self.project, self.l2item])
            )
            rootgrp.institution = 'Chalmers University of Technology'
            rootgrp.source = 'Odin/SMR L2 version {0}'.format(l2version)
            #  rootgrp.history = '?' skip this?
            rootgrp.platform = 'Odin'
            rootgrp.sensor = 'SMR'
            rootgrp.affiliation = (
                'Chalmers University of Technology, ' +
                'Department of Earth and Space Sciences'
            )
            rootgrp.date_created = (
                'Created ' + DT.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            )
            rootgrp.creator_name = 'Donal Murtagh'
            rootgrp.creator_url = 'odin.rss.chalmers.se'
            rootgrp.creator_email = 'donal.murtagh@chalmers.se'
            rootgrp.address = '412 96 Gothenburg, Sweden'
            rootgrp.naming_authority = 'Chalmers University of Technology'
            rootgrp.product_version = prodversion
            rootgrp.level_1_data_version = l1version
            rootgrp.level_2_data_version = l2version
            rootgrp.level_2_data_product = self.l2data['Product']
            rootgrp.file_id = self.odinl2file
            rootgrp.comment = (
                'These data were created at Chalmers as part of the ' +
                'ESA MesosphEO / ESA Odin reprocessing projects'
            )
            rootgrp.summary = (
                'This dataset contains screened level-2 limb ' +
                '{0} profiles from Odin/SMR'.format(self.l2item)
            )
            rootgrp.keywords = (
                '{0}, remote sensing, atmosphere, Odin, SMR'.format(
                    self.l2item
                )
            )
            rootgrp.value_for_nodata = 'NaN'
            #  rootgrp.Conventions = 'CF-1.5' skip this?
            rootgrp.standard_name_vocabulary = (
                'NetCDF Climate and Forecast(CF) Metadata ' +
                'Convention version 18'
            )
            rootgrp.license = (
                'ESA MesosphEO / ESA Odin reprocessing guidelines'
            )
            rootgrp.restriction = (
                'Restricted under the use of ESA MesosphEO / ' +
                'ESA Odin reprocessing guidelines'
            )
            rootgrp.geospatial_lat_min = '-90.0'
            rootgrp.geospatial_lat_max = '+90.0'
            rootgrp.geospatial_lon_min = '-180.0'
            rootgrp.geospatial_lon_max = '+180.0'
            rootgrp.geospatial_vertical_max = get_geospatial_vertical_max(
                rootgrp['Geolocation']['pressure']
            )
            rootgrp.geospatial_vertical_min = get_geospatial_vertical_min(
                rootgrp['Geolocation']['pressure']
            )
            rootgrp.string_date_format = 'YYYYMMDDThhmmssZ'
            rootgrp.time_coverage_start = get_time_coverage_start(
                rootgrp['Geolocation']['time']
            )
            rootgrp.time_coverage_end = get_time_coverage_end(
                rootgrp['Geolocation']['time']
            )
            rootgrp.number_of_press_levels = get_number_of_pres_levels(
                rootgrp['Geolocation']['pressure']
            )
            rootgrp.number_of_profiles = get_number_of_profiles(
                rootgrp['Geolocation']['time']
            )
            rootgrp.file_version = '''fv-{0}'''.format(*[prodversion])
            rootgrp.file_version_description = '''fv-{0}: {1}'''.format(
                *[prodversion, file_vers_description]
            )
        else:
            #  only update attribute that needs to be updated
            rootgrp.date_created = (
                'Created ' + DT.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            )
            rootgrp.time_coverage_start = get_time_coverage_start(
                rootgrp['Geolocation']['time']
            )
            rootgrp.time_coverage_end = get_time_coverage_end(
                rootgrp['Geolocation']['time']
            )
            rootgrp.number_of_profiles = get_number_of_profiles(
                rootgrp['Geolocation']['time']
            )


def get_valid_range(pressure_grid, meas_resp, min_resp=0.7):
    '''get valid range of data w.r.t measurement response'''
    index = np.nonzero(meas_resp >= min_resp)[0]
    if index.shape[0] == 0:
        return [np.nan, np.nan]
    else:
        return [np.max(pressure_grid[index]),
                np.min(pressure_grid[index])]


def interpl2(newgrid, origgrid, origdata):
    '''interpolate to a finer pressure grid'''
    newdata = np.interp(
        np.log(np.array(newgrid)),
        np.flipud(np.log(np.array(origgrid))),
        np.flipud(np.array(origdata))
    )
    index = np.nonzero(newgrid < np.min(origgrid))[0]
    newdata[index] = np.nan
    index = np.nonzero(newgrid > np.max(origgrid))[0]
    newdata[index] = np.nan
    return newdata


def get_time_coverage_start(time):
    '''get time of first scan in file'''
    return (
        DT.datetime(1900, 1, 1) +
        DT.timedelta(
            seconds=np.min(np.array(time)) * 24 * 3600
        )).strftime("%Y%m%dT%H%M%SZ")


def get_time_coverage_end(time):
    '''get time of last scan in file'''
    return (
        DT.datetime(1900, 1, 1) +
        DT.timedelta(
            seconds=np.max(np.array(time)) * 24 * 3600
        )).strftime("%Y%m%dT%H%M%SZ")


def get_number_of_pres_levels(pressure):
    '''get number of pressure levels'''
    return np.array(pressure).shape[0]


def get_number_of_profiles(time):
    '''get number of scans included in file'''
    return np.array(time).shape[0]


def get_geospatial_vertical_max(pressure):
    '''get min pressure level'''
    return '{0} hPa'.format(np.min(np.array(pressure)))


def get_geospatial_vertical_min(pressure):
    '''get max pressure level'''
    return '{0} hPa'.format(np.max(np.array(pressure)))


def mjd2daysince19000101(mjd):
    '''transform mjd to days since 1900-01-01'''
    daydiff = DT.datetime(1900, 1, 1) - DT.datetime(1858, 11, 17)
    return mjd - daydiff.days


def mjd2datetime(mjd):
    '''transform from mjd to datetime'''
    return (
        DT.datetime(1858, 11, 17) +
        DT.timedelta(
            seconds=int(mjd * 24 * 3600)
        )
    )


def fix_longitude(longitude):
    '''make sure longitude is in range [-180, 180]'''
    longitude = np.array([longitude])
    ind = np.nonzero(longitude > 180)[0]
    longitude[ind] = longitude[ind] - 360
    return longitude


def get_resolution(altitude, avks):
    '''get resolution from averaging kernels:
       full width at half maximum'''
    altitude = np.array(altitude)
    avks = np.array(avks)
    #  interpolate avk to a fine grid and check
    #  which elements are greater than max/2
    alt_hres = np.arange(altitude[0], altitude[-1])
    resolution = []
    for indi, avk in enumerate(avks):
        avk_hres = np.interp(alt_hres, altitude, avk)
        index = np.nonzero(avk_hres >= np.max(avk) / 2.0)[0]
        if index.shape[0] == 0:
            resolution.append(np.nan)
            continue
        if index[0] == 0:
            #  take care of edge effects:
            #  double upper width used as proxy
            resolution.append(
                2 * (alt_hres[index][-1] - altitude[indi])
            )
        else:
            resolution.append(
                np.abs(np.max(alt_hres[index]) - np.min(alt_hres[index]))
            )
    return np.array(resolution) * 0.001


def solartime(mjd, longitude, sun=ephem.Sun()):
    '''get solar time'''
    observer = ephem.Observer()
    observer.date = mjd2datetime(mjd)
    observer.long = longitude * np.pi / 180.0
    sun.compute(observer)
    #  sidereal time == ra (right ascension) is the highest point (noon)
    hour_angle = observer.sidereal_time() - sun.ra
    lst = str(ephem.hours(hour_angle + ephem.hours('12:00')).norm)
    #  norm for 24h
    return (float(lst.split(':')[0]) +
            float(lst.split(':')[1]) / 60.0 +
            float(lst.split(':')[2]) / 3600.0)


def geodetic2geocentric(lati, longi, alti):
    '''convert between geodetic to geocentric coordinates'''
    ecef1 = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
    lla1 = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
    ecef2 = pyproj.Proj(proj='geocent', ellps='sphere')
    lla2 = pyproj.Proj(proj='latlong', ellps='sphere')
    xpos, ypos, zpos = pyproj.transform(
        lla1, ecef1, longi, lati, alti, radians=False
    )
    longi, lati, _ = pyproj.transform(
        ecef2, lla2, xpos, ypos, zpos, radians=False
    )
    return lati, longi


def geotomag(alti, lati, longi, date):
    '''transformation from geodetic to geomagnetic
       coordinates:
       call with altitude in kilometers and lat/lon
       in degrees
    '''
    lati, longi = geodetic2geocentric(lati, longi, alti)
    rearth = 6371.0  # mean Earth radius in kilometers
    #  setup the geographic coordinate object with altitude in earth radii
    cvals = coord.Coords(
        [np.float((alti/rearth + rearth)) / rearth,
         np.float(lati),
         np.float(longi)],
        'GEO', 'sph', ['Re', 'deg', 'deg']
    )
    #  set time epoch for coordinates:
    cvals.ticks = Ticktock([date], 'ISO')
    #  return the magnetic coords in the same units as the geographic:
    return cvals.convert('MAG', 'sph')


def get_orbit_from_scanid(con, scanid):
    '''get odin orbit'''
    query = con.query(
        '''
        select orbit from attitude_level1
        where stw between {0} - 1000  and {0} + 1000
        limit 1
        '''.format(scanid)
    )
    result = query.dictresult()
    return int(result[0]['orbit'])


def get_test_data(file_name='odin_result.json'):
    '''function for test'''
    with open(os.path.join(TEST_DATA_DIR, file_name)) as inp:
        return json.load(inp)


def create_scan_list(scan):
    '''function for test, create a list of scan data
       here all scans are identical'''
    scans = []
    for dummy in range(10):
        scans.append(scan)
    return scans


def get_urls_l2scandata(project, freqmode, year, month):
    '''get urls holding l2 scandata for one month'''
    #  create a list of urls holding scan data for one month
    startime = DT.datetime(year, month, 1)
    endtime = startime + relativedelta(months=1)
    urls_l2scandata = []
    while startime < endtime:
        url_scans = (
            'http://malachite.rss.chalmers.se/' +
            'rest_api/v5/level2/development/' +
            '{0}/{1}/scans/?start_time={2}&end_time={3}'.format(
                project,
                freqmode,
                startime.strftime("%Y-%m-%d"),
                (startime + relativedelta(days=1)).strftime("%Y-%m-%d"))
        )
        startime = startime + relativedelta(days=1)
        #  get list of urls
        urls_l2scan = R.get(url_scans).json()
        if urls_l2scan['Count'] > 0:
            for item in urls_l2scan['Data']:
                urls_l2scandata.append(item['URLS']['URL-level2'])
    return urls_l2scandata


def create_l2_file(dbcon, project, freqmode, product, year, month,
                   use_pgrid_cci=False, debug=True):
    '''create l2 file, consisting 1 month of data, data from a single scan
       is added individually to the file within the loop'''
    if debug is False:
        #  'operational' mode
        url_to_scans = get_urls_l2scandata(project, freqmode, year, month)
        print '''{0} scans found.'''.format(len(url_to_scans))
        for url_to_scan in url_to_scans:
            print '''adding {0} to file'''.format(url_to_scan)
            scandata = R.get(url_to_scan).json()
            for l2data in scandata['Data']['L2']['Data']:
                if l2data['Product'] == product:
                    smrncgr = Smrl2filewriter(
                        scandata['Data']['L2i']['Data'],
                        l2data,
                        project,
                        dbcon,
                        use_pgrid_cci=use_pgrid_cci
                    )
                    smrncgr.write_scan_to_file()
    else:
        #  create file based on test data
        scan = get_test_data(file_name='odin_result_meso.json')
        scans = create_scan_list(scan)
        for scandata in scans:
            for l2data in scandata['L2']:
                if l2data['Product'] == product:
                    l2data['ScanID'] += 1  # this is just for testing
                    smrncgr = Smrl2filewriter(
                        scandata['L2I'],
                        l2data,
                        project,
                        dbcon,
                        use_pgrid_cci=use_pgrid_cci
                    )
                    smrncgr.write_scan_to_file()


def test_create_l2_file(dbcon, project, freqmode, product, year, month):
    '''simple test of Smrl2filewriter to check if file can be
       created and some dimensions, units, and values are ok'''
    #  check if file exist
    l2file = os.path.join(
        '/data/odin-l2-data/meso',
        'OdinSMR-L2-meso-O3-557-GHz-45-to-115-km-std-2007-06.nc'
    )
    if os.path.isfile(l2file):
        os.remove(l2file)
    #  create test file, standard grid
    create_l2_file(dbcon, project, freqmode, product, year, month,
                   use_pgrid_cci=False, debug=True)
    #  read and check file content
    #  check some dimension, units, and value
    ncgrp = Dataset(l2file, 'r')
    test = []
    test.append(
        ncgrp['Satellite_specific_data']['freqmode'][0] == 13
    )
    test.append(
        np.array(ncgrp['Retrieval_results']['l2_value']).shape[0] == 10
    )
    test.append(
        np.array(ncgrp['Retrieval_results']['l2_value']).shape[1] == 16
    )
    test.append(
        ncgrp['Retrieval_results']['l2_error'].units == 'VMR'
    )
    test.append(
        np.abs(
            ncgrp['Retrieval_results']['vertical_resolution'][0][0] - 4.558
        ) < 0.001
    )
    ncgrp.close()
    #  delete file
    if os.path.isfile(l2file):
        os.remove(l2file)
    l2file = os.path.join(
        '/data/odin-l2-data/meso',
        'OdinSMR-L2-meso-O3-557-GHz-45-to-115-km-grid-2007-06.nc'
    )
    if os.path.isfile(l2file):
        os.remove(l2file)
    #  create test file , cci-grid
    create_l2_file(dbcon, project, freqmode, product, year, month,
                   use_pgrid_cci=True, debug=True)
    #  read and check file content
    #  check some dimension, units, and value
    ncgrp = Dataset(l2file, 'r')
    test.append(
        ncgrp['Satellite_specific_data']['freqmode'][0] == 13
    )
    test.append(
        np.array(ncgrp['Retrieval_results']['l2_value']).shape[0] == 10
    )
    test.append(
        np.array(ncgrp['Retrieval_results']['l2_value']).shape[1] == 55
    )
    test.append(
        ncgrp['Retrieval_results']['l2_error'].units == 'VMR'
    )
    test.append(
        np.abs(
            ncgrp['Retrieval_results']['vertical_resolution'][0][26] - 4.558
        ) < 0.001
    )
    if np.all(test):
        print '10 of 10 tests passed'
    else:
        raise Exception('Test did not pass!')
    ncgrp.close()
    #  delete file
    if os.path.isfile(l2file):
        os.remove(l2file)


def setup_arguments():
    """setup command line arguments"""
    parser = ArgumentParser(description="Create odin/smr level2 file")
    parser.add_argument("-r", "--project", dest="project",
                        action="store",
                        default='meso',
                        help="level2 processing project "
                        "(default: meso)")
    parser.add_argument("-p", "--product", dest="product",
                        action="store",
                        default='O3 / 557 GHz / 45 to 115 km',
                        help="level2 product of project "
                        "(default: 'O3 / 557 GHz / 45 to 115 km')")
    parser.add_argument("-f", "--freqmode", dest="freqmode",
                        action="store",
                        default='13',
                        help="frequency mode of observation "
                        "(default: 13)")
    parser.add_argument("-y", "--year", dest="year",
                        action="store",
                        default='2007',
                        help="year of observation "
                        "(default: 2007)")
    parser.add_argument("-m", "--month", dest="month",
                        action="store",
                        default='5',
                        help="month of observation "
                        "(default: 5)")
    parser.add_argument("-t", "--pgrid_type", dest="pgrid_type",
                        action="store",
                        default='nominal',
                        help="pressure grid type "
                        "(options: nominal, cci) "
                        "(default: nominal)")
    parser.add_argument("-d", "--debug", dest="debug",
                        action="store",
                        default='False',
                        help="option for testing that script works, "
                        "while set to True, no file is saved"
                        "(default: False)")

    args = parser.parse_args()
    return args


if __name__ == "__main__":

    ARGS = setup_arguments()
    TEST_DATA_DIR = os.path.join(
        os.path.dirname(__file__), 'testdata').replace('scripts',
                                                       'odinapi/test')
    DBCON = DatabaseConnector()

    USE_PGRID_CCI = bool(ARGS.pgrid_type == 'cci')
    if bool(ARGS.debug == 'True'):
        test_create_l2_file(
            DBCON, ARGS.project, ARGS.freqmode, ARGS.product,
            int(ARGS.year), int(ARGS.month)
        )
    else:
        create_l2_file(
            DBCON, ARGS.project, ARGS.freqmode, ARGS.product,
            int(ARGS.year), int(ARGS.month),
            use_pgrid_cci=USE_PGRID_CCI,
            debug=False
        )
    DBCON.close()
