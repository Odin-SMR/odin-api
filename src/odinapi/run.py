import argparse
from logging import config
from os import environ
from pathlib import Path
from textwrap import dedent

from yaml import safe_load

from .api import create_app
from .odin_config import Config, LiveConfig, LocalConfig, SeleniumConfig


def parse_arguments():
    description = dedent(
        """\
        Launch Odin api for local tests

        Production databases:
        Connect to live databases used for production

            Prerequisite
                eval $(ssh-agent)
                ssh-add /path/to/correct_key.pem

                a .env file containing PGPASSWORD and (AWS_PROFILE OR
                AWS_SECRET_ACCESS_KEY and AWS_ACCESS_KEY_ID)
                example:
                    PGPASSWD=<correct_password>
                    AWS_SECRET_ACCESS_KEY=<your-key>
                    AWS_ACCESS_KEY_ID=<your-key-id>

                ssh -L 5432:vulcan.rss.chalmers.se:5432 \\
                    -L 27017:localhost:27017 \\
                    -A -J ec2-user@admin.odin-smr.org \\
                        ec2-user@mongo.odin
            
            WARNING: Risk of changing production databases

        Local databases:
            Prerequisite:
                $ docker run -d -p 127.0.0.1:27017:27017 mongo
                $ docker run -d -p 127.0.0.1:5432:5432 odinsmr/odin_db

                a .env file containing AWS_PROFILE OR
                (AWS_SECRET_ACCESS_KEY and AWS_ACCESS_KEY_ID)
                example:
                    AWS_PROFILE=<your-profile>

        Selenium setup:
            This is used for testing with pytest. Pytest also need
            AWS credentials in the .env file.
        """
    )
    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--live", action="store_true", help="Use production databases")
    group.add_argument("--local", action="store_true", help="Use local databases")
    group.add_argument("--selenium", action="store_true", help="Config for selenium")
    return parser.parse_args()


def main():
    logconf_file = Path(__file__).parent.parent.parent / "logconf.yaml"
    with open(logconf_file) as f:
        logconf = safe_load(f)
    config.dictConfig(logconf)

    args = parse_arguments()
    if args.live:
        app = create_app(LiveConfig())
    elif args.local:
        app = create_app(LocalConfig())
    elif args.selenium:
        app = create_app(SeleniumConfig())
    else:
        app = create_app(Config())
    port_setting = environ.get("FLASK_PORT")
    port = int(port_setting) if port_setting else None
    app.run(port=port)


if __name__ == "__main__":
    main()
