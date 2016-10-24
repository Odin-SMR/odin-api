# pylint: skip-file
"""A simple datamodel implementation"""
import json
from os import environ

from flask import Flask, jsonify
from flasgger import Swagger, BR_SANITIZER
from flasgger.base import OutputView
import flasgger

from odinapi.views.views import (
    DateInfo, DateBackendInfo, ScanSpec, FreqmodeInfo,
    ScanPTZ, ScanAPR, VdsInfo, VdsFreqmodeInfo, VdsScanInfo,
    VdsInstrumentInfo, VdsDateInfo, VdsExtData)
from odinapi.views.level2 import (
    Level2Write, Level2ViewScan, Level2ViewLocations, Level2ViewDay,
    Level2ViewArea, Level2ViewProducts, Level2ViewProjects, Level2ViewProject,
    Level2ViewScans, Level2ViewComments,
    SWAGGER_DEFINITIONS as level2_definitions,
    SWAGGER_RESPONSES as level2_responses, SWAGGER_PARAMETERS as level2_param)
from odinapi.views.views_cached import (
    DateInfoCached, DateBackendInfoCached, FreqmodeInfoCached,
    PeriodInfoCached, L1LogCached)
from odinapi.views.statistics import (
    FreqmodeStatistics, TimelineFreqmodeStatistics)
from odinapi.views.smr_site import (
    ViewIndex, ViewScanSpec, ViewLevel1, ViewLevel2, ViewLevel2Scan,
    ViewLevel1Stats, ViewFreqmodeInfoPlot)
from odinapi.views.data_info import FileInfo


class Odin(Flask):
    """The main app running the odin site"""
    def __init__(self, name):
        super(Odin, self).__init__(name)
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
        self.add_url_rule(
            '/rest_api/<version>/l1_log/<int:freqmode>/<int:scanno>/',
            view_func=L1LogCached.as_view('scanlog')
            )
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
        self.add_url_rule(
            '/rest_api/<version>/scan/<backend>/<int:freqmode>/<int:scanno>/',
            view_func=ScanSpec.as_view('scan')
            )
        self.add_url_rule(
            '/rest_api/<version>/file_info/',
            view_func=FileInfo.as_view('file_info')
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
            '/rest_api/<version>/level2/<project>/<int:freqmode>/comments/',
            view_func=Level2ViewComments.as_view('level2viewcomments')
            )
        self.add_url_rule(
            '/rest_api/<version>/level2/<project>/<int:freqmode>/scans/',
            view_func=Level2ViewScans.as_view('level2viewscans')
            )
        self.add_url_rule(
            ('/rest_api/<version>/level2/<project>'
             '/<int:freqmode>/<int:scanno>/'),
            view_func=Level2ViewScan.as_view('level2viewscan')
            )
        self.add_url_rule(
            '/rest_api/<version>/level2/<project>/products/',
            view_func=Level2ViewProducts.as_view('level2viewproducts')
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
            '/level2/<project>/<freqmode>/<scanno>/',
            view_func=ViewLevel2Scan.as_view('viewlevel2can')
        )
        self.add_url_rule(
            '/browse/<backend>/<int:freqmode>/<int:scanno>/',
            view_func=ViewScanSpec.as_view('viewscan')
            )
        self.add_url_rule(
            '/plot/<date>/<backend>/<int:freqmode>',
            view_func=ViewFreqmodeInfoPlot.as_view('plotscans')
            )
        self.add_url_rule(
            '/rest_api/<version>/statistics/freqmode/',
            view_func=FreqmodeStatistics.as_view('freqmodestatistics')
            )
        self.add_url_rule(
            '/rest_api/<version>/statistics/freqmode/timeline/',
            view_func=TimelineFreqmodeStatistics.as_view('timefmstatistics')
            )
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

DESCRIPTION = """Odin level1 and level2 rest api.

Geographic coordinate system:

* Latitude: -90 to 90
* Longitude: 0 to 360
"""

OrigOutputView = OutputView


class MySwaggerOutput(OrigOutputView):
    """Extended swagger specification view that makes it possible to add
    definitions, responses and parameters to the spec.
    """

    def __init__(self, *args, **kwargs):
        view_args = kwargs.pop('view_args', {})
        self.config = view_args.get('config')
        self.spec = view_args.get('spec')
        self.process_doc = view_args.get('sanitizer', BR_SANITIZER)
        self.template = view_args.get('template')
        super(OrigOutputView, self).__init__(*args, **kwargs)

    def get(self):
        resp = super(MySwaggerOutput, self).get()
        data = json.loads(resp.get_data())
        data['definitions'].update(level2_definitions)
        data['responses'] = level2_responses
        data['parameters'] = level2_param
        return jsonify(data)

flasgger.base.OutputView = MySwaggerOutput


def main():
    """Default function"""
    app = Odin(__name__)
    app.config['SWAGGER'] = {
        "swagger_version": "2.0",
        "specs": [
            {
                "version": "4.0",
                "title": "Odin API",
                "description": DESCRIPTION,
                "endpoint": 'v4_spec',
                "route": '/rest_api/v4/spec',
            }
        ]
    }
    # Swagger ui will be available at /apidocs/index.html
    Swagger(app)

    app.run(
        host='0.0.0.0',
        debug='ODIN_API_PRODUCTION' not in environ,
        threaded=True
        )

if __name__ == "__main__":
    main()
