// Functions for updating overview table and plots:

function initLevel1(date) {
    $('#level1-date').html(date);

    var table = $('#level1-date-table').DataTable({
        "ajax": {
            "url": '/rest_api/v4/freqmode_info/' + date + '/',
            "dataSrc": "Info",
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
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var date = $('#level1-date').text();
        var backend = tr.children().eq(0).text();
        var freqmode = tr.children().eq(1).text();
        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');
        }else {
            row.child( addInfo( row.data(), backend, freqmode )).show();
            tr.addClass('shown');
        }
        // The plot rows don't have the necessary attributes, so don't try to
        // update when those are clicked:
        if ((backend == "AC1") || (backend == "AC2")) {
            clearDataTable();
            updateDataTable(date, backend, freqmode);
            updatePlot(date, backend, freqmode);
        } else if (!tr.hasClass("foldablePlot")) {
            backend = tr.prev().children().eq(0).text();
            freqmode = tr.prev().children().eq(1).text();
            clearDataTable();
            updateDataTable(date, backend, freqmode);
            updatePlot(date, backend, freqmode);
        }
    });
}

function updateLevel1(date) {
    var table;
    table = $('#level1-date-table').DataTable();
    table.ajax.url('/rest_api/v4/freqmode_info/' + date + '/').load();
    $('#level1-date').html(date);
}


function clearLevel1Table() {
    var table;
    table = $('#level1-date-table').DataTable();
    table.clear();
    table.draw();
}


function addInfo (data, backend, freqmode) {
    return '<table width="100%">' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Latitudes of first spectra in scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot" height=128>' +
            '<td colspan="4" id="smart-plot-lat-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Longitudes of first spectra in scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot" height=128>' +
            '<td colspan="4" id="smart-plot-lon-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Solar zenith angles (ZD) of scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot" height=128>' +
            '<td colspan="4" id="smart-plot-sun-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Number of spectra in scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot" height=128>' +
            '<td colspan="4" id="smart-plot-scan-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Quality of spectra in scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot" height=128>' +
            '<td colspan="4" id="smart-plot-quality-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '</table>';
}


function updatePlot(date, back, freq) {
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
        '/rest_api/v4/freqmode_info/' + date + '/' + back + '/' + freq + '/',
        function(data) {
            xticks =[];
            $.each( data.Info, function (index, data) {
                time_point = moment;
                datestring = data.DateTime;
                var momentDate = moment.utc(datestring);
                sun.push( [momentDate.toDate(), data.SunZD] );
                lat.push( [momentDate.toDate(), data.LatStart] );
                lon.push( [momentDate.toDate(), data.LonStart] );
                scan.push([momentDate.toDate(), data.NumSpec] );
                // quality = log2(data.Quality)
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
            plots.push($.plot("#smart-plot-lat-"+back+"-"+freq, [lat], opt));
            plots.push($.plot("#smart-plot-lon-"+back+"-"+freq, [lon], opt));
            plots.push($.plot("#smart-plot-sun-"+back+"-"+freq, [sun], opt));
            plots.push($.plot("#smart-plot-scan-"+back+"-"+freq, [scan], opt));
            plots.push($.plot("#smart-plot-quality-"+back+"-"+freq, [qual], opt));
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

    $("#smart-plot-lat-"+back+"-"+freq+"").bind("plothover",
        function (event, pos, item) {
            hoverOverviewPlot(event, pos, item, plots);
        }
    );
    $("#smart-plot-lon-"+back+"-"+freq+"").bind("plothover",
        function (event, pos, item) {
            hoverOverviewPlot(event, pos, item, plots);
        }
    );
    $("#smart-plot-sun-"+back+"-"+freq+"").bind("plothover",
        function (event, pos, item) {
            hoverOverviewPlot(event, pos, item, plots);
        }
    );
    $("#smart-plot-scan-"+back+"-"+freq+"").bind("plothover",
        function (event, pos, item) {
            hoverOverviewPlot(event, pos, item, plots);
        }
    );
    $("#smart-plot-quality-"+back+"-"+freq+"").bind("plothover",
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
