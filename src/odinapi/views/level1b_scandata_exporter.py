import numpy
import copy
from pg import DB
from sys import stderr,stdout,stdin,argv,exit
from utils import copyemptydict
import matplotlib.pyplot as plt
import matplotlib
from dateutil.relativedelta import relativedelta
from datetime import datetime


class Scan_data_exporter():
    def __init__(self,backend,con):
        self.backend=backend
        self.con=con

    def get_db_data(self,freqmode,calstw):
        '''export orbit data from database tables'''
        self.calstw = calstw

        #extract all target spectrum data for the orbit
        temp=[self.backend,calstw,freqmode]
        query=self.con.query('''
              select calstw,stw,backend,orbit,mjd,lst,intmode,spectra,
              alevel,version,channels,skyfreq,lofreq,restfreq,maxsuppression,
              tsys,sourcemode,freqmode,efftime,sbpath,latitude,longitude,
              altitude,skybeamhit,ra2000,dec2000,vsource,qtarget,qachieved,
              qerror,gpspos,gpsvel,sunpos,moonpos,sunzd,vgeo,vlsr,ssb_fq,
              inttime,ac_level1b.frontend,hotloada,hotloadb,lo,sig_type,
              ac_level1b.soda
              from ac_level1b
              join attitude_level1  using (backend,stw)
              join ac_level0  using (backend,stw)
              join shk_level1  using (backend,stw)
              where calstw={1} and backend='{0}' and version=8
              and sig_type='SIG' and
              freqmode={2}
              order by stw asc,intmode asc'''.format(*temp))
        result=query.dictresult()
    
        #extract all calibration spectrum data for the orbit
        query2=self.con.query('''
               select stw,backend,orbit,mjd,lst,intmode,spectra,alevel,version,
               channels,spectype,skyfreq,lofreq,restfreq,maxsuppression,
               sourcemode,freqmode,sbpath,latitude,longitude,altitude,tspill,
               skybeamhit,ra2000,dec2000,vsource,qtarget,qachieved,qerror,
               gpspos,gpsvel,sunpos,moonpos,sunzd,vgeo,vlsr,ssb_fq,inttime,
               ac_cal_level1b.frontend,hotloada,hotloadb,lo,sig_type,
               ac_cal_level1b.soda
               from ac_cal_level1b
               join attitude_level1  using (backend,stw)
               join ac_level0  using (backend,stw)
               join shk_level1  using (backend,stw)
               where stw={1} and backend='{0}' and version=8
               and freqmode={2}
               order by stw asc,intmode asc,spectype asc'''.format(*temp))
        result2=query2.dictresult()

        if result==[] or result2==[]:
            print '''could not extract all necessary data for '{0}' in scan {1}'''.format(*temp) 
            return 0



        #combine target and calibration data 
        self.specdata=[] #list of both target and calibration spectrum data
        self.scaninfo=[] #list of calstw that tells which scan a spectra belongs too
        for ind,row2 in enumerate(result2):
            #fist add calibration spectrum
            self.specdata.append(row2)
            self.scaninfo.append(row2['stw'])
            if ind<len(result2)-1:
                if result2[ind]['stw']==result2[ind+1]['stw']:
                    continue
            for row in result:
                if row['calstw']==row2['stw']:
                    self.scaninfo.append(row['calstw'])
                    self.specdata.append(row) 
    
        return 1

    def decode_data(self):

        self.spectra = specdict()

        for ind,res in enumerate(self.specdata):

            spec = specdict()

            spec['calstw'] = self.calstw

            for item in ['stw','mjd','orbit','lst','intmode',
                     'channels','skyfreq','lofreq','restfreq',
                     'maxsuppression','sbpath','latitude','longitude',
                     'altitude','skybeamhit','ra2000','dec2000',
                     'vsource','sunzd','vgeo','vlsr','inttime',
                     'hotloada','lo','freqmode','soda']:
                spec[item] = res[item]

            if spec['hotloada']==0:
                spec['hotloada'] = res['hotloadb']

            for item in ['qtarget','qachieved','qerror','gpspos',
                     'gpsvel','sunpos','moonpos']:
                spec[item]=eval(
                           res[item].replace( '{','(').replace('}',')') )   

            ssb_fq1=eval(res['ssb_fq'].replace('{','(').replace('}',')'))
            spec['ssb_fq']= numpy.array(ssb_fq1)*1e6

            #change backend and frontend to integer
            if res['backend'] == 'AC1':

                spec['backend'] = 1

            elif res['backend'] == 'AC2':

                spec['backend'] = 2

            if res['frontend'] == '555':

                spec['frontend'] = 1

            elif res['frontend'] == '495':

                spec['frontend'] = 2

            elif res['frontend'] == '572':

                spec['frontend'] = 3

            elif res['frontend'] == '549':

                spec['frontend'] = 4

            elif res['frontend'] == '119':

                spec['frontend'] = 5

            elif res['frontend'] == 'SPL':

                spec['frontend'] = 6

            data = numpy.ndarray(shape=(res['channels'],),dtype='float64',
                           buffer=self.con.unescape_bytea(res['spectra']))
            spec['spectrum'] = data

            #deal with fields that only are stored for calibration
            #or target signals
            try:
                spec['tsys'] = res['tsys']
                spec['efftime'] = res['efftime']
            except:
                spec['tsys'] = 0.0
                spec['efftime'] = 0.0

            try:
                spec['tspill'] = res['tspill']
                tspill_index = ind
                if res['spectype']=='CAL':
                    spec['type'] = 3
                elif res['spectype']=='SSB':
                    spec['type'] = 9
            except:
                spec['type'] = 8
                spec['tspill'] = self.specdata[tspill_index]['tspill']

            spec['sourcemode'] = res['sourcemode'].replace(
                'STRAT','stratospheric').replace(
                'ODD_H','Odd hydrogen').replace(
                'ODD_N','Odd nitrogen').replace(
                'WATER','Water isotope').replace(
                'SUMMER','Summer mesosphere').replace(
                'DYNAM','Transport')+\
                ' FM='+str(res['freqmode']) 

            spec['level'] = res['alevel']+res['version']

            spec['version'] = 262
            spec['quality'] = 0
            spec['discipline'] = 1
            spec['topic'] = 1
            spec['spectrum_index'] = ind         
            spec['obsmode'] = 2

            spec['freqres'] = 1000000.0
            spec['pointer'] = [ind,res['channels'],1,res['stw']]
            if 1:
                spec['frequency'] = 0
            elif (ind==0 or (ind>0 and self.specdata[ind-1]['lofreq']<>spec['lofreq']
                                and self.specdata[ind-1]['skyfreq']<>spec['skyfreq'])):
                spec['frequency'] = freq(spec['lofreq'], spec['skyfreq'], spec['ssb_fq'])
            else: 
                spec['frequency'] = self.spectra['frequency'][ind-1]            

            for item in spec.keys(): 
                self.spectra[item].append(spec[item])

