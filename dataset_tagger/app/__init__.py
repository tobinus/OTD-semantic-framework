from os import path, environ
from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.config['DB_USERNAME'] = environ.get('DB_USERNAME')
app.config['DB_PASSWD'] = environ.get('DB_PASSWD')
app_path = path.dirname(__file__)

from app import routes
