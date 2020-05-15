require( 'datatables' );
require( 'flot/jquery.flot' );
require( 'flot/jquery.flot.resize');
require( 'flot/jquery.flot.errorbars' );


export function initLevel2Dashboard() {
    $('#select-project-loader').hide();
    $('#select-freqmode-loader').hide();
    fillProjectSelector();
}

function populateSelectWithDataOrSetNoData(settings, data) {
    if (settings.title !== undefined) {
        $(settings.target).append(
            '<option disabled>-- ' + settings.title + ' --</option>');
    }
    if (settings.empty !== undefined && data.Data.length === 0) {
        $(settings.target).append(
            '<option disabled><em>' + settings.empty +
            '</em></option>');
    }
    else if (settings.itemKey === 'Name') {
        /* fillProjectSelector end up here: both title and project name must be selected */
        $.each(data.Data, function (index, item) {
            $(settings.target).append(
                '<option value="' + settings.title + '/' + item[settings.itemKey] + '">' +
                    settings.title + '/' + item[settings.itemKey] + '</option>');
        });
    }
    else {
        $.each(data.Data, function (index, item) {
            $(settings.target).append(
                '<option value="' + item[settings.itemKey] + '">' +
                    item[settings.itemKey] + '</option>');
        });
    }
}

function populateSelectWithFailMessage(settings) {

    if (settings.title !== undefined) {
        $(settings.target).append(
            '<option disabled>-- ' + settings.title + ' --</option>');
    }
    if (settings.fail !== undefined) {
        $(settings.target).append(
            '<option disabled><em>' + settings.fail +
            '</em></option>');
    }
}

function handleSelectLoadingStatus(settings, completeCheck) {
    if (completeCheck.single !== true) {
        completeCheck.requestsEnded[settings.completionIndex] = true;
    }
    if (completeCheck.single === true ||
            completeCheck.requestsEnded.every(function (v) {return v;})) {

        $(settings.loaderTarget).hide();
    }
    $(settings.target).removeAttr('disabled');
}

function promiseRequestWithLoader(settings, completeCheck) {

    $.getJSON(settings.uri)
        .done(function(data) {
            populateSelectWithDataOrSetNoData(settings, data);
        })
        .fail(function(data) {
            populateSelectWithFailMessage(settings);
        })
        .always(function(data) {
            handleSelectLoadingStatus(settings, completeCheck);
            $(settings.target).removeAttr('disabled');
        });
}

function fillProjectSelector() {

    var completeCheck = {
        requestsEnded : [false, false],
        single: false
    };

    var target = '#select-project';
    var targetLoader = '#select-project-loader';

    $(targetLoader).show();
    $(target).empty();
    $(target).attr('disabled', 'disabled');

    $(target).append(
        '<option selected="selected" disabled>Choose project</option>');

    var requests = {
        production : {
            uri : '/rest_api/v5/level2/projects',
            completionIndex: 0,
            title: 'production',
            empty: 'No projects in database',
            fail: 'Failed to load projects',
            target: target,
            loaderTarget: targetLoader,
            itemKey: 'Name'
        },

        development : {
            uri : '/rest_api/v5/level2/development/projects',
            completionIndex: 1,
            title: 'development',
            empty: 'No projects in database',
            fail: 'Failed to load projects',
            target: target,
            loaderTarget: targetLoader,
            itemKey: 'Name'
        }
    };

    promiseRequestWithLoader(requests.production, completeCheck);
    promiseRequestWithLoader(requests.development, completeCheck);
}

export function fillFreqmodeSelector() {
    var target = '#select-freqmode';
    var targetLoader = '#select-freqmode-loader';

    $(targetLoader).show();
    $(target).empty();
    $(target).attr('disabled', 'disabled');
    $(target).append(
        '<option selected="selected" disabled>Choose freqmode</option>');

    var project = $('#select-project').val().replace('production/', '');

    var settings = {
        uri : '/rest_api/v5/level2/' + project,
        empty: 'No freqmodes in database for' + project,
        fail: 'Failed to load freqmodes for' + project,
        target: target,
        loaderTarget: targetLoader,
        itemKey: 'FreqMode'
    };

    var completeCheck = {
        single: true
    };

    promiseRequestWithLoader(settings, completeCheck);
}