class Calibration_step2():
    def __init__(self,con):
        self.con=con
        self.spectra=[caldict()]

    def get_db_data(self,backend,frontend,version,intmode,
            sourcemode,freqmode,ssb_fq,altitude_range,hotload):

        hotload_lower=int(numpy.floor(hotload))
        hotload_upper=int(numpy.ceil(hotload))
        hotload_range='''{{{0},{1}}}'''.format(*[hotload_lower,hotload_upper])  
        temp=[backend,frontend,version,intmode,sourcemode,freqmode,
              ssb_fq,altitude_range,hotload_range]

        #find out if we already have required data
        for ind,spec in enumerate(self.spectra):

            if (spec['backend'] == backend and 
                spec['frontend'] == frontend and
                spec['version'] == version and 
                spec['intmode'] == intmode and 
                spec['sourcemode'] == sourcemode and
                spec['freqmode'] == freqmode and 
                spec['ssb_fq'] == ssb_fq and 
                spec['altitude_range'] == altitude_range and 
                spec['hotload_range'] == hotload_range):
                self.spec = spec
                return

        #now we did not have the required data, so load it    
        query=self.con.query('''
              select hotload_range,median_fit,channels
              from ac_cal_level1c where backend='{0}' and
              frontend='{1}' and version={2} and intmode={3}
              and sourcemode='{4}' and freqmode={5} and ssb_fq='{6}' and
              altitude_range='{7}' and hotload_range='{8}'
                             '''.format(*temp))
        result=query.dictresult()

        if result==[]:
            medianfit=0.0
        else:
            medianfit=numpy.ndarray(shape=(result[0]['channels'],),
                                dtype='float64',
                                buffer=self.con.unescape_bytea(
                                    result[0]['median_fit']))
        self.spec = caldict()
        self.spec['backend'] = backend
        self.spec['frontend'] = frontend
        self.spec['version'] = version
        self.spec['intmode'] = intmode
        self.spec['sourcemode'] = sourcemode
        self.spec['freqmode'] = freqmode
        self.spec['ssb_fq'] = ssb_fq
        self.spec['altitude_range'] = altitude_range
        self.spec['hotload_range'] = hotload_range
        self.spec['spectrum'] = medianfit
        self.spectra.append(self.spec)


    def calibration_step2(self,spec,ind):
        #compensate for ripple on sky beam signal
        t_load = planck(spec['hotloada'][ind],spec['skyfreq'][ind])
        t_sky = planck(2.7,spec['skyfreq'][ind])
        eta = 1-spec['tspill'][ind]/300.0 #main beam efficeiency
        w = 1/eta*(1- ( spec['spectrum'][ind] )/ ( t_load ))
        spec['spectrum'][ind] = spec['spectrum'][ind]-w*self.spec['spectrum']
        return spec



