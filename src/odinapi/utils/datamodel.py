import attr
from typing import List, Any, Dict
import datetime as dt
from enum import Enum
from dateutil.relativedelta import relativedelta


DATEFMT = "%Y-%m-%dT%H:%M:%SZ"


COMMON_FILE_HEADER_DATA = {
    "creator_name": 'Donal Murtagh',
    "creator_url": 'odin.rss.chalmers.se',
    "creator_email": 'donal.murtagh@chalmers.se',
    "address": '412 96 Gothenburg, Sweden',
    "institution": 'Chalmers University of Technology',
    "platform": 'Odin',
    "sensor": 'SMR',
    "version_l1b": "8",
    "version_l2": "3.0.0"
}


class L2Type(Enum):
    l2 = "l2"
    l2i = "l2i"
    l2anc = "l2anc"


class DType(Enum):
    i8 = "i8"
    f4 = "f4"
    double = "double"


class Dimension(Enum):
    d1 = ["time"]
    d2 = ["time", "level"]
    d3 = ["time", "level", "level"]


class Units(Enum):
    time = "days since 1858-11-17 00:00"
    altitude = "m"
    lat = "degrees north"
    lon = "degrees east"
    hours = "hours"
    unitless = "-"
    pressure = "Pa"
    temperature = "K"
    degrees = "degrees"
    koverk = "K/K"
    poverp = "%/%"
    product = "product"


@attr.s
class Filter:
    residual = attr.ib(type=float)
    minlmfactor = attr.ib(type=float)


@attr.s
class Parameter:
    name = attr.ib(type=str)
    units = attr.ib(type=Units)
    description = attr.ib(type=str)
    dtype = attr.ib(type=DType)
    dimension = attr.ib(type=Dimension)
    l2type = attr.ib(type=L2Type)

    def get_description(self, product: str) -> str:
        if self.name == "Profile":
            return (
                "Retrieved temperature profile."
                if "Temperature" in product
                else "Retrieved volume mixing ratio."
            )
        return self.description

    def get_units(self, product: str) -> Units:
        if self.name == "AVK":
            return Units.koverk if "Temperature" in product else Units.poverp
        elif self.units != Units.product:
            return self.units
        else:
            return (
                Units.temperature if "Temperature" in product
                else Units.unitless
            )


@attr.s
class L2File:
    parameters = attr.ib(type=List[Parameter])


@attr.s
class L2anc:
    LST = attr.ib(type=float)
    Orbit = attr.ib(type=int)
    SZA1D = attr.ib(type=float)
    SZA = attr.ib(type=List[float])
    Theta = attr.ib(type=List[float])


@attr.s
class L2:
    InvMode = attr.ib(type=str)
    ScanID = attr.ib(type=int)
    Time = attr.ib(type=dt.datetime)
    Lat1D = attr.ib(type=float)
    Lon1D = attr.ib(type=float)
    Quality = attr.ib(type=float)
    Altitude = attr.ib(type=List[float])
    Pressure = attr.ib(type=List[float])
    Profile = attr.ib(type=List[float])
    Latitude = attr.ib(type=List[float])
    Longitude = attr.ib(type=List[float])
    Temperature = attr.ib(type=List[float])
    ErrorTotal = attr.ib(type=List[float])
    ErrorNoise = attr.ib(type=List[float])
    MeasResponse = attr.ib(type=List[float])
    Apriori = attr.ib(type=List[float])
    VMR = attr.ib(type=List[float])
    AVK = attr.ib(type=List[List[float]])


@attr.s
class L2i:
    GenerationTime = attr.ib(type=dt.datetime)
    Residual = attr.ib(type=float)
    MinLmFactor = attr.ib(type=float)
    FreqMode = attr.ib(type=int)

    @property
    def filter(self) -> Filter:
        return Filter(
            residual=1.5,
            minlmfactor=10. if self.FreqMode in [8., 13., 19.] else 2.
        )

    def isvalid(self) -> bool:
        return (
            self.Residual <= self.filter.residual
            and self.MinLmFactor <= self.filter.minlmfactor
        )


@attr.s
class L2Full:
    l2i = attr.ib(type=L2i)
    l2anc = attr.ib(type=L2anc)
    l2 = attr.ib(type=L2)

    def get_data(self, parameter: Parameter):
        if parameter.l2type == L2Type.l2i:
            return getattr(self.l2i, parameter.name)
        elif parameter.l2type == L2Type.l2anc:
            return getattr(self.l2anc, parameter.name)
        return getattr(self.l2, parameter.name)


def get_file_header_data(
        freqmode: int,
        invmode: str,
        product: str,
        time_coverage_start: dt.datetime,
        time_coverage_end: dt.datetime
) -> Dict[str, str]:
    header_data = {
        "observation_frequency_mode": str(freqmode),
        "inversion_mode": invmode,
        "level2_product_name": product,
        "date_created": dt.datetime.utcnow().strftime(DATEFMT),
        "time_coverage_start": time_coverage_start.strftime(DATEFMT),
        "time_coverage_end": time_coverage_end.strftime(DATEFMT)
    }
    header_data.update(COMMON_FILE_HEADER_DATA)
    return header_data


def to_l2(l2: Dict[str, Any]) -> L2:
    return L2(
        InvMode=l2["InvMode"],
        ScanID=l2["ScanID"],
        Time=dt.datetime(1858, 11, 17) + relativedelta(days=l2["MJD"]),
        Lat1D=l2["Lat1D"],
        Lon1D=l2["Lon1D"],
        Quality=l2["Quality"],
        Altitude=l2["Altitude"],
        Pressure=l2["Pressure"],
        Profile=l2["Profile"],
        Latitude=l2["Latitude"],
        Longitude=l2["Longitude"],
        Temperature=l2["Temperature"],
        ErrorTotal=l2["ErrorTotal"],
        ErrorNoise=l2["ErrorNoise"],
        MeasResponse=l2["MeasResponse"],
        Apriori=l2["Apriori"],
        VMR=l2["VMR"],
        AVK=l2["AVK"],
    )


