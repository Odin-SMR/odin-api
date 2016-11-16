"""
TODO:
    The functionality in this submodule would probably be better
    implemented as a JSON schema, see e.g.:
        http://json-schema.org/examples.html
"""
l2i_prototype = {
    "BLineOffset": [range(12) for _ in range(4)],
    "ChannelsID": [range(639)],
    "FitSpectrum": [range(639)],
    "FreqMode": 0,
    "FreqOffset": 0.0,
    "InvMode": "",
    "LOFreq": [range(12)],
    "MinLmFactor": 0,
    "PointOffset": 0.0,
    "Residual": 0.0,
    "STW": [range(1) for _ in range(12)],
    "ScanID": 0,
    "Tsat": 0.0,
    "SBpath": 0.0,
}

l2_prototype = {
    'AVK': [[0.0]],         # (2-D array of doubles)
    'Altitude': [0.0],      # (array of doubles)
    'Apriori': [0.0],       # (array of doubles)
    'ErrorNoise': [0.0],    # (array of doubles)
    'ErrorTotal': [0.0],    # (array of doubles)
    'FreqMode': 0,          # (int)
    'InvMode': '',          # (string)
    'Lat1D': 0.0,           # (double)
    'Latitude': [0.0],      # (array of doubles)
    'Lon1D': 0.0,           # (double)
    'Longitude': [0.0],     # (array of doubles)
    'MJD': 0.0,             # (double)
    'MeasResponse': [0.0],  # (array of doubles)
    'Pressure': [0.0],      # (array of doubles)
    'Product': '',          # (string)
    'Quality': None,        # (?)
    'ScanID': 0,            # (int)
    'Temperature': [0.0],   # (array of doubles)
    'VMR': [0.0]            # (array of doubles)
}


class JsonModelError(Exception):
    pass


def check_json(data, prototype={"Data": ""}, allowUnexpected=False,
               allowMissing=False, fillMissing=False):
    """
    Go through data, and try to add contents to mimic prototype.

    Will fail if data contains unexpected keys or if expected keys are
    missing, unless this is overridden by keywords.
    """
    lowKey = {}
    for k in prototype.keys():
        lowKey[k.lower()] = k

    if fillMissing:
        fixedData = prototype.copy()
    else:
        fixedData = {}

    for k in data.keys():
        try:
            if isinstance(prototype[lowKey[k.lower()]], dict):
                tmp = check_json(data[k], prototype[lowKey[k.lower()]],
                                 allowUnexpected, allowMissing, fillMissing)
                if "JSONError" in tmp.keys():
                    fixedData["JSONError"] = tmp["JSONError"]
                fixedData[lowKey[k.lower()]] = tmp
            else:
                fixedData[lowKey[k.lower()]] = data[k]
        except KeyError:
            if allowUnexpected:
                fixedData[k] = data[k]
            else:
                raise JsonModelError(
                    "Data contains unexpected key '{0}'".format(k))

    if not allowMissing:
        for k in prototype.keys():
            try:
                fixedData[k]
            except KeyError:
                raise JsonModelError(
                    "Data is missing expected key '{0}'".format(k))

    return fixedData
