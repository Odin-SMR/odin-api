from odinapi.pg_database import squeeze_query


def test_squeeze_query():
    query = """
        This is
            as sample query;
    """
    log_friendly_query = squeeze_query(query)
    assert len(log_friendly_query.splitlines()) == 1
    assert len(log_friendly_query.split(" ")) == 5
