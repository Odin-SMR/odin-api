// Functions used to populate calendar view:

function getStartView(date) {
    // Starting with date, which is a moment object, go back in time to find
    // the closest previous month with any data, but only recurse back to
    // 2001-02-20 at the earliest.
    var startView;

    $.ajax({
        type: 'GET',
        async: false,
        url: '/rest_api/v4/period_info/' + date.format('YYYY/MM/DD/'),
        dataType: "json",
        success: function(data) {
            if (data.Info.length > 0) {
                startView = date;
            } else if (date.isAfter('2001-02-20')) {
                startView = getStartView(date.subtract(7, 'days'));
            } else {
                startView = moment('2001-02-20');
            }
        }
    });
    return startView;
}


function updateCalendar(start) {
    var theDate = start;
    // For ech day, get json from rest:
    if ($('#calendar').fullCalendar('clientEvents',
                theDate.format()).length === 0) {
        $.ajax({
            type: 'GET',
            url: '/rest_api/v4/period_info/' +
                start.format('YYYY/MM/DD/'),
            dataType: "json",
            success: function(data) {
                var events = [];
                // Loop over the elements under Info and create event:
                $.each(data.Info, function(index, theInfo) {
                    theEvent = {
                        title: "FM: " + theInfo.FreqMode + " (" +
                            theInfo.Backend +  "): " +
                            theInfo.NumScan + " scans",
                        start: theInfo.Date,
                        id: theInfo.Date,
                        // This should link to the report for the day:
                        url: "#level1-date",
                        // Add color and textColor based on freqmode:
                        color: FREQMODE_COLOURS[theInfo.FreqMode],
                        textColor: FREQMODE_TEXT_COLOURS[theInfo.FreqMode],
                        // Save some metadata:
                        FreqMode: theInfo.FreqMode,
                        Backend: theInfo.Backend,
                    };
                    events.push(theEvent);
                    // Push event to calendar:
                });
                $('#calendar').fullCalendar('removeEvents');
                $('#calendar').fullCalendar('addEventSource', events);
            }
        });
    }
}