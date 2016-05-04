import numpy as N
import datetime as DT
import requests as R
import json
from date_tools import *


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

def get_geoloc_info(url_string):
    "Get the day of year and mid-latitude of the scan"

    specinfo = json.loads(R.get(url_string).text)
    ScanID = specinfo['Info']['ScanID']
    startlon = specinfo['Info']['LonStart']
    startlat = specinfo['Info']['LatStart']
    endlon = specinfo['Info']['LonEnd']
    endlat = specinfo['Info']['LatEnd']   
    midlat,midlon = getscangeoloc(startlat,startlon,endlat,endlon)
    MJD = (specinfo['Info']['MJDStart'] + specinfo['Info']['MJDEnd'])/2
    datetime = mjd2datetime(MJD)
    doy = datetime.timetuple().tm_yday    

    return MJD,doy,midlat,midlon