def caldict():
    cal = dict()
    lista = ['backend', 'frontend', 'version', 'intmode',
             'sourcemode', 'freqmode', 'ssb_fq',
             'altitude_range', 'hotload_range',
             'spectrum',]

    for item in lista:
        cal[item] = []

    return cal

def specdict():
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
             'pointer', 'tspill','ssb_fq', 
             'calstw','frequency']

    for item in lista:
        spec[item] = []

    return spec


  

def planck(T,f):
    h = 6.626176e-34;     # Planck constant (Js)
    k = 1.380662e-23;     # Boltzmann constant (J/K)
    T0 = h*f/k
    if (T > 0.0): 
        Tb = T0/(numpy.exp(T0/T)-1.0);
    else:         
        Tb = 0.0;

    return Tb


def freq(lofreq,skyfreq,LO):
    n=896
    f=numpy.zeros(shape=(n,))
    seq=[1,1,1,-1,1,1,1,-1,1,-1,1,1,1,-1,1,1] 
    m=0
    for adc in range(8):
        if seq[2*adc]:
            k = seq[2*adc]*112
            df = 1.0e6/seq[2*adc]
            if seq[2*adc+1] < 0:
                df=-df
            for j in range(k): 
                f[m+j] = LO[adc/2] +j*df;
            m += k;
    fdata = numpy.zeros(shape=(n,))
    if skyfreq >= lofreq:
        for i in range(n):
            v = f[i]
            v = lofreq + v
            v /= 1.0e9
            fdata[i] = v
    else: 
        for i in range(n):
            v = f[i]
            v = lofreq - v
            v /= 1.0e9
            fdata[i]=v
    return fdata


