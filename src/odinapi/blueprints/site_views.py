from flask import Blueprint, redirect

from ..views.smr_site import (
    ViewDataAccess,
    ViewFreqmodeInfoPlot,
    ViewIndex,
    ViewLevel1,
    ViewLevel1Stats,
    ViewLevel2,
    ViewLevel2DevScan,
    ViewLevel2PeriodOverview,
    ViewLevel2Scan,
    ViewScanSpec,
)

site_views = Blueprint("site_views", __name__)
site_views.add_url_rule("/", view_func=ViewIndex.as_view("index"))
site_views.add_url_rule("/level1", view_func=ViewLevel1.as_view("level1"))
site_views.add_url_rule(
    "/level1statistics", view_func=ViewLevel1Stats.as_view("level1statistics")
)
site_views.add_url_rule("/level2", view_func=ViewLevel2.as_view("level2"))
site_views.add_url_rule(
    "/level2/<project>/<int:freqmode>/<int:scanno>/",
    view_func=ViewLevel2Scan.as_view("viewlevel2can"),
)
site_views.add_url_rule(
    "/level2/<title>/<project>/<int:freqmode>/<int:scanno>/",
    view_func=ViewLevel2DevScan.as_view("viewlevel2devcan"),
)
site_views.add_url_rule(
    "/level2/overview/<project>/",
    view_func=ViewLevel2PeriodOverview.as_view("level2periodoverview"),
)
site_views.add_url_rule(
    "/browse/<int:freqmode>/<int:scanno>/", view_func=ViewScanSpec.as_view("viewscan")
)
site_views.add_url_rule(
    "/plot/<date>/<int:freqmode>", view_func=ViewFreqmodeInfoPlot.as_view("plotscans")
)
site_views.add_url_rule("/dataaccess", view_func=ViewDataAccess.as_view("dataaccess"))

@site_views.route("/level2_download")
def level2_download():
    return redirect("http://odin-l2netcdf.s3-website.eu-north-1.amazonaws.com/")
