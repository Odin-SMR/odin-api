# pylint: disable=E0401,C0413
'''extract scan data from odin database and display on webapi'''


from datetime import datetime
import numpy as np
from dateutil.relativedelta import relativedelta
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt  # nopep8
from odinapi.views.utils import copyemptydict  # nopep8
from odinapi.views.freq_calibration import Freqcorr572  # nopep8
from odinapi.views.smr_quality import (  # nopep8
    QualityControl,
    QualityDisplay
)
from odinapi.views.smr_frequency import (  # nopep8
    Smrl1bFreqspec,
    Smrl1bFreqsort,
    freqfunc,
    get_bad_ssb_modules,
    doppler_corr
)


class ScandataExporter(object):
    '''class derived to extract and decode scan data from odin database'''
    def __init__(self, backend, con):
        self.backend = backend
        self.con = con
        self.calstw = 0
        self.refdata = []
        self.specdata = []
        self.scaninfo = []
        self.spectra = []

    def get_db_data(self, freqmode, calstw):
        '''export scan data from database tables'''
        self.calstw = calstw
        # extract all target spectrum data for the scan
        temp = [self.backend, calstw, freqmode]
        query = self.con.query('''
              select ac_level1b.stw, calstw, ac_level1b.backend, orbit,
              mjd, lst, intmode, spectra, alevel, version, channels,
              skyfreq, lofreq, restfreq, maxsuppression, tsys, sourcemode,
              freqmode, efftime, sbpath, latitude, longitude, altitude,
              skybeamhit, ra2000, dec2000, vsource, qtarget, qachieved,
              qerror, gpspos, gpsvel, sunpos, moonpos, sunzd, vgeo, vlsr,
              ssb_fq, inttime, ac_level1b.frontend, hotloada, hotloadb, lo,
              sig_type, imageloada, imageloadb, ac_level1b.soda,
              ac_level0.frontend as ac0_frontend
              from ac_level1b
              join attitude_level1 using (backend, stw)
              join ac_level0 using (backend, stw)
              join shk_level1 on ac_level1b.stw = shk_level1.stw and
              ac_level1b.backend = shk_level1.backend and
              ac_level1b.frontend = shk_level1.frontendsplit
              where calstw = {1} and ac_level1b.backend = '{0}' and
              version = 8 and sig_type = 'SIG' and freqmode = {2}
              order by stw asc, intmode asc'''.format(*temp))
        result = query.dictresult()
        # extract all calibration spectrum data for the scan
        query2 = self.con.query('''
               select ac_cal_level1b.stw, ac_cal_level1b.backend, orbit,
               mjd, lst, intmode, spectra, alevel, version, channels,
               spectype, skyfreq, lofreq, restfreq, maxsuppression,
               sourcemode, freqmode, sbpath, latitude, longitude, altitude,
               tspill, skybeamhit, ra2000, dec2000, vsource, qtarget,
               qachieved, qerror, gpspos, gpsvel, sunpos, moonpos, sunzd,
               vgeo, vlsr, ssb_fq, inttime, ac_cal_level1b.frontend,
               hotloada, hotloadb, lo, sig_type, imageloada, imageloadb,
               ac_cal_level1b.soda, ac_level0.frontend as ac0_frontend
               from ac_cal_level1b
               join attitude_level1 using (backend, stw)
               join ac_level0 using (backend, stw)
               join shk_level1 on ac_cal_level1b.stw = shk_level1.stw and
               ac_cal_level1b.backend = shk_level1.backend and
               ac_cal_level1b.frontend = shk_level1.frontendsplit
               where ac_cal_level1b.stw = {1} and
               ac_cal_level1b.backend = '{0}'
               and version = 8 and freqmode = {2}
               order by stw asc, intmode asc, spectype asc'''.format(*temp))
        result2 = query2.dictresult()
        if result2 == []:
            query2 = self.con.query('''
               select ac_cal_level1b.stw, ac_cal_level1b.backend, orbit,
               mjd, lst, intmode, spectra, alevel, version, channels,
               spectype, skyfreq, lofreq, restfreq, maxsuppression,
               sourcemode, freqmode, sbpath, latitude, longitude, altitude,
               tspill, skybeamhit, ra2000, dec2000, vsource, qtarget,
               qachieved, qerror, gpspos, gpsvel, sunpos, moonpos, sunzd,
               vgeo, vlsr, ssb_fq, inttime, ac_cal_level1b.frontend,
               hotloada, hotloadb, lo, sig_type, imageloada, imageloadb,
               ac_cal_level1b.soda, ac_level0.frontend as ac0_frontend
               from ac_cal_level1b
               join attitude_level1 using (backend, stw)
               join ac_level0 using (backend, stw)
               join shk_level1 on ac_cal_level1b.stw = shk_level1.stw and
               ac_cal_level1b.backend = shk_level1.backend
               where ac_cal_level1b.stw = {1} and
               ac_cal_level1b.backend = '{0}'
               and version = 8 and freqmode = {2}
               order by stw asc, intmode asc, spectype asc'''.format(*temp))
            result2 = query2.dictresult()
            if result2 == []:
                query2 = self.con.query('''
                   select ac_cal_level1b.stw, ac_cal_level1b.backend, orbit,
                   mjd, lst, intmode, spectra, alevel, version, channels,
                   spectype, skyfreq, lofreq, restfreq, maxsuppression,
                   sourcemode, freqmode, sbpath, latitude, longitude, altitude,
                   tspill, skybeamhit, ra2000, dec2000, vsource, qtarget,
                   qachieved, qerror, gpspos, gpsvel, sunpos, moonpos, sunzd,
                   vgeo, vlsr, ssb_fq, inttime, ac_cal_level1b.frontend,
                   hotloada, hotloadb, lo, sig_type, imageloada, imageloadb,
                   ac_cal_level1b.soda, ac_level0.frontend as ac0_frontend
                   from ac_cal_level1b
                   left join attitude_level1  using (backend, stw)
                   join ac_level0  using (backend, stw)
                   join shk_level1 on ac_cal_level1b.stw = shk_level1.stw and
                   ac_cal_level1b.backend = shk_level1.backend
                   where ac_cal_level1b.stw = {1} and
                   ac_cal_level1b.backend = '{0}' and
                   version = 8 and freqmode = {2}
                   order by stw asc, intmode asc,
                   spectype asc'''.format(*temp))
                result2 = query2.dictresult()
        # extract all reference spectrum data for the scan
        if self.backend == 'AC1':
            stw_offset = -1
        elif self.backend == 'AC2':
            stw_offset = 0
        stw1 = result[0]['stw'] - 256
        stw2 = result[-1]['stw'] + 256
        query = self.con.query('''
                  select backend, frontend, ac_level0.stw, inttime, cc,
                  sig_type, mech_type, skybeamhit
                  from ac_level0
                  join attitude_level1  using (backend, stw)
                  join fba_level0 on fba_level0.stw = ac_level0.stw+{2}
                  where ac_level0.stw between {0} and {1}
                  and sig_type = 'REF'
                  order by ac_level0.stw
                             '''.format(*[stw1, stw2, stw_offset]))
        self.refdata = query.dictresult()
        if result == [] or result2 == [] or self.refdata == []:
            print('''1: could not extract all necessary data
                     for '{0}' in scan {1}'''.format(*temp))
            return 0
        # combine target and calibration data
        self.specdata = []  # list of both target and calibration spectrum data
        self.scaninfo = []  # list of calstw tells which scan a spectrum belong
        for ind, row2 in enumerate(result2):
            # fist add calibration spectrum
            self.specdata.append(row2)
            self.scaninfo.append(row2['stw'])
            if ind < len(result2) - 1:
                if result2[ind]['stw'] == result2[ind + 1]['stw']:
                    continue
            for row in result:
                if row['calstw'] == row2['stw']:
                    self.scaninfo.append(row['calstw'])
                    self.specdata.append(row)
        return 1

    def decode_refdata(self):
        '''decode reference data'''
        refdata = {
            'backend': [],
            'frontend': [],
            'stw': [],
            'sig_type': [],
            'mech_type': [],
            'skybeamhit': [],
            'inttime': [],
            'cc': [],
        }
        for row in self.refdata:
            for item in refdata:
                if item == 'cc':
                    corrcoef = np.ndarray(
                        shape=(8 * 96,),
                        dtype='float64',
                        buffer=self.con.unescape_bytea(row['cc'])
                    )
                    # store only zerolags
                    zerolag = []
                    for cci in corrcoef[0::96]:
                        zerolag.append(zerolagfunc(cci, 1.0))
                    refdata['cc'].append(zerolag)
                else:
                    refdata[item].append(row[item])
        for item in refdata:
            refdata[item] = np.array(refdata[item])
        self.refdata = refdata

    def decode_specdata(self):
        '''decode spec data'''
        self.spectra = specdict()
        for ind, res in enumerate(self.specdata):
            spec = specdict()
            spec['calstw'] = self.calstw
            for item in ['stw', 'orbit', 'lst', 'intmode',
                         'channels', 'skyfreq', 'lofreq', 'restfreq',
                         'maxsuppression', 'sbpath', 'latitude', 'longitude',
                         'altitude', 'skybeamhit', 'ra2000', 'dec2000',
                         'vsource', 'sunzd', 'vgeo', 'vlsr', 'inttime',
                         'lo', 'freqmode', 'soda', 'ac0_frontend']:
                spec[item] = res[item]
            spec['mjd'] = self.get_mjd(res)
            spec['hotloada'] = choose_nonzero(
                res['hotloada'], res['hotloadb']
            )
            spec['imageloada'] = choose_nonzero(
                res['imageloada'], res['imageloadb']
            )
            for item in ['qtarget', 'qachieved', 'qerror', 'gpspos',
                         'gpsvel', 'sunpos', 'moonpos']:
                try:
                    spec[item] = np.array(
                        res[item].replace('{', '').replace('}', '').split(',')
                    ).astype(float)
                except AttributeError:
                    spec[item] = ()
            spec['ssb_fq'] = np.array(
                res['ssb_fq'].replace('{', '').replace('}', '').split(',')
            ).astype(float) * 1e6
            # change backend and frontend to integer
            spec['backend'] = backend_char2int(res['backend'])
            spec['frontend'] = frontend_char2int(res['frontend'])
            data = np.ndarray(shape=(res['channels'],), dtype='float64',
                              buffer=self.con.unescape_bytea(res['spectra']))
            try:
                if res['ac0_frontend'] == 'SPL' and res['spectype'] == 'SSB':
                    data = data[0:448]
            except KeyError:
                # this operation only needs to be done with SSB data
                pass
            spec['spectrum'] = data
            # deal with fields that only are stored for calibration
            # or target signals
            try:
                spec['tsys'] = res['tsys']
                spec['efftime'] = res['efftime']
            except KeyError:
                spec['tsys'] = 0.0
                spec['efftime'] = 0.0
            try:
                spec['tspill'] = res['tspill']
                tspill_index = ind
                if res['spectype'] == 'CAL':
                    spec['type'] = 3
                elif res['spectype'] == 'SSB':
                    spec['type'] = 9
            except KeyError:
                spec['type'] = 8
                spec['tspill'] = self.specdata[tspill_index]['tspill']
            spec['sourcemode'] = res['sourcemode'].replace(
                'STRAT', 'stratospheric').replace(
                    'ODD_H', 'Odd hydrogen').replace(
                        'ODD_N', 'Odd nitrogen').replace(
                            'WATER', 'Water isotope').replace(
                                'SUMMER', 'Summer mesosphere').replace(
                                    'DYNAM', 'Transport') + \
                ' FM=' + str(res['freqmode'])
            spec['version'] = 8
            spec['quality'] = 0
            spec['discipline'] = 1
            spec['topic'] = 1
            spec['spectrum_index'] = ind
            spec['obsmode'] = 2
            spec['freqres'] = 1000000.0
            spec['frequency'] = 0
            for item in spec:
                self.spectra[item].append(spec[item])

    def get_mjd(self, data):
        '''decode mjd data'''
        if data['mjd'] is not None:
            return data['mjd']
        else:
            if data['spectype'] in ['SSB', 'CAL']:
                # field MJD is missing for some calibration spectra:
                # use MJD of the first target spectrum in scan
                for row in self.specdata:
                    if row['mjd'] is not None:
                        return row['mjd']


