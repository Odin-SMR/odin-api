// Function(s) for mapping Odin Level2 JSON objects to GeoJSON


// Take a Result object from an Info object from the Level2 Odin API
// and return a GeoJSON Feature object:
function result2feature(result) {
    feature = {
        "type": "Feature",
        "properties": {},
        "geometry": {}
    };

    // Set Feature properties:
    for (var property in result) {
        feature.properties[property] = result[property];
    }

    // Set Feature geometry:
    feature.geometry = {
        "type": "Point",
        "coordinates": [result.Longitude, result.Latitude]
    };
    delete feature.properties.Latitude;
    delete feature.properties.Longitude;

    return feature;
}


// Take an Info object from the Level2 Odin API and return a GeoJSON
// FeatureCollection object:
function json2geojson(obj) {
    var geo = {
        "type": "FeatureCollection",
        "features": []
    };

    // Fill GeoJSON object with results from JSON Object:
    var Results = obj.Info.Results;
    for (var ind = 0; ind < Results.length; ind++) {
        geo.features.push(result2feature(Results[ind]));
    }

    return geo;
}
