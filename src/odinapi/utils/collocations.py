"""Module for handling collocation data"""
from odinapi.utils.defs import FREQMODE_TO_BACKEND
from odinapi.views.database import DatabaseConnector


def get_collocations(freqmode, scanid, fields=None):
    """Return collocations for a certain scanid and freqmode"""
    columns = '*'
    if fields:
        columns = ','.join(fields)
    backend = FREQMODE_TO_BACKEND[freqmode]

    query_string = (
        "select {columns} from collocations where backend='{backend}' and "
        "freqmode={freqmode} and scanid={scanid}").format(
            columns=columns, backend=backend, freqmode=freqmode, scanid=scanid)
    con = DatabaseConnector()
    query = con.query(query_string)
    return query.dictresult()


def collocations_table_exist(con):
    """Return True if the collocations table exist"""
    query = con.query(
        "select 1 from information_schema.tables "
        "where table_name='collocations'")
    return bool(list(query.dictresult()))
