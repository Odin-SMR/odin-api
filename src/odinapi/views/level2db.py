from odinapi.database import mongo


class Level2DB(object):

    def __init__(self, project):
        self.L2_collection = mongo.get_collection(
            'level2', 'L2_%s' % project)
        self.L2i_collection = mongo.get_collection(
            'level2', 'L2i_%s' % project)
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

    def get_scan(self, freqmode, scanid):
        match = {'ScanID': scanid, 'FreqMode': freqmode}
        L2i = L2 = None
        L2i = self.L2i_collection.find_one(match)
        if L2i:
            L2i.pop('_id')
            L2 = list(self.L2_collection.find(match))
            for e in L2:
                e.pop('_id')
        return L2i, L2