class CalibrationStep2(object):
    '''class derived to perform calibration step 2,
       i.e. remove ripple'''
    def __init__(self, con, freqmode, version):
        self.con = con
        self.spectra = [caldict()]
        self.spec = []
        self.freqmode = freqmode
        self.version = version
        self.altitude_range = []

    def get_hotload_range(self, hotload):
        '''get hotload ranges'''
        if self.freqmode == 1:
            hotload_grid = np.arange(278.5, 294.5)
        elif self.freqmode == 2:
            hotload_grid = np.arange(278.5, 290.5)
        elif self.freqmode == 8:
            hotload_grid = np.arange(284.5, 289.5)
        elif self.freqmode == 13:
            hotload_grid = np.arange(285.5, 290.5)
        elif self.freqmode == 17:
            hotload_grid = np.arange(278.5, 290.5)
        elif self.freqmode == 19:
            hotload_grid = np.arange(278.5, 290.5)
        elif self.freqmode == 21:
            hotload_grid = np.arange(278.5, 290.5)
        else:
            hotload_grid = np.arange(278.5, 290.5)
        if hotload <= hotload_grid[0]:
            hotload = hotload_grid[0]
        elif hotload >= hotload_grid[-1]:
            hotload = hotload_grid[-1]
        hotload_lower = int(np.floor(hotload))
        hotload_upper = hotload_lower + 1
        ind1 = np.nonzero((hotload <= hotload_grid))[0]
        ind2 = np.nonzero((hotload > hotload_grid))[0]
        hl_1 = hotload_grid[ind1[-1]]
        hotload_range1 = '''{{{0},{1}}}'''.format(
            *[hotload_lower, hotload_upper])
        if ind2.shape[0] > 0:
            hl_2 = hotload_grid[ind2[0]]
        else:
            hl_2 = 300  # dummy
        hotload_range2 = '''{{{0},{1}}}'''.format(
            *[hotload_lower, hotload_upper])
        return [hotload_range1, hotload_range2, hl_1, hl_2]

    def get_altitude_range(self):
        '''get altitude range'''
        if self.freqmode in [1, 8]:
            self.altitude_range = '{70000, 120000}'
        elif self.freqmode in [2, 13, 17, 19, 21]:
            self.altitude_range = '{80000, 120000}'
        else:
            self.altitude_range = None

    def get_db_data(self, intmode, ssb_fq, hotload):
        '''export data from odin database'''
        self.get_altitude_range()
        hotload_range = '''{{{0},{1}}}'''.format(
            *[int(np.floor(hotload)), int(np.ceil(hotload))])
        # find out if we already have required data
        for spec in self.spectra:
            if np.all([spec['version'],
                       spec['intmode'],
                       spec['freqmode'],
                       spec['ssb_fq'],
                       spec['altitude_range'],
                       spec['hotload_range']] ==
                      [self.version,
                       intmode,
                       self.freqmode,
                       ssb_fq,
                       self.altitude_range,
                       hotload_range]):
                self.spec = spec
                return
        if self.freqmode in [1, 2, 8, 13, 17, 19, 21]:
            medianfit = self.get_medianfit(intmode,
                                           ssb_fq,
                                           hotload)
        else:
            medianfit = 0.0
        self.spec = caldict()
        self.spec['version'] = self.version
        self.spec['intmode'] = intmode
        self.spec['freqmode'] = self.freqmode
        self.spec['ssb_fq'] = ssb_fq
        self.spec['altitude_range'] = self.altitude_range
        self.spec['hotload_range'] = hotload_range
        self.spec['spectrum'] = medianfit
        self.spectra.append(self.spec)

    def get_medianfit(self, intmode, ssb_fq, hotload):
        '''get median fit spectrum'''
        [hotload_range1, hotload_range2, hl_1, hl_2] = (
            self.get_hotload_range(hotload)
        )
        query = self.con.query('''
          select hotload_range, altitude_range, median_fit, channels
          from ac_cal_level1c where freqmode = {0} and
          version = {1} and intmode = {2} and ssb_fq = '{3}'
          and altitude_range = '{4}' and hotload_range = '{5}'
          order by hotload_range
                                '''.format(*[self.freqmode,
                                             self.version,
                                             intmode,
                                             ssb_fq,
                                             self.altitude_range,
                                             hotload_range1]))
        result1 = query.dictresult()
        query = self.con.query('''
          select hotload_range, altitude_range, median_fit, channels
          from ac_cal_level1c where freqmode = {0} and
          version = {1} and intmode = {2} and ssb_fq = '{3}'
          and altitude_range = '{4}' and hotload_range = '{5}'
          order by hotload_range
                                '''.format(*[self.freqmode,
                                             self.version,
                                             intmode,
                                             ssb_fq,
                                             self.altitude_range,
                                             hotload_range2]))
        result2 = query.dictresult()
        if len(result1) > 0:
            medianfit1 = np.ndarray(shape=(result1[0]['channels'],),
                                    dtype='float64',
                                    buffer=self.con.unescape_bytea(
                                        result1[0]['median_fit']))
        if len(result2) > 0:
            medianfit2 = np.ndarray(shape=(result2[0]['channels'],),
                                    dtype='float64',
                                    buffer=self.con.unescape_bytea(
                                        result2[0]['median_fit']))
        if len(result1) > 0 and len(result2) > 0:
            weight1 = 1 - np.abs(hl_1 - hotload) / np.abs(hl_2 - hl_1)
            medianfit = weight1 * medianfit1 + (1 - weight1) * medianfit2
        elif len(result1) > 0:
            medianfit = medianfit1
        elif len(result2) > 0:
            medianfit = medianfit2
        else:
            medianfit = 0.0
        return medianfit

    def calibration_step2(self, spec, ind):
        '''remove ripple'''
        t_load = planck(spec['hotloada'][ind], spec['skyfreq'][ind])
        # t_sky = planck(2.7, spec['skyfreq'][ind])
        eta = 1 - spec['tspill'][ind] / 300.0  # main beam efficeiency
        weight = 1 / eta * (1.0 - (spec['spectrum'][ind]) / (t_load))
        if not np.isscalar(self.spec['spectrum']):
            f_ind = np.nonzero((spec['spectrum'][ind] != 0))[0]
            reducespec = np.array(weight * self.spec['spectrum'])
            data = np.array(spec['spectrum'][ind])
            data[f_ind] = data[f_ind] - reducespec[f_ind]
            spec['spectrum'][ind] = data
        return spec


