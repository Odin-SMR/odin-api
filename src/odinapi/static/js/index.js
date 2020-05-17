import $ from 'jquery';


export { getStartView, updateCalendar } from './level1calendar.js';
export { initLevel1, clearLevel1Table, updateLevel1 } from './level1overview.js';
export { initDataTable, updateDataTable, clearDataTable } from './level1scaninfo.js';
export { drawStatistics, renderFreqmodeInfoTable } from './level1statistics.js';
export { initLevel2Dashboard, fillFreqmodeSelector, searchLevel2Scans, plotAltitudeCrossSection} from './level2.js';


import '../../../../node_modules/bootstrap/dist/css/bootstrap.min.css';
import '../../../../node_modules/font-awesome/css/font-awesome.min.css';
import '../../../../node_modules/bootstrap-datepicker/dist/css/bootstrap-datepicker3.css';
import '../../../../node_modules/datatables/media/css/jquery.dataTables.min.css';
import '../../../../node_modules/fullcalendar/dist/fullcalendar.css';


import '../css/footer-distributed-with-address-and-phones.css';
import '../css/dashboard.css';
import '../css/odin.css';


window['$'] = require('jquery');
window['moment'] = require('moment');
window['datepicker'] = require('bootstrap-datepicker')
window['bootstrap'] = require('bootstrap')
