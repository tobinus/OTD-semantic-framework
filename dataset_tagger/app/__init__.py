from os import path

from flask import Flask

from dataset_tagger.config import Config

# Set up app before trying to import routes that rely on it
app = Flask(__name__)
app.config.from_object(Config)
app_path = path.dirname(__file__)

# Set up routes
from dataset_tagger.app import routes
