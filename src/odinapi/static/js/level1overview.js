// Functions for updating overview table and plots:


import * as datatables from 'datatables';
import * as moment from 'moment';
import * as flot from  'flot/jquery.flot';
import * as time from 'flot/jquery.flot.time';
import * as resize from 'flot/jquery.flot.resize';
import * as crosshair from 'flot/jquery.flot.crosshair';


import { clearDataTable, updateDataTable } from './level1scaninfo'


export function initLevel1(date) {
    $('#level1-date').html(date);

    var table = $('#level1-date-table').DataTable({
        "ajax": {
            "url": '/rest_api/v5/freqmode_info/' + date + '/',
            "dataSrc": "Data",
            },
        "columns": [
            {
                "data": "Backend",
                "title": "Backend",
            },
            {
                "data": "FreqMode",
                "title": "FreqMode",
            },
            {
                "data": "NumScan",
                "title": "NumScan",
            },
            {
                "data": "URL",
                "title": "URL",
                "render": function ( data, type, full, meta ) {
                  return '<a href="'+data+'">Get JSON data</a>';
                },
            },
            ],
        "paging":   false,
        "ordering": false,
        "info":     false,
    });

    $('#level1-date-table tbody').on( 'click', 'tr', function () {
        var tr = $(this).closest('tr'),
            row = table.row(tr),
            date = $('#level1-date').text(),
            backend = tr.children().eq(0).text(),
            freqmode = tr.children().eq(1).text();

        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');
        } else {
            row.child(addInfo(freqmode)).show();
            $(this).closest('tbody')
                .find('.highlight')
                .each(function() {$(this).removeClass("highlight");});

            tr.addClass('shown');
            tr.addClass('highlight');

            // The plot rows don't have the necessary attributes,
            // so don't try to update when those are clicked:
            if ((backend == "AC1") || (backend == "AC2")) {
                clearDataTable();
                updateDataTable(date, freqmode);
                updatePlot(date, freqmode);
            } else if (!tr.hasClass("foldablePlot")) {
                backend = tr.prev().children().eq(0).text();
                freqmode = tr.prev().children().eq(1).text();
                clearDataTable();
                updateDataTable(date, freqmode);
                updatePlot(date, freqmode);
            }
        }
    });
}

export function updateLevel1(date) {
    var table;
    table = $('#level1-date-table').DataTable();
    table.ajax.url('/rest_api/v5/freqmode_info/' + date + '/').load();
    $('#level1-date').html(date);
}


export function clearLevel1Table() {
    var table;
    table = $('#level1-date-table').DataTable();
    table.clear();
    table.draw();
}


function addInfo(freqmode) {
    function tableRow(id, description) {
        return '<tr class="foldablePlot"><td colspan="4">' +
            description + ':</td></tr>' +
            '<tr class="foldablePlot" height=128>' +
            '<td colspan="4" id="smart-plot-' + id + '-' + freqmode +
            '" class="plotter"></td></tr>';
    }
    return '<table width="100%">' +
        tableRow("lat", "Latitudes of first spectra in scans") +
        tableRow("lon", "Longitudes of first spectra in scans") +
        tableRow("sun", "Solar zenith angles (ZD) of scans") +
        tableRow("scan", "Number of spectra in scans") +
        tableRow("quality", "Quality of spectra in scans") +
        '</table>';
}


function updatePlot(date, freq) {
    var sun = [];
    var lat = [];
    var lon = [];
    var scan = [];
    var qual = [];
    var opt = {};
    var plots = [];
    var quality = [];
    var currDate = moment.utc(date, 'YYYY-MM-DD');
    $.getJSON(
        '/rest_api/v5/freqmode_info/' + date + '/' + freq + '/',
        function(data) {
            var xticks =[];
            $.each(data.Data, function (index, data) {
                var time_point = moment;
                var datestring = data.DateTime;
                var momentDate = moment.utc(datestring);
                sun.push( [momentDate.toDate(), data.SunZD] );
                lat.push( [momentDate.toDate(), data.LatStart] );
                lon.push( [momentDate.toDate(), data.LonStart] );
                scan.push([momentDate.toDate(), data.NumSpec] );
                qual.push([momentDate.toDate(), data.Quality] );
            });
            opt={
                "series":{
                    "color": "#2C5AA0",
                    "points":{
                        "show":true,
                    }
                },
                "xaxis":{
                    "mode": "time",
                    "minTickSize": [1, "hour"],
                    "min": currDate.startOf("day").toDate().getTime(),
                    "max": currDate.endOf("day").toDate().getTime()
                },
                "grid": {
                    "hoverable": true,
                },
                "crosshair": {
                    "mode": "x"
                },
            };
            plots.push($.plot("#smart-plot-lat-"+freq, [lat], opt));
            plots.push($.plot("#smart-plot-lon-"+freq, [lon], opt));
            plots.push($.plot("#smart-plot-sun-"+freq, [sun], opt));
            plots.push($.plot("#smart-plot-scan-"+freq, [scan], opt));
            plots.push($.plot("#smart-plot-quality-"+freq, [qual], opt));
        }
    );

    $("<div id='tooltip'></div>").css({
        position: "absolute",
        display: "none",
        border: "1px solid #002e74",
        padding: "2px",
        "background-color": "#8bb9ff",
        opacity: 0.90
    }).appendTo("body");

    $(".plotter").bind("plothover",
        function (event, pos, item) {
            hoverOverviewPlot(event, pos, item, plots);
        }
    );

}


function hoverOverviewPlot(event, pos, item, plots) {
    var plot;
    if (item) {
        var x = moment.utc(item.datapoint[0]).format("YYYY-MM-DD HH:mm:ss"),
            y = item.datapoint[1].toFixed(2);

        for (plot in plots) {
            plots[plot].setCrosshair(pos);
        }

        $("#tooltip").html(x + "; " + y)
            .css({top: item.pageY-24, left: item.pageX+8})
            .fadeIn(200);
    } else {
        $("#tooltip").hide();
        for (plot in plots) {
            plots[plot].clearCrosshair();
        }
    }
}
