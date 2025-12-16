"""A complex datamodel implementation"""

from flask import Flask
from flask_cors import CORS

from odinapi.custom_json import CustomJSONProvider

from .odin_config import Config, ProdConfig, TestConfig
from .blueprints import register_blueprints
from .pg_database import db


def create_app(config: Config = ProdConfig()):
    app = Flask("odinapi")
    app.config.from_object(config)
    app.json = CustomJSONProvider(app)
    CORS(app)
    db.init_app(app)
    register_blueprints(app)
    return app


def run():
    return create_app(TestConfig())
