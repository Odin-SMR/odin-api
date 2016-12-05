import datetime as DT
from datetime import datetime
import numpy as np
import NC4eraint as NC
from scipy.integrate import odeint
from scipy.interpolate import splmake, spleval, spline
import msis90 as M90
import os
from date_tools import mjd2datetime, datetime2mjd
from odinapi.utils.hdf5_util import HDF5_LOCK


class Donaletty(dict):
    """
         Create ZPT2 file using the new NetCDF ECMWF files
         Created
             Donal Murtagh July 2011.

    """

    def donaletty(self, g5zpt, datetime, newz, lat, lon):
        """Inputs :
                    g5zpt : heights (km) Pressure (hPa) and temperature profile
                            should extend to at least 60 km
                    datetime : datetime object
                    lat : latitude of observation
            Output : ZPT array [3, 0-120]
        """
        def intatm(z, T, newz, normz, normrho, lat):
            """Integrates the temperature profile to yield a new model
            atmosphere in hydrostatic equilibrium including the effect of
            g(z) and M(z).
            newT, p, rho, nodens, n2, o2, o = intatm(z, T, newz, normz,normrho)
            NOTE z in km and returns pressure in pa
            """
            wn2 = 0.78084    # mixing ratio N2
            wo2 = 0.209476   # mixing ratio O2
            # Ro = 8.3143      # ideal gas constant
            k = 1.38054e-23  # jK-1 Boltzmans constant
            m0 = 28.9644

            def geoid_radius(latitude):
                """
                Function from GEOS5 class.
                GEOID_RADIUS calculates the radius of the geoid at the given
                latitude.
                [Re] = geoid_radius(latitude) calculates the radius of the
                geoid (km) at the given latitude (degrees).
                ---------------------------------------------------------------
                Craig Haley 11-06-04
                ---------------------------------------------------------------
                """
                DEGREE = np.pi / 180.0
                EQRAD = 6378.14 * 1000
                FLAT = 1.0 / 298.257
                Rmax = EQRAD
                Rmin = Rmax * (1.0 - FLAT)
                Re = np.sqrt(1./(np.cos(latitude*DEGREE)**2/Rmax**2
                                 + np.sin(latitude*DEGREE)**2/Rmin**2)) / 1000
                return Re

            def intermbar(z):
                Mbars = np.r_[
                    28.9644, 28.9151, 28.73, 28.40, 27.88, 27.27, 26.68, 26.20,
                    25.80, 25.44, 25.09, 24.75, 24.42, 24.10]
                Mbarz = np.arange(85, 151, 5)
                m = np.interp(z, Mbarz, Mbars)
                return m

            def g(z, lat):
                # Re=6372;
                # g=9.81*(1-2.*z/Re)
                return 9.80616 * (
                    1 - 0.0026373 * np.cos(2 * lat * np.pi/180.) +
                    0.0000059*np.cos(2*lat*np.pi/180.)**2) * \
                    (1-2.*z/geoid_radius(lat))

            def func(y, z, xk, cval, k):
                grad = spleval((xk, cval, k), z)
                return grad

            newT = spline(z, T, newz)
            mbar_over_m0 = intermbar(newz)/m0
            splinecoeff = splmake(newz, g(newz, lat)/newT * mbar_over_m0, 3)
            integral = odeint(func, 0, newz, splinecoeff)
            integral = 3.483*np.squeeze(integral.transpose())
            integral = (1*newT[1]/newT*mbar_over_m0*np.exp(-integral))
            # print integral.shape, newz.shape
            normfactor = normrho/spline(newz, integral, normz)
            rho = normfactor*integral
            nodens = rho/intermbar(newz)*6.02282e23/1e3
            n2 = wn2*mbar_over_m0*nodens
            o2 = nodens*(mbar_over_m0*(1+wo2)-1)
            o = 2*(1-mbar_over_m0)*nodens
            o[o < 0] = 0
            p = nodens*1e6*k*newT
            return newT, p, rho, nodens, n2, o2, o

        Ro = 8.3143  # ideal gas constant
        # k = 1.38054e-23  # jK-1 Boltzman's constant
        # fix Msis from 70-150 km with solar effects
        msis = M90.Msis90(solardatafile=self.solardatafile)
        # msisT=msis.extractPTZprofilevarsolar(
        #     datetime, lat,lon, np.arange(75,151,1))[1]
        # to ensure an ok stratopause Donal wants to add a 50 km point
        # from msis
        msisz = np.r_[49., 50., 51, np.arange(75, 151, 1)]
        msisT = msis.extractPTZprofilevarsolar(datetime, lat, lon, msisz)[1]
        z = np.r_[g5zpt[g5zpt[:, 0] < 60, 0], msisz]
        temp = np.r_[g5zpt[g5zpt[:, 0] < 60, 2], msisT]
        # newz=np.arange(121)
        normrho = np.interp(
            [20], g5zpt[:, 0], g5zpt[:, 1])*28.9644/1000/Ro/np.interp(
                [20], g5zpt[:, 0], g5zpt[:, 2])
        newT, newp, rho, nodens, n2, o2, o = intatm(
            z, temp, newz, 20, normrho[0], lat)
        zpt = np.vstack((newz, newp, newT)).transpose()
        return zpt

    def loadecmwfdata(self):

        # load all ecmwffiles for the day
        hourlist = ['00', '06', '12', '18', '24']
        hour = self.datetime.hour
        ibelow = np.int(np.floor(hour/6))
        self.ecm = []
        for ind in range(ibelow, ibelow+2):
            hourstr = hourlist[ind]
            if hourstr == '24':
                # we need to read data from one day later : time 00
                date = self.datetime.date() + DT.timedelta(days=1)
                hourstr = '00'
                # file_time_index = 0
            else:
                date = self.datetime.date()
                # file_time_index = ind

            ecmwffilename = (
                self.ecmwfpath + date.strftime('%Y/%m/') +
                'ei_pl_' + date.strftime('%Y-%m-%d') +
                '-' + hourstr + '.nc')
            # print ecmwffilename
            # TODO: Opening more than one netcdf file at the same time
            #       can result in segfault.
            self.ecm.append(NC.NCeraint(ecmwffilename, 0))

        self.minlat = self.ecm[0]['lats'][0]
        self.latstep = np.mean(np.diff(self.ecm[0]['lats']))
        self.minlon = self.ecm[0]['lons'][0]
        self.lonstep = np.mean(np.diff(self.ecm[0]['lons']))

    def makeprofile(self, midlat, midlon, datetime, scanid):

        ecmz = np.arange(45)*1000  # needs to be in metres
        newz = np.arange(151)
        # extract T and P for the mid lat and long of each scan
        if midlon > 180:
            midlon = midlon - 360
        latpt = np.int(np.floor((midlat-self.minlat)/self.latstep))
        lonpt = np.int(np.floor((midlon-self.minlon)/self.lonstep))
        if midlon < 0:
            midlon = midlon + 360
        hour = datetime.hour
        ibelow = np.int(np.floor(hour/6))  # index in file w.r.t time
        # iabove = ibelow + 1 #not needed, files only contain one time index
        # if iabove==4:
        #     iabove = 0
        T1 = self.ecm[0].extractprofile_on_z('t', latpt, lonpt, ecmz, 0)
        P1 = self.ecm[0].extractprofile_on_z(
            'p', latpt, lonpt, ecmz, 0)/100.  # to hPa
        T2 = self.ecm[1].extractprofile_on_z('t', latpt, lonpt, ecmz, 0)
        P2 = self.ecm[1].extractprofile_on_z(
            'p', latpt, lonpt, ecmz, 0)/100.  # to hPa
        T = (T1*((ibelow+1)*6.-hour)+T2*(hour-ibelow*6.))/6.
        P = (P1*((ibelow+1)*6.-hour)+P2*(hour-ibelow*6.))/6.
        # tempory fix in case ECMWF make temperatures below the surface nans,
        # P shouldn't matter
        T[np.isnan(T)] = 273.0
        zpt = self.donaletty(
            np.c_[ecmz/1000, P, T], datetime, newz, midlat, midlon)
        datadict = {
            'ScanID': scanid,
            'Z': zpt[:, 0],
            'P': zpt[:, 1],
            'T': zpt[:, 2],
            'latitude': midlat,
            'longitude': midlon,
            'datetime': datetime.strftime('%Y-%m-%dT%H:%M:%S')}
        return datadict

    def __init__(self, datetime, solardatafile, ecmwfpath):
        self.datetime = datetime
        self.solardatafile = solardatafile
        self.ecmwfpath = ecmwfpath


