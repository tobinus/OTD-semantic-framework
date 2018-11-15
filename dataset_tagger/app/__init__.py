from os import path, environ
from flask import Flask
from dataset_tagger.config import Config

app = Flask(__name__)
app.config.from_object(Config)
app_path = path.dirname(__file__)

from dataset_tagger.app import routes
