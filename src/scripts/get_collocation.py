import numpy as N
from pg import DB

class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin',user='odinop',host='localhost')

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


def get_comp_scans(instrument, mjd, dmjd, species, R0):

    data = {
            'file'        : [],
            'file_index'  : [],
            'latitude'    : [],
            'longitude'   : [],
            'mjd'         : [],
            'theta'       : [],
            }

    if instrument == 'mls':
        table = 'mls_scan'
    elif instrument == 'mipas':
        table = 'mipas_scan'
   
    query = con.query('''select file,file_index,latitude,longitude,mjd
                 from {0} where mjd between {1}-{2} and {1}+{2}
                 and species='{3}' '''.format(*[table, mjd, dmjd, species]))

    result = query.dictresult()

    for row in result:
        for item in row.keys():
            data[item].append(row[item])
        # calculate position difference in degrees 
        x, y, z = sph2cart(row['longitude']*deg2rad, row['latitude']*deg2rad, 1.0)
        R1 = N.array([x, y, z])
        data['theta'].append( N.arccos( N.linalg.linalg.dot(R0, R1) ) * 180.0/N.pi )
    
    for item in data.keys():
        data[item] = N.array( data[item] )     

    return data


if __name__ == "__main__":

    # test freqmode and date below
    backend = 'AC1'
    freqmode = 2
    date = '2012-01-01'
    
    instrument = 'mipas'
    species = 'O3'

    # co-location criteria
    dmjd = 0.125 # scans within 3 hours
    dtheta = 1.0 # scans within 1 degree

    con = db()

    odin_scans =  get_odin_scans(con, date, freqmode)

    for scan in odin_scans:

        # calculate scan mean position
        midlat,midlon = getscangeoloc( scan['latstart'], scan['lonstart'],
                                       scan['latend'], scan['lonend'] )
        deg2rad = N.pi/180.0
        x0, y0, z0 = sph2cart(midlon*deg2rad, midlat*deg2rad, 1.0)
        R0 = N.array([x0, y0, z0])
        mjd = (scan['mjdstart'] + scan['mjdend']) / 2.0 

        # search for candidate colloocation scans
        data = get_comp_scans(instrument, mjd, dmjd, species, R0)

        # identify the accepted co-locations
        ind = N.nonzero( (data['theta']<dtheta) )[0] 

        for i in ind:
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
                'file':         data['file'][i],
                'file_index':   data['file_index'][i],
                'latitude':     data['latitude'][i],
                'longitude':    data['longitude'][i],
                'mjd':          data['mjd'][i],
                'dmjd':         N.abs( data['mjd'][i]-mjd ),
                'dtheta':       data['theta'][i],
                'species':      species,   
               }
          
            tempkeys = [temp['backend'],temp['freqmode'],temp['scanid'],temp['file'],temp['file_index']]

            con.query('''delete from collocations 
                     where backend='{0}' and freqmode={1} and scanid={2}
                     and file='{3}' and file_index={4}
                     '''.format(*tempkeys))
            print temp
            con.insert('collocations',temp)
           
    con.close()
