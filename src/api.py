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
from level1b_scandata_exporter import *
from level1b_scanlogdata_exporter import *
import numpy as N
from pg import DB
from sys import stderr,stdout,stdin,argv,exit
import matplotlib.pyplot as plt
from datetime import date,datetime,timedelta
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
from matplotlib import dates,rc
from dateutil.relativedelta import relativedelta
from sys import argv
import matplotlib




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

class ViewScaninfo(MethodView):
    """plots information"""
    def get(self, backend,date,):
        con = db()

        loginfo,date1,date2 = get_scan_logdata(con, backend, date)

        lista = []
        for ind in range(len(loginfo['ScanID'])):
            row = []    
            for item in ['DateTime','FreqMode','StartLat','EndLat','SunZD','AltStart','AltEnd','ScanID']:
                row.append(loginfo[item][ind])
            lista.append(row)
        return render_template('plottest.html', date=date, backend=backend,scanno=loginfo['ScanID'][0],lista=lista)

class ViewScaninfoplot(MethodView):
    """plots information"""
    def get(self, backend,date,):

        con = db()

        loginfo,date1,date2 = get_scan_logdata(con, backend, date)

        accept = request.headers['Accept']

        if "application/json" in accept:
            for item in loginfo.keys():
                try:
                    loginfo[item]=loginfo[item].tolist()
                except:
                    pass
            return jsonify(**loginfo)
        else:
            fig = plot_loginfo(backend,date1,date2,loginfo)
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            return send_file(
                buf, attachment_filename='plot.png', mimetype='image/png')


class ViewScandata(MethodView):
    """plots information"""
    def get(self, backend, scanno):
        
        con=db()
    
        #export data
        calstw = int(scanno)
        spectra = get_scan_data(con, backend, scanno)

        #spectra is a dictionary containing the relevant data

        accept = request.headers['Accept']

        if "application/json" in accept:

            datadict = scan2dictlist(spectra)

            return jsonify(**datadict)
            
        else:

            fig=plot_scan(backend,calstw,spectra)
            con.close()
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)

            return send_file(
                    buf, attachment_filename='plot.png', mimetype='image/png')



class Test(MethodView):
    """View of all scans"""
    def get(self, scanno):
        a = range(10)
        return render_template('plottest.html', scanno=int(scanno),lista=a)



def copyemptydict(a):
    b = dict()
    for item in a.keys():
        b[item] = []
    return b


class db(DB):
    def __init__(self):
        #DB.__init__(self,dbname='odin',user='odinop',host='malachite.rss.chalmers.se',passwd='***REMOVED***')
        DB.__init__(self,dbname='odin',user='odinop',host='postgresql',passwd='***REMOVED***')



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
            '/test/<scanno>',
            view_func=Test.as_view('test')
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
            '/index.html',
            view_func=ViewIndex.as_view('index')
            )
def main():
    """Default function"""
    app = DataModel(__name__)
    app.run(host='0.0.0.0', debug=True)

if __name__ == "__main__":
    main()

