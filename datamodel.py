"""A simple datamodel implementation"""

from flask import Flask, request, send_file
from flask import render_template, jsonify, abort
from flask.views import MethodView
from sqlalchemy import create_engine
import numpy
import io
from matplotlib import use
use("Agg")
from matplotlib.pylab import figure
from date_tools import *



# Views ===============================
class ListScans(MethodView):
    """Find all scans"""

    def get(self):
        """ Get the right info"""
        start_time = request.args['start_time']
        end_time = request.args['end_time']
        date1 = datestring_to_date(start_time)
        date2 = datestring_to_date(end_time)
        stw1, stw2 = stw_from_date(date1, date2)
        engine = create_engine(
            'postgresql://odinop:***REMOVED***'
            '@malachite.rss.chalmers.se:5432/odin'
            )
        con = engine.connect()
        query_string = (
            'select distinct(stw) as scan_id '
            'from ac_cal_level1b '
            'where stw between {0} and {1} and freqmode=2;').format(
                stw1, stw2
                )
        result = con.execute(query_string)
        id_list = list()
        for row in result:
            id_list.append(row['scan_id'])
        return str(stw1) + " " + str(stw2) + " " + str(id_list)

class ViewScan(MethodView):
    """View of all scans"""

    def get(self, scanno):
        """get scandata"""
        engine = create_engine(
            'postgresql://odinop:***REMOVED***'
            '@malachite.rss.chalmers.se:5432/odin'
            )
        con = engine.connect()
        query_string = (
            'select channels, spectra, calstw from ac_level1b '
            'where calstw={0} order by stw').format(int(scanno))
        result = con.execute(query_string)

        spectrum = []
        for row in result:
            data = numpy.ndarray(
                shape=(row[0],),
                dtype='float64',
                buffer=row[1]
                )
            spectrum.append(data.tolist())
        #data = numpy.vstack((data, data))
        accept = request.headers['Accept']
        if "application/json" in accept:
            return jsonify(test="ok", other=2, data=spectrum)
        else:
            return render_template('message.html',text='Don''t know what to do.')

class ViewSpectrum(MethodView):
    """View of all scans"""

    def get(self, scanno):
        """get spectrum"""
        engine = create_engine(
            'postgresql://odinop:***REMOVED***'
            '@malachite.rss.chalmers.se:5432/odin'
            )
        con = engine.connect()
        query_string = (
            'select channels, spectra, calstw from ac_level1b '
            'where stw={0}').format(int(scanno))
        result = con.execute(query_string)
        res = result.fetchall()
        if len(res) == 0:
            return abort(404)
        data = numpy.ndarray(
            shape=(res[0][0],),
            dtype='float64',
            buffer=res[0][1]
            )
        data = numpy.vstack((data, data))
        accept = request.headers['Accept']
        if "application/json" in accept:
            return jsonify(test="ok", other=2, data=data.tolist())
        return 'test'

class PlotSpectrum(MethodView):
    """plots information"""
    def get(self, scanno):
        """Serves the plot"""
        stw = int(scanno)
        engine = create_engine(
            'postgresql://odinop:***REMOVED***@malachite.rss.chalmers.se:5432/odin')
        con = engine.connect()
        query_string = (
            'select channels, spectra, backend, skyfreq, lofreq '
            'from ac_level1b where stw={0}').format(stw)
        result = con.execute(query_string)
        res = result.fetchall()
        backend = res[0][2]
        skyfreq = res[0][3]
        lofreq = res[0][4]
        data = numpy.ndarray(
            shape=(res[0][0],), 
            dtype='float64',
            buffer=res[0][1]
            )
        fig = figure()
        ax = fig.add_axes([.1, .1, .8, .8])
#        ax.plot(freqs, data, ".")
        ax.plot(data)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        return send_file(
            buf, attachment_filename='plot.png', mimetype='image/png')

class ViewIndex(MethodView):
    """View of all scans"""

    def get(self):
        return render_template('index.html')

def freq(lofreq,skyfreq,LO):
    n=896
    f=numpy.zeros(shape=(n,))
    seq=[1,1,1,-1,1,1,1,-1,1,-1,1,1,1,-1,1,1] 
    m=0
    for adc in range(8):
        if seq[2*adc]:
            k = seq[2*adc]*112
            df = 1.0e6/seq[2*adc]
            if seq[2*adc+1] < 0:
                df=-df
            for j in range(k): 
                f[m+j] = LO[adc/2] +j*df;
            m += k;
    fdata = numpy.zeros(shape=(n,))
    if skyfreq >= lofreq:
        for i in range(n):
            v = f[i]
            v = lofreq + v
            v /= 1.0e9
            fdata[i] = v
    else: 
        for i in range(n):
            v = f[i]
            v = lofreq - v
            v /= 1.0e9
            fdata[i]=v
    return fdata

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
            '/index.html',
            view_func=ViewIndex.as_view('index')
            )
def main():
    """Default function"""
    app = DataModel(__name__)
    app.run(host='0.0.0.0', debug=True)

if __name__ == "__main__":
    main()

