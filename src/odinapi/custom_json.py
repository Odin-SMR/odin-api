from typing import Any
from flask.json.provider import DefaultJSONProvider
import datetime as dt

import numpy as np
import simplejson


class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj: Any) -> Any:
        if type(obj) == np.int_:
            return int(obj)
        if type(obj) == np.float_:
            return float(obj)
        if isinstance(obj, dt.datetime) or isinstance(obj, dt.date):
            return obj.isoformat()
        if isinstance(obj, np.ndarray):
            return obj.tolist()

    def loads(self, s: str | bytes, **kwargs: Any) -> Any:
        return simplejson.loads(
            s,
            allow_nan=True,
            **kwargs,
        )

    def dumps(self, obj: Any, **kwargs: Any) -> str:
        return simplejson.dumps(obj, default=self.default, ignore_nan=True)
