""" doc
"""
from flask import send_file, render_template
from flask.views import MethodView
import io
from date_tools import *
from level1b_scandata_exporter_v2 import *
from level1b_scanlogdata_exporter import *
from os import environ
from database import DatabaseConnector


class ViewIndex(MethodView):
    """View of all scans"""

    def get(self):
        return render_template('index.html', data=str('ODIN_API_PRODUCTION' in
                                                      environ))


class ViewLevel1(MethodView):
    """View of all scans"""

    def get(self):
        return render_template('level1.html')


class ViewLevel1Stats(MethodView):
    """View statistics of level1 scans"""

    def get(self):
        return render_template('level1stats.html')


class ViewLevel2(MethodView):
    """View of all scans"""

    def get(self):
        return render_template('level2.html')


class ViewScanSpec(MethodView):
    """plots information: data from a given scan"""
    def get(self, backend, freqmode, scanno):
        con = DatabaseConnector()
        calstw = int(scanno)
        spectra = get_scan_data_v2(con, backend, freqmode, scanno)
        fig = plot_scan(backend, calstw, spectra)
        con.close()
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)

        return send_file(
            buf, attachment_filename='plot.png', mimetype='image/png')


class ViewFreqmodeInfoPlot(MethodView):
    """plots information: loginfo for all scans from a given date and freqmode
    """
    def get(self, date, backend, freqmode):

        con = DatabaseConnector()

        loginfo, date1, date2 = get_scan_logdata(con, backend,
                                                 date+'T00:00:00',
                                                 int(freqmode), 1)

        lista = []
        for ind in range(len(loginfo['ScanID'])):
            row = []
            row.append(loginfo['DateTime'][ind].date())
            for item in ['DateTime', 'FreqMode', 'StartLat', 'EndLat', 'SunZD',
                         'AltStart', 'AltEnd', 'ScanID']:
                row.append(loginfo[item][ind])
            lista.append(row)

        fig = plot_loginfo(backend, date1, date2, loginfo)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        return send_file(buf, attachment_filename='plot.png',
                         mimetype='image/png')
