"""Module for handling collocation data"""
from odinapi.pg_database import squeeze_query
from sqlalchemy import text
from odinapi.utils.defs import FREQMODE_TO_BACKEND
from odinapi.pg_database import db


def get_collocations(freqmode, scanid, fields=None):
    """Return collocations for a certain scanid and freqmode"""
    columns = "*"
    if fields:
        columns = ",".join(fields)
    backend = FREQMODE_TO_BACKEND[freqmode]

    query_string = text(
        squeeze_query(
            f"""\
        select {columns}
        from collocations
        where backend=:backend and
            freqmode=:freqmode and scanid=:scanid"""
        )
    )
    query = db.session.execute(
        query_string, params=dict(backend=backend, freqmode=freqmode, scanid=scanid)
    )
    return [row._asdict() for row in query]


def collocations_table_exist():
    """Return True if the collocations table exist"""
    query = db.session.execute.query(
        text(
            squeeze_query(
                """\
        select 1 from information_schema.tables
        where table_name='collocations'"""
            )
        )
    )
    return query.first() is not None
