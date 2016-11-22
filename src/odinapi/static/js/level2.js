var FREQMODE_TO_BACKEND = {
    "1": "AC2",
    "2": "AC1",
    "8": "AC2",
    "13": "AC1",
    "14": "AC2",
    "17": "AC2",
    "19": "AC1",
    "21": "AC1",
    "22": "AC2",
    "23": "AC1",
    "24": "AC1",
    "25": "AC1",
    "29": "AC1",
    "102": "AC2",
    "113": "AC2",
    "119": "AC2",
    "121": "AC2",
};

function initLevel2Dashboard() {
    fillProjectSelector();
}

function fillProjectSelector() {
    $.getJSON(
        '/rest_api/v4/level2/projects',
        function(data) {
            $('#select-project').empty();
            $('#select-project').append(
                '<option selected="selected" disabled>Choose project</option>');
            $.each(data.Info.Projects, function (index, project) {
                $('#select-project').append(
                    '<option value="' + project.Name + '">' +
                        project.Name + '</option>');
            });
        });
}

function fillFreqmodeSelector() {
    project = $('#select-project').val();
    $.getJSON(
        '/rest_api/v4/level2/' + project,
        function(data) {
            $('#select-freqmode').empty();
            $('#select-freqmode').append(
                '<option selected="selected" disabled>Choose freqmode</option>');
            $.each(data.Info.FreqModes, function (index, freqmode) {
                $('#select-freqmode').append(
                    '<option value="' + freqmode.FreqMode + '">' +
                        freqmode.FreqMode + '</option>');
            });
        });
}

function searchLevel2Scans(form) {
    if (!form.freqmode.value || form.freqmode.value == 'Choose freqmode') {
        alert('Choose freqmode');
        return;
    }
    var param = {};
    if (form.start_date.value)
        param.start_time = form.start_date.value;
    if (form.end_date.value)
        param.end_time = form.end_date.value;
    param = $.param(param);
    var url = '/rest_api/v4/level2/' + form.project.value + '/' +
        form.freqmode.value + '/' + form.types.value;
    if (param)
        url += '?' + param;

    $('#search-results-info').html(
        '<h2>Project: ' + form.project.value + ', freqmode: ' + form.freqmode.value + ', ' + form.types.value + '</h2>');
    var table = $('#search-results').DataTable({
        "ajax":{
            "url": url,
            "dataSrc": "Info.Scans",
        },
        "columns": [
            {
                "data": "ScanID",
                "title": "Scan ID",
            },
            {
                "data": "Date",
                "title": "Day",
            },
            {
                "data": "Error",
                "title": "Message",
                "defaultContent": "<i>N/A</i>"
            },
            {
                "data": "URLS",
                "title": "Level1 data",
                "render": function ( data, type, full, meta ) {
                    return '<a target="_blank" href="' + data['URL-spectra'] +
                        '">JSON data</a>';
                },
            },
            {
                "data": "ScanID",
                "title": "Level1 plot",
                "render": function ( data, type, full, meta ) {
                    return '<a target="_blank" href="/browse/' +
                        FREQMODE_TO_BACKEND[form.freqmode.value] + '/' +
                        form.freqmode.value + '/' + data + '/' +
                        '">Plot</a>';
                },
            },
            {
                "data": "URLS",
                "title": "Level2 data",
                "render": function ( data, type, full, meta ) {
                    return '<a target="_blank" href="' + data['URL-level2'] +
                        '">JSON data</a>';
                },
            },
            {
                "data": "ScanID",
                "title": "Level2 plot",
                "render": function ( data, type, full, meta ) {
                    return '<a target="_blank" href="/level2/' +
                        form.project.value + '/' + form.freqmode.value + '/' +
                        data + '">Plot</a>';
                },
            },
        ],
        "paging":   true,
        "ordering": true,
        "info":     false,
        "destroy": true,
    });

}

function zip(arrays) {
    return arrays[0].map(function(_,i){
        return arrays.map(function(array){return array[i];});
    });
}


function to_ppm(array) {
    return array.map(function(val){return val*1000000;});
}


function to_kilo(array) {
    return array.map(function(val){return val/1000;});
}


