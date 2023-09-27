from flask import Blueprint

from ...views.views import ScanAPR, ScanPTZ, ScanSpec
from ...views.views_cached import L1LogCached_v4

scan = Blueprint("level1_scan", __name__)
scan.add_url_rule(
    "/rest_api/<version>/l1_log/<int:freqmode>/<int:scanno>/",
    view_func=L1LogCached_v4.as_view("scanlog"),
)
scan.add_url_rule(
    "/rest_api/<version>/scan/<backend>/<int:freqmode>/<int:scanno>/",
    view_func=ScanSpec.as_view("scan"),
)
scan.add_url_rule(
    "/rest_api/<version>/ptz/<date>/<backend>/<int:freqmode>/" "<int:scanno>/",
    view_func=ScanPTZ.as_view("ptz"),
)
scan.add_url_rule(
    "/rest_api/<version>/apriori/<species>/<date>/<backend>/"
    "<int:freqmode>/<int:scanno>/",
    view_func=ScanAPR.as_view("apriori"),
)
