# pylint: skip-file
from datetime import datetime
from itertools import chain
from collections import namedtuple

import numpy
from pymongo.errors import DuplicateKeyError
from pymongo import ASCENDING

from odinapi.utils.time_util import datetime2mjd, datetime2stw
from odinapi.database import mongo

PRODUCT_ARRAY_KEYS = [
    'Altitude', 'Pressure', 'Latitude', 'Longitude', 'Temperature',
    'ErrorTotal', 'ErrorNoise', 'MeasResponse', 'Apriori', 'VMR', 'AVK']
EARTH_EQ_RADIUS_KM = 6378.1

# Set a hard limit on the number of L2 documents that can be returned.
# TODO: Support paging
HARD_LIMIT = 50000


class ProjectError(Exception):
    pass


class ProjectAnnotation(namedtuple('ProjectAnnotation', [
    'text', 'created_at', 'freqmode',
])):
    def __new__(typ, text, created_at, freqmode=None):
        assert isinstance(text, basestring)
        assert isinstance(created_at, datetime)
        assert freqmode is None or isinstance(freqmode, int)
        return super(ProjectAnnotation, typ).__new__(
            typ, text, created_at, freqmode,
        )


class ProjectsDB(object):

    def __init__(self):
        self.projects_collection = mongo.get_collection('level2', 'projects')
        self._annotations = mongo.get_collection('level2', 'annotations')
        self._create_indexes()

    def _create_indexes(self):
        self.projects_collection.create_index('name', unique=True)
        self._annotations.create_index('project', unique=False)

    def add_project_if_not_exists(self, project_name):
        try:
            self.projects_collection.insert_one(
                {'name': project_name,
                 'development': True})
        except DuplicateKeyError:
            pass

    def get_project(self, project_name):
        return self.projects_collection.find_one(
            {'name': project_name},
            {'_id': False, 'name': True, 'development': True},
        )

    def get_projects(self, development=True):
        if development is None:
            # Return both development and production projects
            return self.projects_collection.find({}, {'_id': 0})
        else:
            return self.projects_collection.find(
                {'development': development},
                {'_id': False, 'name': True, 'development': True},
            )

    def publish_project(self, name):
        result = self.projects_collection.update_one(
            {'name': name},
            {'$set': {'development': False}},
        )
        if result.modified_count != 1:
            raise ProjectError

    def add_annotation(self, name, annotation):
        assert isinstance(annotation, ProjectAnnotation)
        if self.projects_collection.count({'name': name}) < 1:
            raise ProjectError
        annotationdict = {
            'project': name,
            'created_at': annotation.created_at,
            'text': annotation.text,
            'freqmode': annotation.freqmode,
        }
        self._annotations.insert_one(annotationdict)

    def get_annotations(self, name):
        if self.projects_collection.count({'name': name}) < 1:
            raise ProjectError
        for annotation in self._annotations.find({'project': name}):
            yield ProjectAnnotation(
                text=annotation['text'],
                created_at=annotation['created_at'],
                freqmode=annotation.get('freqmode'),
            )


