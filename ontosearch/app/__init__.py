from flask import Flask
from ontosearch.config import Config
from otd.opendatasemanticframework import ODSFLoader
from os import path

app = Flask(__name__)
app.config.from_object(Config)

app_path = path.dirname(__file__)


odsf_loader = ODSFLoader()
odsf_loader.ensure_all_loaded()


print ("ready")

from ontosearch.app import routes
