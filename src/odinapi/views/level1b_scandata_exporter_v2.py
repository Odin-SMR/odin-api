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
                    zerolag = []
                    for cci in cc[0::96]:
                        zerolag.append( self.zeroLag(cci, 1.0) )
                    refdata['cc'].append(zerolag)
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



    def inv_erfc(self,z):
        p =[1.591863138, -2.442326820, 0.37153461]
        q =[1.467751692, -3.013136362, 1.00000000]
        x = 1.0-z
        y = (x*x-0.5625)
        y = x*(p[0]+(p[1]+p[2]*y)*y)/(q[0]+(q[1]+q[2]*y)*y)
        return y


    def zeroLag(self,zlag,v):
        if (zlag >= 1.0 or zlag <= 0.0): 
            return 0.0
        x = v/self.inv_erfc(zlag)
        return  x*x/2.0



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
        self.check_moon_in_mainbeam()
        
        self.get_zerolagvar()
        
        

    def check_Tspill(self):
        
        qual =  0x0001
        tspill_min = 3
        tspill_max = 12
        
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
        tb_max = 280
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
        ok_inttimes = [0.85, 1.85, 3.85]
        dt=0.01
        # inttime must be within ok_inttimes+-dt to be ok
        ind = N.nonzero( ( N.abs( self.specdata['inttime'] - ok_inttimes[0] ) > dt ) & 
                         ( N.abs( self.specdata['inttime'] - ok_inttimes[1] ) > dt ) &
                         ( N.abs( self.specdata['inttime'] - ok_inttimes[2] ) > dt ) )[0] 
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
        


    def check_moon_in_mainbeam(self):
         # check if moon is in the main beam
         qual = 0x0200
         MOONMB = 0x0200
         ind1 = N.nonzero( (self.specdata['skybeamhit'] & MOONMB == MOONMB))[0]
         if ind1.shape[0]<>0:
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
        self.zerolagvar = []
        #N.ones( (self.specdata['stw'].shape[0], 8) )*-1.0
        ones = N.array(N.ones(8)*-1).tolist()
        for ind,stw in enumerate(self.specdata['stw']):
            if ind<2:
                self.zerolagvar.append(ones)
                continue
            ind1 = N.nonzero( (self.refdata['stw']<stw) )[0]
            ind2 = N.nonzero( (self.refdata['stw']>stw) )[0]

            if ind1.shape[0]==0 or ind2.shape[0]==0:
                self.zerolagvar.append( ones )
                continue

            z1 = N.array(self.refdata['cc'][ind1[-1]])
            z2 = N.array(self.refdata['cc'][ind2[0]])
            dg = N.abs( z1 - z2)
            g = N.array(( z1 + z2 ) / 2.0)
            i = N.nonzero((g>0))[0]
            frac = N.array(ones)
            i = N.nonzero((g>0))[0]
            frac[i] = dg[i]/g[i]*100.0
            self.zerolagvar.append( frac.tolist() )
            #self.zerolagvar[ind] = g



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
             'calstw','frequency','zerolagvar','ssb']

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
     'Frequency'       : spectra['frequency'],
     'ZeroLagVar'      : spectra['zerolagvar'],
     'SSB'             : spectra['ssb'],

    }

    for item in datadict.keys():
        try:
            datadict[item] = datadict[item].tolist()
        except:
            pass
  
    return datadict 


