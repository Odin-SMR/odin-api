from odinapi.api import create_app

from odinapi.odin_config import TestConfig


def test_health_check():
    config = TestConfig()
    app = create_app(config)
    client = app.test_client()
    r = client.get('/rest_api/health_check')
    assert r.status_code == 200