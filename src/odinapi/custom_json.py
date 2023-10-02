from typing import Any
from flask.json.provider import DefaultJSONProvider
import simplejson


class CustomJSONProvider(DefaultJSONProvider):
    def dumps(self, obj: Any, **kwargs: Any) -> str:
        return simplejson.dumps(obj, ignore_nan=True, **kwargs)
