"""A complex datamodel implementation"""
from flask import Flask

from odinapi.custom_json import CustomJSONProvider

from .odin_config import Config, ProdConfig
from .blueprints import register_blueprints
from .pg_database import db


def create_app(config: Config = ProdConfig()):
    app = Flask("odinapi")
    app.config.from_object(config)
    app.json = CustomJSONProvider(app)
    db.init_app(app)
    register_blueprints(app)
    return app
