// Functions for generating statistics page:

function labelFormatter(label, series) {
    var shortLabel = series.shortLabel;
    return "<div style='font-size:7pt; text-align:center; padding:2px; " +
           "color:white;'>" + shortLabel + "<br/>" + Math.round(series.percent) +
           "%</div>";
}


function drawStatistics(year) {
    var data;
    var sum;
    var plotMode;
    var temp = '';

    if (year === '') {
        plotMode = "Total";
    } else {
        plotMode = "Year";
    }

    // Generate freqmode statistics plot:
    data = [];
    sum = 0;
    $.getJSON('/rest_api/v5/statistics/freqmode/?year=' + year,
            function(rawdata) {
        $.each( rawdata.Data, function (ind, val) {
            data[ind] = {
                color: FREQMODE_COLOURS[val.freqmode],
                data: val.sum,
                label: "FM " + val.freqmode + " (" + val.sum + ")",
                shortLabel: "FM " + val.freqmode,
                longLabel: "Frequency mode " + val.freqmode + ": " +
                    val.sum + " scans",
            };
            sum += val.sum;
        });

        $.plot($('#fmStats' + plotMode), data, {
            series: {
                pie: {
                    show: true,
                    radius: 1,
                    innerRadius: 0.382,
                    label: {
                        formatter: labelFormatter,
                        show: true,
                        threshold: 0.05,
                        radius: 0.764,
                        background: {
                            opacity: 0.236,
                            color: '#101010'
                        },
                    },
                },
            },
            grid: {
                hoverable: true,
            },
            legend: {
                show: false,
            },
        });

        if (plotMode == "Total") {
            temp = "";
            $('#totalNumberLabel').html("The data base contains a total of " +
                    sum + " scans");
        } else {
            temp = " for " + year;
        }

        $('#fmStats' + plotMode + 'Label').html(
                "<span style='font-weight:bold;'>" +
                "Total number of scans by frequency mode" + temp + ":" +
                "</span>");

        $('#fmStats' + plotMode + 'Hover').html(
                "<span style='font-weight:bold;'>" +
                "Total number of scans" + temp + ": " + sum + "</span>");
    });

    $('#fmStats' + plotMode).bind("plothover", function(event, pos, obj) {
        if (plotMode == "Total") {
            temp = "";
        } else {
            temp = " for " + year;
        }

        if (!obj) {
            $('#fmStats' + plotMode + 'Hover').html(
                    "<span style='font-weight:bold;'>" +
                    "Total number of scans" + temp + ": " + sum + "</span>");
            return;
        }

        var percent = parseFloat(obj.series.percent).toFixed(2);
        $('#fmStats' + plotMode + 'Hover').html(
                "<span style='font-weight:bold;'>" +
                obj.series.longLabel + temp + " (" + percent + "%)</span>");
    });

    // Generate yearly statistics plot:
    data = [];
    xticks = [];
    $.getJSON('/rest_api/v5/statistics/freqmode/timeline/?year=' + year,
            function(rawdata) {
        $.each( rawdata.Data, function (key, val) {
            data.push({
                data: val,
                color: FREQMODE_COLOURS[key],
                shortLabel: "FM " + key,
                label: "FM " + key,
                longLabel: "Frequency mode " + key,
            });
        });

        if (plotMode == "Total") {
            xticks = rawdata.Years;
        } else {
            xticks = rawdata.Months;
        }

        $.plot($('#timelineStats' + plotMode), data, {
            series: {
                stack: true,
                lines: {
                    show: false,
                    fill: true,
                    steps: false,
                },
                bars: {
                    show: true,
                    barWidth: 0.618,
                    fill: 0.764,
                    color: '#101010',
                },
            },
            legend: {
                show: false,
            },
            xaxis: {
                ticks: xticks,
            },
            grid: {
                hoverable: true,
                clickable: true,
            },
        });

        if (plotMode == "Total") {
            temp = "year";
        } else {
            temp = "month for " + year;
        }

        $('#timelineStats' + plotMode + 'Label').html(
                "<span style='font-weight:bold;'>" +
                "Number of scans and frequency " +
                "mode distribution per " + temp +":" +
                "</span>");

        if (plotMode == "Total") {
            temp = "";
        } else {
            temp = " for " + year;
        }

        $('#timelineStats' + plotMode + 'Hover').html(
                "<span style='font-weight:bold;'>" +
                "Total number of scans" + temp + ": " + sum + "</span>");
    });

    $('#timelineStats' + plotMode + '').bind("plothover",
            function(event, pos, obj) {

        if (!obj) {
            if (plotMode == "Total") {
                temp = "";
            } else {
                temp = " for " + year;
            }

            $('#timelineStats' + plotMode + 'Hover').html(
                "<span style='font-weight:bold;'>" +
                "Total number of scans" + temp +": " + sum + "</span>");
            return;
        }

        var scans = obj.datapoint[1] - obj.datapoint[2];

        if (plotMode == "Total") {
            temp = obj.datapoint[0];
        } else {
            temp = MONTH_NAMES[obj.datapoint[0]];
        }

        $('#timelineStats' + plotMode + 'Hover').html(
                "<span style='font-weight:bold;'>" +
                obj.series.longLabel + ", " + temp + ": " +
                scans + " scans</span>");
    });

    if (plotMode == "Total") {
        $('#timelineStats' + plotMode + '').bind("plotclick",
                function(event, pos, obj) {
            var year;

            if (!obj) {
                return;
            }

            year = obj.datapoint[0];

            drawStatistics(year);
        });
    }
}


// Freqmode Info table:

function renderFreqmodeInfoTable () {
    theTable = "<table class='table'><tr><td></td><td><b>Frequency mode</b></td>" +
        "<td><b>Frequency range [GHz]</b></td><td><b>Species</b></td></tr>";
    $.each(FREQMODE_INFO_TEXT, function(key, val) {
        theTable += "<tr>" +
            "<td bgcolor='" + FREQMODE_COLOURS[key] + "'> </td>" +
            "<td>" + key + "</td>" +
            "<td>" + val[0] + "</td>" +
            "<td>" + val[1] + "</td>" +
            "</tr>";
    });

    theTable += "</table>";

    $('#freqmodeInfoTable').html(theTable);
}