def scan2dictlist(spectra):

    datadict = {
     'Version'         : spectra['version'],
     'Level'           : spectra['level'],
     'Quality'         : spectra['quality'],
     'STW'             : spectra['stw'],
     'MJD'             : spectra['mjd'],
     'Orbit'           : spectra['orbit'],
     'LST'             : spectra['lst'],
     'Source'          : spectra['sourcemode'],
     'Discipline'      : spectra['discipline'],
     'Topic'           : spectra['topic'],
     'Spectrum'        : spectra['spectrum'],
     'ObsMode'         : spectra['obsmode'],
     'Type'            : spectra['type'],
     'Frontend'        : spectra['frontend'],
     'Backend'         : spectra['backend'],
     'SkyBeamHit'      : spectra['skybeamhit'],
     'RA2000'          : spectra['ra2000'],
     'Dec2000'         : spectra['dec2000'],
     'VSource'         : spectra['vsource'],
     'Longitude'       : spectra['longitude'],
     'Latitude'        : spectra['latitude'],
     'Altitude'        : spectra['altitude'],
     'Qtarget'         : spectra['qtarget'],
     'Qachieved'       : spectra['qachieved'],
     'Qerror'          : spectra['qerror'],
     'GPSpos'          : spectra['gpspos'],
     'GPSvel'          : spectra['gpsvel'],
     'SunPos'          : spectra['sunpos'],
     'MoonPos'         : spectra['moonpos'],
     'SunZD'           : spectra['sunzd'],
     'Vgeo'            : spectra['vgeo'],
     'Vlsr'            : spectra['vlsr'],
     'Tcal'            : spectra['hotloada'],
     'Tsys'            : spectra['tsys'],
     'SBpath'          : spectra['sbpath'],
     'LOFreq'          : spectra['lofreq'],
     'SkyFreq'         : spectra['skyfreq'],
     'RestFreq'        : spectra['restfreq'],
     'MaxSuppression'  : spectra['maxsuppression'],
     'AttitudeVersion' : spectra['soda'],
     'FreqRes'         : spectra['freqres'],
     'FreqCal'         : spectra['ssb_fq'],
     'IntMode'         : spectra['intmode'],
     'IntTime'         : spectra['inttime'],
     'EffTime'         : spectra['efftime'],
     'Channels'        : spectra['channels'],
     'FreqMode'        : spectra['freqmode'],
     'TSpill'          : spectra['tspill'],
     'ScanID'          : spectra['calstw'],
     'Frequency'       : spectra['frequency']*1e9,
    }

    for item in datadict.keys():
        try:
            datadict[item] = datadict[item].tolist()
        except:
            pass
  
    return datadict 



