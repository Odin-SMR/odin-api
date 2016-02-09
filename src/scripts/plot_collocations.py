import numpy as N
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
from matplotlib import dates,rc
from datetime import datetime
from dateutil.relativedelta import relativedelta
from mpl_toolkits.basemap import Basemap

def read_colloc_file(infile):


    f = open(infile,'r')
    lines = f.readlines()
    data = {
         'species'    : [],
         'file'       : [],
         'file_index' : [],
         'latitude'   : [],
         'longitude'  : [],
         'mjd'        : [],
         'szd'        : [],
         'dt'         : [],
           }
   
    mjd0 = datetime(1858,11,17)
    for line in lines:

        parts = line.split()

        data['species'].append( parts[0] )
        data['file'].append( parts[1] )
        data['file_index'].append( int(parts[2]) )
        data['latitude'].append( float(parts[3]) )
        data['longitude'].append( float(parts[4]) )
        data['mjd'].append( float(parts[5]) )
        data['szd'].append( float(parts[6]) )
        data['dt'].append( mjd0 + relativedelta(days = float(parts[5]) ))

    for item in data.keys():
        data[item] = N.array( data[item] )

    f.close()

    return data


if __name__ == "__main__":

    datapath = '/home/bengt/work/odin-api/src/scripts/'
   
    mipas_file = datapath + 'test_mipas.txt'
    data1 = read_colloc_file(mipas_file)
   
    mls_file = datapath + 'test_mls.txt'
    data2 = read_colloc_file(mls_file)
 
    smiles_file = datapath + 'test_smiles.txt'
    data3 = read_colloc_file(smiles_file)


    fig = plt.figure(figsize = (15,8))
    fig.suptitle('''Ozone collocations Odin-SMR (FM2): MIPAS , MLS, SMILES(Band-A): dz<=300km, dt<=6 hour''')

    ax1 = plt.subplot2grid((6,8), (0,0), colspan=7,rowspan=1)
    plt.plot(data1['dt'],data1['latitude'],'b.',label='mipas')
    plt.plot(data2['dt'],data2['latitude'],'r.',label='mls')
    plt.plot(data3['dt'],data3['latitude'],'g.',label='smiles')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Lat. [Deg.]')
    plt.legend(bbox_to_anchor=(1.01, 0.95), loc=2, borderaxespad=0.)

    ax1 = plt.subplot2grid((6,8), (1,0), colspan=7,rowspan=1)
    plt.plot(data1['dt'],data1['longitude'],'b.')
    plt.plot(data2['dt'],data2['longitude'],'r.')
    plt.plot(data3['dt'],data3['longitude'],'g.') 
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.yaxis.set_label_text('Lon. [Deg]')
    ax1.axes.xaxis.set_ticklabels([])
    #ax1.xaxis.set_label_text('Date')
    plt.xticks(rotation=10)

    ax1 = plt.subplot2grid((6,8), (2,0), colspan=7,rowspan=1)
    plt.plot(data1['dt'],data1['szd'],'b.')
    plt.plot(data2['dt'],data2['szd'],'r.')
    plt.plot(data3['dt'],data3['szd'],'g.')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.yaxis.set_label_text('SZA. [Deg]')
    hfmt = dates.DateFormatter('%Y/%m/%d-%hh:%mm')
    ax1.xaxis.set_label_text('Date')
    plt.xticks(rotation=10)
         
    ax1 = plt.subplot2grid((2,1), (1,0), colspan=1,rowspan=1)

    m = Basemap(llcrnrlon=-180,llcrnrlat=-90,urcrnrlon=180,urcrnrlat=90,projection='mill')
    m.drawcoastlines(linewidth=1.25)
    m.fillcontinents(color='0.8')
    m.drawparallels(N.arange(-80,81,20),labels=[1,1,0,0])
    m.drawmeridians(N.arange(0,360,60),labels=[0,0,0,1])

    x,y = m(data1['longitude'], data1['latitude'])
    m.plot(x, y, 'bo', markersize=3)
    x,y = m(data2['longitude'], data2['latitude'])
    m.plot(x, y, 'ro', markersize=3)
    x,y = m(data3['longitude'], data3['latitude'])
    m.plot(x, y, 'go', markersize=3)

   
    plt.show()
