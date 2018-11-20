from flask import Flask
from config import Config
from db.graph import get_ontology, get_dataset, get_similarity, get_autotag
from odt.opendatasemanticframework import OpenDataSemanticFramework
from os import path
from utils.db import get_uri

app = Flask(__name__)
app.config.from_object(Config)

app.config['ONTOLOGY_UUID']   = '5b2ab51401d5412566cf4e94'
app.config['DATASETS_UUID']   = '5b2968c501d5412566cf4e86'
app.config['SIMILARITY_UUID'] = '5b2ada4d01d5412566cf4ea1'
app.config['AUTOTAG_UUID']    = '5b2acdfe01d5412566cf4e99'

app_path = path.dirname(__file__)

print ("Indexing...")
ontology_graph = get_ontology(app.config['ONTOLOGY_UUID'])
datasets_graph = get_dataset(app.config['DATASETS_UUID'])
similarity_graph = get_similarity(app.config['SIMILARITY_UUID'])
autotag_graph = get_autotag(app.config['AUTOTAG_UUID'])

CcsId    = "5b2adb9e01d5414513ea9802"
AutoID   = "5b2adb9c01d5414513ea9800"
ManualID = "5b2adb3401d5414513ea97fe"

ontology = OpenDataSemanticFramework(ontology_graph, datasets_graph, compute_ccs=False)
ontology.load_ccs(CcsId)
ontology.load_similarity_graph("tagged", ManualID)
ontology.load_similarity_graph("auto", AutoID)

print ("ready")

from app import routes
