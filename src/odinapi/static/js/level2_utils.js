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
