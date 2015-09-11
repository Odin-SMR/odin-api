"""A simple datamodel implementation"""

from flask import Flask
from views.views import ListScans, ViewSpectrum, PlotSpectrum, ViewScan, ViewScaninfo, ViewScaninfoplot, ViewScandata, ViewDateInfo, ViewDateBackendInfo, ViewFreqmodeInfoPlot, ViewScanSpec, ViewFreqmodeInfoPlot, ViewFreqmodeInfo, ViewIndex

class DataModel(Flask):
    def __init__(self, name):
        super(DataModel, self).__init__(name)
        self.add_url_rule(
            '/FM/scans',
            view_func=ListScans.as_view('listscans')
            )
        self.add_url_rule(
            '/spectrum/<scanno>',
            view_func=ViewSpectrum.as_view('viewspectrum')
            )
        self.add_url_rule(
            '/spectrum/<scanno>/plot.png',
            view_func=PlotSpectrum.as_view('plotspectrum')
            )
        self.add_url_rule(
            '/scan/<scanno>',
            view_func=ViewScan.as_view('viewscan')
            )
        self.add_url_rule(
            '/viewscaninfo/<backend>/<date>',
            view_func=ViewScaninfo.as_view('viewscaninfo')
            )
        self.add_url_rule(
            '/viewscaninfo/<backend>/<date>/plot.png',
            view_func=ViewScaninfoplot.as_view('viewscaninfoplot')
            )
        self.add_url_rule(
            '/viewscan/<backend>/<scanno>',
            view_func=ViewScandata.as_view('viewscandata')
            )
        self.add_url_rule(
            '/viewodinscan/<date>/',
            view_func=ViewDateInfo.as_view('viewdateinfo')
            )
        self.add_url_rule(
            '/viewodinscan/<date>/<backend>/',
            view_func=ViewDateBackendInfo.as_view('viewdatebackendinfo')
            )
        self.add_url_rule(
            '/viewodinscan/<date>/<backend>/<freqmode>/',
            view_func=ViewFreqmodeInfo.as_view('viewfreqmodeinfo')
            )
        self.add_url_rule(
            '/viewodinscan/<date>/<backend>/<freqmode>/plot.png',
            view_func=ViewFreqmodeInfoPlot.as_view('viewfreqmodeinfoplot')
            )
        self.add_url_rule(
            '/viewodinscan/<date>/<backend>/<freqmode>/<scanno>/',
            view_func=ViewScanSpec.as_view('viewscanspec')
            )
        self.add_url_rule(
            '/index.html',
            view_func=ViewIndex.as_view('index')
            )
def main():
    """Default function"""
    app = DataModel(__name__)
    app.run(host='0.0.0.0', debug=True)

if __name__ == "__main__":
    main()

