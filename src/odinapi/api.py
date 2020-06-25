"""A simple datamodel implementation"""
import  math

from flask import Flask, Blueprint
from flask.json import JSONEncoder
import numpy as np

from odinapi.utils.swagger import SwaggerSpecView, SWAGGER
from odinapi.views.views import (
    DateInfo, DateBackendInfo, ScanSpec, FreqmodeInfo,
    ScanPTZ, ScanAPR, VdsInfo, VdsFreqmodeInfo, VdsScanInfo,
    VdsInstrumentInfo, VdsDateInfo, VdsExtData, ConfigDataFiles,
    ScanPTZNoBackend, ScanAPRNoBackend, ScanSpecNoBackend,
    FreqmodeInfoNoBackend, ScanInfoNoBackend, CollocationsView)
from odinapi.views.views_cached import (
    DateInfoCached, DateBackendInfoCached, FreqmodeInfoCached,
    PeriodInfoCached, L1LogCached, L1LogCached_v4, L1LogCachedList,
    FreqmodeInfoCachedNoBackend, ScanInfoCachedNoBackend)
from odinapi.views.level2 import (
    Level2Write, Level2ViewScan, Level2ViewLocations, Level2ViewDay,
    Level2ViewArea, Level2ViewProducts, Level2ViewProjects, Level2ViewProject,
    Level2ViewScans, Level2ViewFailedScans, Level2ViewComments, L2iView,
    L2cView, L2View, L2ancView, Level2ViewProductsFreqmode,
    Level2ProjectPublish, Level2ProjectAnnotations)
from odinapi.views.statistics import (
    FreqmodeStatistics, TimelineFreqmodeStatistics)
from odinapi.views.smr_site import (
    ViewIndex, ViewScanSpec, ViewLevel1, ViewLevel2, ViewLevel2Scan,
    ViewLevel2PeriodOverview, ViewLevel1Stats, ViewFreqmodeInfoPlot,
    ViewLevel2DevScan, ViewDataAccess)
from odinapi.views.data_info import FileInfo, LatestECMF

SWAGGER.add_parameter('freqmode', 'path', int)
SWAGGER.add_parameter('scanno', 'path', int)

DESCRIPTION = (
    "Odin rest api.\n\n"
    "Geographic coordinate system:\n\n"
    "* Latitude: -90 to 90\n"
    "* Longitude: 0 to 360")


