"""A simple datamodel implementation"""

from flask import Flask
from views.views import DateInfo, DateBackendInfo
from views.views import ScanSpec
from views.views import FreqmodeInfo
from views.smr_site import ViewIndex, ViewFreqmodeInfoPlot
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
            '/',
            view_func=ViewIndex.as_view('index')
            )
        self.add_url_rule(
            '/browse/<backend>/<freqmode>/<scanno>/',
            view_func=ViewFreqmodeInfoPlot.as_view('viewscan')
            )
def main():
    """Default function"""
    app = Odin(__name__)
    app.run(host='0.0.0.0', debug=not environ.has_key('ODIN_API_PRODUCTION'))

if __name__ == "__main__":
    main()

