"""A complex datamodel implementation"""
import logging
import logging.config
from os import environ

from flask import Flask

from .blueprints import register_blueprints
from .pg_database import db


host = environ.get("PGHOST")
dbname = environ.get("PGDBNAME")
user = environ.get("PGUSER")
passwd = environ.get("PGPASS")
sslmode = environ.get("PGSSLMODE", "verify-full")

logger = logging.getLogger(__name__)


class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{user}:{passwd}@{host}/{dbname}?sslmode={sslmode}"
    )
    SQLALCHEMY_ENGINE_OPTIONS = dict(pool_size=3, max_overflow=5, pool_recycle=300)


logger.info("Starting OdinAPI")


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    register_blueprints(app)
    return app


app = create_app()
