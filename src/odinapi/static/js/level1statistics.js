// Functions for generating statistics page:
import $ from 'jquery';
import 'flot/jquery.flot';
import 'flot/jquery.flot.time';
import 'flot/jquery.flot.resize';
import 'flot/jquery.flot.pie';
import 'flot/jquery.flot.stack';

import './odin_api_common';

function labelFormatter(label, series) {
    return `<div style='font-size:7pt;text-align:center;padding:2px;color:white;'>${series.shortLabel}<br/>${Math.round(series.percent)}%</div>`;
}

export function drawStatistics(year) {
    const plotMode = year === '' ? 'Total' : 'Year';
    let temp = '';

    // Generate freqmode statistics plot:
    let data = [];
    let sum = 0;
    $.getJSON(`/rest_api/v5/statistics/freqmode/?year=${year}`, (rawdata) => {
        $.each(rawdata.Data, (ind, val) => {
            data[ind] = {
                color: FREQMODE_COLOURS[val.freqmode],
                data: val.sum,
                label: `FM ${val.freqmode} (${val.sum})`,
                shortLabel: `FM ${val.freqmode}`,
                longLabel: `Frequency mode ${val.freqmode}: ${val.sum} scans`,
            };
            sum += val.sum;
        });

        $.plot($(`#fmStats${plotMode}`), data, {
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
                            color: '#101010',
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

        if (plotMode === 'Total') {
            temp = '';
            $('#totalNumberLabel').html(`The database contains a total of ${sum} scans`);
        } else {
            temp = ` for ${year}`;
        }

        $(`#fmStats${plotMode}Label`).html(
            `<span style='font-weight:bold;'>Total number of scans by frequency mode${temp}:</span>`,
        );

        $(`#fmStats${plotMode}Hover`).html(
            `<span style='font-weight:bold;'>Total number of scans${temp}: ${sum}</span>`,
        );
    });

    $(`#fmStats${plotMode}`).bind('plothover', (event, pos, obj) => {
        temp = plotMode === 'Total' ? '' : ` for ${year}`;
        if (!obj) {
            $(`#fmStats${plotMode}Hover`).html(
                `<span style='font-weight:bold;'>Total number of scans${temp}: ${sum}</span>`,
            );
            return;
        }

        const percent = parseFloat(obj.series.percent).toFixed(2);
        $(`#fmStats${plotMode}Hover`).html(
            `<span style='font-weight:bold;'>${obj.series.longLabel}${temp} (${percent}%)</span>`,
        );
    });

    // Generate yearly statistics plot:
    data = [];
    $.getJSON(`/rest_api/v5/statistics/freqmode/timeline/?year=${year}`, (rawdata) => {
        $.each(rawdata.Data, (key, val) => {
            data.push({
                data: val,
                color: FREQMODE_COLOURS[key],
                shortLabel: `FM ${key}`,
                label: `FM ${key}`,
                longLabel: `Frequency mode ${key}`,
            });
        });

        const xticks = plotMode === 'Total' ? rawdata.Years : rawdata.Months;

        $.plot($(`#timelineStats${plotMode}`), data, {
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
                tickDecimals: 0,
            },
            grid: {
                hoverable: true,
                clickable: true,
            },
        });

        temp = plotMode === 'Total' ? '' : `month for ${year}`;
        $(`#timelineStats${plotMode}Label`).html(
            `<span style='font-weight:bold;'>Number of scans and frequency mode distribution per ${temp}:</span>`,
        );

        temp = plotMode === 'Total' ? '' : ` for ${year}`;
        $(`#timelineStats${plotMode}Hover`).html(
            `<span style='font-weight:bold;'>Total number of scans${temp}: ${sum}</span>`,
        );
    });

    $(`#timelineStats${plotMode}`).bind('plothover', (event, pos, obj) => {
        if (!obj) {
            temp = plotMode === 'Total' ? '' : ` for ${year}`;
            $(`#timelineStats${plotMode}Hover`).html(
                `<span style='font-weight:bold;'>Total number of scans${temp}: ${sum}</span>`,
            );
            return;
        }
        const scans = obj.datapoint[1] - obj.datapoint[2];
        temp = plotMode === 'Total' ? obj.datapoint[0] : MONTH_NAMES[obj.datapoint[0]];
        $(`#timelineStats${plotMode}Hover`).html(
            `<span style='font-weight:bold;'>${obj.series.longLabel}, ${temp}: ${scans} scans</span>`,
        );
    });

    if (plotMode === 'Total') {
        $(`#timelineStats${plotMode}`).bind('plotclick',
            (event, pos, obj) => {
                if (!obj) {
                    return;
                }
                drawStatistics(obj.datapoint[0]);
            });
    }
}

// Freqmode Info table:
export function renderFreqmodeInfoTable() {
    let theTable = "<table class='table'><tr><td></td><td><b>Frequency mode</b></td>"
        + '<td><b>Frequency range [GHz]</b></td><td><b>Species</b></td></tr>';
    $.each(FREQMODE_INFO_TEXT, (key, val) => {
        theTable += '<tr>'
            + `<td bgcolor='${FREQMODE_COLOURS[key]}'></td>`
            + `<td>${key}</td>`
            + `<td>${val[0]}</td>`
            + `<td>${val[1]}</td>`
            + '</tr>';
    });
    theTable += '</table>';
    $('#freqmodeInfoTable').html(theTable);
}
