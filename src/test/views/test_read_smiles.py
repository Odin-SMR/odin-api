from pathlib import Path
import pytest

from odinapi.views.read_smiles import read_smiles_file

from .partiallistmatch import PartialListMatch


@pytest.fixture
def smiles_basepath_pattern():
    p = Path(__file__)
    for p in p.parents:
        if p.name == "src":
            p = p.parent
            break
    return p / "data" / "vds-data" / "ISS_SMILES_Level2" / "{0}" / "v2.4"


def test_read_smiles_file_geolocation_fields(smiles_basepath_pattern):
    data = read_smiles_file(
        "SMILES_L2_O3_B_008-11-0502_20091112.he5",
        "2009-11-13",
        "O3",
        3,
        smiles_basepath_pattern=str(smiles_basepath_pattern),
    )
    geoloc = data["geolocation_fields"]
    assert geoloc == {
        "Altitude": PartialListMatch(46, [8.0, 10.0, 12.0], name="Altitude"),
        "AscendingDescending": 1,
        "Latitude": -24.1200008392334,
        "LineofSightAngle": 91.33999633789062,
        "LocalTime": 2.069999933242798,
        "Longitude": 147.88999938964844,
        "MJD": 55147.675520833334,
        "Reserved": 0,
        "SolarZenithAngle": 126.05000305175781,
        "Time": 1636733565.0,
        "TimeUTC": "2009-11-12T16:12:45.000",
    }
