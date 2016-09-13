"""
Module for connecting to mongodb level2 database.

Environment variables:

- ODINAPI_MONGODB_HOST (default=level2db)
- ODINAPI_MONGODB_PORT (default=27017)
- ODINAPI_MONGODB_USERNAME (default=<empty>)
- ODINAPI_MONGODB_PASSWORD (default=<empty>)

Example:

>>> col = get_collection('level2', 'L2')
>>> col.find_one()
"""

from os import environ

from pymongo import MongoClient

CLIENT = None


def get_collection(database, collection):
    """Return Collection object"""
    global CLIENT
    if not CLIENT:
        CLIENT = MongoClient(
            environ.get('ODINAPI_MONGODB_HOST', 'level2db'),
            int(environ.get('ODINAPI_MONGODB_PORT', 27017)))
    return auth(CLIENT[database][collection])


def auth(db):
    username = environ.get('ODINAPI_MONGODB_USERNAME')
    if username:
        db.authenticate(
            username, password=environ.get('ODINAPI_MONGODB_PASSWORD'))
    return db
