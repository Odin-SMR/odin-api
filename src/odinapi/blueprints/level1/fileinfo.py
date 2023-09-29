from flask import Blueprint

from odinapi.views.data_info import FileInfo


fileinfo = Blueprint("fileinfo", __name__)
fileinfo.add_url_rule(
    "/rest_api/<version>/file_info/", view_func=FileInfo.as_view("file_info")
)