def choose_nonzero(value1, value2):
    '''choose value1 if non-zero'''
    if value1 > 0:
        return value1
    else:
        return value2


def caldict():
    '''creates an empty dictionary'''
    cal = dict()
    lista = ['version', 'intmode',
             'freqmode', 'ssb_fq',
             'altitude_range', 'hotload_range',
             'spectrum', ]
    for item in lista:
        cal[item] = []
    return cal


def specdict():
    '''creates an empty dictionary'''
    spec = dict()
    lista = ['stw', 'backend', 'orbit', 'mjd', 'level',
             'lst', 'spectrum', 'intmode', 'channels',
             'skyfreq', 'lofreq', 'restfreq', 'maxsuppression',
             'tsys', 'sourcemode', 'freqmode', 'efftime',
             'sbpath', 'latitude', 'longitude', 'altitude',
             'skybeamhit', 'ra2000', 'dec2000', 'vsource',
             'qtarget', 'qachieved', 'qerror', 'gpspos',
             'gpsvel', 'sunpos', 'moonpos', 'sunzd', 'vgeo',
             'vlsr', 'inttime', 'frontend', 'hotloada',
             'lo', 'sigtype', 'version', 'quality',
             'discipline', 'topic', 'spectrum_index',
             'obsmode', 'type', 'soda', 'freqres',
             'pointer', 'tspill', 'ssb_fq', 'ac0_frontend',
             'calstw', 'frequency', 'zerolagvar', 'ssb', 'imageloada']
    for item in lista:
        spec[item] = []
    return spec


