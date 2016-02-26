#! /usr/bin/env python
from pyhdf import VS, HDF
import os
from glob import glob as glob

fm_dict = {
    2: {"dir": "SM_AC1e",  "species": ['HNO3', 'O3']},
}

L2P_path = "/odin/smr/Data/SMRl2/SMRhdf/Qsmr-2-0"
VDS_path = "/odin/external/vds-data/scanpos"
instrument = "Odin-SMR-Qsmr-2-old"


if __name__ == "__main__":
    for fm in fm_dict.keys():
        print "Processing FM:", fm
        files = glob(os.path.join(L2P_path, fm_dict[fm]['dir'], '*.L2P'))
        for f in files:
            print "Processing file:", f
            # Open HDF file:
            hdf = HDF.HDF(f)
            vs = VS.VS(hdf)

            # Set up attachments and indexes:
            gloc = vs.attach('Geolocation')
            i_gloc = {x: i for i, x in enumerate(gloc._fields)}
            retr = vs.attach('Retrieval')
            i_retr = {x: i for i, x in enumerate(retr._fields)}

            # Extract meta-data:
            for r0 in gloc[:]:
                latitude = r0[i_gloc['Latitude']]
                longitude = r0[i_gloc['Longitude']]
                year = r0[i_gloc['Year']]
                month = r0[i_gloc['Month']]
                mjd = r0[i_gloc['MJD']]
                for species in fm_dict[fm]['species']:
                    index2 = [x[i_retr['ID2']] for x in retr[:]
                              if (x[i_retr['ID1']] == r0[i_gloc['ID1']] and
                                  x[i_retr['SpeciesNames']].startswith(species)
                                  )
                              ][0]

                    # Construct contents:
                    temp = [
                        species,
                        "{0}-{1}".format(fm_dict[fm]['dir'],
                                         os.path.basename(f)),
                        index2,
                        latitude,
                        longitude,
                        mjd
                        ]
                    line = ("{0}\t{1}\t{2}\t{3:7.2f}\t{4:7.2f}\t{5:7.4f}"
                            "\n".format(*temp))

                    # Construct filename:
                    filename = ("{0}/{1}_scanpos_{2:02}_{3}_{4}{5:02}"
                                ".txt".format(VDS_path, instrument, fm,
                                              species, year, month))
                    # Write to file (append):
                    with open(filename, 'a') as fp:
                        fp.write(line)

            # Clean up:
            gloc.detach()
            retr.detach()
            vs.end()
            hdf.close()
