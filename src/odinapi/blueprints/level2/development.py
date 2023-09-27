from flask import Blueprint

from odinapi.views.level2 import (
    L2ancView,
    L2cView,
    L2iView,
    L2View,
    Level2ProjectAnnotations,
    Level2ProjectPublish,
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
)

development = Blueprint("level2_development", __name__)
development.add_url_rule(
    "/rest_api/<version>/level2/development/projects/",
    view_func=Level2ViewProjects.as_view("level2devviewprojects", development=True),
)
development.add_url_rule(
    "/rest_api/<version>/level2/development/<project>/",
    view_func=Level2ViewProject.as_view("level2devviewproject", development=True),
)
development.add_url_rule(
    "/rest_api/v5/level2/development/<project>/publish",
    view_func=Level2ProjectPublish.as_view("level2publishproject"),
)
development.add_url_rule(
    "/rest_api/v5/level2/development/<project>/annotations",
    view_func=Level2ProjectAnnotations.as_view("level2devannotations"),
)
development.add_url_rule(
    "/rest_api/<version>/level2/development/<project>/<int:freqmode>/" "comments/",
    view_func=Level2ViewComments.as_view("level2devviewcomments", development=True),
)
development.add_url_rule(
    "/rest_api/<version>/level2/development/<project>/<int:freqmode>/" "scans/",
    view_func=Level2ViewScans.as_view("level2devviewscans", development=True),
)
development.add_url_rule(
    "/rest_api/<version>/level2/development/<project>/<int:freqmode>/" "failed/",
    view_func=Level2ViewFailedScans.as_view("level2devviewfailed", development=True),
)
development.add_url_rule(
    (
        "/rest_api/<version>/level2/development/<project>"
        "/<int:freqmode>/<int:scanno>/"
    ),
    view_func=Level2ViewScan.as_view("level2devviewscan", development=True),
)
development.add_url_rule(
    "/rest_api/<version>/level2/development/<project>/products/",
    view_func=Level2ViewProducts.as_view("level2devviewproducts", development=True),
)
development.add_url_rule(
    "/rest_api/<version>/level2/development/<project>/<int:freqmode>/" "products/",
    view_func=Level2ViewProductsFreqmode.as_view(
        "level2devviewfmproducts", development=True
    ),
)
development.add_url_rule(
    (
        "/rest_api/<version>/level2/development/<project>"
        "/<int:freqmode>/<int:scanno>/L2i/"
    ),
    view_func=L2iView.as_view("level2devL2i", development=True),
)
development.add_url_rule(
    (
        "/rest_api/<version>/level2/development/<project>"
        "/<int:freqmode>/<int:scanno>/L2c/"
    ),
    view_func=L2cView.as_view("level2devL2c", development=True),
)
development.add_url_rule(
    (
        "/rest_api/<version>/level2/development/<project>"
        "/<int:freqmode>/<int:scanno>/L2anc/"
    ),
    view_func=L2ancView.as_view("level2devL2anc", development=True),
)
development.add_url_rule(
    (
        "/rest_api/<version>/level2/development/<project>"
        "/<int:freqmode>/<int:scanno>/L2/"
    ),
    view_func=L2View.as_view("level2devL2", development=True),
)
development.add_url_rule(
    "/rest_api/<version>/level2/development/<project>/locations",
    view_func=Level2ViewLocations.as_view("level2devviewlocations", development=True),
)
development.add_url_rule(
    "/rest_api/<version>/level2/development/<project>/<date>/",
    view_func=Level2ViewDay.as_view("level2devviewday", development=True),
)
development.add_url_rule(
    "/rest_api/<version>/level2/development/<project>/area",
    view_func=Level2ViewArea.as_view("level2devviewarea", development=True),
)