def inv_erfc(zerolag):
    '''inverse error function'''
    pcoef = [1.591863138, -2.442326820, 0.37153461]
    qcoef = [1.467751692, -3.013136362, 1.00000000]
    xterm = 1.0 - zerolag
    yterm = (xterm * xterm - 0.5625)
    yterm = (xterm * (pcoef[0] + (pcoef[1] + pcoef[2] * yterm) * yterm) /
             (qcoef[0] + (qcoef[1] + qcoef[2] * yterm) * yterm))
    return yterm


def backend_char2int(backend):
    '''convert from char to int'''
    if backend == 'AC1':
        return 1
    elif backend == 'AC2':
        return 2


def frontend_char2int(frontend):
    '''convert from char to int'''
    if frontend == '555':
        return 1
    elif frontend == '495':
        return 2
    elif frontend == '572':
        return 3
    elif frontend == '549':
        return 4
    elif frontend == '119':
        return 5
    elif frontend == 'SPL':
        return 6


def zerolagfunc(zlag, vterm):
    '''zerolag function'''
    if zlag >= 1.0 or zlag <= 0.0:
        return 0.0
    else:
        xterm = vterm / inv_erfc(zlag)
    return xterm * xterm / 2.0


def planck(temp, freq):
    '''planck tb'''
    hconst = 6.626176e-34     # Planck constant (Js)
    kconst = 1.380662e-23     # Boltzmann constant (J/K)
    temp0 = hconst * freq / kconst
    if temp > 0.0:
        tbright = temp0 / (np.exp(temp0 / temp) - 1.0)
    else:
        tbright = 0.0
    return tbright