class Odin(Flask):
    """The main app running the odin site"""
    def __init__(self, name):
        super(Odin, self).__init__(name)

        self.add_url_rule(
            '/rest_api/<version>/config_data/data_files/',
            view_func=ConfigDataFiles.as_view('configdatafiles')
        )
        self.add_url_rule(
            '/rest_api/<version>/config_data/latest_ecmf_file/',
            view_func=LatestECMF.as_view('latestecmf')
        )

        self.add_url_rule(
            '/rest_api/<version>/spec',
            view_func=SwaggerSpecView.as_view(
                'swagger', 'Odin API', description=DESCRIPTION)
        )

        self._add_level1_views()
        self._add_level2_views()
        self._add_level2_development_views()
        self._add_vds_views()
        self._add_site_views()
        self._add_stats_views()

    def _add_level1_views(self):
        self._add_level1_cached()
        self._add_level1_raw()
        self._add_level1_scan()

        self._add_level1_no_backend_views()

        self.add_url_rule(
            '/rest_api/<version>/file_info/',
            view_func=FileInfo.as_view('file_info')
        )

    def _add_level1_no_backend_views(self):
        self._add_level1_no_backend_cached()
        self._add_level1_no_backend_raw()
        self._add_level1_no_backend_scan()

    def _add_level1_no_backend_scan(self):
        self.add_url_rule(
            '/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/Log/',
            view_func=L1LogCached.as_view('scanlogv5')
        )
        self.add_url_rule(
            '/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/L1b/',
            view_func=ScanSpecNoBackend.as_view('l1bv5')
        )
        self.add_url_rule(
            '/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/ptz/',
            view_func=ScanPTZNoBackend.as_view('ptznobackend')
        )
        self.add_url_rule(
            '/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/'
            'apriori/<species>/',
            view_func=ScanAPRNoBackend.as_view('apriorinobackend')
        )
        self.add_url_rule(
            ('/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/'
             'collocations/'),
            view_func=CollocationsView.as_view('collocations')
        )
        self.add_url_rule(
            ('/rest_api/<version>/level1/<int:freqmode>/scans/'),
            view_func=L1LogCachedList.as_view('scanslist')
        )

    def _add_level1_no_backend_cached(self):
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/<int:freqmode>/',
            view_func=FreqmodeInfoCachedNoBackend.as_view('scansinfonobackend')
        )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/<int:freqmode>/<int:scanno>/',  # noqa
            view_func=ScanInfoCachedNoBackend.as_view('scaninfonobackend')
        )

    def _add_level1_no_backend_raw(self):
        self.add_url_rule(
            '/rest_api/<version>/freqmode_raw/<date>/<int:freqmode>/',
            view_func=FreqmodeInfoNoBackend.as_view(
                'scansinforawnobackend')
        )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_raw/<date>/'
            '<int:freqmode>/<int:scanno>/',
            view_func=ScanInfoNoBackend.as_view(
                'scaninforawnobackend')
        )

    def _add_level1_cached(self):
        self.add_url_rule(
            '/rest_api/<version>/period_info/<int:year>/<int:month>/'
            '<int:day>/',
            view_func=PeriodInfoCached.as_view('periodinfo')
        )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/',
            view_func=DateInfoCached.as_view('freqmodeinfo')
        )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/<backend>/',
            view_func=DateBackendInfoCached.as_view('backendinfo')
        )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/<backend>/'
            '<int:freqmode>/',
            view_func=FreqmodeInfoCached.as_view('scansinfo')
        )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/<backend>/'
            '<int:freqmode>/<int:scanno>/',
            view_func=FreqmodeInfoCached.as_view('scaninfo')
        )

    def _add_level1_raw(self):
        self.add_url_rule(
            '/rest_api/<version>/freqmode_raw/<date>/',
            view_func=DateInfo.as_view('freqmoderaw')
        )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_raw/<date>/<backend>/',
            view_func=DateBackendInfo.as_view('backendraw')
        )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_raw/<date>/<backend>/'
            '<int:freqmode>/',
            view_func=FreqmodeInfo.as_view('scansraw')
        )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_raw/<date>/<backend>/'
            '<int:freqmode>/<int:scanno>/',
            view_func=FreqmodeInfo.as_view('scanraw')
        )

    def _add_level1_scan(self):
        self.add_url_rule(
            '/rest_api/<version>/l1_log/<int:freqmode>/<int:scanno>/',
            view_func=L1LogCached_v4.as_view('scanlog')
        )
        self.add_url_rule(
            '/rest_api/<version>/scan/<backend>/<int:freqmode>/<int:scanno>/',
            view_func=ScanSpec.as_view('scan')
        )
        self.add_url_rule(
            '/rest_api/<version>/ptz/<date>/<backend>/<int:freqmode>/'
            '<int:scanno>/',
            view_func=ScanPTZ.as_view('ptz')
        )
        self.add_url_rule(
            '/rest_api/<version>/apriori/<species>/<date>/<backend>/'
            '<int:freqmode>/<int:scanno>/',
            view_func=ScanAPR.as_view('apriori')
        )

    def _add_level2_views(self):
        # TODO: These urls should later only show data from official projects
        self.add_url_rule(
            '/rest_api/<version>/level2',
            view_func=Level2Write.as_view('level2write')
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/projects/',
            view_func=Level2ViewProjects.as_view('level2viewprojects')
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/<project>/',
            view_func=Level2ViewProject.as_view('level2viewproject')
        )
        self.add_url_rule(
            '/rest_api/v5/level2/<project>/annotations',
            view_func=Level2ProjectAnnotations.as_view('level2annotations')
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/<project>/<int:freqmode>/comments/',
            view_func=Level2ViewComments.as_view('level2viewcomments')
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/<project>/<int:freqmode>/scans/',
            view_func=Level2ViewScans.as_view('level2viewscans')
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/<project>/<int:freqmode>/failed/',
            view_func=Level2ViewFailedScans.as_view('level2viewfailed')
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/<project>'
             '/<int:freqmode>/<int:scanno>/'),
            view_func=Level2ViewScan.as_view('level2viewscan')
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/<project>'
             '/<int:freqmode>/<int:scanno>/L2i/'),
            view_func=L2iView.as_view('level2L2i')
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/<project>'
             '/<int:freqmode>/<int:scanno>/L2c/'),
            view_func=L2cView.as_view('level2L2c')
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/<project>'
             '/<int:freqmode>/<int:scanno>/L2anc/'),
            view_func=L2ancView.as_view('level2L2anc')
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/<project>'
             '/<int:freqmode>/<int:scanno>/L2/'),
            view_func=L2View.as_view('level2L2')
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/<project>/products/',
            view_func=Level2ViewProducts.as_view('level2viewproducts')
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/<project>'
             '/<int:freqmode>/products/'),
            view_func=Level2ViewProductsFreqmode.as_view(
                'level2viewfmproducts')
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/<project>/locations',
            view_func=Level2ViewLocations.as_view('level2viewlocations')
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/<project>/<date>/',
            view_func=Level2ViewDay.as_view('level2viewday')
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/<project>/area',
            view_func=Level2ViewArea.as_view('level2viewarea')
        )

    def _add_level2_development_views(self):
        """Add views for browsing development projects"""
        self.add_url_rule(
            '/rest_api/<version>/level2/development/projects/',
            view_func=Level2ViewProjects.as_view(
                'level2devviewprojects', development=True)
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/development/<project>/',
            view_func=Level2ViewProject.as_view(
                'level2devviewproject', development=True)
        )
        self.add_url_rule(
            '/rest_api/v5/level2/development/<project>/publish',
            view_func=Level2ProjectPublish.as_view('level2publishproject')
        )
        self.add_url_rule(
            '/rest_api/v5/level2/development/<project>/annotations',
            view_func=Level2ProjectAnnotations.as_view('level2devannotations')
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/development/<project>/<int:freqmode>/'
            'comments/',
            view_func=Level2ViewComments.as_view(
                'level2devviewcomments', development=True)
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/development/<project>/<int:freqmode>/'
            'scans/',
            view_func=Level2ViewScans.as_view(
                'level2devviewscans', development=True)
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/development/<project>/<int:freqmode>/'
            'failed/',
            view_func=Level2ViewFailedScans.as_view(
                'level2devviewfailed', development=True)
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/development/<project>'
             '/<int:freqmode>/<int:scanno>/'),
            view_func=Level2ViewScan.as_view(
                'level2devviewscan', development=True)
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/development/<project>/products/',
            view_func=Level2ViewProducts.as_view(
                'level2devviewproducts', development=True)
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/development/<project>/<int:freqmode>/'
            'products/',
            view_func=Level2ViewProductsFreqmode.as_view(
                'level2devviewfmproducts', development=True)
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/development/<project>'
             '/<int:freqmode>/<int:scanno>/L2i/'),
            view_func=L2iView.as_view('level2devL2i', development=True)
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/development/<project>'
             '/<int:freqmode>/<int:scanno>/L2c/'),
            view_func=L2cView.as_view('level2devL2c', development=True)
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/development/<project>'
             '/<int:freqmode>/<int:scanno>/L2anc/'),
            view_func=L2ancView.as_view('level2devL2anc', development=True)
        )
        self.add_url_rule(
            ('/rest_api/<version>/level2/development/<project>'
             '/<int:freqmode>/<int:scanno>/L2/'),
            view_func=L2View.as_view('level2devL2', development=True)
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/development/<project>/locations',
            view_func=Level2ViewLocations.as_view(
                'level2devviewlocations', development=True)
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/development/<project>/<date>/',
            view_func=Level2ViewDay.as_view(
                'level2devviewday', development=True)
        )
        self.add_url_rule(
            '/rest_api/<version>/level2/development/<project>/area',
            view_func=Level2ViewArea.as_view(
                'level2devviewarea', development=True)
        )

    def _add_site_views(self):
        self.add_url_rule(
            '/',
            view_func=ViewIndex.as_view('index')
        )
        self.add_url_rule(
            '/level1',
            view_func=ViewLevel1.as_view('level1')
        )
        self.add_url_rule(
            '/level1statistics',
            view_func=ViewLevel1Stats.as_view('level1statistics')
        )
        self.add_url_rule(
            '/level2',
            view_func=ViewLevel2.as_view('level2')
        )
        self.add_url_rule(
            '/level2/<project>/<int:freqmode>/<int:scanno>/',
            view_func=ViewLevel2Scan.as_view('viewlevel2can')
        )
        self.add_url_rule(
            '/level2/<title>/<project>/<int:freqmode>/<int:scanno>/',
            view_func=ViewLevel2DevScan.as_view('viewlevel2devcan')
        )
        self.add_url_rule(
            '/level2/overview/<project>/',
            view_func=ViewLevel2PeriodOverview.as_view('level2periodoverview')
        )
        self.add_url_rule(
            '/browse/<int:freqmode>/<int:scanno>/',
            view_func=ViewScanSpec.as_view('viewscan')
        )
        self.add_url_rule(
            '/plot/<date>/<int:freqmode>',
            view_func=ViewFreqmodeInfoPlot.as_view('plotscans')
        )
        self.add_url_rule(
            '/dataaccess',
            view_func=ViewDataAccess.as_view('dataaccess')
        )

    def _add_stats_views(self):
        self.add_url_rule(
            '/rest_api/<version>/statistics/freqmode/',
            view_func=FreqmodeStatistics.as_view('freqmodestatistics')
        )
        self.add_url_rule(
            '/rest_api/<version>/statistics/freqmode/timeline/',
            view_func=TimelineFreqmodeStatistics.as_view('timefmstatistics')
        )

    def _add_vds_views(self):
        self.add_url_rule(
            '/rest_api/<version>/vds/',
            view_func=VdsInfo.as_view('vdsinfo')
        )
        self.add_url_rule(
            '/rest_api/<version>/vds/<backend>/<freqmode>/',
            view_func=VdsFreqmodeInfo.as_view('vdsfreqmodeinfo')
        )
        self.add_url_rule(
            '/rest_api/<version>/vds/<backend>/<freqmode>/allscans',
            view_func=VdsScanInfo.as_view('vdsScaninfo')
        )
        self.add_url_rule(
            '/rest_api/<version>/vds/<backend>/<freqmode>/<species>'
            '/<instrument>/',
            view_func=VdsInstrumentInfo.as_view('vdsinstrumentinfo')
        )
        self.add_url_rule(
            '/rest_api/<version>/vds/<backend>/<freqmode>/<species>'
            '/<instrument>/<date>/',
            view_func=VdsDateInfo.as_view('vdsdateinfo')
        )
        self.add_url_rule(
            '/rest_api/<version>/vds_external/<instrument>/<species>'
            '/<date>/<file>/<file_index>/',
            view_func=VdsExtData.as_view('vdsextdata')
        )


app = Odin(__name__)

# Swagger ui will be available at /apidocs/index.html
blueprint = Blueprint(
    'swagger', __name__, static_url_path='/apidocs',
    static_folder='/swagger-ui')
app.register_blueprint(blueprint)


class ExtendedEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.int_):
            return int(obj)
        if isinstance(obj, np.float_):
            if not np.isfinite(obj):
                return None
            return float(obj)
        if isinstance(obj, float) and not math.isfinite(obj):
            return None

        return JSONEncoder.default(self, obj)


app.json_encoder = ExtendedEncoder
