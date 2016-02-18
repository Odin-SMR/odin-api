import numpy as N
from pg import DB
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import random

class db(DB):
    def __init__(self):
        #DB.__init__(self,dbname='odin',user='odinop',host='localhost')
        DB.__init__(self,dbname='odin',user='odinop',
                    host='malachite.rss.chalmers.se',passwd='***REMOVED***')

class db1(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin',user='odinop',host='localhost')
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



def get_odin_scans(con, date1, date2, freqmode):

    query = con.query('''select date,freqmode,backend,scanid,altend,altstart,datetime,
                         latend,latstart,lonend,lonstart,mjdend,mjdstart,numspec,sunzd
                         from scans_cache where date between '{0}' and '{1}' and freqmode={2}          
                         '''.format(*[date1, date2, freqmode]))
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
    elif instrument == 'sageIII':
        file = 'Meteor3M_SAGEIII_Solar_scanpos_{0}_{1}{2:02}.txt'.format(*[species, date_i.year,date_i.month])

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
    con1 = db1()
   
    scaninfo = []
    scaninfo2 = []
    scaninfo3 = []

    # co-location criteria
    r = 6371.0 #Earth radius in km
    dz = 300.0 #km
    dtheta = dz/(r*2*N.pi/360.0) # scans within dz km must be within an angle of dtheta

    # define observation period for the various sensors
    if instrument == 'mipas':
  
        date0 = datetime(2002,7,1)
        date1 = datetime(2012,4,30)
        total_months = (date1 - date0).days/30 + 1
        ni_max = 5

    elif instrument == 'mls':

        date0 = datetime(2004,8,1)
        date1 = datetime(2015,5,31)
        total_months = (date1 - date0).days/30 + 1
        ni_max = 5

    elif instrument == 'smiles':
  
        date0 = datetime(2009,10,1)
        date1 = datetime(2010,4,30)
        total_months = (date1 - date0).days/30 + 1
        ni_max = 1000

    elif instrument == 'sageIII':
  
        date0 = datetime(2002,5,1)
        date1 = datetime(2005,11,30)
        total_months = (date1 - date0).days/30 + 1
        ni_max = 1000

    # create latitude bins 
    dlat = 10
    left_lat_limits = N.arange(-85,85,dlat)
   

    # loop over each month of the relevant observation period 
    for month_i in range(total_months):
        
        date1 = date0 + relativedelta(months = month_i)
        date2 = date0 + relativedelta(months = month_i + 1) + relativedelta(days = -1)
        date1 = '{0}-{1:02}-{2:02}'.format(*[date1.year,date1.month,date1.day])
        date2 = '{0}-{1:02}-{2:02}'.format(*[date2.year,date2.month,date2.day])        

        print date1,date2        

        odin_scans =  get_odin_scans(con, date1, date2, freqmode)
        if len(odin_scans) == 0:
            continue
       
        current_file = []
        data = []
        current_file2 = []
        data2 = []
        current_file3 = []
        data3 = []

 
        # loop over each latitude bin: stop when ni_max collocations are identified and stored
        for left_lat_limit in left_lat_limits:

            if instrument=='mls' or instrument=='mipas':

                if left_lat_limit==-85 or left_lat_limit==75:
                    dmjd = 1/24.0 # scans within 1 hour
                else:
                    dmjd = 6/24.0 # scans within 6 hours

            if instrument=='sageIII' or instrument=='smiles':
                dmjd = 1/24.0 # scans within 1 hour

            random.shuffle(odin_scans)
            ni = 0
            lat_limits = [left_lat_limit, left_lat_limit + dlat]             
            print lat_limits

            for scan in odin_scans:
  
                if scan['altstart']<0 or scan['altend']<0:
                    continue 

                # calculate odin scan mean position
                midlat,midlon = getscangeoloc( scan['latstart'], scan['lonstart'],
                                       scan['latend'], scan['lonend'] )

                if midlat > lat_limits[0] and midlat <= lat_limits[1]:
                    pass
                else:
                    continue

                deg2rad = N.pi/180.0
                x0, y0, z0 = sph2cart(midlon*deg2rad, midlat*deg2rad, 1.0)
                R0 = N.array([x0, y0, z0])
                mjd = (scan['mjdstart'] + scan['mjdend']) / 2.0 

                # search for candidate collocation scans
        
                # 1. read scan data from matching month: 
                if len(species_list)==1:
                    sourcefile, data = read_comp_file(instrument, species_list[0], mjd, current_file = current_file, data = data)
                    if data == []:
                        continue
                    else:
                        current_file = sourcefile
                        data = data   
                         
      
                elif len(species_list)==2:
                    sourcefile, data = read_comp_file(instrument, species_list[0], mjd, current_file = current_file, data = data) 
                    sourcefile2, data2 = read_comp_file(instrument, species_list[1], mjd, current_file = current_file2, data = data2)
                    if data == [] or data2 == []:
                        continue
                    else:
                        current_file = sourcefile
                        data = data     
                        current_file2 = sourcefile2
                        data2 = data2
          
                elif len(species_list)==3:
                    sourcefile, data = read_comp_file(instrument, species_list[0], mjd, current_file = current_file, data = data) 
                    sourcefile2, data2 = read_comp_file(instrument, species_list[1], mjd, current_file = current_file2, data = data2)
                    sourcefile3, data3 = read_comp_file(instrument, species_list[2], mjd, current_file = current_file3, data = data3)
                    if data == [] or data2 == [] or data3 == []:
                        continue
                    else:
                        current_file = sourcefile
                        data = data     
                        current_file2 = sourcefile2
                        data2 = data2 
                        current_file3 = sourcefile3
                        data3 = data3  
    
                # 2. search in the data from matching month
                
                okdata = get_comp_scans(data, mjd, dmjd, R0)
                # okdata contains scans that matches in time
                if okdata['mjd']==[]:
                    continue
        
                if len(species_list) > 1:
                    okdata2 = get_comp_scans(data2, mjd, dmjd, R0)
                    if okdata2['mjd']==[]:
                        continue
                if len(species_list) > 2:
                    okdata3 = get_comp_scans(data3, mjd, dmjd, R0)
                    if okdata3['mjd']==[]:
                        continue
  

                # identify the accepted co-locations
                ind = N.nonzero( (okdata['theta']<dtheta) )[0] 
                if ind.shape[0] == 0:
                    continue

                if len(species_list) > 1:
                    ind2 = N.nonzero( (okdata2['theta']<dtheta) )[0] 
                    if ind2.shape[0] == 0:
                        continue

                if len(species_list) > 2:
                    ind3 = N.nonzero( (okdata3['theta']<dtheta) )[0] 
                    if ind3.shape[0] == 0:
                        continue

                # find the closest scan
                tempind = N.argsort( okdata['theta'][ind] )
                if len(species_list) > 1:
                    tempind2 = N.argsort( okdata2['theta'][ind2] )
                if len(species_list) > 2:
                    tempind3 = N.argsort( okdata3['theta'][ind3] )                

                for i in [ind[tempind][0]]:
                    #Backend, Freqmode, ScanID, File, File_Index
                    temp = { 
                      'date':         scan['date'],
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
                      'species':      okdata['species'][i],   
                       }
                    temp2 = [ 
                             okdata['species'][i], 
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
                    con1.query('''delete from collocations 
                         where backend='{0}' and freqmode={1} and scanid={2}
                         and file='{3}' and file_index={4}
                         '''.format(*tempkeys))
                    con1.insert('collocations',temp)
                    print scan['date'],n,ni
                    n = n + 1
                    ni = ni + 1

                if len(species_list) > 1:

                    for i in [ind2[tempind2][0]]:
                        temp = { 
                      'date':         scan['date'],
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
                      'file':         okdata2['file'][i],
                      'file_index':   okdata2['file_index'][i],
                      'latitude':     okdata2['latitude'][i],
                      'longitude':    okdata2['longitude'][i],
                      'mjd':          okdata2['mjd'][i],
                      'dmjd':         N.abs( okdata2['mjd'][i]-mjd ),
                      'dtheta':       okdata2['theta'][i],
                      'species':      okdata2['species'][i],   
                           }
                        temp2 = [ 
                             okdata2['species'][i], 
                             okdata2['file'][i], 
                             okdata2['file_index'][i], 
                             okdata2['latitude'][i],
                             okdata2['longitude'][i],
                             okdata2['mjd'][i],
                             scan['sunzd'],
                               ]
                        line = "{0}\t{1}\t{2}\t{3:7.2f}\t{4:7.2f}\t{5:7.4f}\t{6:7.2f}\n".format(*temp2)
                        scaninfo2.append(line)
                        tempkeys = [temp['backend'],temp['freqmode'],temp['scanid'],temp['file'],temp['file_index']]
                        con1.query('''delete from collocations 
                         where backend='{0}' and freqmode={1} and scanid={2}
                         and file='{3}' and file_index={4}
                         '''.format(*tempkeys))
                        con1.insert('collocations',temp)

                if len(species_list) > 2:

                    for i in [ind3[tempind3][0]]:
                        temp = { 
                      'date':         scan['date'],
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
                      'file':         okdata3['file'][i],
                      'file_index':   okdata3['file_index'][i],
                      'latitude':     okdata3['latitude'][i],
                      'longitude':    okdata3['longitude'][i],
                      'mjd':          okdata3['mjd'][i],
                      'dmjd':         N.abs( okdata3['mjd'][i]-mjd ),
                      'dtheta':       okdata3['theta'][i],
                      'species':      okdata3['species'][i],   
                           }
                        temp2 = [ 
                             okdata3['species'][i], 
                             okdata3['file'][i], 
                             okdata3['file_index'][i], 
                             okdata3['latitude'][i],
                             okdata3['longitude'][i],
                             okdata3['mjd'][i],
                             scan['sunzd'],
                               ]
                        line = "{0}\t{1}\t{2}\t{3:7.2f}\t{4:7.2f}\t{5:7.4f}\t{6:7.2f}\n".format(*temp2)
                        scaninfo3.append(line)
                        tempkeys = [temp['backend'],temp['freqmode'],temp['scanid'],temp['file'],temp['file_index']]
                        con1.query('''delete from collocations 
                         where backend='{0}' and freqmode={1} and scanid={2}
                         and file='{3}' and file_index={4}
                         '''.format(*tempkeys))
                        con1.insert('collocations',temp)




                if ni == ni_max:
                    break

    outfile ="/home/bengt/work/odin-api/src/scripts/test_{0}.txt".format(*[instrument])
    print outfile
    f = open(outfile, 'w')
    f.writelines(scaninfo)
    f.close() 
           
    con.close()
    con1.close()


if __name__ == "__main__":


    # test freqmode and date below
    

    # Backend    Freqmode    Instrument     Species
    #-----------------------------------------------------
    # AC1        2           SMILES         O3, HNO3
    #                        MLS            O3, HNO3
    #                        MIPAS          O3, HNO3
    #                        SAGEIII        O3 
    #-----------------------------------------------------
    # AC1        13          SMILES         O3
    #                        MLS            O3, H2O
    #                        MIPAS          O3, H2O
    #                        SAGEIII        O3,
    #-----------------------------------------------------
    # AC1        19          SMILES         O3
    #                        MLS            O3, H2O
    #                        MIPAS          O3, H2O
    #                        SAGEIII        O3,
    #-----------------------------------------------------
    # AC1        21          SMILES         O3, NO
    #                        MLS            O3, H2O
    #                        MPIAS          O3, H2O
    #                        SAGEIII        O3,
    #-----------------------------------------------------
    # AC2        1           SMILES         O3
    #                        MLS            O3, ClO, N2O
    #                        MIPAS          O3, N2O
    #                        SAGEIII        O3,
    #-----------------------------------------------------
    # AC2        8           SMILES         O3
    #                        MLS            O3, H2O
    #                        MIPAS          O3, H2O
    #                        SAGEIII        O3,
    #-----------------------------------------------------
    # AC2        14          SMILES         O3
    #                        MLS            O3, CO
    #                        MIPAS          O3, CO
    #                        SAGEIII        O3,
    #-----------------------------------------------------
    # AC2        17          SMILES         O3
    #                        MLS            O3, H2O
    #                        MIPAS          O3, H2O
    #                        SAGEIII        O3
    #-----------------------------------------------------
    # Time span:
    # MIPAS:    200207 - 201204
    # SMILES:   200910 - 201004
    # SAGEIII:  200205 - 200511
    # MLS:      200408 - 201505 
    #-----------------------------------------------------
       

    filepath = '/home/bengt/work/odin-api/data/vds-data/scanpos/'

    for fm in [1, 2, 8, 13, 14, 17, 19, 21]:
        print fm

        if fm==2:

            backend = 'AC1'
            freqmode = 2

            species_list = ['HNO3','O3']
            for instrument in ['smiles','mls','mipas']:
                get_collocation(instrument)
            
            species_list = ['O3']
            instrument = 'sageIII'
            get_collocation(instrument)

        elif fm==1:

            backend = 'AC2'
            freqmode = 1

            species_list = ['O3','ClO','N2O']
            instrument = 'mls'
            get_collocation(instrument)

            species_list = ['O3','N2O']
            instrument = 'mipas'
            get_collocation(instrument)
            
            species_list = ['O3']
            for instrument in ['smiles','sageIII']:
                get_collocation(instrument)
 

        elif fm==8:

            backend = 'AC2'
            freqmode = 8

            species_list = ['O3','H2O']    
            for instrument in ['mls','mipas']:
                get_collocation(instrument)

            species_list = ['O3']
            for instrument in ['smiles','sageIII']:
                get_collocation(instrument)


        elif fm==13:

            backend = 'AC1'
            freqmode = 13
             
            species_list = ['O3','H2O']
            for instrument in ['mls','mipas']:
                get_collocation(instrument)

            species_list = ['O3']
            for instrument in ['smiles','sageIII']:
                get_collocation(instrument)



        elif fm==14:

            backend = 'AC2'
            freqmode = 14

            species_list = ['O3','CO']
            for instrument in ['mls','mipas']:
                get_collocation(instrument)

            species_list = ['O3']
            for instrument in ['smiles','sageIII']:
                get_collocation(instrument)


        elif fm==17:

            backend = 'AC2'
            freqmode = 17
            
            species_list = ['O3','H2O']
            for instrument in ['mls','mipas']:
                get_collocation(instrument)

            species_list = ['O3']
            for instrument in ['smiles','sageIII']:
                get_collocation(instrument)

   
        elif fm==19:

            backend = 'AC1'
            freqmode = 19
            
            species_list = ['O3','H2O']
            for instrument in ['mls','mipas']:
                get_collocation(instrument)

            species_list = ['O3']
            for instrument in ['smiles','sageIII']:
                get_collocation(instrument)


    
        elif fm==21:

            backend = 'AC1'
            freqmode = 21

            species_list = ['O3','H2O']
            for instrument in ['mls','mipas']:
                get_collocation(instrument)
           
            species_list = ['O3','NO']
            instrument = 'smiles'
            get_collocation(instrument)

            species_list = ['O3']
            instrument = 'sageIII'
            get_collocation(instrument)


            




