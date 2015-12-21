function initLevel1(date) {
    var table = $('#level1-date').DataTable({
        "ajax": {
            "url": '/rest_api/v3/freqmode_info/'+date,
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

    $('#level1-date tbody').on( 'click', 'tr', function () {
        var tr = $(this).closest('tr')
        var row = table.row(tr)
        var backend = $(this).children().eq(0).text()
        var freqmode = $(this).children().eq(1).text()
        if (row.child.isShown()) {
            row.child.hide()
            tr.removeClass('shown')
        }else {
            console.log(backend)
            row.child( addInfo( row.data(), backend, freqmode )).show()
            tr.addClass('shown')
        }
        //updateOverview(date, backend, freqmode)
        updateDataTable(date, backend, freqmode)
        updatePlot(date, backend, freqmode)
    });
}

function updateLevel1(date) {
    var table;
    table = $('#level1-date').DataTable();
    table.ajax.url('/rest_api/v3/freqmode_info/' + date).load();
}

function addInfo (data, backend, freqmode) {
    return '<table width="100%">'+
        '<tr><td id="smart-plot-lat-' + backend + '-' + freqmode +
        '" class="plotter"></td></tr>' +
        '<tr><td id="smart-plot-lon-' + backend + '-' + freqmode +
        '" class="plotter"></td></tr>' +
        '<tr><td id="smart-plot-sun-' + backend + '-' + freqmode +
        '" class="plotter"></td></tr>'+
        '<tr><td id="smart-plot-scan-'+ backend + '-' + freqmode +
        '" class="plotter"></td></tr>'+
        '</table>'
}

function updateOverview(url) {
  $('#info-image').attr('src', url.replace("rest_api/v3/scan", "browse"));
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
                $.plot("#smart-plot-lat-"+back+'-'+freq, [lat], opt)//{series:{points: {show:true}}})
                $.plot("#smart-plot-lon-"+back+'-'+freq, [lon], opt)//{series:{points: {show:true}}})
                $.plot("#smart-plot-sun-" +back+'-'+freq, [sun], opt)
                $.plot("#smart-plot-scan-" +back+'-'+freq, [scan], opt)
            })
        }

function initDataTable() {
    var date = '2015-01-03'
    var back = 'AC2'
    var freq = '1'
    var table = $('#info-table').DataTable( {
        "ajax": {
            "dataSrc": "Info",
            "url": '/rest_api/v3/freqmode_info/' + date + '/' + back + '/' + freq,
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
                        return '<a href="' + data + '">Get JSON data</a>';
                    },
                },
                {
                    "data": "URL",
                    "title": "Scan overview",
                    "render": function ( data, type, full, meta ) {
                        return '<a href="#info-image">Show overview</a>';
                    },
                },
         ],
    });

    $('#info-table tbody').on( 'click', 'tr', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var url = $(this).children().eq(5).find('a').attr("href");

        updateOverview(url);
    });
}


function updateDataTable(date, back, freq) {
    var table;
    table = $('#info-table').DataTable();
    table.ajax.url('/rest_api/v3/freqmode_info/' + date + '/' + back + '/' + freq).load();
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
  '29': 'Black',
}

function updateCalendar(start, end, timezone, callback) {
    var theDate = start;
    var events = [];
    // Loop over time interval in view:
    while (theDate < end) {
        // For ech day, get json from rest:
        $.ajax({
            type: 'GET',
            url: '/rest_api/v3/freqmode_info/' +
                 theDate.stripTime().format() + '/',
            async: false,
            dataType: "json",
            success: function(data) {
                // Check if there are scans in Info, if so, loop
                // over the elements under Info and add to events list:
                $.each(data.Info, function(index, theInfo) {
                    theEvent = {
                        title: "FM: " + theInfo.FreqMode + " (" +
                               theInfo.Backend +  "): " +
                               theInfo.NumScan + " scans",
                        start: theDate.stripTime().format(),
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
                    events.push(theEvent);
                });
            }
        });
        // Increment loop "Moment":
        theDate.add(1, 'd');
    }
    // Callback with events list  makes Calendar update:
    callback(events);
}

