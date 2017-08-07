from pg import DB
from os import environ


class DatabaseConnector(DB):
    def __init__(self):
        super(DatabaseConnector, self).__init__(
            host=environ.get("PGHOST"),
            dbname=environ.get("PGDBNAME"),
            user=environ.get("PGUSER"),
            passwd=environ.get("PGPASS")
            )
