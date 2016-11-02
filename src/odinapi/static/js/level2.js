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
                if (product.Product == 'Temperature') {
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

                $.plot('#product' + index + ' #vmr', vmr_plot, opt_vmr);

                var avk = [];
                var avk_transposed = zip(product.AVK);
                for(var i=0; i < avk_transposed.length; i++) {
                    avk.push(zip([avk_transposed[i], altitude_km]));
                }
                avk.push({'data': zip([product.MeasResponse, altitude_km]),
                          'color': 'black'});
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
