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
        "crosshair": {
            "mode": "x"
        },
    };

    var container = document.querySelector('#' + container_id);
    var template = document.querySelector('#alt-cross-section-plot-product');

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
                $.plot('#product' + index + ' #vmr',
                       [{"data": zip([to_ppm(product.VMR), altitude_km]),
                         "label": "Odin-SMR-v3"},
                        {"data": zip([to_ppm(product.Apriori), altitude_km]),
                         "label": "Odin-SMR-apriori"}],
                       opt_vmr);
                var avk = [];
                for(var i=0; i < product.AVK.length; i++) {
                    avk.push(zip([product.AVK[i], altitude_km]));
                }
                avk.push({'data': zip([product.MeasResponse, altitude_km]),
                          'color': 'black'});
                $.plot('#product' + index + ' #avk', avk, opt_vmr);
            });
        }
    );
}