def scan2dictlist_v4(spectra):

    datadict = {
     'Version'         : spectra['version'][2::],
     'Quality'         : spectra['quality'][2::],
     'STW'             : spectra['stw'][2::],
     'MJD'             : spectra['mjd'][2::],
     'Orbit'           : spectra['orbit'][2::],
     'Spectrum'        : spectra['spectrum'][2::],
     'TrecSpectrum'    : spectra['spectrum'][0],
     'Frontend'        : spectra['frontend'][2::],
     'Backend'         : spectra['backend'][2::],
     'RA2000'          : spectra['ra2000'][2::],
     'Dec2000'         : spectra['dec2000'][2::],
     'Longitude'       : spectra['longitude'][2::],
     'Latitude'        : spectra['latitude'][2::],
     'Altitude'        : spectra['altitude'][2::],
     #'Qtarget'         : spectra['qtarget'][2::],
     #'Qachieved'       : spectra['qachieved'][2::],
     #'Qerror'          : spectra['qerror'][2::],
     'GPSpos'          : spectra['gpspos'][2::],
     'GPSvel'          : spectra['gpsvel'][2::],
     'SunPos'          : spectra['sunpos'][2::],
     'MoonPos'         : spectra['moonpos'][2::],
     'SunZD'           : spectra['sunzd'][2::],
     'Vgeo'            : spectra['vgeo'][2::],
     'Tcal'            : spectra['hotloada'][2::],
     'Trec'            : spectra['tsys'][2::],
     'SBpath'          : spectra['sbpath'][2::],
     'LOFreq'          : spectra['lofreq'][2::],
     'SkyFreq'         : spectra['skyfreq'][2::],
     'RestFreq'        : spectra['restfreq'][2::],
     #'MaxSuppression'  : spectra['maxsuppression'][2::],
     'AttitudeVersion' : spectra['soda'][2::],
     'FreqRes'         : spectra['freqres'][2::],
     'FreqCal'         : spectra['ssb_fq'][2::],
     'IntTime'         : spectra['inttime'][2::],
     'EffTime'         : spectra['efftime'][2::],
     'Channels'        : spectra['channels'][2::],
     'FreqMode'        : spectra['freqmode'][2::],
     'TSpill'          : spectra['tspill'][2::],
     'ScanID'          : spectra['calstw'][2::],
     'Apodization'     : N.ones(len(spectra['quality']),dtype='int'),
     'Frequency'       : spectra['frequency'],
     'ZeroLagVar'      : spectra['zerolagvar'][2::],

    }
    
    for item in datadict.keys():
        try:
            datadict[item] = datadict[item].tolist()
        except:
            pass
  
    return datadict 


#-------------------------------------------------------------------
#function [f] = qsmr_frequency(scan_h,numspec)
#
# DESCRIPTION:  Generates frequency per spectrum in scan, 
#               2001/21/9. Partly provided by Frank Merino,
#               updated by C. jimenez, M. Olberg, N. Lautie, 
#               J. Urban (2002-2007).
#
# INPUT:        (struct) scan_h:  structure created by call such as below: 
#                               scan_h = read_hdfheader(SMR,file_id,nrec).
#               (int) num_spec: spectrum number in HDF file for which
#                               the frequencies shall be determined.
#
# OUT:          (double) frequency vector (AOS) or matrix (AC) [Hz].
#              
# VERSION:      2007-Jan-26 (JU) 
#-------------------------------------------------------------------


class Scan_h():
    def __init__(self):
        self.Level = []
        self.Channels = [] 
        self.IntMode = []
        self.FreqCal = []
        self.Quality = []
        self.SkyFreq = []
        self.Backend = [] 
        self.FreqRes = []
        self.RestFreq = []
        self.LOFreq = []