def to_l2anc(l2: Dict[str, Any]) -> L2anc:
    return L2anc(
        LST=l2["LST"],
        Orbit=l2["Orbit"],
        SZA1D=l2["SZA1D"],
        SZA=l2["SZA"],
        Theta=l2["Theta"],
    )


def to_l2i(l2: Dict[str, Any]) -> L2i:
    return L2i(
        GenerationTime=dt.datetime.strptime(l2["GenerationTime"], DATEFMT),
        Residual=l2["Residual"],
        MinLmFactor=l2["MinLmFactor"],
        FreqMode=l2["FreqMode"],
    )


def generate_filename(
        project: str, product: str, date_start: dt.datetime) -> str:
    return "Odin-SMR_L2_{project}_{product}_{year}-{month:02}.nc".format(
        project=project,
        product=product.replace(
            " / ", "-").replace(" - ", "-").replace(" ", "-"),
        year=date_start.year,
        month=date_start.month
    )


L2FILE = L2File([
    Parameter(
        "GenerationTime",
        Units.time,
        'Processing date.',
        DType.f4,
        Dimension.d1,
        L2Type.l2i,
    ),
    Parameter(
        "Altitude",
        Units.altitude,
        "Altitude of retrieved values.",
        DType.f4,
        Dimension.d2,
        L2Type.l2,
    ),
    Parameter(
        "Apriori",
        Units.product,
        "A priori profile used in the inversion algorithm.",
        DType.f4,
        Dimension.d2,
        L2Type.l2,
    ),
    Parameter(
        "AVK",
        Units.product,
        "Averaging kernel matrix.",
        DType.f4,
        Dimension.d3,
        L2Type.l2
    ),
    Parameter(
        "ErrorNoise",
        Units.product,
        (
            "Error due to measurement thermal noise (square root of the "
            "diagonal elements of the corresponding error matrix)."
        ),
        DType.f4,
        Dimension.d2,
        L2Type.l2,
    ),
    Parameter(
        "ErrorTotal",
        Units.product,
        (
            "Total retrieval error, corresponding to the error due to thermal"
            " noise and all interfering smoothing errors (square root of the"
            " diagonal elements of the corresponding error matrix)."
        ),
        DType.f4,
        Dimension.d2,
        L2Type.l2,
    ),
    Parameter(
        "Lat1D",
        Units.lat,
        "A scalar representative latitude of the retrieval.",
        DType.f4,
        Dimension.d1,
        L2Type.l2,
    ),
    Parameter(
        "Latitude",
        Units.lat,
        "Approximate latitude of each retrieval value.",
        DType.f4,
        Dimension.d2,
        L2Type.l2,
    ),
    Parameter(
        "Lon1D",
        Units.lon,
        "A scalar representative longitude of the retrieval.",
        DType.f4,
        Dimension.d1,
        L2Type.l2,
    ),
    Parameter(
        "Longitude",
        Units.lon,
        "Approximate longitude of each retrieval value.",
        DType.f4,
        Dimension.d2,
        L2Type.l2,
    ),
    Parameter(
        "LST",
        Units.hours,
        "Mean local solar time for the scan.",
        DType.f4,
        Dimension.d1,
        L2Type.l2anc,
    ),
    Parameter(
        "MeasResponse",
        Units.unitless,
        (
            "Measurement response, defined as the row sum of the averaging"
            " kernel matrix."
        ),
        DType.f4,
        Dimension.d2,
        L2Type.l2,
    ),
    Parameter(
        "Orbit",
        Units.unitless,
        "Odin/SMR orbit number.",
        DType.f4,
        Dimension.d1,
        L2Type.l2anc,
    ),
    Parameter(
        "Pressure",
        Units.pressure,
        "Pressure grid of the retrieved profile.",
        DType.f4,
        Dimension.d2,
        L2Type.l2,
    ),
    Parameter(
        "Profile",
        Units.product,
        "Retrieved temperature or volume mixing ratio profile.",
        DType.f4,
        Dimension.d2,
        L2Type.l2,
    ),
    Parameter(
        "ScanID",
        Units.unitless,
        "Satellite time word scan identifier.",
        DType.i8,
        Dimension.d1,
        L2Type.l2,
    ),
    Parameter(
        "SZA1D",
        Units.degrees,
        (
            "Mean solar zenith angle of the observations used in the"
            " retrieval process."
        ),
        DType.f4,
        Dimension.d1,
        L2Type.l2anc,
    ),
    Parameter(
        "SZA",
        Units.degrees,
        (
            "Approximate solar zenith angle corresponding to each retrieval"
            " value."
        ),
        DType.f4,
        Dimension.d2,
        L2Type.l2anc,
    ),
    Parameter(
        "Temperature",
        Units.temperature,
        (
            "Estimate of the temperature profile (corresponding to the"
            " ZPT input data)."
        ),
        DType.f4,
        Dimension.d2,
        L2Type.l2,
    ),
    Parameter(
        "Theta",
        Units.temperature,
        "Estimate of the potential temperature profile.",
        DType.f4,
        Dimension.d2,
        L2Type.l2anc,
    ),
    Parameter(
        "Time",
        Units.time,
        "Mean time of the scan.",
        DType.double,
        Dimension.d1,
        L2Type.l2,
    )
])
