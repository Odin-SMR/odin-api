from flask import Blueprint

from odinapi.views.views import ConfigDataFiles

config = Blueprint("config", __name__)
config.add_url_rule(
    "/rest_api/<version>/config_data/data_files/",
    view_func=ConfigDataFiles.as_view("configdatafiles"),
)