def qsmr_frequency(scan_h,ispec,numspec=3):
   
    #--- filling S to use Franks mscript
    S = Scan_h()
    S.Level     = scan_h['level'][numspec]
    S.Channels  = scan_h['channels'][numspec]
    S.IntMode   = scan_h['intmode'][numspec]
    S.FreqCal   = scan_h['ssb_fq'][numspec];
    S.Quality   = scan_h['quality'][numspec];
    S.SkyFreq   = scan_h['skyfreq'][ispec];
    S.Backend   = scan_h['backend'][numspec];
    S.FreqRes   = scan_h['freqres'][numspec];
    S.RestFreq  = scan_h['restfreq'][ispec];
    S.Quality = 0

    # -- correcting Doppler in LO
    S.LOFreq    = scan_h['lofreq'][ispec]-(S.SkyFreq-S.RestFreq);

    # Note:
    # S.Backend(numspec) == 1 -> AC1
    # S.Backend(numspec) == 2 -> AC2
    # S.Backend(numspec) == 3 -> AOS
    # otherwise : FBA

    # --- START FRANKS MSCRIPT---------------------------------------

    n = S.Channels;
    f = [];

    # --  == 1 missing

    #--- if FSORTED frequency sorting performed ---------------------
    # if bitand(hex2dec(S.Level), hex2dec('0080'))==1
    # if bitand(S.Level, hex2dec('0080'))==1
  
    # ISORTED bit is now part of Quality %%%

    #JU%if bitand(hex2dec(S.Quality), hex2dec('02000000'))
    
    if S.Quality & 0x02000000:

        x = N.arange(0,n)-N.floor(n/2);
        f = N.zeros(n);
        c = S.FreqCal[end:-1:1];    # MO uses fliplr, but we have here a
        #c = fliplr(S.FreqCal);     # column vector (PE 060602)
        f = polyval(c, x);
        mode = 0;

    else: #------------------------------------------------------------
    
    
        if S.Backend == 3:    
            # -- AOS
            x = N.arange(0,n)-N.floor(n/2);
            c = S.FreqCal[end:-1:1];   # MO uses fliplr, but we have here a
            f = 3900.0e6*N.ones(1,n)-(polyval(c, x)-2100.0e6);
            mode = 0;
      
        else: 
            # -- autocorrelators
            # new code for spectra which have ADC_SEQ set %%% 

            if S.IntMode & 256:
                #
                # The IntMode reported by the correlator is interpreted as
                # a bit pattern. Because this bit pattern only describes ADC
                # 2-8, the real bit pattern is obtained by left shifting it
                # by one bit and adding one (i.e. it is assumed that ADC 1
                # is always on).
                #
                # The sidebands used are represented by vector ssb, this is
                # hard-wired into the correlators:
                ssb = [1, -1, 1, -1, -1, 1, -1, 1];
      
                # Analyse the correlator mode by reading the bit pattern
                # from right to left(!) and calculating a sequence of 16
                # integers whose meaning is as follows:
                #
                # n1 ssb1 n2 ssb2 n3 ssb3 ... n8 ssb8
                # 
                # n1 ... n8 are the numbers of chips that are cascaded 
                # to form a band. 
                # ssb1 ... ssb8 are +1 or -1 for USB or SSB, respectively.  
                # Unused ADCs are represented by zeros.
                #
                # examples (the "classical" modes):
                #
                # mode 0x00: ==> bit pattern 00000001
                # 8  1  0  0  0  0  0  0  0  0  0  0  0  0  0  0
                # i.e. ADC 1 uses 8 chips in upper-side band mode
                #
                # mode 0x08: ==> bit pattern 00010001
                # 4  1  0  0  0  0  0  0  4 -1  0  0  0  0  0  0
                # i.e. ADC 1 uses 4 chips in upper-side band mode
                # and  ADC 5 uses 4 chips in lower-side band mode
                #
                # mode 0x2A: ==> bit pattern 01010101
                # 2  1  0  0  2  1  0  0  2 -1  0  0  2 -1  0  0
                # i.e. ADC 1 uses 2 chips in upper-side band mode
                # and  ADC 3 uses 2 chips in upper-side band mode
                # and  ADC 5 uses 2 chips in lower-side band mode
                # and  ADC 7 uses 2 chips in lower-side band mode
                #
                # mode 0x7F: ==> bit pattern 11111111
                # 1  1  1 -1  1  1  1 -1  1 -1  1  1  1 -1  1  1
                # i.e. ADC 1 uses 1 chip in upper-side band mode
                # and  ADC 2 uses 1 chip in lower-side band mode
                # and  ADC 3 uses 1 chip in upper-side band mode
                # and  ADC 4 uses 1 chip in lower-side band mode
                # and  ADC 5 uses 1 chip in lower-side band mode
                # and  ADC 6 uses 1 chip in upper-side band mode
                # and  ADC 7 uses 1 chip in lower-side band mode
                # and  ADC 8 uses 1 chip in upper-side band mode
                #
                mode = S.IntMode & 255;
                bands = 0;
                seq = N.zeros(16, dtype='int');
                m = 0;
                for bit in range(8):
                    if ( ( mode & (1<<bit) ) !=0 ):
                        m = bit
                    seq[2*m] = seq[2*m]+1;
               
                for bit in range(8):
                    if seq[2*bit] > 0:
                        seq[2*bit+1] = ssb[bit];
                    else:
                        seq[2*bit+1] = 0;
        
                f = N.zeros( shape=(8,112) );

                bands = [1, 2, 3, 4, 5, 6, 7, 8];      # default: use all bands
                if S.IntMode & 512:                    # test for split mode
                    if S.IntMode & 1024:
                        bands = [3, 4, 7, 8];          # upper band
                    else:
                        bands = [1, 2, 5, 6];          # lower band
                for adc in N.array(bands)-1:     
                    if seq[2*adc] > 0:
                        df = 1.0e6/seq[2*adc];
                        if seq[2*adc+1] < 0:
                            df = -df;
                        for j in range(1,seq[2*adc]+1):
                            m = adc+j-1;
                            # The frequencies are calculated by noting that two
                            # consecutive ADCs share the same internal SSB-LO:
                            f[m,:] = S.FreqCal[N.round(adc/2)] * N.ones(112) + N.arange(0,112,1) * df + (j-1) * 112 * df;

                if S.IntMode & 512:     # for split mode keep used bands only
                    f = f[bands,:];
                

                ####  end of new code %%%
      
      
            else:
              
                df = S.FreqRes;
                mode = S.IntMode & 15;
                if S.IntMode & (1 << 4):
                    if S.IntMode & ( 1 << 5 ):
                        if mode == 2:
                            m = n;
                            f = S.FreqCal[2-1] * N.ones(m) - N.arange(m-1, -1, 1) * df;
                        elif mode == 3:
                            m = n/2;
                            f = [ 
                                S.FreqCal[4-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                                S.FreqCal[3-1] * N.ones(m) + N.arange(0, m, 1) * df 
                                ];
                        else:
                            m = n/4;
                            f = [ 
                                S.FreqCal[3-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                                S.FreqCal[3-1] * N.ones(m) + N.arange(0, m, 1) * df,
                                S.FreqCal[4-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                                S.FreqCal[4-1] * N.ones(m) + N.arange(0, m, 1) * df 
                                ];
                        
                    else:
                        if mode == 2:
                            m = n;
                            f = S.FreqCal[1-1] * N.ones(m) + N.arange(0, m , 1) * df;
                        elif mode == 3:
                            m = n/2;
                            f = [ 
                                S.FreqCal[2-1] * N.ones(m) - N.arange(m-1,-1,-1) * df,
                                S.FreqCal[1-1] * N.ones(m) + N.arange(0, m, 1) * df 
                                ];
                        else:
                            m = n/4;
                            f = [ 
                                S.FreqCal[1-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                                S.FreqCal[1-1] * N.ones(m) + N.arange(0, m, 1) * df,
                                S.FreqCal[2-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                                S.FreqCal[2-1] * N.ones(m) + N.arange(0, m, 1) * df 
                                ];
                else:
                    if mode == 1:
                        m = n;
                        f = S.FreqCal[1-1] * N.ones(m) + N.arange(0, m, 1) * df;
                    elif mode == 2:
                        m = n/2;
                        f = [ 
                            S.FreqCal[1-1] * N.ones(m) + N.arange(0, m, 1) * df,
                            S.FreqCal[2-1] * N.ones(m) - N.arange(m-1, -1, -1) * df 
                            ];
                    elif mode == 3:
                        m = n/4;
                        f = [ 
                            S.FreqCal[2-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                            S.FreqCal[1-1] * N.ones(m) + N.arange(0, m, 1) * df,
                            S.FreqCal[4-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                            S.FreqCal[3-1] * N.ones(m) + N.arange(0, m, 1) * df 
                            ];
                    else:
                        m = n/8;
                        f = [ 
                            S.FreqCal[1-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                            S.FreqCal[1-1] * N.ones(m) + N.arange(0, m, 1) * df,
                            S.FreqCal[2-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                            S.FreqCal[2-1] * N.ones(m) + N.arange(0, m, 1) * df,
                            S.FreqCal[3-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                            S.FreqCal[3-1] * N.ones(m) + N.arange(0, m, 1) * df,
                            S.FreqCal[4-1] * N.ones(m) - N.arange(m-1, -1, -1) * df,
                            S.FreqCal[4-1] * N.ones(m) + N.arange(0, m, 1) * df 
                            ];
    # --------------------------------------------------------

    if f==[]:
        print 'qsmr_frequency.py: no frequencies, spectrum not frequency sorted!'
        return []
   
    #f = f'; %'

    if S.Quality & int('00001000', 2) == 0:

        if (S.SkyFreq - S.LOFreq) > 0.0:
            f = S.LOFreq + f;
        else:
            f = S.LOFreq - f;

    # --- END FRANKS MSCRIPT---------------------------------------

    return f




# smrl1b_ac_freqsort   Sorts AC spectra
#
#   Auto-correlator spectra are sorted, on the same time as data coming from
#   bad modules, and with interference from internal IF signals, can be
#   removed. AC spectra have over-lapping parts. That is, some frequencies are
#   repeated.
#
#   Modules to be removed are specified by selecting a frequency inside the
#   module. This frequency can not be inside overlapping frequency
#   parts. This argument can be a vector. Several modules are then removed.
#
#   If *rm_edge_channels* is set, then first and last channel of each module
#   is removed. This in order to remove possible contamination of internal
#   IF signals. 
#
#   Spectra can be sorted in several ways (*sortmeth*):
#
#     'mean' : Data at over-lapping frequencies are averaged.
#
#     'from_start' : First value for duplictaed frequencies is kept. Second
#     value is ignored.
#
#     'from_end' : Second value for duplicated frequencies is kept. First
#     value is ignored.
#
#   The function can sort several spectra in parallel. Each frequency and
#   spectrum vector is then a column in *f* and *y*, respectively. The
#   sorting is based then solely on data in first column of *f*.
#
# FORMAT   [f,y] = smrl1b_ac_freqsort(f,y,bad_modules,rm_edge_chs,sortmeth)
#        
# OUT   f           Sorted frequency column vector(s). 
#       y           Sorted spectrum column vector(s).
# IN    f           Sorted frequency vector.
#       y           Sorted spectrum vector.
# OPT   bad_modules See above. Default is [].
#       rm_edge_chs Removal of egede channels. Default is false.
#       sortmeth    See above. Default is 'mean'.

# 2006-11-08   Created by Patrick Eriksson.


def smrl1b_ac_freqsort(f, y, bad_modules=[], rm_edge_chs=False, sortmeth='mean'):

    f0 = N.array(f)
    f = N.array(f)
    y = N.array(y)
    ssb_ind = N.ones(896)
    for ind in range(8):
        ssb_ind[ind*112:(ind+1)*112] = ind +1

    if f.shape[0] == 896:

        #- Remove bad modules
        #

        if not bad_modules==[]  or  rm_edge_chs:

            ind = N.ones(896);

            if not bad_modules == []:
                #- find frequency limit for each module
                fs = N.array(f)
                fs.shape = (8,112)
                fs = N.array([ N.min(fs,1) , N.max(fs,1) ]);
                for i in range(len(bad_modules)):
                    ii = N.nonzero( (bad_modules[i] >= fs[0,:])  &  (bad_modules[i] <= fs[1,:]) )[0];
                    if ii.shape[0] == 0 or ii.shape[0] > 1:
                        error                    
                    ind[(ii)*112 + N.arange(0,112,1) ] = 0;
            if rm_edge_chs:
               
                ind[ N.append( N.arange(0,896,112), N.arange(111,896,112) ) ] = 0;
        
            ind = N.nonzero( (ind>0) )[0];

            f = N.array(f)
            y = N.array(y)
            f = f[ind];
            y = y[ind];
            ssb_ind = ssb_ind[ind]

    #- Sort
    #
    if sortmeth == 'from_middle':
        [f, y, ssb_ind] = sort_from_middle( f, y , ssb_ind, f0);
    elif sortmeth == 'from_start':
        [f, y, ssb_ind] = sort_from_start( f, y , ssb_ind);
    elif sortmeth=='from_end':
        [f,y] = sort_from_end( f, y );
    elif sortmeth == 'mean':
        [f1,y1]  = sort_from_start( f, y );
        [f2,y2]  = sort_from_end( f, y );
        f        = f1;
        y        = ( y1 + y2 ) / 2.0;
    
    ind = N.argsort(f)
    f = f[ind];
    y = y[ind];
    ssb_ind = ssb_ind[ind] 

    ssb = []
    for ind in range(8):
        i = N.nonzero( (ssb_ind==ind+1) )[0]
        if i.shape[0]>0:
            ssb.extend( [ind+1,N.min(i)+1,N.max(i)+1])
        else:
            ssb.extend( [ind+1,-1,-1])
    return f,y,ssb

def sort_from_middle(f, y, ssb_ind, f0):

    #- Sort
    #
    # remove overlapping channels
    # choose the channel which is closest to its 
    # sub-band frequency center
    fs = N.array(f0)
    fs.shape = (8,112)
    fs = N.mean(fs,1)

    ind = []
    for i in range(f.shape[0]):
        multi_f = N.nonzero( (f[i]==f) )[0]
        if multi_f.shape[0]==1:
            ind.append(i)
        else:
            ssb_ind_i = N.array(ssb_ind[multi_f]-1).astype(int)
            ssb_f0 = fs[ssb_ind_i]
            ii = N.argsort( N.abs(ssb_f0 - f[i]) )
            ind.append(multi_f[ii[0]])

    ind = N.unique(N.array(ind))
    f = f[ind];
    y = y[ind];
    ssb_ind = ssb_ind[ind]
    ind = N.argsort(f)
    f = f[ind];
    y = y[ind];
    ssb_ind = ssb_ind[ind]

    return f,y,ssb_ind


def sort_from_start(f,y, ssb_ind):
    n = f.shape[0];
    [fu,ind] = N.unique( f[ N.arange(n-1,-1,-1) ] , return_index=True);
    ind      = n - 1 - ind;
    f        = f[ind];
    y        = y[ind];
    ssb_ind  = ssb_ind[ind];
    return f,y,ssb_ind


def sort_from_end(f,y):
    [fu,ind] = N.unique( f, return_index=True);
    f        = f[ind];
    y        = y[ind];
    return f,y






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
        return {}
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

    # add frequency vector to each spectrum in the o.spectra structure
    rm_edge_ch = True
    if backend=='AC1':
        bad_modules = N.array([1,2])
    elif backend=='AC2':
        bad_modules = N.array([3])
    
    sortmeth = 'mean'
    sortmeth = 'from_start'
    spectra = N.array(o.spectra['spectrum'])
    o.spectra['spectrum'] = []
    o.spectra['frequency'] = []
    o.spectra['ssb'] = []
    channels = []
    freqinfo = { 'IFreqGrid' : [], 'LOFreq' : [], 'SubBandIndex' : []}
    for numspec in range( len(o.spectra['stw']) ): 
        
        f = qsmr_frequency(o.spectra,numspec)
        f = N.array(f)
        # check if any sub-band is "dead" and the append to bad_modules
        ys = N.array(spectra[numspec])
        ys.shape = (8,112) 
        ytest = N.mean(ys,1)
        badssb_ind = N.nonzero( (ytest==0) )[0]
        if badssb_ind.shape[0]>0:
            bad_modules = N.append( bad_modules, badssb_ind + 1 )   

        f_modules = N.mean(f,1)
        remove_modules = f_modules[bad_modules-1]
        f.shape = (f.shape[0]*f.shape[1],)    
        y = spectra[numspec]
        f,y,ssb = smrl1b_ac_freqsort(f, y, remove_modules, rm_edge_ch, sortmeth)  

        # -- correcting Doppler in LO
        skyfreq  = o.spectra['skyfreq'][numspec]
        lofreq   = o.spectra['lofreq'][numspec]
        restfreq = o.spectra['restfreq'][numspec]
        lofreq   = lofreq - ( skyfreq - restfreq );

        if (skyfreq - lofreq) > 0.0:
            #f = S.LOFreq + f;
            f = (f - lofreq)
        else:
            #f = S.LOFreq - f;
            f = -(lofreq - f) 
        if numspec == 0:
            #o.spectra['frequency'].append(f.tolist())
            #o.spectra['frequency'].append(f.tolist())
            freqinfo['IFreqGrid'] = f.tolist()
            freqinfo['SubBandIndex'].append(ssb[1::3])
            freqinfo['SubBandIndex'].append(ssb[2::3])
            o.spectra['ssb'].append(ssb)
            #o.spectra['ssb'].append({'ssb':ssb,'lofreq':lofreq})
        if numspec>1:
            freqinfo['LOFreq'].append(lofreq)
        channels.append(y.shape[0])
        o.spectra['spectrum'].append(y.tolist())
    
    o.spectra['frequency'] = freqinfo 
    o.spectra['channels'] = channels

    #o.spectra is a dictionary containing the relevant data
    return o.spectra



