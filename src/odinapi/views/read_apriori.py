import os

import numpy as np
import scipy.io as sio


def get_datadict(data, source):
    def get_index(key):
        idxs = [
            i for i, v in enumerate(view)
            if v.size == 1 and np.asscalar(v) == key
        ]
        if idxs:
            return idxs[0] - 1
        return None

    def get_data(key):
        idx = get_index(key)
        if idx is None:
            return np.array([])
        return view[idx]

    view = data[source][0][0]
    return {
        'vmr': get_data('Volume mixing ratio'),
        'pressure': get_data('Pressure'),
        'latitude': get_data('Latitude'),
        'doy': get_data('DOY'),
        'altitude': get_data('Altitude'),
    }


def get_vmr_interpolated_for_doy(vmr, doys, doy):
    deltas = np.min(
        [
            (doys[:, 0].astype(float) - doy) % 365,
            (doy - doys[:, 0].astype(float)) % 365,
        ],
        axis=0,
    )
    ind1, ind2 = np.arange(deltas.size)[np.argsort(deltas)][:2]
    doy1 = float(np.asscalar(doys[ind1]))
    doy2 = float(np.asscalar(doys[ind2]))
    ddoy = min((doy1 - doy2) % 365, (doy2 - doy1) % 365)
    w1 = deltas[ind2] / ddoy
    w2 = deltas[ind1] / ddoy
    vmr = vmr[:, :, :, ind1] * w1 + vmr[:, :, :, ind2] * w2
    return vmr[:, :, 0]


def get_vmr_interpolated_for_lat(vmr, latitudes, latitude):
    deltas = np.abs(latitudes[:, 0] - latitude)
    ind1, ind2 = np.arange(deltas.size)[np.argsort(deltas)][:2]
    lat1 = np.asscalar(latitudes[ind1])
    lat2 = np.asscalar(latitudes[ind2])
    if np.sign(lat1 - latitude) != np.sign(lat2 - latitude):
        dlat = np.abs(lat1 - lat2)
        w1 = deltas[ind2] / dlat
        w2 = deltas[ind1] / dlat
        return vmr[:, ind1] * w1 + vmr[:, ind2] * w2

    return vmr[:, ind1]


def get_apriori(
    species, day_of_year, latitude,
    source=None,
    datadir="/var/lib/odindata/apriori/",
):
    filename = (
        "apriori_{}_{}.mat".format(species, source)
        if source else "apriori_{}.mat".format(species)
    )
    path = os.path.join(datadir, filename)
    data = sio.loadmat(path)

    datadict = get_datadict(data, 'Bdx' if source is None else source.upper())

    doy = float(day_of_year)
    vmr = get_vmr_interpolated_for_doy(datadict['vmr'], datadict['doy'], doy)

    # a priori data is gridded on a latitude grid
    # covering -85 to 85:
    # below we make sure latitude is within these limits
    latitude = max(min(float(latitude), 85.0), -85.0)
    vmr = get_vmr_interpolated_for_lat(vmr, datadict['latitude'], latitude)

    return {
        'altitude': datadict['altitude'].ravel(),
        'pressure': datadict['pressure'].ravel(),
        'species': species,
        'vmr': vmr,
        # Below only used in testing
        'latitude': latitude,
        'path': path,
    }
