// Functions for rendering L2 period overview map


// A Molflow inspired rainbow colour scale from red to blue:
function molour_scale() {
    var blue = "#2c5aa0";
    var cyan = "#02c5aa";
    var red = "#a02c5a";
    var magenta = "#aa02c5";
    var green = "#5aa02c";
    var yellow = "#c5aa02";
    return [blue, cyan, green, yellow, red, magenta];
}


// Function for rendering L2 period overview map:
function renderLevel2PeriodOverview(project, parameter, parameters) {
    // Set up page texts:
    $('#periodOverviewTitle').html(project + " overview");
    $('#periodOverviewInfo').html(parameters.product + " for " +
            parameters.start_time + " to " + parameters.end_time + ", " +
            Number(parameters.min_altitude)/1000 + " km - " +
            Number(parameters.max_altitude)/1000 + " km");

    // Set up the map:
    var url = "/rest_api/v4/level2/testproject/area?" + $.param(parameters);
    var width = 720,
        height = 720;

    var projection = d3.geoAzimuthalEqualArea()
        .scale(0.75 * height / Math.PI)
        .translate([width / 2, height / 2]);

    var path = d3.geoPath()
        .projection(projection);

    var graticule = d3.geoGraticule();

    var svg = d3.select("#overviewmap")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    svg.append("path")
        .datum(graticule)
        .attr("class", "graticule")
        .attr("d", path);

    d3.queue()
        .defer(d3.json, "/static/data/world-50m.json")
        .awaitAll(function (world) {
            renderOverviewMap(svg, path, world);
        });

    $.getJSON(url, function (data) {
        if (data.Info.Nr > 0) {
            renderOverviewData(svg, path, json2geojson(data), parameter);
        }
    });

}


// Function for rendering L2 period world map:
function renderOverviewMap(svg, path, world) {
   // Render world map
    d3.json("/static/data/world-50m.json", function(error, world) {
        if (error) throw error;

        svg.insert("path", ".graticule")
            .datum(topojson.feature(world, world.objects.land))
            .attr("class", "land")
            .attr("d", path);

        svg.insert("path", ".graticule")
            .datum(topojson.mesh(world, world.objects.countries,
            function(a, b) {
                return a !== b;
            }))
            .attr("class", "boundary")
            .attr("d", path);
    });
}


// Function for rendering L2 period data to world map:
function renderOverviewData(svg, path, data_geojson, parameter) {
    // Constants:
    var rad = "Altitude";

    // Calculate limits:
    var length = data_geojson.features.length;
    var alts = [];
    var datas = [];
    for (var ind=0; ind<length; ind++) {
        var alt = data_geojson.features[ind].properties.Altitude;
        alts.push(Number(alt));
        var data = data_geojson.features[ind].properties[parameter];
        datas.push(Number(data));
    }
    var mins = {
        "Altitude": Math.min.apply(Math, alts),
        "Data": Math.min.apply(Math, datas),
    };
    var maxs = {
        "Altitude": Math.max.apply(Math, alts),
        "Data": Math.max.apply(Math, datas),
    };

    // Create scaling functions:
    var radius = d3.scaleLinear()
        .domain([mins[rad], maxs[rad]])
        .range([1, 4]);

    var colour = d3.scaleLinear()
        .domain([
            mins.Data,
            mins.Data + 0.2 * (maxs.Data - mins.Data),
            mins.Data + 0.4 * (maxs.Data - mins.Data),
            mins.Data + 0.6 * (maxs.Data - mins.Data),
            mins.Data + 0.8 * (maxs.Data - mins.Data),
            maxs.Data
        ])
        .range(molour_scale());

    // "Draw" data:
    svg.selectAll("circle")
        .data(data_geojson.features)
        .enter()
        .append("path")
        .attr("fill-opacity", 0.618)
        .attr("fill", function(d) {
            return colour(d.properties[parameter]);
        })
        .attr("d", path.pointRadius(function(d) {
            // This is a little ugly, but can't figure out how to do it right:
            if (d.hasOwnProperty("properties")) {
                return radius(d.properties[rad]);
            }
        }));
}
