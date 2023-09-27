from flask import Blueprint

from odinapi.views.views_cached import (
    DateBackendInfoCached,
    DateInfoCached,
    FreqmodeInfoCached,
    PeriodInfoCached,
)


cached = Blueprint("level1_cached", __name__)
cached.add_url_rule(
    "/rest_api/<version>/period_info/<int:year>/<int:month>/" "<int:day>/",
    view_func=PeriodInfoCached.as_view("periodinfo"),
)
cached.add_url_rule(
    "/rest_api/<version>/freqmode_info/<date>/",
    view_func=DateInfoCached.as_view("freqmodeinfo"),
)
cached.add_url_rule(
    "/rest_api/<version>/freqmode_info/<date>/<backend>/",
    view_func=DateBackendInfoCached.as_view("backendinfo"),
)
cached.add_url_rule(
    "/rest_api/<version>/freqmode_info/<date>/<backend>/" "<int:freqmode>/",
    view_func=FreqmodeInfoCached.as_view("scansinfo"),
)
cached.add_url_rule(
    "/rest_api/<version>/freqmode_info/<date>/<backend>/"
    "<int:freqmode>/<int:scanno>/",
    view_func=FreqmodeInfoCached.as_view("scaninfo"),
)
