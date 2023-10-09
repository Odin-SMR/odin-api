from flask import Blueprint

from ..views.views import (
    VdsDateInfo,
    VdsExtData,
    VdsFreqmodeInfo,
    VdsInfo,
    VdsInstrumentInfo,
    VdsScanInfo,
)

vds_views = Blueprint("vds_views", __name__)

vds_views.add_url_rule("/rest_api/<version>/vds/", view_func=VdsInfo.as_view("vdsinfo"))
vds_views.add_url_rule(
    "/rest_api/<version>/vds/<backend>/<freqmode>/",
    view_func=VdsFreqmodeInfo.as_view("vdsfreqmodeinfo"),
)
vds_views.add_url_rule(
    "/rest_api/<version>/vds/<backend>/<freqmode>/allscans",
    view_func=VdsScanInfo.as_view("vdsScaninfo"),
)
vds_views.add_url_rule(
    "/rest_api/<version>/vds/<backend>/<freqmode>/<species>/<instrument>/",
    view_func=VdsInstrumentInfo.as_view("vdsinstrumentinfo"),
)
vds_views.add_url_rule(
    "/rest_api/<version>/vds/<backend>/<freqmode>/<species>/<instrument>/<date>/",
    view_func=VdsDateInfo.as_view("vdsdateinfo"),
)
vds_views.add_url_rule(
    "/rest_api/<version>/vds_external/<instrument>/<species>"
    "/<date>/<file>/<file_index>/",
    view_func=VdsExtData.as_view("vdsextdata"),
)
