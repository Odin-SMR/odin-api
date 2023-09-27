from flask import Blueprint

from odinapi.views.level2 import (
    L2ancView,
    L2cView,
    L2iView,
    L2View,
    Level2ProjectAnnotations,
    Level2ViewArea,
    Level2ViewComments,
    Level2ViewDay,
    Level2ViewFailedScans,
    Level2ViewLocations,
    Level2ViewProducts,
    Level2ViewProductsFreqmode,
    Level2ViewProject,
    Level2ViewProjects,
    Level2ViewScan,
    Level2ViewScans,
    Level2Write,
)

production = Blueprint("level2_production", __name__)
production.add_url_rule(
    "/rest_api/<version>/level2", view_func=Level2Write.as_view("level2write")
)
production.add_url_rule(
    "/rest_api/<version>/level2/projects/",
    view_func=Level2ViewProjects.as_view("level2viewprojects"),
)
production.add_url_rule(
    "/rest_api/<version>/level2/<project>/",
    view_func=Level2ViewProject.as_view("level2viewproject"),
)
production.add_url_rule(
    "/rest_api/v5/level2/<project>/annotations",
    view_func=Level2ProjectAnnotations.as_view("level2annotations"),
)
production.add_url_rule(
    "/rest_api/<version>/level2/<project>/<int:freqmode>/comments/",
    view_func=Level2ViewComments.as_view("level2viewcomments"),
)
production.add_url_rule(
    "/rest_api/<version>/level2/<project>/<int:freqmode>/scans/",
    view_func=Level2ViewScans.as_view("level2viewscans"),
)
production.add_url_rule(
    "/rest_api/<version>/level2/<project>/<int:freqmode>/failed/",
    view_func=Level2ViewFailedScans.as_view("level2viewfailed"),
)
production.add_url_rule(
    ("/rest_api/<version>/level2/<project>" "/<int:freqmode>/<int:scanno>/"),
    view_func=Level2ViewScan.as_view("level2viewscan"),
)
production.add_url_rule(
    ("/rest_api/<version>/level2/<project>" "/<int:freqmode>/<int:scanno>/L2i/"),
    view_func=L2iView.as_view("level2L2i"),
)
production.add_url_rule(
    ("/rest_api/<version>/level2/<project>" "/<int:freqmode>/<int:scanno>/L2c/"),
    view_func=L2cView.as_view("level2L2c"),
)
production.add_url_rule(
    ("/rest_api/<version>/level2/<project>" "/<int:freqmode>/<int:scanno>/L2anc/"),
    view_func=L2ancView.as_view("level2L2anc"),
)
production.add_url_rule(
    ("/rest_api/<version>/level2/<project>" "/<int:freqmode>/<int:scanno>/L2/"),
    view_func=L2View.as_view("level2L2"),
)
production.add_url_rule(
    "/rest_api/<version>/level2/<project>/products/",
    view_func=Level2ViewProducts.as_view("level2viewproducts"),
)
production.add_url_rule(
    ("/rest_api/<version>/level2/<project>" "/<int:freqmode>/products/"),
    view_func=Level2ViewProductsFreqmode.as_view("level2viewfmproducts"),
)
production.add_url_rule(
    "/rest_api/<version>/level2/<project>/locations",
    view_func=Level2ViewLocations.as_view("level2viewlocations"),
)
production.add_url_rule(
    "/rest_api/<version>/level2/<project>/<date>/",
    view_func=Level2ViewDay.as_view("level2viewday"),
)
production.add_url_rule(
    "/rest_api/<version>/level2/<project>/area",
    view_func=Level2ViewArea.as_view("level2viewarea"),
)
