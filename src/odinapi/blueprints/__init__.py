from flask import Flask

from .config import config
from .level1 import register_blueprints as l1_register_blueprints
from .level2 import register_blueprints as l2_register_blueprints
from .site_views import site_views
from .stats import stats
from .vds_views import vds_views


def register_blueprints(app: Flask):
    app.register_blueprint(config)
    app.register_blueprint(site_views)
    app.register_blueprint(stats)
    app.register_blueprint(vds_views)
    l1_register_blueprints(app)
    l2_register_blueprints(app)
