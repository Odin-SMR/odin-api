// Functions for updating overview table and plots:

function initLevel1(date) {
    $('#level1-date').html(date);

    var table = $('#level1-date-table').DataTable({
        "ajax": {
            "url": '/rest_api/v3/freqmode_info/' + date + '/',
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
        })

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
    table.ajax.url('/rest_api/v3/freqmode_info/' + date).load();
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
        '<tr class="foldablePlot">' +
            '<td colspan="4" id="smart-plot-lat-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Longitudes of first spectra in scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4" id="smart-plot-lon-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Solar zenith angles (ZD) of scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4" id="smart-plot-sun-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Number of spectra in scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4" id="smart-plot-scan-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '</table>';
}

function updatePlot(date, back, freq) {
        var sun = []
        var lat = []
        var lon = []
        var scan = []
        var opt = {}
        var currDate = moment(date, 'YYYY-MM-DD')
        $.getJSON(
            '/rest_api/v1/freqmode_info/'+date+'/'+back+'/'+freq,
            function(data) {
                xticks =[]
                $.each( data["SunZD"], function (index, value) {
                    time_point = moment
                    datestring = date + " " +data["DateTime"][index].split(" ")[4]
                    var momentDate = moment(
                        datestring,
                        'YYYY-MM-DD HH:mm:ss');
                    sun.push( [momentDate.toDate(), value] );
                    lat.push( [momentDate.toDate(), data["StartLat"][index]] );
                    lon.push( [momentDate.toDate(), data["StartLon"][index]] );
                    scan.push( [momentDate.toDate(), data["NumSpec"][index]] );
                    //xticks.push([index, data["DateTime"][index]])
                })
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
                    }
                }
                $.plot("#smart-plot-lat-"+back+'-'+freq, [lat], opt);//{series:{points: {show:true}}})
                $.plot("#smart-plot-lon-"+back+'-'+freq, [lon], opt);//{series:{points: {show:true}}})
                $.plot("#smart-plot-sun-" +back+'-'+freq, [sun], opt);
                $.plot("#smart-plot-scan-" +back+'-'+freq, [scan], opt);
            })
        }


// Functions for updating scan info table and plots:

function initDataTable(date, back, freq) {
    var table = $('#info-table').DataTable( {
        "ajax": {
            "dataSrc": "Info",
            "url": '/rest_api/v3/freqmode_info/' + date + '/' + back + '/' +
                freq + '/',
            },
        "data": [],
        "columns": [
                {
                    "data": "DateTime",
                    "title": "DateTime",
                },
                {
                    "data": "AltStart",
                    "title": "AltStart",
                },
                {
                    "data": "AltEnd",
                    "title": "AltEnd",
                },
                {
                    "data":"FreqMode",
                    "title": "FreqMode",
                },
                {
                    "data": "SunZD",
                    "title": "SunZD",
                    "render": function ( data, type, full, meta ) {
                        return parseFloat(data).toFixed(2);
                    }
                },
                {
                    "data": "URL",
                    "title": "Data URL (JSON)",
                    "render": function ( data, type, full, meta ) {
                        return '<a href="' + data.replace("v3", "v4") +
                               '">Get JSON data</a>';
                    },
                },
         ],
    });

    $('#info-table tbody').on( 'click', 'tr', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var url = $(this).children().eq(5).find('a').attr("href").replace("v4", "v3");
        var url_array = url.split('/');
        var id = url_array[url_array.length - 1];
        if (row.child.isShown()) {
            row.child.hide()
            tr.removeClass('shown')
        }else {
            row.child(addOverview(url, id)).show()
            tr.addClass('shown')
        }

        updateOverview(url, id);
    });
}

function updateOverview(url, id) {
    $('#info-image-' + id).attr('src', url.replace("rest_api/v3/scan", "browse"));
}

function addOverview(url, id) {
    return '<img id="info-image-' + id + '" class="img-responsive"' +
           ' src="{{ url_for("static", filename="images/empty.png") }}"/>'
}

