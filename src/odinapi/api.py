"""A simple datamodel implementation"""

from flask import Flask
from odinapi.views.views import DateInfo, DateBackendInfo
from odinapi.views.views import ScanSpec, FreqmodeInfo
from odinapi.views.smr_site import ViewIndex, ViewScanSpec, ViewLevel1
from odinapi.views.smr_site import ViewFreqmodeInfoPlot
from odinapi.views.data_info import FileInfo
from odinapi.views.views import ScanPTZ, ScanAPR
from os import environ

class Odin(Flask):
    """The main app running the odin site"""
    def __init__(self, name):
        super(Odin, self).__init__(name)
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/',
            view_func=DateInfo.as_view('freqmodeinfo')
            )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/<backend>/',
            view_func=DateBackendInfo.as_view('backendinfo')
            )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/<backend>/<freqmode>/',
            view_func=FreqmodeInfo.as_view('scaninfo')
            )
        self.add_url_rule(
            '/rest_api/<version>/scan/<backend>/<freqmode>/<scanno>/',
            view_func=ScanSpec.as_view('scan')
            )
        self.add_url_rule(
            '/rest_api/<version>/file_info/',
            view_func=FileInfo.as_view('file_info')
            )
        self.add_url_rule(
            '/rest_api/<version>/ptz/<date>/<backend>/<freqmode>/<scanno>/',
            view_func=ScanPTZ.as_view('ptz')
            )
        self.add_url_rule(
            '/rest_api/<version>/apriori/<species>/<date>/<backend>/<freqmode>/<scanno>/',
            view_func=ScanAPR.as_view('apriori')
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
            '/level2',
            view_func=ViewLevel1.as_view('level2')
            )
        self.add_url_rule(
            '/browse/<backend>/<freqmode>/<scanno>/',
            view_func=ViewScanSpec.as_view('viewscan')
            )
        self.add_url_rule(
            '/plot/<date>/<backend>/<freqmode>',
            view_func=ViewFreqmodeInfoPlot.as_view('plotscans')
            )
def main():
    """Default function"""
    app = Odin(__name__)
    app.run(
        host='0.0.0.0',
        debug=not environ.has_key('ODIN_API_PRODUCTION'),
        threaded=True
        )

if __name__ == "__main__":
    main()