def scan2dictlist_v2():
    '''dummy'''
    return []


def scan2dictlist_v4(spectra):
    '''create a dictionary with lists'''
    datadict = {
        'Version': spectra['version'][2::],
        'Quality': spectra['quality'][2::],
        'STW': spectra['stw'][2::],
        'MJD': spectra['mjd'][2::],
        'Orbit': spectra['orbit'][2::],
        'Spectrum': spectra['spectrum'][2::],
        'TrecSpectrum': spectra['spectrum'][0],
        'Frontend': spectra['frontend'][2::],
        'Backend': spectra['backend'][2::],
        'RA2000': spectra['ra2000'][2::],
        'Dec2000': spectra['dec2000'][2::],
        'Longitude': spectra['longitude'][2::],
        'Latitude': spectra['latitude'][2::],
        'Altitude': spectra['altitude'][2::],
        # 'Qtarget': spectra['qtarget'][2::],
        # 'Qachieved': spectra['qachieved'][2::],
        # 'Qerror': spectra['qerror'][2::],
        'GPSpos': spectra['gpspos'][2::],
        'GPSvel': spectra['gpsvel'][2::],
        'SunPos': spectra['sunpos'][2::],
        'MoonPos': spectra['moonpos'][2::],
        'SunZD': spectra['sunzd'][2::],
        'Vgeo': spectra['vgeo'][2::],
        'Tcal': spectra['hotloada'][2::],
        'Trec': spectra['tsys'][2::],
        'SBpath': spectra['sbpath'][2::],
        # 'LOFreq': spectra['lofreq'][2::],
        # 'SkyFreq': spectra['skyfreq'][2::],
        # 'RestFreq': spectra['restfreq'][2::],
        # 'MaxSuppression': spectra['maxsuppression'][2::],
        'AttitudeVersion': spectra['soda'][2::],
        'FreqRes': spectra['freqres'][2::],
        'FreqCal': spectra['ssb_fq'][2::],
        'IntTime': spectra['inttime'][2::],
        'EffTime': spectra['efftime'][2::],
        'Channels': spectra['channels'][2::],
        'FreqMode': spectra['freqmode'][2::],
        'TSpill': spectra['tspill'][2::],
        'ScanID': spectra['calstw'][2::],
        'Apodization': np.ones(len(spectra['quality']) - 2, dtype='int'),
        'Frequency': spectra['frequency'],
        'ZeroLagVar': spectra['zerolagvar'][2::],
    }
    for item in datadict:
        try:
            datadict[item] = datadict[item].tolist()
        except AttributeError:
            pass
    return datadict


def plot_scan(backend, calstw, spectra):
    '''plot scan data'''
    fig = plt.figure(figsize=(15, 8))
    mjd0 = datetime(1858, 11, 17)
    datei = mjd0 + relativedelta(days=spectra['mjd'][2])
    if spectra['quality'][0] == 0:
        qualstr = 'The Quality of Level1B data for this scan is ok.'
    else:
        qdgr = QualityDisplay(spectra['quality'][0])
        qualstr = qdgr.get_flaginfo()
    titledata = [backend, calstw, spectra['sourcemode'][0],
                 datei, hex(spectra['quality'][0]), qualstr]
    fig.suptitle(
        '''Scan logdata for {0} : {2} : scan-ID {1} : Quality {4} : {3}
        {5}'''.format(*titledata), fontsize=9
    )
    font = {'family': 'sans-serif',
            'size': 9}
    matplotlib.rc('font', **font)
    plot_tangent_altitude(spectra)
    plot_integration_time(spectra)
    plot_noise(spectra)
    plot_latlon(spectra)
    plot_trec_spectrum(spectra)
    plot_spectrum(spectra)
    plot_highalt_spectrum(spectra)
    plot_band_average(spectra)
    plt.show()
    return fig


def plot_tangent_altitude(spectra):
    '''plot tangent altitudes'''
    ax1 = plt.subplot2grid((9, 6), (0, 0), colspan=2, rowspan=1)
    xvec = np.arange(len(spectra['mjd'][2::]))
    plt.plot(xvec, spectra['altitude'][2::] / 1e3, 'b.')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Ztan [Km]')


def plot_integration_time(spectra):
    '''plot integration time'''
    ax1 = plt.subplot2grid((9, 6), (1, 0), colspan=2, rowspan=1)
    xvec = np.arange(len(spectra['mjd'][2::]))
    plt.plot(xvec, spectra['inttime'][2::], 'b.')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('IntTime [s]')
    plt.ylim([0, 4])


def plot_noise(spectra):
    '''plot estimated noise'''
    ax1 = plt.subplot2grid((9, 6), (2, 0), colspan=2, rowspan=1)
    noise = spectra['tsys'][2::] / np.sqrt(spectra['efftime'][2::] * 1e6)
    xvec = np.arange(len(spectra['mjd'][2::]))
    plt.plot(xvec, noise, 'b.')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.yaxis.set_label_text('Noise [K]')
    ax1.xaxis.set_label_text('Spectrum Index [-]')
    plt.ylim([0, 4])


