from pg import DB

class DatabaseConnector(DB):
    def __init__(self):
        super(DatabaseConnector, self).__init__(
            dbname='odin',
            user='odinop',
            host='postgresql',
            passwd='***REMOVED***'
            )

