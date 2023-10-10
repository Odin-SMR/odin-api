from flask import Blueprint

from ...views.views import DateBackendInfo, DateInfo, FreqmodeInfo


raw = Blueprint("level1_raw", __name__)
raw.add_url_rule(
    "/rest_api/<version>/freqmode_raw/<date>/",
    view_func=DateInfo.as_view("freqmoderaw"),
)
raw.add_url_rule(
    "/rest_api/<version>/freqmode_raw/<date>/<backend>/",
    view_func=DateBackendInfo.as_view("backendraw"),
)
raw.add_url_rule(
    "/rest_api/<version>/freqmode_raw/<date>/<backend>/<int:freqmode>/",
    view_func=FreqmodeInfo.as_view("scansraw"),
)
raw.add_url_rule(
    "/rest_api/<version>/freqmode_raw/<date>/<backend>/<int:freqmode>/<int:scanno>/",
    view_func=FreqmodeInfo.as_view("scanraw"),
)
