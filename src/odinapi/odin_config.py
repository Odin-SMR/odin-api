from os import environ

from dotenv import find_dotenv, dotenv_values

pg_host = environ.get("PGHOST")
pg_dbname = environ.get("PGDBNAME")
pg_user = environ.get("PGUSER")
pg_passwd = environ.get("PGPASS")
pg_sslmode = environ.get("PGSSLMODE", "verify-full")

mongo_host = environ.get("ODINAPI_MONGODB_HOST", "level2db")
mongo_port = int(environ.get("ODINAPI_MONGODB_PORT", 27017))
mongo_timeout = int(environ.get("ODINAPI_MONGODB_SERVER_TIMEOUT", 180000))

local_dotenv = dotenv_values(find_dotenv())
vulcan_pg_passwd = local_dotenv.get("PGPASSWD", "")

aws_profile = local_dotenv.get("AWS_PROFILE")
if aws_profile:
    environ.setdefault("AWS_PROFILE", aws_profile)

aws_secret = local_dotenv.get("AWS_SECRET_ACCESS_KEY")
if aws_secret:
    environ.setdefault("AWS_SECRET_ACCESS_KEY", aws_secret)

aws_access = local_dotenv.get("AWS_ACCESS_KEY_ID")
if aws_access:
    environ.setdefault("AWS_ACCESS_KEY_ID", aws_access)


class Config:
    TESTING = False


class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{pg_user}:{pg_passwd}@{pg_host}/{pg_dbname}?sslmode={pg_sslmode}"

    SQLALCHEMY_ENGINE_OPTIONS = dict(pool_size=3, max_overflow=5, pool_recycle=300)

    MONGO_DATABASE_URI = (
        f"mongodb://{mongo_host}:{mongo_port}/?serverSelectionTimeoutMS={mongo_timeout}"
    )


class LocalConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg://odinop@localhost/odin"
    MONGO_DATABASE_URI = "mongodb://localhost"
    DEBUG = True


class SeleniumConfig(Config):
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI", "")
    MONGO_DATABASE_URI = environ.get("MONGO_DATABASE_URI", "")
    DEBUG = True


class LiveConfig(Config):
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg://odin:{vulcan_pg_passwd}@localhost/odin?sslmode=verify-ca"
    )
    MONGO_DATABASE_URI = "mongodb://localhost"
    DEBUG = True


class TestConfig(LocalConfig):
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg://odinop@postgresql/odin"
    MONGO_DATABASE_URI = "mongodb://localhost"
    TESTING = True
    DEBUG = True