function find_max(data, error) {
    var added = [];
    for (i = 0; i < data.length; i++) {
        added.push(data[i] + error[i]);
    }
    return Math.max.apply(Math, added);
}


function find_min(data, error) {
    var added = [];
    for (i = 0; i < data.length; i++) {
        added.push(data[i] - error[i]);
    }
    return Math.min.apply(Math, added);
}


function plotAltitudeCrossSection(container_id, project, scanid, freqmode) {
    opt_vmr = {
        "grid": {
            "hoverable": true,
        },
    };

    var container = document.querySelector('#' + container_id);
    var template = document.querySelector('#alt-cross-section-plot-product');

    $("<div id='tooltip'></div>").css({
        position: "absolute",
        display: "none",
        border: "1px solid #002e74",
        padding: "2px",
        "background-color": "#8bb9ff",
        opacity: 0.80
    }).appendTo("body");

    $.getJSON(
        '/rest_api/v4/level2/' + project + '/' + freqmode + '/' + scanid + '/',
        function(data) {
            $.each(data.Info.L2, function (index, product) {
                template.content.querySelector('h2').textContent = product.Product;
                template.content.querySelector(
                    '.alt-cross-section-plot-product').setAttribute(
                        'id', 'product' + index);
                var product_container = document.importNode(
                    template.content, true);
                container.appendChild(product_container);

                var altitude_km = to_kilo(product.Altitude);
                var std_times_two = product.ErrorTotal.map(
                    function(val){return val*2;});

                var calculated, error, apriori;
                if (product.Product.startsWith('Temperature')) {
                    calculated = product.Temperature;
                    error = std_times_two;
                    apriori = product.Apriori;
                }
                else {
                    calculated = to_ppm(product.VMR);
                    error = to_ppm(std_times_two);
                    apriori = to_ppm(product.Apriori);
                }
                var vmr_plot = [
                {
                    "data": zip([
                            calculated,
                            altitude_km,
                            error
                    ]),
                    "label": "Odin-SMR-v3",
                    "color": "#2c5aa0",
                    "lines": {"show": true},
                    "points": {
                        "show": true,
                        "errorbars": "x",
                        "xerr": {
                            "show": true,
                            "color": "#2c5aa0",
                            "upperCap": "-",
                            "lowerCap": "-"
                        }
                    }
                },
                {
                    "data": zip([apriori, altitude_km]),
                    "label": "Odin-SMR-apriori",
                    "color": "#5aa02c",
                }];

                var vmr_max = find_max(calculated, error);
                if (vmr_max < Math.max.apply(Math, apriori)) {
                    vmr_max = Math.max.apply(Math, apriori);
                }
                opt_vmr.xaxis = {
                    "max": vmr_max * 1.05,
                };

                $.plot('#product' + index + ' #vmr', vmr_plot, opt_vmr);

                var avk = [];
                var avk_transposed = zip(product.AVK);
                for(var i=0; i < avk_transposed.length; i++) {
                    avk.push(zip([avk_transposed[i], altitude_km]));
                }
                avk.push({'data': zip([product.MeasResponse, altitude_km]),
                          'color': 'black'});

                opt_vmr.xaxis = {
                    "max": 1.5,
                    "min": -0.5,

                };

                $.plot('#product' + index + ' #avk', avk, opt_vmr);

                $("#product" + index + " #vmr").bind("plothover",
                    function (event, pos, item) {
                        level2tooltip(event, pos, item);
                    }
                );

                $("#product" + index + " #avk").bind("plothover",
                    function (event, pos, item) {
                        level2tooltip(event, pos, item);
                    }
                );
            });
        }
    );

}


function level2tooltip(event, pos, item) {
    if (item) {
        var x = item.datapoint[0],
            y = item.datapoint[1],
            s, tooltip_string;
        if (item.datapoint.length == 3) {
            s = item.datapoint[2];
            tooltip_string = y.toPrecision(4) + ": " + x.toPrecision(4) +
                "&plusmn; " + s.toPrecision(4);
        } else {
            tooltip_string = y.toPrecision(4) + ": " + x.toPrecision(4);
        }
        $("#tooltip").html(tooltip_string)
            .css({top: item.pageY-24, left: item.pageX+8})
            .fadeIn(200);
    } else {
        $("#tooltip").hide();
    }
}
