import os
import tempfile

from pyhdf import HDF, VS  # type: ignore

from odinapi.odin_aws.s3 import s3_fileobject

BUCKET = "odin-smr"
PREFIX = "SMRhdf"
L2P_PATH_2_1 = "Qsmr-2-1"
L2P_PATH_2_0 = "Qsmr-2-0"
L2P_PATH_2_3 = "Qsmr-2-3"
L2P_PATH_2_4 = "Qsmr-2-4"


def read_qsmr_file(filename, species, index2):
    # Open HDF file:
    index2 = int(index2)
    l2p_path = ""
    if filename.split(".")[0].endswith("020"):
        l2p_path = L2P_PATH_2_0
    elif filename.split(".")[0].endswith("021"):
        l2p_path = L2P_PATH_2_1
    elif filename.split(".")[0].endswith("023"):
        l2p_path = L2P_PATH_2_3
    elif filename.split(".")[0].endswith("024"):
        l2p_path = L2P_PATH_2_4
    filename = str(os.path.join(*filename.split("-")))
    with tempfile.NamedTemporaryFile() as tmp:
        buffer = s3_fileobject(f"s3://{BUCKET}/{PREFIX}/{l2p_path}/{filename}")
        if buffer:
            tmp.write(buffer.read())
        hdf = HDF.HDF(tmp.name)
        vs = VS.VS(hdf)

        # Attatch and create indexes:
        gloc = vs.attach("Geolocation")
        i_gloc = {x: i for i, x in enumerate(gloc._fields)}
        retr = vs.attach("Retrieval")
        i_retr = {x: i for i, x in enumerate(retr._fields)}
        data = vs.attach("Data")
        i_data = {x: i for i, x in enumerate(data._fields)}

        try:
            # Get the index in the geoloc table associated with the scan:
            index1 = [x[i_retr["ID1"]] for x in retr[:] if x[i_retr["ID2"]] == index2][
                0
            ]

            # Extract geolocation data to dictionary:
            gloc_dict = {}
            Geolocation = [x for x in gloc[:] if x[i_gloc["ID1"]] == index1][0]
            for key in i_gloc:
                gloc_dict[key] = Geolocation[i_gloc[key]]

            # Extract Data to dictionary:
            data_dict = {}
            Data = [x for x in data[:] if x[i_data["ID2"]] == index2]
            for key in i_data:
                data_dict[key] = [x[i_data[key]] for x in Data]
        except IndexError:
            gloc_dict = {}
            data_dict = {}

        # Clean up:
        gloc.detach()
        retr.detach()
        data.detach()
        vs.end()
        hdf.close()

    # Return:
    return {"Data": data_dict, "Geolocation": gloc_dict}
