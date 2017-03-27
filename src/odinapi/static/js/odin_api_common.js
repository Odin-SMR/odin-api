FREQMODE_COLOURS = {
    // Websafe colours:
    '0':   '#101010', //'Black',
    '1':   '#E6E6FA', // 'Lavender',
    '2':   '#4169E1', // 'RoyalBlue',
    '8':   '#800080', // 'Purple',
    '13':  '#B22222', // 'FireBrick',
    '14':  '#228B22', // 'ForestGreen',
    '17':  '#8B4513', // 'SaddleBrown',
    '19':  '#C0C0C0', // 'Silver',
    '21':  '#87CEEB', // 'SkyBlue',
    '22':  '#000080', // 'Navy',
    '23':  '#663399', // 'RebeccaPurple',
    '24':  '#008080', // 'Teal',
    '25':  '#FFD700', // 'Gold',
    '29':  '#4682B4', // 'SteelBlue',
    '102': '#6495ED', // 'CornFlowerBlue',
    '113': '#CD5C5C', // 'IndianRed',
    '119': '#DCDCDC', // 'Gainsboro',
    '121': '#B0E0E6', // 'PowderBlue',
};


FREQMODE_TEXT_COLOURS = {
    // Colours with decent contrast with freqmodeColours:
    '0':   'White',
    '1':   'Black',
    '2':   'White',
    '8':   'White',
    '13':  'White',
    '14':  'White',
    '17':  'White',
    '19':  'Black',
    '21':  'Black',
    '22':  'White',
    '23':  'White',
    '24':  'White',
    '25':  'Black',
    '29':  'Black',
    '102': 'Black',
    '113': 'Black',
    '119': 'Black',
    '121': 'Black',
};


FREQMODE_TO_BACKEND = {
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


FREQMODE_INFO_TEXT = {
    0: ["unclassified", "-"],
    1: ["501.180 - 501.580, 501.980 - 502.380", "ClO, O3, N2O"],
    2: ["544.100 - 544.902", "HNO3, O3"],
    8: ["488.950 - 489.350, 488.35 - 488.750", "H2(18)O, O3, H2O"],
    13: ["556.598 - 557.398", "H2(16)O, O3"],
    14: ["576.062 - 576.862", "CO, O3"],
    17: ["489.950 - 490.750", "HDO, (18)O3"],
    19: ["556.550 - 557.350", "H2O, O3"],
    21: ["551.152 - 551.552, 551.752 - 552.152", "NO, O3, H2(17)O"],
    22: ["576.254 - 576.654, 577.069 - 577.469", "CO, O3, HO2, (18)O3"],
    23: ["488.350 - 488.750, 556.702 - 557.102", "H2(16)0, O3"],
    24: ["576.062 - 576.862", "CO, O3"],
    25: ["502.998 - 504.198", "H2(16)O, O3"],
    29: ["499.400 - 499.800", "BrO"],
    102: ["544.100 - 544.902", "HNO3, O3"],
    113: ["556.598 - 557.398", "H2(16)O, O3"],
    119: ["556.550 - 557.350", "H2O, O3"],
    121: ["551.152 - 551.552, 551.752 - 552.152", "NO, O3, H2(17)O"],
};


MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
    13: "Undecimber"
};


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


function log2(val) {
  return Math.log(val) / Math.LN2;
}
