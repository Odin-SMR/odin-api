// Functions for updating scan info table and plots:

function initDataTable(date, back, freq) {
    if (back === '') {
        back = "AC1";
    }
    if (freq === '') {
        freq = "2";
    }
    var table = $('#info-table').DataTable( {
        "ajax": {
            "dataSrc": "Info",
            "url": '/rest_api/v4/freqmode_info/' + date + '/' + back + '/' +
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
                    "data":"Quality",
                    "title": "Quality",
                },
                {
                    "data": "SunZD",
                    "title": "SunZD",
                    "render": function ( data, type, full, meta ) {
                        return parseFloat(data).toFixed(2);
                    }
                },
                {
                    "data": "URLS.URL-spectra",
                    "title": "Data URL (JSON)",
                    "render": function ( data, type, full, meta ) {
                        return '<a href="' + data + '">Get JSON data</a>';
                    },
                },
         ],
    });

    $('#info-table tbody').on( 'click', 'tr', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var url = $(this).children().eq(6).find('a').attr("href");
        var url_array = url.split('/');
        var id = url_array[url_array.length - 2];
        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');
        }else {
            row.child(addOverview(url, id)).show();
            tr.addClass('shown');
        }

        updateOverview(url, id);
    });
}


function updateOverview(url, id) {
    $('#info-image-' + id).attr('src', url.replace("rest_api/v4/scan",
                                                   "browse"));
}


function addOverview(url, id) {
    return '<img id="info-image-' + id + '" class="img-responsive"' +
           ' src="{{ url_for("static", filename="images/empty.png") }}"/>';
}


function updateDataTable(date, back, freq) {
    var table;
    table = $('#info-table').DataTable();
    table.ajax.url('/rest_api/v4/freqmode_info/' + date + '/' + back + '/' +
            freq + '/').load();
}


function clearDataTable() {
    var table;
    table = $('#info-table').DataTable();
    table.clear();
    table.draw();
}
