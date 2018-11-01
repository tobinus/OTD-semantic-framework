from flask import Flask
from config import Config
from odt.database import load_ontology, load_dataset, load_similarity, load_autotagged
from odt.opendatasemanticframework import OpenDataSemanticFramework
from os import path, environ
from dotenv import load_dotenv, find_dotenv

# Allow user to specify database credentials in a file, rather than only through
# environment variables
dotenv_file = find_dotenv()
if dotenv_file:
    print(f'Loading environment variables from "{dotenv_file}"')
    load_dotenv(dotenv_file)
else:
    print(
        'No .env file found in this or any parent directory, relying on '
        'directly supplied environment variables only'
    )


app = Flask(__name__)
app.config.from_object(Config)
app.config['DB_USERNAME'] = environ.get('DB_USERNAME', '')
app.config['DB_PASSWD'] = environ.get('DB_PASSWD', '')
app.config['DB_HOST'] = environ.get('DB_HOST', 'localhost')
app.config['DB_NAME'] = environ.get('DB_NAME', 'ontodb')

app.config['ONTOLOGY_UUID']   = '5b2ab51401d5412566cf4e94'
app.config['DATASETS_UUID']   = '5b2968c501d5412566cf4e86'
app.config['SIMILARITY_UUID'] = '5b2ada4d01d5412566cf4ea1'
app.config['AUTOTAG_UUID']    = '5b2acdfe01d5412566cf4e99'

uri = 'mongodb://{0}:{1}@{2}/{3}'.format(
    app.config['DB_USERNAME'],
    app.config['DB_PASSWD'],
    app.config['DB_HOST'],
    app.config['DB_NAME']
)
app_path = path.dirname(__file__)

print ("Indexing...")
ontology_graph = load_ontology(uri, app.config['ONTOLOGY_UUID'])
datasets_graph = load_dataset(uri, app.config['DATASETS_UUID'])
similarity_graph = load_similarity(uri, app.config['SIMILARITY_UUID'])
autotag_graph = load_autotagged(uri, app.config['AUTOTAG_UUID'])

CcsId    = "5b2adb9e01d5414513ea9802"
AutoID   = "5b2adb9c01d5414513ea9800"
ManualID = "5b2adb3401d5414513ea97fe"

ontology = OpenDataSemanticFramework(ontology_graph, datasets_graph, compute_ccs=False)
ontology.load_ccs(uri, CcsId)
ontology.load_similarity_graph("tagged", uri, ManualID)
ontology.load_similarity_graph("auto", uri, AutoID)

print ("ready")

from app import routes