function updateDataTable(date, back, freq) {
    var table;
    table = $('#info-table').DataTable();
    table.ajax.url('/rest_api/v3/freqmode_info/' + date + '/' + back + '/' +
            freq + '/').load();
}

function clearDataTable() {
    var table;
    table = $('#info-table').DataTable();
    table.clear();
    table.draw();
}


// Functions used to populate calendar view:

var freqmodeColours = {
  '0': 'Black',
  '1': 'AliceBlue',
  '2': 'RoyalBlue',
  '8': 'Purple',
  '13': 'FireBrick',
  '14': 'ForestGreen',
  '17': 'SaddleBrown',
  '19': 'Silver',
  '21': 'LightSkyBlue',
  '22': 'Navy',
  '23': 'RebeccaPurple',
  '24': 'Teal',
  '25': 'Gold',
  '29': 'LightSteelBlue',
}

var freqmodeTextColours = {
  '0': 'White',
  '1': 'Black',
  '2': 'White',
  '8': 'White',
  '13': 'White',
  '14': 'White',
  '17': 'White',
  '19': 'Black',
  '21': 'Black',
  '22': 'White',
  '23': 'White',
  '24': 'White',
  '24': 'Black',
  '29': 'Black',
}

function updateCalendar(start, end) {
    var theDate = start;
    // Loop over time interval in view:
    while (theDate < end) {
        // For ech day, get json from rest:
        if ($('#calendar').fullCalendar('clientEvents',
                    theDate.format()).length == 0) {
            $.ajax({
                type: 'GET',
                url: '/rest_api/v3/freqmode_info/' +
                    theDate.stripTime().format() + '/',
                dataType: "json",
                success: function(data) {
                    // Loop over the elements under Info and create event:
                    $.each(data.Info, function(index, theInfo) {
                        theEvent = {
                            title: "FM: " + theInfo.FreqMode + " (" +
                                theInfo.Backend +  "): " +
                                theInfo.NumScan + " scans",
                            start: data.Date,
                            id: data.Date,
                            // This should link to the report for the day:
                            // url: theInfo.URL,
                            url: "#level1-date",
                            // Add color and textColor based on freqmode:
                            color: freqmodeColours[theInfo.FreqMode],
                            textColor: freqmodeTextColours[theInfo.FreqMode],
                            // Save some metadata:
                            FreqMode: theInfo.FreqMode,
                            Backend: theInfo.Backend,
                        };
                        // Push event to calendar:
                        $('#calendar').fullCalendar('renderEvent', theEvent, true);
                    });
                }
            });
        };
        // Increment loop "Moment":
        theDate.add(1, 'd');
    }
}


// Functions for generating statistics plots:

function drawStatistics() {
    var data;
    var sum;

    // Generate freqmode statistics plot:
    data = [];
    sum = 0;
    $.getJSON('/rest_api/v4/statistics/freqmode', function(rawdata) {
        $.each( rawdata["Data"], function (ind, val) {
            data[ind] = {
                color: freqmodeColours[val["freqmode"]],
                data: val["sum"],
                label: "FM: " + val["freqmode"] + " (" + val["sum"] + ")",
            }
            sum += val["sum"];
        });

        $.plot($('#fmStats'), data, {
            series: {
                pie: {
                    show: true,
                    radius: 1,
                }
            }
        });
        $('#fmStatsLabel').html("Total number of scans by freqmode:");

        $('#totalNumberLabel').html("The data base contains a total of " +
                sum + " scans");
    });

    // Generate yearly statistics plot:
    data = [];
    sum = 0;
    $.getJSON('/rest_api/v4/statistics/annual', function(rawdata) {
        $.each( rawdata["Data"], function (ind, val) {
            data[ind] = {
                data: val["sum"],
                label: val["year"] + " (" + val["sum"] + ")",
            }
            sum += val["sum"];
        });

        $.plot($('#annualStats'), data, {
            series: {
                pie: {
                    show: true,
                    radius: 1,
                }
            }
        });
        $('#annualStatsLabel').html("Total number of scans by year:");
    });
}