export function searchLevel2Scans(form) {
    if (!form.freqmode.value || form.freqmode.value == 'Choose freqmode') {
        alert('Choose freqmode');
        return;
    }
    var param = {};
    if (form.start_date.value)
        param.start_time = form.start_date.value;
    if (form.end_date.value)
        param.end_time = form.end_date.value;
    if (form.offset.value) {
        form.offset.value = getOffsetValue(form.offset.value);
        param.offset = form.offset.value;
    } else  {
        form.offset.value = 0;
    }
    param = $.param(param);
    var project = form.project.value.replace('production/', '');
    var url = '/rest_api/v5/level2/' + project + '/' +
        form.freqmode.value + '/' + form.types.value;
    if (param)
        url += '?' + param;

    var count;
    $.ajax({
        url: url,
        async: false,
        dataType: 'json',
        success: function (json) {
            count = json.length;
        }
    });
    var lowerbound = parseInt(form.offset.value, 10) + 1;
    var upperbound = Math.min(parseInt(form.offset.value, 10) + 1000, count);
    // highest valid offset
    var maxoffset = Math.floor((parseInt(count, 10) - 1) / 1000) * 1000;
    // create an informative string that will be displayed on UI
    // together with the data table,
    // table only displays a maximum of 1000 entries and the
    // string will help the user to understand how to get
    // data (or other) data in table
    var search_results_str = 'Project: ' + project + ', ' +
        'Freqmode: ' + form.freqmode.value + ', ' +
        'Type: ' + form.types.value + ': ' +
        'In total data from ' + count + ' scans is available. ';
    if (lowerbound >= count) {
        // no data is displayed in table due to too high offset
        search_results_str = search_results_str +
            'You have entered an offset (' +
            form.offset.value + ') ' +
            'that is greater or equal to the ' +
            'total number of available scans. ' +
            'Update offset to be less or equal to ' +
            maxoffset + ' to get entries to scans in table.';
    } else {
        // data is displayed
        search_results_str = search_results_str +
            'The table is showing entries for scan ' + lowerbound +
            ' to ' + upperbound + ' within selected range. ';
        if (count > 1000) {
            // table does not show entries to all data within given limits
            search_results_str = search_results_str +
                'Update start date or offset to get entries to ' +
                'other scans in table.';
        }
    }
    $('#search-results-info').html('<h2>' + search_results_str + '</h2>');
    var table = $('#search-results').DataTable({
        "ajax":{
            "url": url,
            "dataSrc": "Data",
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
                        project + '/' + form.freqmode.value + '/' +
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


function getOffsetValue(value) {
    if (!isPositiveInteger(value)) {
        // only allow positive integers
        // otherwise set it to 0,
        // however, the template should help
        // user to properly fill in the form
        // and not end up here
        return 0;
    } else {
        return value;
    }
}


function isPositiveInteger(n) {
    return 0 === n % (!isNaN(parseFloat(n)) && 0 <= ~~n);
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
    for (var i = 0; i < data.length; i++) {
        added.push(data[i] + error[i]);
    }
    return Math.max.apply(Math, added);
}


function find_min(data, error) {
    var added = [];
    for (var i = 0; i < data.length; i++) {
        added.push(data[i] - error[i]);
    }
    return Math.min.apply(Math, added);
}


export function plotAltitudeCrossSection(container_id, project_mode, project, scanid, freqmode) {
    var opt_vmr = {
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

    var scanurl = '/rest_api/v5/level2/' + project_mode + '/' + project + '/' +
        freqmode + '/' + scanid + '/';
    var url = scanurl.replace('production/', '');

    $.getJSON(
        url,
        function(data) {
            $.each(data.Data.L2.Data, function (index, product) {
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
