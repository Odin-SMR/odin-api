from odinapi.database import mongo


class Level2DB(object):

    def __init__(self):
        self.L2_collection = mongo.get_collection('level2', 'L2')
        self.L2i_collection = mongo.get_collection('level2', 'L2i')
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes if they do not already exist"""
        self.L2_collection.create_index(
            [('ScanID', 1),
             ('FreqMode', 1)
             ])
        self.L2i_collection.create_index(
            [('ScanID', 1),
             ('FreqMode', 1)
             ], unique=True)

    def store(self, L2, L2i):
        self.L2i_collection.insert_one(L2i)
        self.L2_collection.insert_many(L2)

    def delete(self, scanid, freqmode):
        self.L2i_collection.delete_many({
            'ScanID': scanid,
            'FreqMode': freqmode})
        self.L2_collection.delete_many(
            {'ScanID': scanid,
             'FreqMode': freqmode})
