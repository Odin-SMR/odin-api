"""A complex datamodel implementation"""
import logging
from pathlib import Path

from flask import Flask
from yaml import safe_load


LOG_CONFIG = Path(__file__).parent.parent / "logconf.yaml"


with open(LOG_CONFIG) as f:
    logconf_dict = safe_load(f)
logging.config.dictConfig(logconf_dict)  # type: ignore
logger = logging.getLogger(__name__)
logger.info("Starting OdinAPI")
app = Flask(__name__)
