import numpy
import numpy as N
import copy
from pg import DB
from sys import stderr,stdout,stdin,argv,exit
import matplotlib.pyplot as plt
import matplotlib
from dateutil.relativedelta import relativedelta
from datetime import datetime
from utils import copyemptydict

class Scan_data_exporter():
    def __init__(self,backend,con):
        self.backend=backend
        self.con=con

    def get_db_data(self,freqmode,calstw):
        '''export orbit data from database tables'''
        self.calstw = calstw

        #extract all target spectrum data for the scan
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
    
        #extract all calibration spectrum data for the scan
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

        #extract all reference spectrum data for the scan
        if self.backend == 'AC1':
            stw_offset = -1
        elif self.backend == 'AC2':
            stw_offset = 0
        
        stw1 = result[0]['stw'] - 256
        stw2 = result[-1]['stw'] + 256
        query = self.con.query('''
                  select backend,frontend,ac_level0.stw,inttime,cc,
                  sig_type,mech_type,skybeamhit
                  from ac_level0
                  join attitude_level1  using (backend,stw)
                  join fba_level0 on fba_level0.stw=ac_level0.stw+{2}
                  where ac_level0.stw between {0} and {1}
                  and sig_type='REF' 
                  order by ac_level0.stw
                             '''.format(*[stw1,stw2,stw_offset]))

        self.refdata = query.dictresult()
         

        if result==[] or result2==[] or self.refdata==[]:
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

        refdata = {
                'backend':    [],
                'frontend':   [],
                'stw':        [],
                'sig_type':   [],
                'mech_type':  [],
                'skybeamhit': [],
                'inttime':    [],
                'cc':         [],   
                   }
        for row in self.refdata:
            for item in refdata.keys():
                if item=='cc':
                    cc = N.ndarray(shape=(8*96,),dtype='float64',
                         buffer=self.con.unescape_bytea(row['cc']))
                    # store only zerolags
                    refdata['cc'].append(cc[0::96])
                else:
                    refdata[item].append(row[item])
        
        for item in refdata.keys():
            refdata[item] = N.array(refdata[item])

        self.refdata = refdata

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


