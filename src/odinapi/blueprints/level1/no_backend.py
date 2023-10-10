from flask import Blueprint

from odinapi.views.views import (
    CollocationsView,
    FreqmodeInfoNoBackend,
    ScanAPRNoBackend,
    ScanInfoNoBackend,
    ScanPTZNoBackend,
    ScanSpecNoBackend,
)
from odinapi.views.views_cached import (
    FreqmodeInfoCachedNoBackend,
    L1LogCached,
    L1LogCachedList,
    ScanInfoCachedNoBackend,
)

no_backend = Blueprint("no_backend", __name__)
no_backend.add_url_rule(
    "/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/Log/",
    view_func=L1LogCached.as_view("scanlogv5"),
)
no_backend.add_url_rule(
    "/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/L1b/",
    view_func=ScanSpecNoBackend.as_view("l1bv5"),
)
no_backend.add_url_rule(
    "/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/ptz/",
    view_func=ScanPTZNoBackend.as_view("ptznobackend"),
)
no_backend.add_url_rule(
    "/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/apriori/<species>/",
    view_func=ScanAPRNoBackend.as_view("apriorinobackend"),
)
no_backend.add_url_rule(
    ("/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/collocations/"),
    view_func=CollocationsView.as_view("collocations"),
)
no_backend.add_url_rule(
    ("/rest_api/<version>/level1/<int:freqmode>/scans/"),
    view_func=L1LogCachedList.as_view("scanslist"),
)

no_backend.add_url_rule(
    "/rest_api/<version>/freqmode_info/<date>/<int:freqmode>/",
    view_func=FreqmodeInfoCachedNoBackend.as_view("scansinfonobackend"),
)
no_backend.add_url_rule(
    "/rest_api/<version>/freqmode_info/<date>/<int:freqmode>/<int:scanno>/",
    view_func=ScanInfoCachedNoBackend.as_view("scaninfonobackend"),
)

no_backend.add_url_rule(
    "/rest_api/<version>/freqmode_raw/<date>/<int:freqmode>/",
    view_func=FreqmodeInfoNoBackend.as_view("scansinforawnobackend"),
)
no_backend.add_url_rule(
    "/rest_api/<version>/freqmode_raw/<date>/<int:freqmode>/<int:scanno>/",
    view_func=ScanInfoNoBackend.as_view("scaninforawnobackend"),
)
