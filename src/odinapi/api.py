"""A complex datamodel implementation"""

from pathlib import Path

import yaml
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger  # type: ignore

from odinapi.custom_json import CustomJSONProvider

from .odin_config import Config, ProdConfig, TestConfig
from .blueprints import register_blueprints
from .pg_database import db


def load_swagger_specs():
    """Load all YAML spec files from the swagger_specs directory."""
    specs_dir = Path(__file__).parent / "swagger_specs"
    all_paths = {}

    if specs_dir.exists():
        for yaml_file in specs_dir.glob("*.yaml"):
            with open(yaml_file, "r") as f:
                spec_content = yaml.safe_load(f)
                if spec_content and "paths" in spec_content:
                    all_paths.update(spec_content["paths"])

    return {"paths": all_paths} if all_paths else {}


def create_app(config: Config = ProdConfig()):
    app = Flask("odinapi")
    app.config.from_object(config)
    app.json = CustomJSONProvider(app)
    CORS(app)

    # Load YAML specifications
    yaml_specs = load_swagger_specs()

    # Initialize Swagger/OpenAPI documentation
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/rest_api/v5/spec",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
        "openapi": "3.0.3",
    }
    swagger_template = {
        "openapi": "3.0.3",
        "info": {
            "title": "Odin API",
            "description": "Odin rest api.\n\nGeographic coordinate system:\n\n* Latitude: -90 to 90\n* Longitude: 0 to 360",
            "version": "v5",
        },
        "servers": [{"url": "/", "description": "Default server"}],
    }

    # Merge YAML specs into the template
    swagger_template.update(yaml_specs)

    Swagger(app, config=swagger_config, template=swagger_template)

    db.init_app(app)
    register_blueprints(app)
    return app


def run():
    return create_app(TestConfig())
