from flask import Blueprint

from odinapi.utils.swagger import SwaggerSpecView
from odinapi.views.data_info import LatestECMF
from odinapi.views.views import ConfigDataFiles

DESCRIPTION = (
    "Odin rest api.\n\n"
    "Geographic coordinate system:\n\n"
    "* Latitude: -90 to 90\n"
    "* Longitude: 0 to 360"
)

config = Blueprint("config", __name__)
config.add_url_rule(
    "/rest_api/<version>/config_data/data_files/",
    view_func=ConfigDataFiles.as_view("configdatafiles"),
)
config.add_url_rule(
    "/rest_api/<version>/config_data/latest_ecmf_file/",
    view_func=LatestECMF.as_view("latestecmf"),
)

config.add_url_rule(
    "/rest_api/<version>/spec",
    view_func=SwaggerSpecView.as_view("swagger", "Odin API", description=DESCRIPTION),
)
