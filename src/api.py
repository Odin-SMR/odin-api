"""A simple datamodel implementation"""

from flask import Flask
from views.views import ViewDateInfo, ViewDateBackendInfo
from views.views import ViewFreqmodeInfoPlot, ViewScanSpec
from views.views import ViewFreqmodeInfo, ViewIndex

class Odin(Flask):
    """The main app running the odin site"""
    def __init__(self, name):
        super(Odin, self).__init__(name)
        self.add_url_rule(
            '/viewscan/<date>/',
            view_func=ViewDateInfo.as_view('viewdateinfo')
            )
        self.add_url_rule(
            '/viewscan/<date>/<backend>/',
            view_func=ViewDateBackendInfo.as_view('viewdatebackendinfo')
            )
        self.add_url_rule(
            '/viewscan/<date>/<backend>/<freqmode>/',
            view_func=ViewFreqmodeInfo.as_view('viewfreqmodeinfo')
            )
        self.add_url_rule(
            '/viewscan/<date>/<backend>/<freqmode>/plot.png',
            view_func=ViewFreqmodeInfoPlot.as_view('viewfreqmodeinfoplot')
            )
        self.add_url_rule(
            '/viewscan/<date>/<backend>/<freqmode>/<scanno>/',
            view_func=ViewScanSpec.as_view('viewscanspec')
            )
        self.add_url_rule(
            '/index.html',
            view_func=ViewIndex.as_view('index')
            )
def main():
    """Default function"""
    app = Odin(__name__)
    app.run(host='0.0.0.0', debug=True)

if __name__ == "__main__":
    main()

