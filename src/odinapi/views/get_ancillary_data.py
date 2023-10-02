from textwrap import dedent
import numpy as np
import ephem
from sqlalchemy import text  # type: ignore
from odinapi.views.geoloc_tools import sph2cart
from odinapi.utils.time_util import mjd2datetime
from odinapi.pg_database import db


def get_theta(pressure, temperature):
    """calculate potential temperature profile"""
    # standard reference pressure [Pa]
    ref_pressure = 1e5
    # gas constant [kg m**2 s**-2 K**-1 mol*-1]
    gas_constant = 8.3144598
    # specific heat capacity at constant pressure for air
    spec_heat_capacity = 29.07
    return temperature * (ref_pressure / pressure) ** (
        gas_constant / spec_heat_capacity
    )


def get_solartime(mjd, longitude):
    """calculate solar time"""
    sun = ephem.Sun()
    observer = ephem.Observer()
    observer.date = mjd2datetime(mjd)
    observer.long = longitude * np.pi / 180.0
    sun.compute(observer)
    hour_angle = observer.sidereal_time() - sun.ra
    lst = str(ephem.hours(hour_angle + ephem.hours("12:00")).norm)
    return (
        float(lst.split(":")[0])
        + float(lst.split(":")[1]) / 60.0
        + float(lst.split(":")[2]) / 3600.0
    )


def get_sza_at_retrieval_position(
    latitudes, longitudes, latitudes_att, longitudes_att, sza_att
):
    """get solar zenith angle (sza) at each retrieval position
    by interpolation
    """
    deg2rad = np.pi / 180.0
    attitude_coordinates_list = np.transpose(
        np.array(sph2cart(longitudes_att * deg2rad, latitudes_att * deg2rad, 1))
    )
    sza_ret = []
    for latitude, longitude in zip(latitudes, longitudes):
        retrieval_coordinates = np.array(
            sph2cart(longitude * deg2rad, latitude * deg2rad, 1)
        )
        angle_between_positions = []
        for attitude_coordinates in attitude_coordinates_list:
            angle_between_positions.append(
                np.arccos(
                    np.linalg.linalg.dot(attitude_coordinates, retrieval_coordinates)
                )
            )
        sza_ret.append(sza_att[np.argmin(angle_between_positions)])
    return sza_ret


def get_orbit(orbit):
    return int(np.floor(np.mean(orbit)))


def get_attitude_data(scanno):
    """get attitude data from level1 database"""
    result = db.session.execute(
        text(
            dedent(
                """\
        select stw, latitude, longitude,
        sunzd, orbit
        from ac_level1b
        join attitude_level1 using (stw)
        where calstw = :s
        order by stw"""
            )
        ),
        params=dict(s=scanno),
    )
    dict_list = dict(stw=[], latitude=[], longitude=[], sunzd=[], orbit=[])
    for row in result:
        dict_list["stw"].append(row.stw)
        dict_list["latitude"].append(row.latitude)
        dict_list["longitude"].append(row.longitude)
        dict_list["sunzd"].append(row.sunzd)
        dict_list["orbit"].append(row.orbit)

    return dict_list


def get_ancillary_data(level2_data):
    """collect ancillary data for level2 data"""
    anc_data = []
    attitude_data = get_attitude_data(level2_data[0]["ScanID"])
    orbit = get_orbit(attitude_data["orbit"])
    for product in level2_data:
        sza_at_retrieval_pos = get_sza_at_retrieval_position(
            product["Latitude"],
            product["Longitude"],
            np.array(attitude_data["latitude"]),
            np.array(attitude_data["longitude"]),
            np.array(attitude_data["sunzd"]),
        )
        sza1d_at_retrieval_pos = get_sza_at_retrieval_position(
            [product["Lat1D"]],
            [product["Lon1D"]],
            np.array(attitude_data["latitude"]),
            np.array(attitude_data["longitude"]),
            np.array(attitude_data["sunzd"]),
        )
        theta = get_theta(
            np.array(product["Pressure"]), np.array(product["Temperature"])
        )
        lst_scan = get_solartime(product["MJD"], product["Lon1D"])
        anc_data.append(
            {
                "InvMode": product["InvMode"],
                "FreqMode": product["FreqMode"],
                "ScanID": product["ScanID"],
                "MJD": product["MJD"],
                "Orbit": orbit,
                "Lat1D": product["Lat1D"],
                "Lon1D": product["Lon1D"],
                "Latitude": product["Latitude"],
                "Longitude": product["Longitude"],
                "Pressure": product["Pressure"],
                "SZA1D": float(np.around(sza1d_at_retrieval_pos, decimals=3)),
                "SZA": np.around(sza_at_retrieval_pos, decimals=3).tolist(),
                "LST": float(np.around(lst_scan, decimals=3)),
                "Theta": np.around(theta, decimals=3).tolist(),
            }
        )
    return anc_data
