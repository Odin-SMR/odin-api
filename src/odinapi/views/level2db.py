from itertools import chain

from odinapi.database import mongo

PRODUCT_ARRAY_KEYS = [
    'Altitude', 'Pressure', 'Latitude', 'Longitude', 'Temperature',
    'ErrorTotal', 'ErrorNoise', 'MeasResponse', 'Apriori', 'VMR', 'AVK']


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
        self.L2_collection.create_index(
            [
                ('Product', 1),
                ('Altitude', 1),
                ('MJD', 1),
                ('Location', '2dsphere')
            ]
        )
        self.L2_collection.create_index(
            [
                ('Product', 1),
                ('Altitude', 1),
                ('MJD', 1),
                ('Latitude', 1),
                ('Longitude', 1)
            ]
        )

    def store(self, L2, L2i):
        """Store the output from the qsmr processing for a freqmode and
        scan id.
        """
        self.L2i_collection.insert_one(L2i)
        products = chain(*(expand_product(p) for p in L2))
        self.L2_collection.insert_many(list(products))

    def delete(self, scanid, freqmode):
        """Delete info and all products for a freqmode and scanid"""
        self.L2i_collection.delete_many({
            'ScanID': scanid,
            'FreqMode': freqmode})
        self.L2_collection.delete_many(
            {'ScanID': scanid,
             'FreqMode': freqmode})

    def get_scan(self, freqmode, scanid):
        """Return info and all products for a freqmode and scanid.

        Use the same format as the output from the qsmr processing.
        """
        match = {'ScanID': scanid, 'FreqMode': freqmode}
        L2i = L2 = None
        L2i = self.L2i_collection.find_one(match)
        if L2i:
            L2i.pop('_id')
            L2 = list(self.L2_collection.find(match))
            for e in L2:
                e.pop('_id')
            L2 = collapse_products(L2)
        return L2i, L2


def collapse_products(products):
    """Group the products, this is the inverse of expand_product"""
    products.sort(key=lambda p: (p['Product'], p['Altitude']))
    prods = {}
    for product in products:
        pname = product['Product']
        if pname not in prods:
            prods[pname] = get_collapsed_product_dict(product)
        else:
            prod = prods[pname]
            for array_key in PRODUCT_ARRAY_KEYS:
                prod[array_key].append(product[array_key])
    return prods.values()


def expand_product(product):
    """Generate one document for each altitude"""
    p = product
    for (altitude, pressure, lat, lon, temp, errtot, errnoise, measresp,
         apriori, vmr, avk) in zip(
             *[p[array_key] for array_key in PRODUCT_ARRAY_KEYS]):
        yield {
            'Product': p['Product'],
            'FreqMode': p['FreqMode'],
            'ScanID': p['ScanID'],
            'InvMode': p['InvMode'],
            'MJD': p['MJD'],
            'Lat1D': p['Lat1D'],
            'Lon1D': p['Lon1D'],
            'Quality': p['Quality'],
            'Altitude': altitude,
            'Pressure': pressure,
            'Latitude': lat,
            'Longitude': lon,
            'Location': {'type': 'Point', 'coordinates': [lon, lat]},
            'Temperature': temp,
            'ErrorTotal': errtot,
            'ErrorNoise': errnoise,
            'MeasResponse': measresp,
            'Apriori': apriori,
            'VMR': vmr,
            'AVK': avk
        }


def get_collapsed_product_dict(product):
    p = product
    return {
        'Product': p['Product'],
        'FreqMode': p['FreqMode'],
        'ScanID': p['ScanID'],
        'InvMode': p['InvMode'],
        'MJD': p['MJD'],
        'Lat1D': p['Lat1D'],
        'Lon1D': p['Lon1D'],
        'Quality': p['Quality'],
        'Altitude': [p['Altitude']],
        'Pressure': [p['Pressure']],
        'Latitude': [p['Latitude']],
        'Longitude': [p['Longitude']],
        'Temperature': [p['Temperature']],
        'ErrorTotal': [p['ErrorTotal']],
        'ErrorNoise': [p['ErrorNoise']],
        'MeasResponse': [p['MeasResponse']],
        'Apriori': [p['Apriori']],
        'VMR': [p['VMR']],
        'AVK': [p['AVK']]
    }