def save_zptfile(basedir, date, scanid, zpt):
    # save data to a netcdf file
    datedir = date.strftime('%Y/%m/')
    datadir = basedir + datedir
    if not os.path.exists(datadir):
        os.makedirs(datadir)
    fullfile = get_expected_filename(basedir, date, scanid)

    rootgrp = NC.Dataset(fullfile, 'w', format='NETCDF4')
    datagrp = rootgrp.createGroup('Data')
    # level = datagrp.createDimension('level', 151)

    Z = datagrp.createVariable('Z', 'f4', ('level',))
    Z.units = 'Km'
    Z[:] = zpt['Z']

    P = datagrp.createVariable('P', 'f4', ('level',))
    P.units = 'hPa'
    P[:] = zpt['P']

    T = datagrp.createVariable('T', 'f4', ('level',))
    T.units = 'K'
    T[:] = zpt['T']

    Lat = datagrp.createVariable('latitude', 'f4')
    Lat.units = 'degrees north'
    Lat[:] = zpt['latitude']

    Lon = datagrp.createVariable('longitude', 'f4')
    Lon.units = 'degrees east'
    Lon[:] = zpt['longitude']

    rootgrp.description = (
        'PTZ data for odin-smr level2-processing data source is '
        'ECMWF and NRLMSIS91')
    rootgrp.history = 'Created ' + str(DT.datetime.now())
    rootgrp.geoloc_latitude = "{0} degrees north".format(zpt['latitude'])
    rootgrp.geoloc_longitude = "{0} degrees east".format(zpt['longitude'])
    rootgrp.geoloc_datetime = "{0}".format(zpt['datetime'])

    rootgrp.close()


