"""
Part of odin-api, tools to make it happen
"""

from requests import get
from requests.exceptions import HTTPError
from datetime import date, timedelta
from psycopg2 import connect

def odin_connection():
    """Connects to the database, returns a connection"""
    connection_string = (
        "host='malachite.rss.chalmers.se' "
        "dbname='odin' "
        "user='odinop' "
        "password='***REMOVED***'"
        )
    connection = connect(connection_string)
    return connection

def add_to_database(cursor, day, freqmode, numscans, backend):
    """Add an entry to the database, delete the oldone first"""
    cursor.execute(
        """
        delete from measurements_cache
        where date=%s and freqmode=%s and nscans=%s and backend=%s
        """,
        (day, freqmode, numscans, backend))
    cursor.execute(
        'insert into measurements_cache values(%s,%s,%s,%s)',
        (day, freqmode, numscans, backend))

def main():
    """Script to populate database with 'cached'info"""
    step = timedelta(days=-1)
    current_date = date(2016, 1, 17)
    end_date = date(2009, 1, 1)
    db_connection = odin_connection()
    db_cursor = db_connection.cursor()
    while current_date >= end_date:
        url = (
            'http://odin.rss.chalmers.se/'
            'rest_api/v4/freqmode_raw/{}/'.format(current_date.isoformat())
            )
        response = get(url)
        try:
            response.raise_for_status()
        except HTTPError, msg:
            print current_date, msg
            continue
        json_data = response.json()
        for freqmode in json_data['Info']:
            add_to_database(
                db_cursor,
                json_data['Date'],
                freqmode['FreqMode'],
                freqmode['NumScan'],
                freqmode['Backend']
                )
        db_connection.commit()
        print current_date, "OK"
        current_date = current_date + step
    db_cursor.close()
    db_connection.close()

if __name__ == '__main__':
    main()
