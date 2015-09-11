""" doc
"""
from flask import request, send_file
from flask import render_template, jsonify
from flask.views import MethodView
import io
from matplotlib import use
use("Agg")
from date_tools import *
from utils import copyemptydict
from level1b_scandata_exporter import *
from level1b_scanlogdata_exporter import *
from pg import DB
from sys import stderr, stdout, stdin, argv, exit
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
from matplotlib import dates, rc
from dateutil.relativedelta import relativedelta
import matplotlib

class ViewIndex(MethodView):
    """View of all scans"""

    def get(self):
        return render_template('index.html')



class ViewDateInfo(MethodView):
    """plots information"""
    def get(self, date):
        con = DatabaseConnector()
        date1 = datetime.strptime(date, '%Y-%m-%d')
        date2 = date1 + relativedelta(days=+1)
        mjd1 = date2mjd(date1)
        mjd2 = date2mjd(date2)
        stw1 = mjd2stw(mjd1)
        stw2 = mjd2stw(mjd2)
        temp = [stw1, stw2, mjd1, mjd2]
        query_str = ''' select freqmode, backend, count(distinct(stw)) from
             ac_cal_level1b
             join attitude_level1 using(backend,stw)
             where stw between {0} and {1}
             and mjd between {2} and {3}
             group by backend,freqmode
             order by backend,freqmode '''.format(*temp)

        query = con.query(query_str)

        result = query.dictresult()
        lista = []
        datadict1 = {
            'Date'     : [],
            'Info'  : [],
            }
        datadict2 = {
            'Backend'  : [],
            'FreqMode' : [],
            'NumScan'  : [],
            'URL'      : [],
            }

        datadict1['Date'].append(str(date1.date()))
        for row in result:
            datadict2 = {
                'Backend'  : [],
                'FreqMode' : [],
                'NumScan'  : [],
                'URL'      : [],
                }
            lista.append(
                [date1.date(), row['backend'], row['freqmode'], row['count']])
            datadict2['Backend'] = row['backend']
            datadict2['FreqMode'] = row['freqmode']
            datadict2['NumScan'] = row['count']
            temp = [
                request.url_root,
                str(date1.date()),
                row['backend'],
                row['freqmode']
                ]
            datadict2['URL'] = '''{0}viewscan/{1}/{2}/{3}'''.format(*temp)
            datadict1['Info'].append(datadict2)
        con.close()
        accept = request.headers['Accept']

        if "application/json" in accept:
            return jsonify(**datadict1)
        else:
            return render_template(
                'scan_info.html', scanno=int(1), lista=lista)

class ViewDateBackendInfo(MethodView):
    """plots information"""
    def get(self, date, backend):

        con = DatabaseConnector()
        date1 = datetime.strptime(date, '%Y-%m-%d')
        date2 = date1 + relativedelta(days = +1)
        mjd1 = date2mjd(date1)
        mjd2 = date2mjd(date2)
        stw1 = mjd2stw(mjd1)
        stw2 = mjd2stw(mjd2)
        temp = [stw1, stw2, mjd1, mjd2, backend]
        query_str = '''
             select freqmode, backend, count(distinct(stw)) from
             ac_cal_level1b
             join attitude_level1 using(backend,stw)
             where stw between {0} and {1}
             and mjd between {2} and {3}
             and backend='{4}'
             group by backend,freqmode
             order by backend,freqmode
                         '''.format(*temp)

        query = con.query(query_str)

        result = query.dictresult()
        lista = []
        for row in result:
            lista.append([date1.date(),row['backend'],row['freqmode'],row['count']])
        con.close()
        accept = request.headers['Accept']

        if "application/json" in accept:

            return jsonify(**lista)

        else:

            return render_template('scan_info.html', scanno=int(1),lista=lista)

class ViewFreqmodeInfo(MethodView):
    """loginfo for all scans from a given date and freqmode"""
    def get(self, date, backend, freqmode):
        con = DatabaseConnector()
        loginfo, date1, date2 = get_scan_logdata(
            con, backend, date+'T00:00:00', int(freqmode), 1)
        lista = []
        for ind in range(len(loginfo['ScanID'])):
            row = []
            row.append(loginfo['DateTime'][ind].date())
            for item in ['DateTime', 'FreqMode', 'StartLat', 'EndLat', 'SunZD', 'AltStart', 'AltEnd', 'ScanID']:
                row.append(loginfo[item][ind])
            lista.append(row)
        accept = request.headers['Accept']
        if "application/json" in accept:
            for item in loginfo.keys():
                try:
                    loginfo[item] = loginfo[item].tolist()
                except:
                    pass
            loginfo['Info'] = []
            for fm, scanid in zip(loginfo['FreqMode'], loginfo['ScanID']):
                datadict = {'ScanID':[], 'URL':[]}
                temp = [request.url_root, date, backend, fm, scanid]
                datadict['ScanID'] = scanid
                datadict['URL'] = '''{0}viewodinscan/{1}/{2}/{3}/{4}'''.format(*temp)
                loginfo['Info'].append(datadict)
            return jsonify(**loginfo)
        else:
            return render_template(
                'scan_data.html',
                date=loginfo['DateTime'][0].date(),
                backend=backend,
                freqmode=freqmode,
                lista=lista)

class ViewFreqmodeInfoPlot(MethodView):
    """plots information: loginfo for all scans from a given date and freqmode"""
    def get(self, date, backend, freqmode):


        con = DatabaseConnector()

        loginfo,date1,date2 = get_scan_logdata(con, backend,date+'T00:00:00',int(freqmode),1)

        lista = []
        for ind in range(len(loginfo['ScanID'])):
            row = []
            row.append( loginfo['DateTime'][ind].date() )
            for item in ['DateTime','FreqMode','StartLat','EndLat','SunZD','AltStart','AltEnd','ScanID']:
                row.append(loginfo[item][ind])
            lista.append(row)

        accept = request.headers['Accept']

        if "application/json" in accept:


            return jsonify(**lista)

        else:
            fig = plot_loginfo(backend,date1,date2,loginfo)
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            return send_file(
                    buf, attachment_filename='plot.png', mimetype='image/png')



class ViewScanSpec(MethodView):
    """plots information: data from a given scan"""
    def get(self, date, backend, freqmode, scanno):

        con=DatabaseConnector()

        #export data
        calstw = int(scanno)
        
        spectra = get_scan_data(con, backend, freqmode, scanno)

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

class DatabaseConnector(DB):
    def __init__(self):
        super(DatabaseConnector, self).__init__(
            dbname='odin',
            user='odinop',
            host='postgresql',
            passwd='***REMOVED***'
            )

