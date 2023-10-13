import re

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

pattern = re.compile(r"\s+")


def squeeze_query(query: str) -> str:
    log_friendly_query = re.sub(pattern, " ", query)
    return log_friendly_query.strip()
