import os
import tempfile
from typing import Tuple

import boto3
import numpy as np
import numpy.typing as npt
from scipy.io import loadmat  # type: ignore

DAYS_PER_YEAR = 365  # neglect leap year


def get_datadict(data, source):
    def get_index(key):
        idxs = [i for i, v in enumerate(view) if v.size == 1 and v.item() == key]
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
        "vmr": get_data("Volume mixing ratio"),
        "pressure": get_data("Pressure"),
        "latitude": get_data("Latitude"),
        "doy": get_data("DOY"),
        "altitude": get_data("Altitude"),
    }


def get_interpolation_weights(xs: npt.NDArray, x: float) -> Tuple[int, int, float, float]:
    assert x > xs[0] and x <= xs[-1]
    ind2 = np.argmax(x <= xs)
    ind1 = ind2 - 1
    dx = xs[ind2] - xs[ind1]
    w1 = (xs[ind2] - x) / dx
    return int(ind1), int(ind2), w1, 1.0 - w1


def get_interpolation_weights_for_lat(
    lats: npt.NDArray, lat: float
) -> Tuple[int, int, float, float]:
    if lat <= lats[0]:
        return 0, lats.size - 1, 1.0, 0.0
    if lat >= lats[-1]:
        return 0, lats.size - 1, 0.0, 1.0
    return get_interpolation_weights(lats, lat)


def get_interpolation_weights_for_doy(
    xs: npt.NDArray, x: float
) -> Tuple[int, int, float, float]:
    if x <= xs[0] or x >= xs[-1]:
        dx = DAYS_PER_YEAR + xs[0] - xs[-1]
        xi = min(x, DAYS_PER_YEAR)  # neglect leap year
        w1 = ((xi - xs[-1]) % DAYS_PER_YEAR) / dx
        return 0, xs.size - 1, w1, 1.0 - w1
    return get_interpolation_weights(xs, x)


def get_vmr_interpolated_for_doy(vmr, doys, doy):
    ind1, ind2, w1, w2 = get_interpolation_weights_for_doy(doys.flatten(), doy)
    vmr = vmr[:, :, :, ind1] * w1 + vmr[:, :, :, ind2] * w2
    return vmr[:, :, 0]


def get_vmr_interpolated_for_lat(vmr, latitudes, latitude):
    ind1, ind2, w1, w2 = get_interpolation_weights_for_lat(
        latitudes.flatten(), latitude
    )
    return vmr[:, ind1] * w1 + vmr[:, ind2] * w2


def get_apriori(
    species,
    day_of_year,
    latitude,
    source=None,
    datadir="/var/lib/odindata/apriori/",
):
    filename = (
        "apriori_{}_{}.mat".format(species, source)
        if source
        else "apriori_{}.mat".format(species)
    )
    path = os.path.join(datadir, filename)
    s3 = boto3.client("s3")

    with tempfile.NamedTemporaryFile(suffix=".mat") as tmp:
        s3.download_fileobj("odin-apriori", path, tmp)
        tmp.seek(0)
        data = loadmat(tmp.name)
 
        datadict = get_datadict(data, "Bdx" if source is None else source.upper())

        doy = float(day_of_year)
        vmr = get_vmr_interpolated_for_doy(datadict["vmr"], datadict["doy"], doy)

        vmr = get_vmr_interpolated_for_lat(vmr, datadict["latitude"], latitude)

        return {
            "altitude": datadict["altitude"].ravel(),
            "pressure": datadict["pressure"].ravel(),
            "species": species,
            "vmr": vmr,
            # Below only used in testing
            "latitude": latitude,
            "path": path,
        }