def plot_scan(backend,calstw,spectra):

    fig = plt.figure(figsize = (15,8))
    mjd0 = datetime(1858,11,17)
    datei = mjd0 + relativedelta(days = spectra['mjd'][0])

    fig.suptitle('''Scan logdata for {0} : {2} : scan-ID {1} : {3}'''.format(*[backend, calstw, spectra['sourcemode'][0],datei]))
    font = {'family' : 'sans-serif',
        'size'   : 8}
    matplotlib.rc('font', **font)    

    #plot tangent altitudes
    ax1 = plt.subplot2grid((9,6), (0,0), colspan=2,rowspan=1)
    dx = numpy.arange(len(spectra['mjd'][2::]))
    plt.plot(dx,spectra['altitude'][2::]/1e3,'b.')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Ztan [Km]')

    #plot integration time
    ax1 = plt.subplot2grid((9,6), (1,0), colspan=2,rowspan=1)
    plt.plot(dx,spectra['inttime'][2::],'b.')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('IntTime [s]')
    plt.ylim([0,4])

    #plot estimated noise
    ax1 = plt.subplot2grid((9,6), (2,0), colspan=2,rowspan=1)
    noise = spectra['tsys']/numpy.sqrt(spectra['efftime']*1e6)
    plt.plot(dx,noise[2::],'b.')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.yaxis.set_label_text('Noise [K]')
    ax1.xaxis.set_label_text('Spectrum Index [-]')
    plt.ylim([0,4])     

    #plot latitude and longitude
    ax1 = plt.subplot2grid((8,6), (3,0), colspan=2,rowspan=1)
    plt.plot(spectra['longitude'],spectra['latitude'],'b.')
    ax1.grid(True)
    ax1.minorticks_on()
    xmin = numpy.floor(numpy.min(spectra['longitude']))
    xmax = numpy.ceil(numpy.max(spectra['longitude']))
    plt.xlim([xmin,xmax])
    ymin = numpy.floor(numpy.min(spectra['latitude']))
    ymax = numpy.ceil(numpy.max(spectra['latitude']))
    plt.ylim([ymin,ymax])
    ax1.yaxis.set_label_text('Lat. [Deg.]')
    ax1.xaxis.set_label_text('Lon. [Deg]')  

    #plot Trec spectrum
    f = freq(spectra['lofreq'][0],spectra['skyfreq'][0],spectra['ssb_fq'][0])
    ax1 = plt.subplot2grid((7,5), (0,2), colspan=4,rowspan=1)

    if backend =='AC1':
        plt.plot(f,spectra['spectrum'][0],'.',markersize=0.5)
        plt.plot(f[112*2::],spectra['spectrum'][0][112*2::],'.')
    elif backend =='AC2':
        plt.plot(f,spectra['spectrum'][0],'.')

    ax1.grid(True)
    ax1.minorticks_on()
    limx = numpy.array([numpy.floor(numpy.min(f*2)),numpy.ceil(numpy.max(f*2))])/2
    plt.xlim(limx)
    ind = numpy.nonzero((spectra['spectrum'][0]<>0))[0]
    ymax = numpy.max(spectra['spectrum'][0][ind])
    ymin = numpy.min(spectra['spectrum'][0][ind])
    dy = 100
    limy = [numpy.floor(ymin*dy)/dy-dy,numpy.ceil(ymax*dy)/dy+dy]
    plt.ylim(limy)
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Trec. [K]')

    #plot all spectrum in scan
    ax1 = plt.subplot2grid((7,5), (1,2), colspan=4,rowspan=4)
    if backend == 'AC1':
        for z,s in zip(spectra['altitude'],spectra['spectrum'][2::]):
            plt.plot(f,s,'k.',markersize=0.5)
        for z,s in zip(spectra['altitude'][2::3],spectra['spectrum'][2::3]):
            plt.plot(f[112*2::],s[112*2::],'.',label=numpy.int(numpy.around(z/1e3)))
    elif backend == 'AC2':
        for z,s in zip(spectra['altitude'],spectra['spectrum'][2::]):
            plt.plot(f,s,'k.',markersize=0.5)
        for z,s in zip(spectra['altitude'][2::3],spectra['spectrum'][2::3]):
            plt.plot(f,s,'.',label=numpy.int(numpy.around(z/1e3)))

    ax1.grid(True)
    ax1.minorticks_on()
    plt.legend(bbox_to_anchor=(1.02, 0.95), loc=2, borderaxespad=0.)
    limx = numpy.array([numpy.floor(numpy.min(f*2)),numpy.ceil(numpy.max(f*2))])/2
    ax1.yaxis.set_label_text('Tb. [K]')
    ax1.axes.xaxis.set_ticklabels([])
    plt.xlim(limx)
    plt.ylim([-10, 250])

    #plot average of high altitude spectra
    zmax = numpy.max(spectra['altitude'])
    ind = numpy.nonzero((spectra['altitude'] >= zmax-20e3 ))[0]
    ax1 = plt.subplot2grid((7,5), (5,2), colspan=4,rowspan=2)
    data = []
    for i,s in zip(ind,spectra['spectrum'][ind]):
        if i>1:
            data.append(s)
    data = numpy.array(data)
    data = numpy.mean(data,0)
    zmin = numpy.min(spectra['altitude'][ind])
    zmax = numpy.max(spectra['altitude'][ind])
    zmin = numpy.int(numpy.around(zmin/1e3))
    zmax = numpy.int(numpy.around(zmax/1e3))
    plt.plot(f,data,'k.',markersize=0.5)
    if backend == 'AC1':
        plt.plot(f[112*2::],data[112*2::],'.',label='''high altitude ({0}-{1} Km) average'''.format(*[zmin,zmax]))
    elif backend == 'AC2':
        plt.plot(f,data,'.',label='''high altitude ({0}-{1} Km) average'''.format(*[zmin,zmax])) 
    plt.ylim([-10,10])
    plt.legend(bbox_to_anchor=(0.02, 0.95), loc=2, borderaxespad=0.)
    ax1.grid(True)
    ax1.minorticks_on()
    limx = numpy.array([numpy.floor(numpy.min(f*2)),numpy.ceil(numpy.max(f*2))])/2
    plt.xlim(limx)
    ax1.yaxis.set_label_text('Tb. [K]')
    ax1.xaxis.set_label_text('Freq. [GHz]')

   
    #plot average of each band as function of tangent altitude
    ax1 = plt.subplot2grid((7,32), (4,0), colspan=9,rowspan=3)
    s1 = len(spectra['spectrum'][2::])
    band = 8
    x = numpy.ndarray(shape=(s1,band))
    for band in range(8):
        for i,s in enumerate(spectra['spectrum'][2::]):
            x[i,band] = numpy.mean(s[band*112:(band+1)*112])
        if backend=='AC1' and band<2:
            plt.plot(x[:,band],spectra['altitude'][2::]/1e3,'.-',markersize=0.5,lw=0.2,label=band)
        else:
            plt.plot(x[:,band],spectra['altitude'][2::]/1e3,'.-',label=band)
    plt.legend(bbox_to_anchor=(1.02, 1.0), loc=2, borderaxespad=0.)
    ax1.grid(True)
    ax1.minorticks_on()
    plt.xlim([-10,250])
    ax1.xaxis.set_label_text('Band average Tb. [K]')
    ax1.yaxis.set_label_text('Ztan. [Km]')

    return fig



