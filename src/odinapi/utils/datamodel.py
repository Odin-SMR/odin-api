import attr
from typing import List, Any, Dict, Union
import datetime as dt
from enum import Enum, unique, auto
from dateutil.relativedelta import relativedelta

import numpy as np  # type: ignore


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


@unique
class L2Type(Enum):
    l2 = auto()
    l2i = auto()
    l2anc = auto()


@unique
class L2ancDesc(Enum):
    LST = "Mean local solar time for the scan."
    Orbit = "Odin/SMR orbit number."
    SZA1D = (
        "Mean solar zenith angle of the observations used in the retrieval "
        "process.")
    SZA = (
        "Approximate solar zenith angle corresponding to each retrieval"
        " value.")
    Theta = "Estimate of the potential temperature profile."

    @property
    def l2type(self) -> L2Type:
        return L2Type.l2anc


@unique
class L2Desc(Enum):
    Altitude = "Altitude of retrieved values."
    Apriori = "A priori profile used in the inversion algorithm."
    AVK = "Averaging kernel matrix."
    ErrorNoise = (
        "Error due to measurement thermal noise (square root of the "
        "diagonal elements of the corresponding error matrix).")
    ErrorTotal = (
        "Total retrieval error, corresponding to the error due to thermal"
        " noise and all interfering smoothing errors (square root of the"
        " diagonal elements of the corresponding error matrix).")
    InvMode = "Inversion mode."
    Lat1D = "A scalar representative latitude of the retrieval."
    Latitude = "Approximate latitude of each retrieval value."
    Lon1D = "A scalar representative longitude of the retrieval."
    Longitude = "Approximate longitude of each retrieval value."
    MeasResponse = (
        "Measurement response, defined as the row sum of the averaging"
        " kernel matrix.")
    Pressure = "Pressure grid of the retrieved profile."
    Profile = "Retrieved temperature or volume mixing ratio profile."
    Quality = "Quality flag."
    ScanID = "Satellite time word scan identifier."
    Temperature = (
        "Estimate of the temperature profile (corresponding to the"
        " ZPT input data).")
    Time = "Mean time of the scan."
    VMR = "Volume mixing ratio or retrieved profile."

    @property
    def l2type(self) -> L2Type:
        return L2Type.l2


@unique
class L2iDesc(Enum):
    GenerationTime = "Processing date."
    Residual = (
        "The difference between the spectra matching retrieved state and used "
        "measurement spectra"
    )
    MinLmFactor = (
        "The minimum value of the Levenberg - Marquardt factor during "
        "the OEM iterations"
    )
    FreqMode = "Odin/SMR observation frequency mode."

    @property
    def l2type(self) -> L2Type:
        return L2Type.l2i


@unique
class DType(Enum):
    i8 = "i8"
    f4 = "f4"
    double = "double"


@unique
class Dimension(Enum):
    d1 = ["time"]
    d2 = ["time", "level"]
    d3 = ["time", "level", "level"]


@unique
class Unit(Enum):
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
class Parameter:
    description = attr.ib(type=Union[L2Desc, L2ancDesc, L2iDesc])
    unit = attr.ib(type=Unit)
    dtype = attr.ib(type=DType)
    dimension = attr.ib(type=Dimension)

    @property
    def name(self) -> str:
        return self.description.name

    @property
    def l2type(self) -> L2Type:
        return self.description.l2type

    def get_description(self, istemperature: bool) -> str:
        if self.description == L2Desc.Profile:
            return (
                "Retrieved temperature profile."
                if istemperature
                else "Retrieved volume mixing ratio."
            )
        return self.description.value

    def get_unit(self, istemperature: bool) -> Unit:
        if self.description == L2Desc.AVK:
            return Unit.koverk if istemperature else Unit.poverp
        elif self.unit != Unit.product:
            return self.unit
        else:
            return (
                Unit.temperature if istemperature
                else Unit.unitless
            )


@attr.s
class L2File:
    parameters = attr.ib(type=List[Parameter])


@attr.s
class Filter:
    residual = attr.ib(type=float)
    minlmfactor = attr.ib(type=float)


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
            np.isfinite(self.Residual)
            and np.isfinite(self.MinLmFactor)
            and self.Residual <= self.filter.residual
            and self.MinLmFactor <= self.filter.minlmfactor
        )