def plot_latlon(spectra):
    '''plot latitude and longitude'''
    ax1 = plt.subplot2grid((8, 6), (3, 0), colspan=2, rowspan=1)
    plt.plot(spectra['longitude'][2::], spectra['latitude'][2::], 'b.')
    ax1.grid(True)
    ax1.minorticks_on()
    xmin = np.floor(np.min(spectra['longitude'][2::]))
    xmax = np.ceil(np.max(spectra['longitude'][2::]))
    plt.xlim([xmin, xmax])
    ymin = np.floor(np.min(spectra['latitude'][2::]))
    ymax = np.ceil(np.max(spectra['latitude'][2::]))
    plt.ylim([ymin, ymax])
    ax1.yaxis.set_label_text('Lat. [Deg.]')
    ax1.xaxis.set_label_text('Lon. [Deg]')


def plot_trec_spectrum(spectra):
    '''plot Trec spectrum'''
    ax1 = plt.subplot2grid((7, 5), (0, 2), colspan=4, rowspan=1)
    freqvec = np.array(spectra['frequency']['IFreqGrid'] +
                       spectra['frequency']['LOFreq'][0]) / 1e9
    xmin = np.floor(np.min(freqvec * 2)) / 2
    xmax = np.ceil(np.max(freqvec * 2)) / 2
    plt.plot(freqvec, spectra['spectrum'][0], '.')
    ax1.grid(True)
    ax1.minorticks_on()
    xmin = np.floor(np.min(freqvec * 2)) / 2
    xmax = np.ceil(np.max(freqvec * 2)) / 2
    plt.xlim([xmin, xmax])
    # ind = np.nonzero((spectra['spectrum'][0] != 0))[0]
    # ymax = np.max(spectra['spectrum'][0][ind])
    # ymin = np.min(spectra['spectrum'][0][ind])
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Trec. [K]')


def plot_spectrum(spectra):
    '''plot all spectrum in scan'''
    ax1 = plt.subplot2grid((7, 5), (1, 2), colspan=4, rowspan=4)
    freqvec = np.array(spectra['frequency']['IFreqGrid'] +
                       spectra['frequency']['LOFreq'][0]) / 1e9
    xmin = np.floor(np.min(freqvec * 2)) / 2
    xmax = np.ceil(np.max(freqvec * 2)) / 2
    for speci in spectra['spectrum'][2::]:
        plt.plot(freqvec, speci, 'k.', markersize=0.5)
    for ztan, spei in zip(spectra['altitude'][2::3],
                          spectra['spectrum'][2::3]):
        plt.plot(freqvec, spei, '.', label=np.int(np.around(ztan/1e3)))
    ax1.grid(True)
    ax1.minorticks_on()
    plt.legend(bbox_to_anchor=(1.02, 0.95), loc=2, borderaxespad=0.)
    ax1.yaxis.set_label_text('Tb. [K]')
    ax1.axes.xaxis.set_ticklabels([])
    plt.xlim([xmin, xmax])
    plt.ylim([-10, 250])


def plot_highalt_spectrum(spectra):
    '''plot average of high altitude spectra'''
    ax1 = plt.subplot2grid((7, 5), (5, 2), colspan=4, rowspan=2)
    zmax = np.max(spectra['altitude'][2::])
    ind = np.nonzero((spectra['altitude'] >= zmax - 20e3))[0]
    freqvec = np.array(spectra['frequency']['IFreqGrid'] +
                       spectra['frequency']['LOFreq'][0]) / 1e9
    xmin = np.floor(np.min(freqvec * 2)) / 2
    xmax = np.ceil(np.max(freqvec * 2)) / 2
    data = []
    index = 0
    for speci in spectra['spectrum']:
        if index > 1 and index in ind:
            data.append(speci)
        index = index + 1
    data = np.array(data)
    data = np.mean(data, 0)
    zmin = np.min(spectra['altitude'][ind])
    zmin = np.int(np.around(zmin / 1e3))
    zmax = np.int(np.around(zmax / 1e3))
    plt.plot(freqvec, data, 'k.', markersize=0.5)
    textstr = '''high altitude ({0}-{1} Km) average'''.format(*[zmin, zmax])
    plt.plot(freqvec, data, '.', label=textstr)
    plt.ylim([-10, 10])
    plt.legend(bbox_to_anchor=(0.02, 0.95), loc=2, borderaxespad=0.)
    ax1.grid(True)
    ax1.minorticks_on()
    plt.xlim([xmin, xmax])
    ax1.yaxis.set_label_text('Tb. [K]')
    ax1.xaxis.set_label_text('Freq. [GHz]')


def plot_band_average(spectra):
    '''plot average of each band as function of tangent altitude'''
    ax1 = plt.subplot2grid((7, 32), (4, 0), colspan=9, rowspan=3)
    slen = len(spectra['spectrum'][2::])
    band = 8
    xaver = np.ndarray(shape=(slen, band))
    for band in range(8):
        ind1 = spectra['frequency']['SubBandIndex'][0][band]
        ind2 = spectra['frequency']['SubBandIndex'][1][band]
        for index, speci in enumerate(spectra['spectrum'][2::]):
            xaver[index, band] = np.mean(speci[ind1 - 1:ind2 - 1])
        if ind1 != -1:
            plt.plot(xaver[:, band], spectra['altitude'][2::] / 1e3,
                     '.-', label=band)
    plt.legend(bbox_to_anchor=(1.02, 1.0), loc=2, borderaxespad=0.)
    ax1.grid(True)
    ax1.minorticks_on()
    plt.xlim([-10, 250])
    ax1.xaxis.set_label_text('Band average Tb. [K]')
    ax1.yaxis.set_label_text('Ztan. [Km]')


