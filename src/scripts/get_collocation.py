import numpy as N
from pg import DB
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

class db(DB):
    def __init__(self):
        #DB.__init__(self,dbname='odin',user='odinop',host='localhost')
        DB.__init__(self,dbname='odin',user='odinop',
                    host='malachite.rss.chalmers.se',passwd='***REMOVED***')

#class db1(DB):
#    def __init__(self):
#        DB.__init__(self,dbname='odin',user='odinop',host='localhost')
        #DB.__init__(self,dbname='odin',user='odinop',
        #            host='malachite.rss.chalmers.se',passwd='***REMOVED***')


def sph2cart(az, el, r):

    rcos_theta = r * N.cos(el)
    x = rcos_theta * N.cos(az)
    y = rcos_theta * N.sin(az)
    z = r * N.sin(el)
    return x, y, z

def cart2sph(x, y, z):

    hxy = N.hypot(x, y)
    r = N.hypot(hxy, z)
    el = N.arctan2(z, hxy)
    az = N.arctan2(y, x)
    return az, el, r


def getscangeoloc(startlat,startlon,endlat,endlon):

    deg2rad = N.pi/180.0
    rad2deg = 180/N.pi
    startlat = startlat * deg2rad
    startlon = startlon * deg2rad
    endlat = endlat * deg2rad
    endlon = endlon * deg2rad
    [xs,ys,zs] = sph2cart(startlon ,startlat,1)
    [xe,ye,ze] = sph2cart(endlon , endlat,1)
    [midlon,midlat,r] = cart2sph((xs+xe)/2.0, (ys+ye)/2.0, (zs+ze)/2.0)
    midlon = midlon * rad2deg
    midlat = midlat * rad2deg
    return midlat,midlon



def get_odin_scans(con, date, freqmode):

    query = con.query('''select date,freqmode,backend,scanid,altend,altstart,datetime,
                         latend,latstart,lonend,lonstart,mjdend,mjdstart,numspec,sunzd
                         from scans_cache where date='{0}' and freqmode={1}          
                         '''.format(*[date, freqmode]))
    result = query.dictresult()
    return result


def get_comp_scans(data, mjd, dmjd, R0):

    okdata = {
            'species'     : [],
            'file'        : [],
            'file_index'  : [],
            'latitude'    : [],
            'longitude'   : [],
            'mjd'         : [],
            'theta'       : [],
            }

    ind = N.nonzero( ( data['mjd'] > mjd - dmjd ) & ( data['mjd'] < mjd + dmjd ) )[0]    
    deg2rad = N.pi/180.0
    for i_ind in ind:
        for item in ['species', 'file', 'file_index', 'latitude', 'longitude', 'mjd']:
            okdata[item].append(data[item][i_ind]) 
        # calculate position difference in degrees 
        x, y, z = sph2cart(data['longitude'][i_ind]*deg2rad, data['latitude'][i_ind]*deg2rad, 1.0)
        R1 = N.array([x, y, z])
        okdata['theta'].append( N.arccos( N.linalg.linalg.dot(R0, R1) ) * 180.0/N.pi )
    
    for item in okdata.keys():
        okdata[item] = N.array( okdata[item] )     

    return okdata


def read_comp_file(instrument, species, mjd_i, current_file=[], data=[]):

    mjd0 = datetime(1858,11,17)
    date_i = mjd0 + relativedelta(days = mjd_i)

    if instrument == 'mls':
        file = 'Aura_MLS_scanpos_{0}_{1}{2:02}.txt'.format(*[species, date_i.year,date_i.month]) 
    elif instrument == 'mipas':
        file = 'Envisat_MIPAS_scanpos_{0}_{1}{2:02}.txt'.format(*[species, date_i.year,date_i.month])
    elif instrument == 'smiles':
        file = 'ISS_SMILES_scanpos_{0}_A_{1}{2:02}.txt'.format(*[species, date_i.year,date_i.month])

    if file == current_file:
        return file, data
    
    file_i = filepath + file
    if not os.path.isfile(file_i):
        return [],[]

    f = open(file_i,'r')
    lines = f.readlines()
    data = {
         'species'    : [],
         'file'       : [],
         'file_index' : [],
         'latitude'   : [],
         'longitude'  : [],
         'mjd'        : [],
           }

    for line in lines:

        parts = line.split()

        data['species'].append( parts[0] )
        data['file'].append( parts[1] )
        data['file_index'].append( int(parts[2]) )
        data['latitude'].append( float(parts[3]) )
        data['longitude'].append( float(parts[4]) )
        data['mjd'].append( float(parts[5]) )

    for item in data.keys():
        data[item] = N.array( data[item] )

    f.close()

    return file, data


