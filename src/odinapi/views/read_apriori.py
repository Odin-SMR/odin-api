import scipy.io as sio
import numpy as N


def get_apriori(species,day_of_year,latitude):

    
    doy = float(day_of_year)
    latitude = float(latitude)
    # a priori data is gridded on a latitude grid
    # covering -85 to 85: 
    # below we make sure latitude is within these limits
    latitude = N.min( [latitude, 85.0] )
    latitude = N.max( [latitude, -85.0] )        

    filename = '''/var/lib/odindata/apriori/apriori_{0}.mat'''.format(species)
    a = sio.loadmat(filename)
 
    datadict = {
        'vmr':      a['Bdx'][0][0][4],
        'pressure': a['Bdx'][0][0][7],
        'latitude': a['Bdx'][0][0][10],
        'doy':      a['Bdx'][0][0][16],
           }


    # Interpolation in doy
    ind1 = N.nonzero(datadict['doy']<=doy)[0]
    ind1 = ind1[-1]
    doy1 = N.float64(datadict['doy'][ind1])
    diff1 = N.abs(doy1-doy)

    ind2 = N.nonzero(datadict['doy']>doy)[0]
    ind2 = ind2[0]
    doy2 = N.float64(datadict['doy'][ind2])
    diff2 = N.abs(doy2-doy)

    ddoy = N.abs(doy1-doy2)

    w1 = diff2/ddoy
    w2 = diff1/ddoy

    vmr = datadict['vmr'][:,:,:,ind1]*w1 + datadict['vmr'][:,:,:,ind2]*w2
    vmr = vmr[:,:,0]

    # Interpolation in lat

    ind1 = N.nonzero(datadict['latitude']<=latitude)[0]
    ind1 = ind1[-1]
    lat1 = N.float64(datadict['latitude'][ind1])
    diff1 = N.abs(lat1-latitude)

    ind2 = N.nonzero(datadict['latitude']>latitude)[0]
    if not ind2.shape[0]==0:
        # average vmr 
        ind2 = ind2[0]
        lat2 = N.float64(datadict['latitude'][ind2])
        diff2 = N.abs(lat2-latitude)

        dlat = N.abs(lat1-lat2)
        w1 = diff2/dlat
        w2 = diff1/dlat

        vmr = vmr[:,ind1]*w1 + vmr[:,ind2]*w2

    else:
        vmr = vmr[:,ind1]

    datadict['pressure'].shape = (datadict['pressure'].shape[0])
    data = {'pressure':datadict['pressure'], 'vmr':vmr, 
            'species':species, 'latitude':latitude, 'day_of_year':doy,
            'source':filename}

    return data


