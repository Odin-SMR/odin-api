from flask import Flask

from .cached import cached
from .fileinfo import fileinfo
from .no_backend import no_backend
from .raw import raw
from .scan import scan


def register_blueprints(app: Flask):
    app.register_blueprint(no_backend)
    app.register_blueprint(raw)
    app.register_blueprint(fileinfo)
    app.register_blueprint(scan)
    app.register_blueprint(cached)