def smr_lofreqcorr(scangr):
    '''perform a frequency correction based on Donalds study:
       correction is dependent of frontend
    '''
    driftpara = {
        '1': [-9.77071337e-08, -3.04935334e-10, 1.00004369],
        '2': [-2.85146234e-08, -6.44075856e-10, 1.00005892],
        '19': [-4.93032042e-08, -6.11110969e-10, 1.00005802],
        '13': [-7.20429255e-08, -9.88146910e-10, 1.00007687],
    }
    driftpara['av'] = []
    for ind in range(3):
        driftpara['av'].append(
            (driftpara['2'][ind] + driftpara['19'][ind])/2.0)
    for ind, lofreq in enumerate(scangr.spectra['lo']):
        kfactor = 1.0
        if scangr.spectra['frontend'][ind] == 1:
            # 555: use results derived for FM 13
            fmode = '13'
        elif scangr.spectra['frontend'][ind] == 2:
            # 495: use results derived from FM 1
            fmode = '1'
        elif scangr.spectra['frontend'][ind] == 4:
            # 549: use average results derived from FM 2 and 19
            fmode = 'av'
        else:
            # do not  do any main LO correction for the non-locked frontends
            # but make a specific ssb frequency correction for fm22 data
            if scangr.spectra['freqmode'][ind] == 22:
                scangr.spectra['ssb_fq'][ind][0] = (
                    scangr.spectra['ssb_fq'][ind][0] - 10.5e6
                )
            continue
        kfactor = (driftpara[fmode][0] * scangr.spectra['imageloada'][ind] +
                   driftpara[fmode][1] * scangr.spectra['mjd'][ind] +
                   driftpara[fmode][2])
        scangr.spectra['lofreq'][ind] = lofreq * kfactor


def unsplit_splitmode(scangr):
    '''unpslit data (from splitmode) to make it symmetric with
       data from other modes
    '''
    spectra = copyemptydict(scangr.spectra)
    stw = np.array(scangr.spectra['stw'])
    for ind, _ in enumerate(stw):
        tempdata = copyemptydict(scangr.spectra)
        for item in scangr.spectra:
            tempdata[item] = scangr.spectra[item][ind]
        spectrum = np.zeros(896)
        if scangr.spectra['intmode'][0] == 2047:
            spectrum[224:448] = scangr.spectra['spectrum'][ind][0:224]
            spectrum[672:896] = scangr.spectra['spectrum'][ind][224:448]
        else:
            spectrum[0:224] = scangr.spectra['spectrum'][ind][0:224]
            spectrum[448:672] = scangr.spectra['spectrum'][ind][224:448]
        tempdata['spectrum'] = spectrum
        tempdata['intmode'] = 511
        for item in tempdata:
            spectra[item].append(tempdata[item])
    scangr.spectra = spectra
    for item in scangr.spectra:
        scangr.spectra[item] = np.array(scangr.spectra[item])
    return scangr


def unsplit_normalmode(scangr):
    ''' unsplit deta from intmode != 511 e.g. freqmode 1'''
    spectra = copyemptydict(scangr.spectra)
    for stw_i in np.sort(np.unique(scangr.spectra['stw'])):
        for spectype in [3, 9, 8]:
            specind = np.nonzero((scangr.spectra['stw'] == stw_i) &
                                 (scangr.spectra['type'] == spectype))[0]
            if specind.shape[0] != 2:
                continue
            tempdata = copyemptydict(scangr.spectra)
            for item in scangr.spectra:
                tempdata[item] = scangr.spectra[item][specind[0]]
            freqvec = freqfunc(tempdata['lofreq'],
                               tempdata['skyfreq'],
                               tempdata['ssb_fq'])
            freqi = []
            for item in range(4):
                freqi.append(np.mean(freqvec[item * 224:(item + 1) * 224]))
            spectrum = []
            part1 = scangr.spectra['spectrum'][specind[0]]
            part2 = scangr.spectra['spectrum'][specind[1]]
            spec1i = 0
            spec2i = 0
            for indi in np.argsort(np.array(freqi)):
                if tempdata['skyfreq'] < tempdata['lofreq']:
                    # Lower sideband mode, e.g. FM 8:
                    if indi >= 2:
                        spectrum = np.append(
                            spectrum, part1[spec1i * 224:(spec1i + 1) * 224])
                        spec1i = spec1i + 1
                    else:
                        spectrum = np.append(
                            spectrum, part2[spec2i * 224:(spec2i + 1) * 224])
                        spec2i = spec2i + 1
                else:
                    # Upper sideband mode, e.g. FM 1:
                    if indi < 2:
                        spectrum = np.append(
                            spectrum, part1[spec1i * 224:(spec1i + 1) * 224])
                        spec1i = spec1i + 1
                    else:
                        spectrum = np.append(
                            spectrum, part2[spec2i * 224:(spec2i + 1) * 224])
                        spec2i = spec2i + 1
            tempdata['spectrum'] = spectrum
            tempdata['intmode'] = 511
            for item in tempdata:
                spectra[item].append(tempdata[item])
    scangr.spectra = spectra
    for item in scangr.spectra:
        scangr.spectra[item] = np.array(scangr.spectra[item])
    return scangr


