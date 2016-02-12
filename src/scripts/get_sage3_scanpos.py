import os
import numpy as np
from glob import glob as glob
from readS3 import Sage3Solar, Sage3Lunar


def get_mean_geolocation(latitudes, longitudes):
    deg2rad = np.pi / 180
    theta = (-latitudes + 90) * deg2rad
    phi = longitudes * deg2rad

    x = np.nanmean(np.sin(theta) * np.cos(phi))
    y = np.nanmean(np.sin(theta) * np.sin(phi))
    z = np.nanmean(np.cos(theta))

    latitude = -(np.arccos(z) - 0.5 * np.pi) / deg2rad
    longitude = np.atan2(y, x) / deg2rad

    return latitude, longitude


if __name__ == "__main__":
    sage_datapath = ("/odin/external/vds-data/Meteor3M_SAGEIII_Level2")
    vdspath = ("/odin/external/vds-data/scanpos")

    solar_species = ("O3", "NO2", "H2O")
    lunar_species = ("O3", "NO2", "NO3", "OClO")

    for year in xrange(2001, 2006):
        for month in xrange(1, 13):
            datapath = "{0}/{1}/{2:02}/".format(sage_datapath, year, month)
            solar_files = glob(os.path.join(datapath, 'v04', '*ssp*.h5'))
            lunar_files = glob(os.path.join(datapath, 'v03', '*lsp*.h5'))
            solar_dict = {'type': 'Solar',
                          'files': solar_files,
                          'species': solar_species,
                          'data': Sage3Solar}
            lunar_dict = {'type': 'Lunar',
                          'files': lunar_files,
                          'species': lunar_species,
                          'data': Sage3Lunar}

            for event_dict in [solar_dict, lunar_dict]:
                scaninfo = {}
                if len(event_dict['files']) == 0:
                    continue

                for theFile in event_dict['files']:
                    data = event_dict['data'](theFile)
                    latitude, longitude = get_mean_geolocation(data.latitudes,
                                                               data.longitudes)

                    for species in event_dict['species']:
                        temp = [
                            species,
                            os.path.basename(theFile),
                            0,
                            latitude,
                            longitude,
                            np.nanmean(data.datetimes_mjd)
                            ]
                        line = ("{0}\t{1}\t{2}\t{3:7.2f}\t{4:7.2f}\t{5:7.4f}"
                                "\n".format(*temp))
                        try:
                            scaninfo[species].append(line)
                        except KeyError:
                            scaninfo[species] = [line]

                for species in event_dict['species']:
                    outfile = ("{0}/Meteor3M_SAGEIII_{1}_scanpos_{2}_{3}"
                               "{4:02}.txt".format(vdspath, event_dict['type'],
                                                   species, year, month))
                    print outfile
                    with open(outfile, 'w') as f:
                        f.writelines(scaninfo)