def get_scan_data(con, backend, freqmode, scanno):
    
    #export data
    calstw = int(scanno)
    o = Scan_data_exporter(backend,con)
    ok = o.get_db_data(freqmode,calstw)

    if ok==0:
        print 'data for scan {0} not found'.format(calstw)
        exit(0)

    o.decode_data()

 
    #perform calibration step2 for target spectrum
    c = Calibration_step2(con)
    for ind,s in enumerate(o.specdata):
        if o.spectra['type'][ind] == 8:
            altitude_range = '{80000,120000}'
            #load calibration (high-altitude) spectrum
            c.get_db_data(s['backend'],s['frontend'],s['version'],
                          s['intmode'],s['sourcemode'],s['freqmode'],
                          s['ssb_fq'],altitude_range,s['hotloada'])
            spec = c.calibration_step2(o.spectra, ind)

    for item in o.spectra.keys():
        o.spectra[item] = numpy.array(o.spectra[item])

    if o.spectra['intmode'][0]<>511:
        #print 'plotting of data with intmode<>511 is not yet implemented'
        #unsplit spectra
        stw = numpy.sort(numpy.unique(o.spectra['stw']))
        spectra = copyemptydict(o.spectra)
        for ind, stw_i in enumerate(stw):
            for spectype in [3,9,8]:
                specind = numpy.nonzero( (o.spectra['stw']==stw_i) &
                                        (o.spectra['type']==spectype) )[0]

                if specind.shape[0]<>2:
                    continue

                b = copyemptydict(o.spectra)

                for item in o.spectra.keys():
                    b[item] = o.spectra[item][specind[0]]

                f = freq(b['lofreq'],b['skyfreq'],b['ssb_fq'])
                fi = []
                for band in range(4):
                    fi.append( numpy.mean( f[band*224:(band+1)*224] ) )
                i1 = numpy.argsort(numpy.array(fi))
                spectrum = []
                s1 = o.spectra['spectrum'][specind[0]]
                s2 = o.spectra['spectrum'][specind[1]]
                s1i = 0
                s2i = 0
                for i in i1:
                    if i<2:
                        spectrum = numpy.append( spectrum, s1[s1i*224:(s1i+1)*224] )
                        s1i = s1i + 1
                    else:
                        spectrum = numpy.append( spectrum, s2[s2i*224:(s2i+1)*224] )
                        s2i = s2i + 1
                b['spectrum'] = spectrum
                b['intmode'] = 511
                for item in b.keys():
                    spectra[item].append(b[item])

        o.spectra = spectra
        for item in o.spectra.keys():
            o.spectra[item] = numpy.array(o.spectra[item])

    #o.spectra is a dictionary containing the relevant data
    return o.spectra