def check_if_file_exist(basedir, date, scanid):

    fullfile = get_expected_filename(basedir, date, scanid)
    return os.path.isfile(fullfile)


def load_zptfile(basedir, date, scanid):

    fullfile = get_expected_filename(basedir, date, scanid)
    fgr = NC.Dataset(fullfile, mode='r')
    data = fgr.groups['Data']
    Z = data.variables['Z'][:]
    P = data.variables['P'][:]
    T = data.variables['T'][:]
    midlat = float(data.variables['latitude'][:])
    midlon = float(data.variables['longitude'][:])
    datetime = fgr.geoloc_datetime
    zpt = {'ScanID': scanid, 'Z': Z, 'P': P, 'T': T,
           'latitude': midlat, 'longitude': midlon, 'datetime': datetime}
    fgr.close()

    return zpt


def get_expected_filename(basedir, date, scanid):

    datedir = date.strftime('%Y/%m/')
    datadir = basedir + datedir
    filename = "ZPT_{0}.nc".format(scanid)
    fullfile = datadir + filename
    return fullfile


def run_donaletty(mjd, midlat, midlon, scanid):

    # this function can run donaletty for a given scan
    basedir = '/var/lib/odindata'
    # basedir = '/home/bengt/work/odin-api/data'
    ecmwfpath = basedir + '/ECMWF/'
    zptpath = basedir + '/ZPT/'
    solardatafile = basedir + '/Solardata2.db'

    date = mjd2datetime(mjd)

    with HDF5_LOCK:
        if check_if_file_exist(zptpath, date, scanid):
            zpt = load_zptfile(zptpath, date, scanid)
        else:
            # create file
            a = Donaletty(date, solardatafile, ecmwfpath)
            a.loadecmwfdata()
            zpt = a.makeprofile(midlat, midlon, date, scanid)
            save_zptfile(zptpath, date, scanid, zpt)

    zpt['datetime'] = datetime2mjd(
        datetime.strptime(zpt['datetime'], '%Y-%m-%dT%H:%M:%S'))
    return zpt

# midlat = -33.0
# midlon = 275.0
# mjd = 57034.9008
# scanid = 7014769646
# run_donaletty(mjd,midlat,midlon,scanid)
