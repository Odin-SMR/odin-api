from os import environ

from dotenv import find_dotenv, dotenv_values

pg_host = environ.get("PGHOST")
pg_dbname = environ.get("PGDBNAME")
pg_user = environ.get("PGUSER")
pg_passwd = environ.get("PGPASS")
pg_sslmode = environ.get("PGSSLMODE", "verify-full")

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

    SQLALCHEMY_ENGINE_OPTIONS = dict(
        pool_size=8,
        max_overflow=8,
        pool_recycle=300,
        pool_timeout=15,
    )


class LocalConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg://odinop@localhost/odin"
    DEBUG = True


class SeleniumConfig(Config):
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI", "")
    DEBUG = True


class LiveConfig(Config):
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg://odin:{vulcan_pg_passwd}@localhost/odin?sslmode=verify-ca"
    )
    DEBUG = True


class TestConfig(LocalConfig):
    # Use environment variables for test database hosts to support both
    # devcontainer (service names) and CI (localhost) environments
    pg_test_host = environ.get("ODINAPI_TEST_PGHOST", "postgresql")
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://odinop@{pg_test_host}/odin"
    TESTING = True
    DEBUG = True