def apply_calibration_step2(con, scangr):
    '''apply correction'''
    calgr = CalibrationStep2(con,
                             scangr.spectra['freqmode'][2],
                             scangr.spectra['version'][2])
    for index, speci in enumerate(scangr.specdata):
        if scangr.spectra['type'][index] == 8:
            # load calibration (high-altitude) spectrum
            calgr.get_db_data(speci['intmode'],
                              speci['ssb_fq'],
                              speci['hotloada'])
            # apply correction
            calgr.calibration_step2(scangr.spectra, index)
    for item in scangr.spectra:
        scangr.spectra[item] = np.array(scangr.spectra[item])
    return scangr


def get_freqinfo(scangr, debug=False):
    '''add frequency info for each spectrum in scan'''
    spectra = np.array(scangr.spectra['spectrum'])
    scangr.spectra['spectrum'] = []
    scangr.spectra['frequency'] = []
    channels = []
    freqinfo = {
        'IFreqGrid': [],
        'LOFreq': [],
        'SubBandIndex': [],
        'ChannelsID': [],
        'AppliedDopplerCorr': [],
    }
    freqgr = Smrl1bFreqspec()
    freqsortgr = Smrl1bFreqsort()

    for numspec, _ in enumerate(scangr.spectra['stw']):
        freqvec = freqgr.get_frequency(scangr.spectra, numspec)
        bad_modules = get_bad_ssb_modules(
            scangr.spectra['backend'][numspec], spectra, freqvec, debug
        )
        freqvec.shape = (freqvec.shape[0] * freqvec.shape[1],)
        freqvec, tempspec, ssb, channels_id = (
            freqsortgr.get_sorted_ac_spectrum(
                freqvec, spectra[numspec], bad_modules
            )
        )
        # correcting freqvec for Doppler
        lofreq, freqvec = doppler_corr(scangr.spectra['skyfreq'][numspec],
                                       scangr.spectra['restfreq'][numspec],
                                       scangr.spectra['lofreq'][numspec],
                                       freqvec)
        if (scangr.spectra['frontend'][0] == 3 and
                (scangr.spectra['freqmode'][0] == 14 or
                 scangr.spectra['freqmode'][0] == 22 or
                 scangr.spectra['freqmode'][0] == 24)):
            # make a frequency adjustement of measurements from 572 frontend
            # according to Julias description in L1ATBD
            if numspec == 0:
                fcgr = Freqcorr572(lofreq + freqvec,
                                   spectra[2::, channels_id],
                                   scangr.spectra['altitude'][2::])
                fcgr.run_freq_corr()
            if fcgr.correction_is_ok:
                lofreq = lofreq - fcgr.fdiff * 1e9
            else:
                # mark that frequency can not be trusted
                scangr.spectra['quality'][numspec] = (
                    scangr.spectra['quality'][numspec] + 0x0400
                )
        if numspec == 0:
            freqinfo['IFreqGrid'] = freqvec.tolist()
            freqinfo['SubBandIndex'].append(ssb[1::3])
            freqinfo['SubBandIndex'].append(ssb[2::3])
            freqinfo['ChannelsID'] = np.array(channels_id + 1).tolist()
        if numspec > 1:
            freqinfo['LOFreq'].append(lofreq)
            freqinfo['AppliedDopplerCorr'].append(
                -(scangr.spectra['skyfreq'][numspec] -
                  scangr.spectra['restfreq'][numspec]))
        channels.append(tempspec.shape[0])
        scangr.spectra['spectrum'].append(
            np.around(tempspec, decimals=3).tolist()
        )
    scangr.spectra['frequency'] = freqinfo
    scangr.spectra['channels'] = channels
    return scangr


def get_scan_data_v2(con, backend, freqmode, scanno, debug=False):
    '''get scan data'''
    calstw = int(scanno)
    scangr = ScandataExporter(backend, con)
    try:
        isok = scangr.get_db_data(freqmode, calstw)
    except IndexError:
        isok = 0
    if isok == 0:
        print('data for scan {0} not found'.format(calstw))
        return {}
    scangr.decode_refdata()
    scangr.decode_specdata()
    # perform calibration step2 for target spectrum
    scangr = apply_calibration_step2(con, scangr)
    if scangr.spectra['ac0_frontend'][0] == 'SPL':
        # "unpslit data" to make it symmetric with data from other modes
        scangr = unsplit_splitmode(scangr)
    if (scangr.spectra['intmode'][0] != 511 and
            scangr.spectra['ac0_frontend'][0] != 'SPL'):
        # unsplit data from none 511 intmode
        scangr = unsplit_normalmode(scangr)
    # perform a frequency correction based on Donals study:
    smr_lofreqcorr(scangr)
    # add frequency vector to each spectrum in the scangr.spectra structure
    scangr = get_freqinfo(scangr, debug)
    # scangr.spectra is a dictionary containing the relevant data
    # quality control of data
    qualgr = QualityControl(scangr.spectra, scangr.refdata)
    qualgr.run_control()
    scangr.spectra['quality'] = qualgr.quality
    scangr.spectra['zerolagvar'] = qualgr.zerolagvar
    # scangr.spectra is a dictionary containing the relevant data
    return scangr.spectra
