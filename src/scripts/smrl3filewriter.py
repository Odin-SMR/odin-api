#! /usr/bin/env python
import os
from argparse import ArgumentParser
import datetime as DT
import numpy as np
from netCDF4 import Dataset


# grids used for averaging data
PRESSURE_GRID_CCI = np.array([
    450, 400, 350, 300, 250, 200, 170, 150, 130, 115, 100,
    90, 80, 70, 50, 40, 30, 20, 15, 10, 7, 5, 4, 3, 2, 1.5,
    1.0, 0.7, 0.5, 0.4, 0.3, 0.2, 0.15, 0.1, 0.07, 0.05, 0.04,
    0.03, 0.02, 0.015, 0.01, 0.007, 0.005, 0.004, 0.003, 0.002,
    0.0015, 0.001, 0.0007, 0.0005, 0.0004, 0.0003, 0.0002,
    0.00015, 0.0001
])
LATITUDE_GRID = np.arange(-85.0, 90.0, 10.0)
QUARTILE = np.array([25.0, 50.0, 75.0])


FILE_ATTRIBUTES = {
    'title': (
        "ESA MesosphEO / ESA Odin reprocessing "
        "{} {} product level 3"),
    'institution': 'Chalmers University of Technology',
    'platform': 'Odin',
    'sensor': 'SMR',
    'affiliation': (
        "Chalmers University of Technology, "
        "Department of Earth and Space Sciences"),
    'source': 'Odin/SMR L3 version 3.0',
    'level_1_data_version': '8.0',
    'level_2_data_version': '3.0',
    'level_3_data_version': '3.0',
    'creator_url': "odin.rss.chalmers.se",
    'creator_name': 'Kristell Perot',
    'creator_email': 'kristell.perot@chalmers.se',
    'address': "412 96 Gothenburg, Sweden",
    'project_name': "ESA MesosphEO",
    'string_date_format': "YYYYMMDDThhmmssZ",
    'geospatial_vertical_max': "{} hPa".format(PRESSURE_GRID_CCI[-1]),
    'geospatial_vertical_min': "{} hPa".format(PRESSURE_GRID_CCI[0]),
    'value_for_nodata': "NaN",
}


DATA_SELECTION = (
    "No filtering has been applied before averaging the data, "
    "in order to avoid introducing any bias. "
    "All latitude-time cells characterised by a mean measurement "
    "response lower than 0.75 are not reliable and should not "
    "be considered."
)