class Quality_control():
    def __init__(self,specdata,refdata):
        self.refdata = refdata
        self.specdata = specdata
    def run_control(self):
        # Quality check of a scan
        # ===================================================== 
        # 1. check Tspill  - outside of valid range
        # 2. check Trec    - outside of valid range
        # 3. check Noise   - outside of valid range   
        # 4. check Scan    - corrupt scanning (tangent altitude is not 
        #                    decreasing or increasing as expected) 
        # 5. check nr of atmospheric spectra 
        # 
        # Quality check of each spectrum of a scan
        # =====================================================
        # 1. Tb            - outside of valid range (0-300)
        # 2. Sig           - corrupt integration time
        # 3. Ref           - observation sequence 
        # 4. Ref           - integration times
    
        self.quality = N.zeros(self.specdata['stw'].shape[0])
    
        self.check_Tspill()
        self.check_Trec()
        self.check_Noise()
        self.check_scan()
        self.check_nr_of_spec()
    
        self.check_Tb()
        self.check_Int()
        self.check_obs_sequence()

        self.filter_references()

        self.check_ref_inttime()
        
        self.get_zerolagvar()
        
        

    def check_Tspill(self):
        
        qual =  0x0001
        tspill_min = 3
        tspill_max = 10
        
        if not self.specdata['tspill'][0] >= tspill_min and self.specdata['tspill'][0] <= tspill_max:  
            self.quality = self.quality + qual

    def check_Trec(self):
        
        qual = 0x0002
        trec_min = 2000
        trec_max = 4000

        if not self.specdata['tsys'][3] >= trec_min and self.specdata['tsys'][3] <= trec_max:  
            self.quality = self.quality + qual
          
    def check_Noise(self):
        
        qual = 0x0004
        noise_min = 0.5
        noise_max = 6
        B = 1e6
        noise = self.specdata['tsys'][3]/(self.specdata['efftime'][2::]*B)**0.5
        l = N.nonzero( (noise <= noise_min) |
                        (noise >= noise_max) )[0]
        if not l.shape[0]==0:
            self.quality = self.quality + qual    
        
    def check_scan(self):
        
        qual = 0x0008
        # check that scanning is either upwards or downwards
        altdiff = numpy.diff( self.specdata['altitude'][2::] )
        l = ( numpy.nonzero( (altdiff + 0.1 >= 0) )[0].shape[0] == altdiff.shape[0] or
              numpy.nonzero( (altdiff - 0.1 <= 0) )[0].shape[0] == altdiff.shape[0] )
        if not l:
            self.quality = self.quality + qual

    def check_nr_of_spec(self):
        
        # check that scan contains at least n target spectra
        qual = 0x0010
        n = 5 
        sig_ind = numpy.nonzero( (self.specdata['type']==8) )[0]
        if not sig_ind.shape[0]>=n:
            self.quality = self.quality + qual


    def check_Tb(self):
        # check Tb, search for physically unrealistic values
        qual = 0x0020
        tb_min = -15
        tb_max = 250
        if self.specdata['backend'][0]==1:
            # do not consider to test band 1 and 2 of AC1
            specind = N.arange(112*2,112*8,1)
        elif self.specdata['backend'][0]==2:
            # do not consider to test band 3 of AC2       
            specind = N.append( N.arange(0,112*2,1), N.arange(112*3,112*8,1))     

        for ind, spec in enumerate(self.specdata['spectrum']):
            if ind<2:
               # do not consider calibration spectrum here
               continue
            
            q1 = numpy.nonzero( ( spec[specind] <= tb_min ) |
                                ( spec[specind] >= tb_max ) )[0]        
            if not q1.shape[0]==0:
                self.quality[ind] = self.quality[ind] + qual
                
     
    def check_Int(self):
        # check that integration times are valid
        qual = 0x0040
        inttime_min = 0.5
        inttime_max = 10
        ind = N.nonzero( (self.specdata['inttime']<inttime_min) | (self.specdata['inttime']>=inttime_max) )[0] 
        self.quality[ind] = self.quality[ind] + qual

    def check_obs_sequence(self):
        # check if atmospheric spectrum is collected between two accepted sky beam 1 references
        qual = 0x0080
        for ind,stw in enumerate(self.specdata['stw']):
            if ind<2:
                continue
            ind1 = N.nonzero( (self.refdata['stw']<stw) )[0]
            ind2 = N.nonzero( (self.refdata['stw']>stw) )[0]

            if ind1.shape[0]==0 or ind2.shape[0]==0:
                self.quality[ind] = self.quality[ind] + qual
                continue
            
            if ind1.shape[0]<2:
                self.quality[ind] = self.quality[ind] + qual
                continue
 
            if ( self.refdata['mech_type'][ind1[-2]]<>'SK1' or
                 self.refdata['mech_type'][ind1[-1]]<>'SK1' or 
                 self.refdata['mech_type'][ind2[0]]<>'SK1'):
                self.quality[ind] = self.quality[ind] + qual
                continue

            EARTH1=0x0001
            MOON1=0x0002
            GALAX1=0x0004
            SUN1=0x0008

            test1 = N.nonzero( (self.refdata['skybeamhit'][ind1[-1]] & EARTH1 == EARTH1) |
                               (self.refdata['skybeamhit'][ind1[-1]] & MOON1 == MOON1) |
                               (self.refdata['skybeamhit'][ind1[-1]] & SUN1 == SUN1) )[0]
            test2 = N.nonzero( (self.refdata['skybeamhit'][ind2[0]] & EARTH1 == EARTH1) |
                               (self.refdata['skybeamhit'][ind2[0]] & MOON1 == MOON1) |
                               (self.refdata['skybeamhit'][ind2[0]] & SUN1 == SUN1) )[0]
           
            if test1.shape[0]<>0 or test1.shape[0]<>0:
                self.quality[ind] = self.quality[ind] + qual  


    def check_ref_inttime(self):
        # check that surrounding references integration time are the same
        qual = 0x0100
  
        for ind,stw in enumerate(self.specdata['stw']):
            if ind<2:
                continue
            ind1 = N.nonzero( (self.refdata['stw']<stw) )[0]
            ind2 = N.nonzero( (self.refdata['stw']>stw) )[0]

            if ind1.shape[0]==0 or ind2.shape[0]==0:
                self.quality[ind] = self.quality[ind] + qual
                continue

            if N.abs(self.refdata['inttime'][ind1[-1]]-
                     self.refdata['inttime'][ind2[0]]) > 0.2:
                self.quality[ind] = self.quality[ind] + qual
        


    def filter_references(self):
        # identify reference signals that we do not trust,
        # 1. we only trust signals from SK1 (skybeam 1) if the 
        #    previous signal also was SK1 and not if SK1 
        # 2. we only use SK1 beam if it does not hit an object
        EARTH1=0x0001
        MOON1=0x0002
        GALAX1=0x0004
        SUN1=0x0008

        # check which SK1 references the beam hit an object
        test1 = N.nonzero( (self.refdata['sig_type']=='REF') & (self.refdata['mech_type']=='SK1') )[0]
        test2 = N.nonzero( (self.refdata['skybeamhit'] & EARTH1 == EARTH1) |
                           (self.refdata['skybeamhit'] & MOON1 == MOON1) |
                           (self.refdata['skybeamhit'] & SUN1 == SUN1) )[0]
        badind1 = N.intersect1d(test1,test2)

        # check that previous ref is SK1 
        badind2 = N.nonzero( (self.refdata['sig_type']=='REF') & (self.refdata['mech_type']!='SK1'))[0]
        # add all following references to index list of untrusted references
        badind2 = N.unique(N.union1d(badind2,badind2+1))

        # combine bad indexes
        badind = N.unique(N.union1d(badind1,badind2))   

        # store the good referenes
        allind = N.arange(self.refdata['sig_type'].shape[0])
        okind = N.setdiff1d(allind,badind)

        for item in self.refdata.keys(): 
            self.refdata[item] = self.refdata[item][okind]

       
    def get_zerolagvar(self):
        # identify the power variation of the two surrounding reference measurements
        self.zerolagvar = N.zeros( (self.specdata['stw'].shape[0], 8) )
        for ind,stw in enumerate(self.specdata['stw']):
            if ind<2:
                continue
            ind1 = N.nonzero( (self.refdata['stw']<stw) )[0]
            ind2 = N.nonzero( (self.refdata['stw']>stw) )[0]

            if ind1.shape[0]==0 or ind2.shape[0]==0:
                continue

            dg = N.abs(self.refdata['cc'][ind1[-1]] - self.refdata['cc'][ind2[0]])
            g = ( self.refdata['cc'][ind1[-1]] + self.refdata['cc'][ind2[0]] ) / 2.0
            self.zerolagvar[ind] = dg/g*100




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
             'calstw','frequency','zerolagvar']

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


def scan2dictlist_v2(spectra):

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
     'ZeroLagVar'      : spectra['zerolagvar']
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
    plt.show()
    return fig



def get_scan_data_v2(con, backend, freqmode, scanno):
    
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

    q = Quality_control(o.spectra, o.refdata)
    q.run_control()    
    o.spectra['quality'] = q.quality
    o.spectra['zerolagvar'] = q.zerolagvar

    #o.spectra is a dictionary containing the relevant data
    return o.spectra



