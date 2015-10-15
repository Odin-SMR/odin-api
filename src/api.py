"""A simple datamodel implementation"""

from flask import Flask
from views.views import DateInfo, DateBackendInfo
from views.views import ScanSpec, FreqmodeInfo
from views.smr_site import ViewIndex, ViewScanSpec, ViewLevel1, ViewFreqmodeInfoPlot, ViewLevel2
from views.data_info import FileInfo
from os import environ

class Odin(Flask):
    """The main app running the odin site"""
    def __init__(self, name):
        super(Odin, self).__init__(name)
        self.add_url_rule(
            '/rest_api/v1/freqmode_info/<date>/',
            view_func=DateInfo.as_view('freqmodeinfo')
            )
        self.add_url_rule(
            '/rest_api/v1/freqmode_info/<date>/<backend>/',
            view_func=DateBackendInfo.as_view('backendinfo')
            )
        self.add_url_rule(
            '/rest_api/v1/freqmode_info/<date>/<backend>/<freqmode>/',
            view_func=FreqmodeInfo.as_view('scaninfo')
            )
        self.add_url_rule(
            '/rest_api/v1/scan/<backend>/<freqmode>/<scanno>/',
            view_func=ScanSpec.as_view('scan')
            )
        self.add_url_rule(
            '/rest_api/v1/file_info/',
            view_func=FileInfo.as_view('file_info')
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
    app.run(host='0.0.0.0', debug=not environ.has_key('ODIN_API_PRODUCTION'))

if __name__ == "__main__":
    main()

