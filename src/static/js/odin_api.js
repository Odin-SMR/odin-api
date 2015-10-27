function updateLevel1(date) {
  $.getJSON('/rest_api/v1/freqmode_info/'+date,
    function(data) {
      var table;
      table = `
<thead>
  <tr>
    <th>Backend</th>
    <th>Freqmode</th>
    <th>#scans</th>
  </tr>
</thead>
<tbody id="scans">`;
      var start_atag
      for (var i = 0; i<data.Info.length; i++) {
        start_atag = '<a href="' + data.Info[i].URL + '">';
        table = table + '<td>'+data.Info[i].Backend+'</td>\n';
        table = table + '<td>'+data.Info[i].FreqMode+'</td>\n';
        table = table + '<td>'+data.Info[i].NumScan+'</td>\n';
        table = table + '</tr>\n';
      };
      table = table + '</tbody>\n';
      $('#level1-date').html(table);
      $('#level1-date > tbody > tr').on('click', function(){
        var backend = $(this).children().eq(0).text()
        var freqmode = $(this).children().eq(1).text()
        updateOverview(date, backend,freqmode)
        updateDataTable(date, backend,freqmode)
        }); 
    });
}

function updateOverview(date, back, freq) {
  $('#info-image').attr('src','/plot/'+date+'/'+back+'/'+freq);
}

function updateDataTable(date, back, freq) {
/*  $.getJSON('/rest_api/v1/freqmode_info/'+date+'/AC2/1',
    function(data) {
      var table;
      table = `
<thead>i
  <tr>
    <th>Date</th>
  </tr>
</thead>
<tbody>`;
      for (var i = 0; i<data.MJD.length; i++) {
        table = table + '<tr>';
        table = table + '<td>'+data.DateTime[i]+'</td>\n';
        table = table + '</tr>\n';
      };
      table = table + '</tbody>\n';
      $('#info-table').html(table);
    });*/
    $('#info-table').DataTable( {
        "ajax": {
            "url": '/rest_api/v1/freqmode_info/'+date+'/'+back+'/'+freq,
            "dataSrc": "Info"
        },
        "columnDefs":[
            {
                "render": function (data, type, row) {
                    return '<a href="'+data+'">data</>'
                },
                "targets":1
            },
            {
                "render": function (data, type, row) {
                    return '<a href="'+data.replace("rest_api/v1/scan","browse")+'">plot</>'
                },
                "targets":2
            },
        ],
        "columns": [
           {"data": "ScanID"},
           {"data": "URL"},
           {"data": "URL"},
           ]
    });
}
