function initLevel1(date) {
    var table = $('#level1-date').DataTable({
        "ajax": {
            "url": '/rest_api/v1/freqmode_info/'+date,
            "dataSrc": "Info",
            },
        "columns": [
            {"data": "Backend"},
            {"data": "FreqMode"},
            {"data": "NumScan"},
            {"data": "URL"},
            ],
        "paging":   false,
        "ordering": false,
        "info":     false
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
        updateOverview(date, backend,freqmode)
        updateDataTable(date, backend,freqmode)
        updatePlot(date, backend, freqmode)
    }); 
}

function addInfo (data, backend, freqmode) {
    console.log(backend)
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
function updateLevel1(date) {
    var table;
    table = $('#level1-date').DataTable();
    table.ajax.url('/rest_api/v1/freqmode_info/' + date).load();
}

function updateOverview(date, back, freq) {
  $('#info-image').attr('src','/plot/'+date+'/'+back+'/'+freq);
}

function updateDataTable(date, back, freq) {
        var table
        var dataSet = []
        table = $('#info-table').DataTable();
        $.getJSON(
            '/rest_api/v1/freqmode_info/'+date+'/'+back+'/'+freq,
            function(data) {
                $.each( data["SunZD"], function (index, value) {
                    dataSet.push( [
                        data["DateTime"][index],
                        data["AltStart"][index],
                        data["AltEnd"][index],
                        data["FreqMode"][index],
                        data["SunZD"][index],
                        data["Info"][index]["URL"],
                    ])
            })
        table.clear().draw();
        table.rows.add(dataSet); // Add new data
        table.columns.adjust().draw(); // Redraw the DataTable
        })
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
                        "points":{
                            "show":true
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
        $('#info-table').DataTable( {
            "data": [],
            "columns": [
                {"title": "DateTime"},
                {"title": "AltStart"},
                {"title": "AltEnd"},
                {"title": "FreqMode"},
                {"title": "SunZD"},
                {"title": "URL"},
            ]
    });
}
