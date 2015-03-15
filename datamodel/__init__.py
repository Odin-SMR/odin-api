from flask import Flask

app = Flask(__name__)
from datamodel import views
