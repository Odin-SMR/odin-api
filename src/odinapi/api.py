"""A complex datamodel implementation"""

from flask import Flask
from flask_cors import CORS
from flasgger import Swagger  # type: ignore

from odinapi.custom_json import CustomJSONProvider

from .odin_config import Config, ProdConfig, TestConfig
from .blueprints import register_blueprints
from .pg_database import db


def create_app(config: Config = ProdConfig()):
    app = Flask("odinapi")
    app.config.from_object(config)
    app.json = CustomJSONProvider(app)
    CORS(app)

    # Initialize Swagger/OpenAPI documentation
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/rest_api/v5/spec",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    }
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Odin API",
            "description": "Odin rest api.\n\nGeographic coordinate system:\n\n* Latitude: -90 to 90\n* Longitude: 0 to 360",
            "version": "v5",
        },
        "basePath": "/",
    }
    Swagger(app, config=swagger_config, template=swagger_template)

    db.init_app(app)
    register_blueprints(app)
    return app


def run():
    return create_app(TestConfig())
