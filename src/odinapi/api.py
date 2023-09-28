"""A complex datamodel implementation"""
import logging
import logging.config
from os import environ

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


host = environ.get("PGHOST")
dbname = environ.get("PGDBNAME")
user = environ.get("PGUSER")
passwd = environ.get("PGPASS")
sslmode = environ.get("PGSSLMODE", "verify-full")

logger = logging.getLogger(__name__)

logger.info("Starting OdinAPI")
app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"postgresql://{user}:{passwd}@{host}/{dbname}?sslmode={sslmode}"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = dict(
    pool_size=3, max_overflow=5, pool_recycle=3600
)
db = SQLAlchemy(app)
