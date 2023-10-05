from flask import current_app
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

CLIENT: MongoClient | None = None


def get_connection() -> MongoClient:
    """Return MongoClient object"""
    connection_str = current_app.config["MONGO_DATABASE_URI"]
    global CLIENT
    if not CLIENT:
        CLIENT = MongoClient(connection_str)
    return CLIENT


def get_database(db_name: str) -> Database:
    """Return Database object"""
    return get_connection().get_database(db_name)


def get_collection(db_name: str, collection: str) -> Collection:
    """Return Collection object"""
    return get_database(db_name).get_collection(collection)
