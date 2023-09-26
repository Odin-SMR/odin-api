"""
Module for connecting to mongodb level2 database.

Environment variables:

- ODINAPI_MONGODB_HOST (default=level2db)
- ODINAPI_MONGODB_PORT (default=27017)
- ODINAPI_MONGODB_USERNAME (default=<empty>)
- ODINAPI_MONGODB_PASSWORD (default=<empty>)
- ODINAPI_MONGODB_SERVER_TIMEOUT (default=180000 ms)

Example:

>>> col = get_collection('level2', 'L2')
>>> col.find_one()
"""

from os import environ
import logging
from typing import Optional

from pymongo import MongoClient

CLIENT: Optional[MongoClient] = None

logger = logging.getLogger("Mongo")


def get_connection():
    """Return MongoClient object"""
    global CLIENT
    if not CLIENT:
        logger.debug("Creating a new Client")
        host = environ.get("ODINAPI_MONGODB_HOST", "level2db")
        port = int(environ.get("ODINAPI_MONGODB_PORT", 27017))
        timeout = int(environ.get("ODINAPI_MONGODB_SERVER_TIMEOUT", 180000))
        logger.info(f"Connecing to {host}:{port}")
        CLIENT = MongoClient(host, port, serverSelectionTimeoutMS=timeout)
    logger.debug(f"Using connection to {CLIENT.server_info}")
    return CLIENT


def get_database(db_name):
    """Return Database object"""
    return get_connection()[db_name]


def get_collection(database, collection):
    """Return Collection object"""
    return get_database(database)[collection]
