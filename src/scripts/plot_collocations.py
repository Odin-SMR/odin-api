import numpy as N
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
from matplotlib import dates,rc
from datetime import datetime
from dateutil.relativedelta import relativedelta
from mpl_toolkits.basemap import Basemap
from pg import DB


class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin',user='odinop',host='localhost')
        #DB.__init__(self,dbname='odin',user='odinop',
        #            host='malachite.rss.chalmers.se',passwd='***REMOVED***')




def read_colloc_file(freqmode, instrument, species):


    query = con.query('''select species,file,file_index,latitude,longitude,
                         mjd,sunzd from collocations where freqmode={0}
                         and instrument='{1}' and species='{2}' 
                         order by mjd'''.format(*[freqmode,instrument,species]))
    result = query.dictresult()
    
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
    for row in result:

        data['species'].append( row['species'] )
        data['file'].append( row['file'] )
        data['file_index'].append( row['file_index'] )
        data['latitude'].append( row['latitude']) 
        data['longitude'].append( row['longitude'] )
        data['mjd'].append( row['mjd'] )
        data['szd'].append( row['sunzd'] )
        data['dt'].append( mjd0 + relativedelta(days = row['mjd'] ))

    for item in data.keys():
        data[item] = N.array( data[item] )


    return data





def plot_data4xxx(freqmode, instrument, species):


    
    data1 = read_colloc_file(freqmode, 'mls', species)
    data2 = read_colloc_file(freqmode, 'mipas', species)
    data3 = read_colloc_file(freqmode, 'sageIII', species)
    data4 = read_colloc_file(freqmode, 'smiles', species)

    fig = plt.figure(figsize = (15,8))
    fig.suptitle('''{1} collocations to Odin-SMR (FM{0}): dz<=300km, dt<=? hour'''.format(*[freqmode, species]))

    ax1 = plt.subplot2grid((6,8), (0,0), colspan=7,rowspan=1)
    plt.plot(data1['dt'],data1['latitude'],'b.',label='mls')
    plt.plot(data2['dt'],data2['latitude'],'r.',label='mipas')
    plt.plot(data3['dt'],data3['latitude'],'g.',label='sageIII')
    plt.plot(data4['dt'],data4['latitude'],'c.',label='smiles')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Lat. [Deg.]')
    plt.legend(bbox_to_anchor=(1.01, 0.95), loc=2, borderaxespad=0.)

    ax1 = plt.subplot2grid((6,8), (1,0), colspan=7,rowspan=1)
    plt.plot(data1['dt'],data1['longitude'],'b.')
    plt.plot(data2['dt'],data2['longitude'],'r.')
    plt.plot(data3['dt'],data3['longitude'],'g.')
    plt.plot(data4['dt'],data4['longitude'],'c.')
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
    plt.plot(data4['dt'],data4['szd'],'c.')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.yaxis.set_label_text('SZA. [Deg]')
    hfmt = dates.DateFormatter('%Y/%m/%d-%hh:%mm')
    ax1.xaxis.set_label_text('Date')
    plt.xticks(rotation=10)

    ax1 = plt.subplot2grid((2,4), (1,0), colspan=1,rowspan=1)

    m = Basemap(llcrnrlon=-180,llcrnrlat=-90,urcrnrlon=180,urcrnrlat=90,projection='mill')
    fs = 10
    ms = 2
    a = 0.25

    ax1 = plt.subplot2grid((2,4), (1,0), colspan=1,rowspan=1)
    plt.title('mls')
    x,y = m(data1['longitude'], data1['latitude'])
    m.plot(x, y, 'bo', markersize=ms,alpha=a)
    m.drawcoastlines(linewidth=1.25)
    m.fillcontinents(color='0.8')
    m.drawmeridians(N.arange(0,360,60),labels=[0,0,0,1],fontsize=fs)
    m.drawparallels(N.arange(-80,81,20),labels=[1,0,0,0],fontsize=fs)

    ax1 = plt.subplot2grid((2,4), (1,1), colspan=1,rowspan=1)
    plt.title('mipas')
    x,y = m(data2['longitude'], data2['latitude'])
    m.plot(x, y, 'ro', markersize=ms,alpha=a)
    m.drawcoastlines(linewidth=1.25)
    m.fillcontinents(color='0.8')
    m.drawmeridians(N.arange(0,360,60),labels=[0,0,0,1],fontsize=fs)
    m.drawparallels(N.arange(-80,81,20),labels=[1,0,0,0],fontsize=fs)

    ax1 = plt.subplot2grid((2,4), (1,2), colspan=1,rowspan=1)
    plt.title('sageIII')
    x,y = m(data3['longitude'], data3['latitude'])
    m.plot(x, y, 'go', markersize=ms,alpha=a)
    m.drawcoastlines(linewidth=1.25)
    m.fillcontinents(color='0.8')
    m.drawmeridians(N.arange(0,360,60),labels=[0,0,0,1],fontsize=fs)
    m.drawparallels(N.arange(-80,81,20),labels=[1,0,0,0],fontsize=fs)

    ax1 = plt.subplot2grid((2,4), (1,3), colspan=1,rowspan=1)
    plt.title('smiles')
    x,y = m(data4['longitude'], data4['latitude'])
    m.plot(x, y, 'co', markersize=ms,alpha=a)
    m.drawcoastlines(linewidth=1.25)
    m.fillcontinents(color='0.8')
    m.drawmeridians(N.arange(0,360,60),labels=[0,0,0,1],fontsize=fs)
    m.drawparallels(N.arange(-80,81,20),labels=[1,0,0,0],fontsize=fs)

    plt.show()




if __name__ == "__main__":

    datapath = '/home/bengt/work/odin-api/src/scripts/'
    #plot_data4smiles_period()
    instrument = 'sageIII'
    species= 'O3'
    freqmode = 1
    con =db()
    plot_data4xxx(freqmode, instrument, species)
    con.close()