class SmrL3File(object):
    '''class derived to generate Odin/SMR level3 netcdf files'''
    def __init__(self, project, product, l3_data):
        self.project = project
        self.product = product
        self.dataset = Dataset(self.l3_filename(), 'w', format='NETCDF4')
        self.l3_data = l3_data

    def l3_filename(self):
        return os.path.join(
            LEVEL3_PROJECT_DATADIR,
            'OdinSMR-L3-{}-{}.nc'.format(self.project, self.product))

    def create_dimensions(self):
        self.dataset.createDimension(
            'time', self.l3_data['time'].shape[0])
        self.dataset.createDimension(
            'level', PRESSURE_GRID_CCI.shape[0])
        self.dataset.createDimension(
            'latitude', LATITUDE_GRID.shape[0])
        self.dataset.createDimension(
            'quartile', QUARTILE.shape[0])

    def _create_group_variables(self, group, variables):
        dataset_group = self.dataset.createGroup(group)
        for variable in variables:
            var = dataset_group.createVariable(
                variable['name'], variable['type'], variable['dimension'])
            var.units = variable['unit']
            var[:] = variable['data']

    def create_grids_group(self):
        group_variables = [
            {
                'name': 'time',
                'unit': 'days since 1900-01-01 00:00:00.0',
                'dimension': ('time'),
                'type': 'f8',
                'data': self.l3_data['time'],
            },
            {
                'name': 'pressure',
                'unit': 'hPa',
                'dimension': ('level'),
                'type': 'f4',
                'data': PRESSURE_GRID_CCI,
            },
            {
                'name': 'latitude',
                'unit': 'degrees north',
                'dimension': ('latitude'),
                'type': 'f4',
                'data': LATITUDE_GRID,
            },
            {
                'name': 'quartile',
                'unit': '-',
                'dimension': ('quartile'),
                'type': 'f4',
                'data': QUARTILE,
            },
        ]
        self._create_group_variables('Grids', group_variables)

    def create_gridding_results_group(self):
        if 'Temperature' in self.product:
            l3_data_name = 'temperature'
            l3_data_unit = 'K'
        else:
            l3_data_name = 'concentration'
            l3_data_unit = 'VMR'
        group_variables = [
            {
                'name': l3_data_name,
                'unit': l3_data_unit,
                'dimension': ('time', 'level', 'latitude'),
                'type': 'f4',
                'data': self.l3_data['l2_median'],
            },
            {
                'name': '{}_error'.format(l3_data_name),
                'unit': l3_data_unit,
                'dimension': ('time', 'level', 'latitude'),
                'type': 'f4',
                'data': self.l3_data['l2_error'],
            },
            {
                'name': 'standard_deviation',
                'unit': l3_data_unit,
                'dimension': ('time', 'level', 'latitude'),
                'type': 'f4',
                'data': self.l3_data['standard_deviation'],
            },
            {
                'name': 'quartiles',
                'unit': l3_data_unit,
                'dimension': ('time', 'level', 'latitude', 'quartile'),
                'type': 'f4',
                'data': self.l3_data['quartiles'],
            },
            {
                'name': 'number_of_measurements',
                'unit': '-',
                'dimension': ('time', 'latitude'),
                'type': 'f4',
                'data': self.l3_data['number_of_measurements'],
            },
            {
                'name': 'mean_measurement_response',
                'unit': '-',
                'dimension': ('time', 'level', 'latitude'),
                'type': 'f4',
                'data': self.l3_data['mean_measurement_response'],
            },
        ]
        self._create_group_variables('Gridding_results', group_variables)

    def create_statistical_method_group(self):
        group = 'Statistical_methods'
        group_variables = [
            {
                'name': 'average_latitude',
                'unit': 'degrees north',
                'dimension': ('time', 'latitude'),
                'type': 'f4',
                'data': self.l3_data['average_latitude'],
            },
            {
                'name': 'average_time',
                'unit': 'days since 1900-01-01 00:00:00.0',
                'dimension': ('time', 'latitude'),
                'type': 'f8',
                'data': self.l3_data['average_time']
            },
        ]
        self._create_group_variables(
            group, group_variables)
        self.dataset[group].estimating_method = "median"
        self.dataset[group].interpolation_method = (
            "linear interpolation in log of pressure")

    def create_data_selection_group(self):
        dataset_group = self.dataset.createGroup('Data_selection')
        dataset_group.data_selection = DATA_SELECTION

    def write_global_netcdf_attributes(self):
        self.dataset.title = FILE_ATTRIBUTES['title'].format(
            self.project, self.product)
        self.dataset.project_name = FILE_ATTRIBUTES['project_name']
        self.dataset.institution = FILE_ATTRIBUTES['institution']
        self.dataset.platform = FILE_ATTRIBUTES['platform']
        self.dataset.sensor = FILE_ATTRIBUTES['sensor']
        self.dataset.affiliation = FILE_ATTRIBUTES['affiliation']
        self.dataset.source = FILE_ATTRIBUTES['source']
        self.dataset.date_created = (
            'Created ' + DT.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        )
        self.dataset.source = FILE_ATTRIBUTES['source']
        self.dataset.level_1_data_version = FILE_ATTRIBUTES[
            'level_1_data_version']
        self.dataset.level_2_data_version = FILE_ATTRIBUTES[
            'level_2_data_version']
        self.dataset.level_3_data_version = FILE_ATTRIBUTES[
            'level_3_data_version']
        self.dataset.file_id = self.l3_filename()
        self.dataset.level_3_data_product = self.product
        self.dataset.creator_url = FILE_ATTRIBUTES['creator_url']
        self.dataset.creator_name = FILE_ATTRIBUTES['creator_name']
        self.dataset.creator_email = FILE_ATTRIBUTES['creator_email']
        self.dataset.address = FILE_ATTRIBUTES['address']
        self.dataset.string_date_format = FILE_ATTRIBUTES[
            'string_date_format']
        self.dataset.geospatial_vertical_max = FILE_ATTRIBUTES[
            'geospatial_vertical_max']
        self.dataset.geospatial_vertical_min = FILE_ATTRIBUTES[
            'geospatial_vertical_min']
        self.dataset.time_coverage_start = get_datetime_from_l3_time(
            self.l3_data['time'][0])
        self.dataset.time_coverage_end = get_datetime_from_l3_time(
            self.l3_data['time'][-1])
        self.dataset.number_of_months_covered = self.l3_data['time'].shape[0]
        self.dataset.value_for_nodata = FILE_ATTRIBUTES['value_for_nodata']


