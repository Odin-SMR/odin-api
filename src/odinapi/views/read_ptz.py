import logging
from typing import List, Literal, TypedDict

import pyarrow.compute as pc  # type: ignore
import pyarrow.dataset as ds  # type: ignore
import s3fs  # type: ignore

logger = logging.getLogger("odin.ptz")

Backend = Literal["AC1", "AC2"]


class PTZ(TypedDict):
    Pressure: list[float]
    Temperature: list[float]
    Altitude: list[float]
    Latitude: float
    Longitude: float
    MJD: float


def prefix_names(stw: int) -> List[str]:
    dir_name = stw >> 6 * 4
    return [f"{dir_name:x}", f"{dir_name-1:x}"]


def get_ptz(
    backend: Backend, scanid: int, mjd: int, lat: float, lon: float
) -> PTZ | None:
    s3 = s3fs.S3FileSystem()
    result: PTZ | None = None
    for prefix in prefix_names(scanid):
        s3_path = f"odin-zpt/{backend.lower()}/{prefix}"
        try:
            dataset = ds.dataset(s3_path, format="parquet", filesystem=s3)
        except FileNotFoundError:
            logger.warning(
                "Path does not exist: %s, looking for scanid %x(%i)",
                s3_path,
                scanid,
                scanid,
            )
            continue
        table = dataset.to_table(filter=ds.field("ScanID") == scanid)
        if table.num_rows == 0:
            logger.debug(
                "No ptz data found for scanid %x(%i) in path %s",
                scanid,
                scanid,
                s3_path,
            )
            continue
        ptz = table.sort_by("z")
        logger.debug("found scanid %x(%i) in path %s", scanid, scanid, s3_path)
        result = PTZ(
            Altitude=pc.multiply(ptz["z"], 1000).to_pylist(),  # type:ignore
            Pressure=pc.round(pc.multiply(ptz["p"], 100), ndigits=8).to_pylist(),  # type: ignore
            Temperature=pc.round(ptz["t"], ndigits=3).to_pylist(),  # type:ignore
            Latitude=lat,
            Longitude=lon,
            MJD=mjd,
        )
    return result
