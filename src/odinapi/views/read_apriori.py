import os

import numpy as np
import scipy.io as sio
from typing import Tuple


DAYS_PER_YEAR = 365  # neglect leap year


def get_datadict(data, source):
    def get_index(key):
        idxs = [
            i for i, v in enumerate(view)
            if v.size == 1 and v.item() == key
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


def get_interpolation_weights(
    xs: np.array, x: float, doy_interpolation: bool = False
) -> Tuple[int, int, float, float]:
    if x >= xs[-1]:
        if doy_interpolation:
            dx = xs[0] + (DAYS_PER_YEAR - xs[-1])
            w1 = (min(x, DAYS_PER_YEAR) - xs[-1]) / dx
            return 0, xs.size - 1, w1, 1. - w1
        return 0, xs.size - 1, 0., 1.
    if x <= xs[0]:
        if doy_interpolation:
            dx = xs[0] + (DAYS_PER_YEAR - xs[-1])
            w2 = (xs[0] - x) / dx
            return 0, xs.size - 1, 1. - w2, w2
        return 0, xs.size - 1, 1., 0.
    ind2 = np.argmax(x <= xs)
    ind1 = ind2 - 1
    dx = xs[ind2] - xs[ind1]
    w1 = (xs[ind2] - x) / dx
    return ind1, ind2, w1, 1. - w1


def get_vmr_interpolated_for_doy(vmr, doys, doy):
    ind1, ind2, w1, w2 = get_interpolation_weights(
        doys.flatten(), doy, doy_interpolation=True
    )
    vmr = vmr[:, :, :, ind1] * w1 + vmr[:, :, :, ind2] * w2
    return vmr[:, :, 0]


def get_vmr_interpolated_for_lat(vmr, latitudes, latitude):
    ind1, ind2, w1, w2 = get_interpolation_weights(
        latitudes.flatten(), latitude
    )
    return vmr[:, ind1] * w1 + vmr[:, ind2] * w2


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