def get_datetime_from_l3_time(days):
    date = DT.datetime(1900, 1, 1) + DT.timedelta(days=days)
    return date.strftime("%Y%m%dT%H%M%SZ")


def read_odin_l2_file(dataset):
    l2_data = {
        'time': np.array(dataset['Geolocation']['time'][:]),
        'latitude': np.array(dataset['Geolocation']['latitude']),
        'l2_value': np.array(dataset['Retrieval_results']['l2_value']),
        'measurement_response': np.array(
            dataset['Specific_data_for_selection']['measurement_response'])
    }
    return l2_data


def get_length_of_dimensions(list_of_l2_data):
    return {
        'time': len(list_of_l2_data),
        'level': PRESSURE_GRID_CCI.shape[0],
        'latitude': LATITUDE_GRID.shape[0],
        'quartile': 3,
    }


def get_empty_l2_data_dict(list_of_l2_data):
    length_of_dimensions = get_length_of_dimensions(
        list_of_l2_data)
    shape_2d = (
        length_of_dimensions['time'],
        length_of_dimensions['latitude'],
    )
    shape_3d = (
        length_of_dimensions['time'],
        length_of_dimensions['level'],
        length_of_dimensions['latitude'],
    )
    shape_4d = (
        length_of_dimensions['time'],
        length_of_dimensions['level'],
        length_of_dimensions['latitude'],
        length_of_dimensions['quartile'],
    )
    return {
        'time': np.full(len(list_of_l2_data), np.nan),
        'l2_median': np.full(shape_3d, np.nan),
        'l2_error': np.full(shape_3d, np.nan),
        'standard_deviation': np.full(shape_3d, np.nan),
        'mean_measurement_response': np.full(shape_3d, np.nan),
        'number_of_measurements': np.full(shape_2d, np.nan),
        'quartiles': np.full(shape_4d, np.nan),
        'average_latitude': np.full(shape_2d, np.nan),
        'average_time': np.full(shape_2d, np.nan),
    }


def get_zonal_average_of_l2_data(list_of_l2_data):
    zonal_average_data = get_empty_l2_data_dict(list_of_l2_data)
    dlat = (LATITUDE_GRID[1] - LATITUDE_GRID[0]) / 2.0
    for time_ind, l2_data in enumerate(list_of_l2_data):
        zonal_average_data['time'][
            time_ind] = get_representative_time_of_data(l2_data['time'])
        for lat_ind, latitude in enumerate(LATITUDE_GRID):
            ind = np.nonzero(
                np.abs(l2_data['latitude'] - latitude) < dlat)[0]
            if ind.shape[0] == 0:
                # no data for current latitude bin
                continue
            zonal_average_data['l2_median'][
                time_ind, :, lat_ind] = get_l2_median(
                    l2_data['l2_value'][ind, :])
            zonal_average_data['l2_error'][
                time_ind, :, lat_ind] = get_l2_error(
                    l2_data['l2_value'][ind, :])
            zonal_average_data['standard_deviation'][
                time_ind, :, lat_ind] = get_l2_std(
                    l2_data['l2_value'][ind, :])
            zonal_average_data['mean_measurement_response'][
                time_ind, :, lat_ind] = get_mean_measurement_response(
                    l2_data['measurement_response'][ind, :])
            zonal_average_data['number_of_measurements'][
                time_ind, lat_ind] = get_number_of_measurements(
                    l2_data['l2_value'][ind, :])
            zonal_average_data['quartiles'][
                time_ind, :, lat_ind, :] = get_quartiles(
                    l2_data['l2_value'][ind, :])
            zonal_average_data['average_latitude'][
                time_ind, lat_ind] = get_average_latitude(
                    l2_data['latitude'][ind])
            zonal_average_data['average_time'][
                time_ind, lat_ind] = get_average_time(l2_data['time'][ind])
    return zonal_average_data


