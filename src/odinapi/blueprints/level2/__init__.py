from flask import Flask

from .development import development
from .production import production


def register_blueprints(app: Flask):
    app.register_blueprint(production)
    app.register_blueprint(development)
