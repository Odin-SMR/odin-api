from flask import Blueprint


swagger = Blueprint(
    "swagger", __name__, static_url_path="/apidocs", static_folder="/swagger-ui"
)