def get_representative_time_of_data(l2_time):
    '''get time since 1900-01-01 for day 15 in current month'''
    date_1900_01_01 = DT.datetime(1900, 1, 1)
    date_for_first_measurement = (
        date_1900_01_01 + DT.timedelta(days=l2_time[0]))
    representative_time = DT.datetime(
        date_for_first_measurement.year, date_for_first_measurement.month, 15)
    time_since_1900_01_01 = representative_time - date_1900_01_01
    return time_since_1900_01_01.days


def get_l2_median(l2_value):
    return np.median(l2_value, 0)


def get_l2_error(l2_value):
    return np.std(l2_value, 0) / np.sqrt(l2_value.shape[0])


def get_l2_std(l2_value):
    return np.std(l2_value, 0)


def get_mean_measurement_response(measurement_response):
    return np.mean(measurement_response, 0)


def get_number_of_measurements(l2_value):
    return l2_value.shape[0]


def get_quartiles(l2_value):
    return np.array(
        np.percentile(l2_value, list(QUARTILE), axis=0)
    ).transpose()


def get_average_latitude(latitude):
    return np.mean(latitude)


def get_average_time(time):
    return np.mean(time)


def generate_l3_file(project, product, data_folder):
    l2_files = [
        l2_file for l2_file in os.listdir(data_folder)
        if product in l2_file and 'grid' in l2_file]
    l2_files.sort()
    list_of_l2_data = []
    for l2_file in l2_files:
        odin_l2_file = os.path.join(data_folder, l2_file)
        list_of_l2_data.append(
            read_odin_l2_file(
                Dataset(odin_l2_file, 'r', format='NETCDF4')))
    average_of_l2_data = get_zonal_average_of_l2_data(
        list_of_l2_data)
    smrl3file = SmrL3File(project, product, average_of_l2_data)
    smrl3file.create_dimensions()
    smrl3file.create_grids_group()
    smrl3file.create_gridding_results_group()
    smrl3file.create_statistical_method_group()
    smrl3file.create_data_selection_group()
    smrl3file.write_global_netcdf_attributes()


def setup_arguments():
    """setup command line arguments"""
    parser = ArgumentParser(description="Create odin/smr level3 file")
    parser.add_argument("-r", "--project", dest="project",
                        action="store",
                        default='Meso14All',
                        help="level2 processing project "
                        "(default: Meso14All)")
    parser.add_argument("-p", "--product", dest="product",
                        action="store",
                        default='CO-576-GHz',
                        help="level2 product of project "
                        "(default: CO-576-GHz)")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    ARGS = setup_arguments()
    LEVEL2_DATADIR = '/data/odin-l2-data'
    LEVEL3_DATADIR = '/data/odin-l3-data'
    LEVEL2_PROJECT_DATADIR = os.path.join(LEVEL2_DATADIR, ARGS.project)
    LEVEL3_PROJECT_DATADIR = os.path.join(LEVEL3_DATADIR, ARGS.project)
    generate_l3_file(ARGS.project, ARGS.product, LEVEL2_PROJECT_DATADIR)