@attr.s
class L2Full:
    l2i = attr.ib(type=L2i)
    l2anc = attr.ib(type=L2anc)
    l2 = attr.ib(type=L2)

    # validators connect this class to L2iDesc, L2iDesc, L2Desc, and Parameter
    @l2i.validator
    def _check_includes_all_l2idesc_attributes(self, attribute, value):
        assert all([hasattr(self.l2i, v.name) for v in L2iDesc])

    @l2anc.validator
    def _check_includes_all_l2ancdesc_attributes(self, attribute, value):
        assert all([hasattr(self.l2anc, v.name) for v in L2ancDesc])

    @l2.validator
    def _check_includes_all_l2desc_attributes(self, attribute, value):
        assert all([hasattr(self.l2, v.name) for v in L2Desc])

    def get_data(self, parameter: Parameter):
        if parameter.l2type is L2Type.l2i:
            return getattr(self.l2i, parameter.name)
        elif parameter.l2type is L2Type.l2anc:
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


def to_l2(l2: Dict[str, Any], product: str) -> L2:
    profile = (
        l2["Temperature"] if is_temperature(product)
        else l2["VMR"]
    )
    return L2(
        InvMode=l2["InvMode"],
        ScanID=l2["ScanID"],
        Time=dt.datetime(1858, 11, 17) + relativedelta(days=l2["MJD"]),
        Lat1D=l2["Lat1D"],
        Lon1D=l2["Lon1D"],
        Quality=l2["Quality"],
        Altitude=l2["Altitude"],
        Pressure=l2["Pressure"],
        Profile=profile,
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


def is_temperature(product: str) -> bool:
    return "Temperature" in product


L2FILE = L2File([
    Parameter(
        L2iDesc.GenerationTime, Unit.time, DType.f4, Dimension.d1
    ),
    Parameter(
        L2Desc.Altitude, Unit.altitude, DType.f4, Dimension.d2
    ),
    Parameter(
        L2Desc.Apriori, Unit.product, DType.f4, Dimension.d2
    ),
    Parameter(
        L2Desc.AVK, Unit.product, DType.f4, Dimension.d3
    ),
    Parameter(
        L2Desc.ErrorNoise, Unit.product, DType.f4, Dimension.d2
    ),
    Parameter(
        L2Desc.ErrorTotal, Unit.product, DType.f4, Dimension.d2
    ),
    Parameter(
        L2Desc.Lat1D, Unit.lat, DType.f4, Dimension.d1
    ),
    Parameter(
        L2Desc.Latitude, Unit.lat, DType.f4, Dimension.d2
    ),
    Parameter(
        L2Desc.Lon1D, Unit.lon, DType.f4, Dimension.d1
    ),
    Parameter(
        L2Desc.Longitude, Unit.lon, DType.f4, Dimension.d2
    ),
    Parameter(
        L2ancDesc.LST, Unit.hours, DType.f4, Dimension.d1
    ),
    Parameter(
        L2Desc.MeasResponse, Unit.unitless, DType.f4, Dimension.d2
    ),
    Parameter(
        L2ancDesc.Orbit, Unit.unitless, DType.f4, Dimension.d1
    ),
    Parameter(
        L2Desc.Pressure, Unit.pressure, DType.f4, Dimension.d2
    ),
    Parameter(
        L2Desc.Profile, Unit.product, DType.f4, Dimension.d2
    ),
    Parameter(
        L2Desc.ScanID, Unit.unitless, DType.i8, Dimension.d1
    ),
    Parameter(
        L2ancDesc.SZA1D, Unit.degrees, DType.f4, Dimension.d1
    ),
    Parameter(
        L2ancDesc.SZA, Unit.degrees, DType.f4, Dimension.d2
    ),
    Parameter(
        L2Desc.Temperature, Unit.temperature, DType.f4, Dimension.d2
    ),
    Parameter(
        L2ancDesc.Theta, Unit.temperature, DType.f4, Dimension.d2
    ),
    Parameter(
        L2Desc.Time, Unit.time, DType.double, Dimension.d1
    )
])
