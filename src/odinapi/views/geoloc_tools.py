import numpy as N
from odinapi.utils.time_util import mjd2datetime


def sph2cart(azimuth, elevation, radius):
    rcos_theta = radius * N.cos(elevation)
    x_cart = rcos_theta * N.cos(azimuth)
    y_cart = rcos_theta * N.sin(azimuth)
    z_cart = radius * N.sin(elevation)
    return x_cart, y_cart, z_cart


def cart2sph(x_cart, y_cart, z_cart):
    hypot_xy = N.hypot(x_cart, y_cart)
    radius = N.hypot(hypot_xy, z_cart)
    elevation = N.arctan2(z_cart, hypot_xy)
    azimuth = N.arctan2(y_cart, x_cart)
    return azimuth, elevation, radius


def getscangeoloc(lat_start, lon_start, lat_end, lon_end):
    deg2rad = N.pi / 180.0
    rad2deg = 180 / N.pi
    lat_start = lat_start * deg2rad
    lon_start = lon_start * deg2rad
    lat_end = lat_end * deg2rad
    lon_end = lon_end * deg2rad
    [x_start, y_start, z_start] = sph2cart(lon_start, lat_start, 1)
    [x_end, y_end, z_end] = sph2cart(lon_end, lat_end, 1)
    [lon_mid, lat_mid, _] = cart2sph(
        (x_start + x_end) / 2.0, (y_start + y_end) / 2.0, (z_start + z_end) / 2.0
    )
    lon_mid = lon_mid * rad2deg
    lat_mid = lat_mid * rad2deg
    return lat_mid, lon_mid


def get_geoloc_info(logdata):
    "Get the day of year and mid-latitude of the scan"
    lon_start = logdata["LonStart"][0]
    lat_start = logdata["LatStart"][0]
    lon_end = logdata["LonEnd"][0]
    lat_end = logdata["LatEnd"][0]
    lat_mid, lon_mid = getscangeoloc(lat_start, lon_start, lat_end, lon_end)
    mjd_mid = (logdata["MJDStart"][0] + logdata["MJDEnd"][0]) / 2
    datetime_scan = mjd2datetime(mjd_mid)
    doy = datetime_scan.timetuple().tm_yday
    return (mjd_mid, doy, lat_mid, lon_mid)
