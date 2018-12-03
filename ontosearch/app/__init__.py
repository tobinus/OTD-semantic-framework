from flask import Flask
from ontosearch.config import Config
from db.graph import get_ontology, get_dataset, get_similarity, get_autotag
from otd.opendatasemanticframework import OpenDataSemanticFramework
from otd.constants import SIMTYPE_AUTOTAG, SIMTYPE_SIMILARITY
from os import path

app = Flask(__name__)
app.config.from_object(Config)

app_path = path.dirname(__file__)

ontology = OpenDataSemanticFramework(None, None, False)
ontology.load_similarity_graph(SIMTYPE_SIMILARITY, 'similarity', None)
ontology.load_similarity_graph(SIMTYPE_AUTOTAG, 'autotag', None)

print ("ready")

from ontosearch.app import routes