class Level2DB(object):

    def __init__(self, project, mongo_db=None):
        if mongo_db is None:
            mongo_db = mongo.get_database('level2')
        self.L2_collection = mongo_db['L2_%s' % project]
        self.L2i_collection = mongo_db['L2i_%s' % project]
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes if they do not already exist"""
        self.L2i_collection.create_index(
            [('FreqMode', 1),
             ('ScanID', 1)
             ], unique=True)
        self.L2i_collection.create_index(
            [('FreqMode', 1),
             ('ProcessingError', 1),
             ('Comments', 1),
             ('ScanID', 1)
             ])
        self.L2_collection.create_index(
            [('FreqMode', 1),
             ('ScanID', 1)
             ])
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
        self.L2_collection.create_index(
            [
                ('Product', 1),
                ('Pressure', 1),
                ('MJD', 1),
                ('Location', '2dsphere')
            ]
        )
        self.L2_collection.create_index(
            [
                ('Product', 1),
                ('Pressure', 1),
                ('MJD', 1),
                ('Latitude', 1),
                ('Longitude', 1)
            ]
        )

    def store(self, L2, L2i, L2c):
        """Store the output from the qsmr processing for a freqmode and
        scan id.
        """
        L2i['Comments'] = L2c.split('\n')
        self.L2i_collection.insert_one(L2i)
        if L2:
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
        L2i = L2 = L2c = None
        L2i = self.L2i_collection.find_one(
            match, {'_id': 0, 'ProcessingError': 0})
        if L2i:
            L2c = L2i.pop('Comments', [])
            L2 = collapse_products(
                list(self.L2_collection.find(
                    match, {'_id': 0, 'Location': 0})))
        return L2i, L2, L2c

    def get_L2i(self, freqmode, scanid):
        match = {'ScanID': scanid, 'FreqMode': freqmode}
        return self.L2i_collection.find_one(match, {
            '_id': 0, 'Comments': 0, 'ProcessingError': 0})

    def get_L2c(self, freqmode, scanid):
        match = {'ScanID': scanid, 'FreqMode': freqmode}
        obj = self.L2i_collection.find_one(match, {'_id': 0, 'Comments': 1})
        return obj['Comments']

    def get_L2(self, freqmode, scanid, product=None):
        match = {'ScanID': scanid, 'FreqMode': freqmode}
        if product:
            match['Product'] = product
        return collapse_products(
            list(self.L2_collection.find(
                match, {'_id': 0, 'Location': 0})))

    def get_freqmodes(self):
        """Return list of unique freqmodes in the project"""
        return self.L2i_collection.distinct('FreqMode')

    def get_products(self, freqmode=None):
        """Return list of unique products in the project"""
        match = {}
        if freqmode:
            match['FreqMode'] = freqmode
        return self.L2_collection.distinct('Product', filter=match)

    def get_comments(self, freqmode, offset=None, limit=None):
        """Return unique comments for a freqmode"""
        pipeline = [
            {'$match': {'FreqMode': freqmode}},
            {'$unwind': "$Comments"},
            {'$group': {'_id': '$Comments'}},
            {'$sort': {'_id': 1}},
        ]
        if offset is not None:
            pipeline.append({'$skip': offset})
        if limit is not None:
            pipeline.append({'$limit': limit})
        for group in self.L2i_collection.aggregate(pipeline):
            yield group['_id']

    def count_comments(self, freqmode):
        pipeline = [
            {'$match': {'FreqMode': freqmode}},
            {'$unwind': "$Comments"},
            {'$group': {'_id': '$Comments'}},
            {'$count': 'count'},
        ]
        return self.L2i_collection.aggregate(pipeline).next()['count']

    def _get_scans(self, freqmode, fields, start_time=None, end_time=None,
                   comment=None, failed=False, limit=None, offset=None):
        limit = HARD_LIMIT if limit is None else limit
        offset = 0 if offset is None else offset
        query = {'FreqMode': freqmode, 'ProcessingError': failed}
        if start_time or end_time:
            query['ScanID'] = {}
            if start_time:
                query['ScanID']['$gte'] = datetime2stw(start_time)
            if end_time:
                query['ScanID']['$lt'] = datetime2stw(end_time)
        if comment:
            query['Comments'] = comment

        return (
            self.L2i_collection.find(query, fields).skip(offset).limit(limit)
        )

    def get_scans(self, freqmode, **kwargs):
        """Return matching scans that succeeded the level2 processing
        """
        fields = {'ScanID': 1, '_id': 0}
        for scan in self._get_scans(freqmode, fields, **kwargs):
            yield scan

    def count_scans(self, freqmode, **kwargs):
        scans = self._get_scans(freqmode, {'ScanID': 1}, **kwargs)
        return scans.count()

    def get_failed_scans(self, freqmode, **kwargs):
        """Return matching scans that failed the level2 processing"""
        fields = {'ScanID': 1, 'Comments': {'$slice': -1}, '_id': 0}
        for scan in self._get_scans(freqmode, fields, failed=True, **kwargs):
            yield scan

    def count_failed_scans(self, freqmode, **kwargs):
        scans = self._get_scans(freqmode, {'ScanID': 1}, failed=True, **kwargs)
        return scans.count()

    def get_product_count(self):
        """Return count grouped by product"""
        # TODO: $group does not use the indexes
        counts = list(self.L2_collection.aggregate([
            {'$group': {'_id': '$Product', 'count': {'$sum': 1}}}
        ]))
        return {count['_id']: count['count'] for count in counts}

    def get_measurements(self, products,
                         min_altitude=None, max_altitude=None,
                         min_pressure=None, max_pressure=None,
                         start_time=None, end_time=None, areas=None,
                         fields=None):
        if not products:
            products = self.L2_collection.distinct('Product')
        elif isinstance(products, basestring):
            products = [products]
        query = {'Product': {'$in': products}}

        if min_altitude or max_altitude:
            query['Altitude'] = {}
            if min_altitude:
                query['Altitude']['$gte'] = min_altitude
            if max_altitude:
                query['Altitude']['$lte'] = max_altitude

        if min_pressure or max_pressure:
            query['Pressure'] = {}
            if min_pressure:
                query['Pressure']['$gte'] = min_pressure
            if max_pressure:
                query['Pressure']['$lte'] = max_pressure

        if start_time or end_time:
            query['MJD'] = {}
            if start_time:
                query['MJD']['$gte'] = datetime2mjd(start_time)
            if end_time:
                query['MJD']['$lt'] = datetime2mjd(end_time)

        if areas:
            if isinstance(areas, GeographicArea):
                areas = [areas]
            query = {'$and': [
                query, {'$or': [area.query for area in areas]}]}

        # TODO:
        # Raise if indexes cannot be used proparly?
        # Examples when indexes are missing:
        # - No pressure/altitude limits, but start_time/end_time/areas
        #   provided.
        # - Longitude limits without latitude limits.
        # - Pressure and altitude limits at the same time.

        fields = fields or {}
        if fields:
            fields = {field: 1 for field in fields}
        fields['_id'] = 0
        fields['Location'] = 0
        sort = [('FreqMode', ASCENDING), ('ScanID', ASCENDING)]

        for conc in self.L2_collection.find(
                query, fields, sort=sort, limit=HARD_LIMIT):
            yield conc


class GeographicArea(object):
    def __init__(self, min_lat=None, max_lat=None, min_lon=None, max_lon=None):
        assert any([min_lat, max_lat, min_lon, max_lon])
        # TODO: Support other lat/lon formats.
        query = {}
        if min_lat and max_lat:
            if float(min_lat) > float(max_lat):
                raise ValueError(
                    'Min latitude must not be larger than max latitude')
        if min_lon and max_lon:
            if float(min_lon) > float(max_lon):
                raise ValueError(
                    'Min longitude must not be larger than max longitude')
        # TODO: Enforce -90 <= lat <= 90 and 0 <= lon <= 360.
        #       But we want to be able to find scans with out of bounds
        #       coordinates for now.
        if min_lat or max_lat:
            query['Latitude'] = {}
            if min_lat:
                query['Latitude']['$gte'] = float(min_lat)
            if max_lat:
                query['Latitude']['$lte'] = float(max_lat)
        if min_lon or max_lon:
            query['Longitude'] = {}
            if min_lon:
                query['Longitude']['$gte'] = float(min_lon)
            if max_lon:
                query['Longitude']['$lte'] = float(max_lon)
        self.query = query


class GeographicCircle(GeographicArea):
    def __init__(self, lat, lon, radius):
        lat, lon = float(lat), float(lon)
        validate_lat_lon(lat, lon)
        self.query = {'Location': {
            '$geoWithin': {'$centerSphere': [
                [to_geojson_longitude(lon), lat], radius/EARTH_EQ_RADIUS_KM]}}}


def collapse_products(products):
    """Group the products, this is the inverse of expand_product"""
    products.sort(key=lambda p: (p['Product'], -p['Pressure']))
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
    if not isinstance(p['VMR'], list):
        if p['VMR'] is None or numpy.isnan(p['VMR']):
            p['VMR'] = [None for _ in range(len(p['Altitude']))]
    for (altitude, pressure, lat, lon, temp, errtot, errnoise, measresp,
         apriori, vmr, avk) in zip(
             *[p[array_key] for array_key in PRODUCT_ARRAY_KEYS]):
        doc = {
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
            'Temperature': temp,
            'ErrorTotal': errtot,
            'ErrorNoise': errnoise,
            'MeasResponse': measresp,
            'Apriori': apriori,
            'VMR': vmr,
            'AVK': avk
        }
        location = get_geojson_point(lat, lon)
        if location:
            doc['Location'] = location
        if doc['Quality'] is not None and numpy.isnan(doc['Quality']):
            # NaN is not a valid JSON symbol according to the spec and will
            # break loading of the data in some environments.
            # TODO: Check for NaN and Infinity in all of the data.
            doc['Quality'] = None
        yield doc


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


def get_geojson_point(lat, lon):
    try:
        validate_lat_lon(lat, lon)
        return {'type': 'Point', 'coordinates': [
            to_geojson_longitude(lon), lat]}

    except ValueError:
        return None


def to_geojson_longitude(lon):
    return (lon + 180) % 360 - 180


def validate_lat_lon(lat, lon):
    if not -90 <= lat <= 90:
        raise ValueError('Latitude must be between -90 and 90')
    if not 0 <= lon <= 360:
        raise ValueError('Latitude must be between 0 and 360')