def get_collocation(instrument):

    n = 1

    con = db()
    #con1 = db1()
   
    scaninfo = []
    date0 = datetime(2009,10,1)
    for day_i in range(200):
        
        date = date0 + relativedelta(days = day_i)
        date = '{0}-{1:02}-{2:02}'.format(*[date.year,date.month,date.day])
        print date        

        odin_scans =  get_odin_scans(con, date, freqmode)
        if len(odin_scans) == 0:
            continue
       

        current_file = []
        data = []
        for scan in odin_scans:
  
            if scan['altstart']<0 or scan['altend']<0:
                continue 

            # calculate scan mean position
            midlat,midlon = getscangeoloc( scan['latstart'], scan['lonstart'],
                                       scan['latend'], scan['lonend'] )
            deg2rad = N.pi/180.0
            x0, y0, z0 = sph2cart(midlon*deg2rad, midlat*deg2rad, 1.0)
            R0 = N.array([x0, y0, z0])
            mjd = (scan['mjdstart'] + scan['mjdend']) / 2.0 

            # search for candidate collocation scans
        
            # 1. read scan data from matching month
            sourcefile, data = read_comp_file(instrument, species, mjd, current_file = current_file, data = data)
            if sourcefile == []:
                continue
            else:
                current_file = sourcefile
                data = data     
    
            # 2. search in the data from matching month
            okdata = get_comp_scans(data, mjd, dmjd, R0)
            # okdata contains scans that matches in time
            if okdata['mjd']==[]:
                continue
        
            # identify the accepted co-locations
            ind = N.nonzero( (okdata['theta']<dtheta) )[0] 
            if ind.shape[0] == 0:
                continue
            # find the closest scan
            tempind = N.argsort( okdata['theta'][ind] )

            for i in [ind[tempind][0]]:
                #Backend, Freqmode, ScanID, File, File_Index
                temp = { 
                  'date':         date,
                  'backend':      backend,
                  'freqmode':     freqmode,
                  'scanid':       scan['scanid'],
                  'altend':       scan['altend'],
                  'altstart':     scan['altstart'],
                  'latend':       scan['latend'],
                  'latstart':     scan['latstart'],
                  'lonend':       scan['lonend'],
                  'lonstart':     scan['lonstart'],
                  'mjdend':       scan['mjdend'],
                  'mjdstart':     scan['mjdstart'],
                  'numspec':      scan['numspec'],
                  'sunzd':        scan['sunzd'],
                  'datetime':     scan['datetime'],
                  'instrument':   instrument,
                  'file':         okdata['file'][i],
                  'file_index':   okdata['file_index'][i],
                  'latitude':     okdata['latitude'][i],
                  'longitude':    okdata['longitude'][i],
                  'mjd':          okdata['mjd'][i],
                  'dmjd':         N.abs( okdata['mjd'][i]-mjd ),
                  'dtheta':       okdata['theta'][i],
                  'species':      species,   
                   }
                temp2 = [ 
                             species, 
                             okdata['file'][i], 
                             okdata['file_index'][i], 
                             okdata['latitude'][i],
                             okdata['longitude'][i],
                             okdata['mjd'][i],
                             scan['sunzd'],
                               ]
                line = "{0}\t{1}\t{2}\t{3:7.2f}\t{4:7.2f}\t{5:7.4f}\t{6:7.2f}\n".format(*temp2)
                scaninfo.append(line)
                tempkeys = [temp['backend'],temp['freqmode'],temp['scanid'],temp['file'],temp['file_index']]
                con.query('''delete from collocations 
                         where backend='{0}' and freqmode={1} and scanid={2}
                         and file='{3}' and file_index={4}
                         '''.format(*tempkeys))
                #print temp
                con.insert('collocations',temp)
                print date,n
                n = n + 1
    outfile ="/home/bengt/work/odin-api/src/scripts/test_{0}.txt".format(*[instrument])
    print outfile
    f = open(outfile, 'w')
    f.writelines(scaninfo)
    f.close() 
           
    con.close()
    #con1.close()


if __name__ == "__main__":


    # test freqmode and date below
    backend = 'AC1'
    freqmode = 2
    for species in ['HNO3','O3']:

        # co-location criteria
        dmjd = 1/24.0 # scans within 1 hours
        dz = 300.0 #km
        r = 6371.0 #Earth radius in km
        dtheta = dz/(r*2*N.pi/360.0) # scans within dz km must be within an angle of dtheta


        filepath = '/home/bengt/work/odin-api/data/vds-data/scanpos/'
        instrument = 'mls'
        get_collocation(instrument)
        instrument = 'smiles'
        get_collocation(instrument)
        instrument = 'mipas'
        get_collocation(instrument)
