from pymongo import MongoClient
from bson.objectid import ObjectId
from rdflib import Namespace
from rdflib.namespace import RDF, RDFS, OWL, DC, FOAF, XSD, SKOS
from rdflib import URIRef
from rdflib import Graph
from json import loads as json_loads
import pandas as pd

ODT = Namespace('http://www.quaat.com/ontologies#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')

def load_graph(uri, uuid, key):
    client = MongoClient(uri)
    db = client.ontodb
    onts = db.ontologies    
    doc = onts.find_one({'_id': ObjectId(uuid)})
    d = doc[key].decode("utf-8")
    graph = Graph()
    graph.bind('odt', ODT)
    graph.bind('dcat', DCAT)
    graph.bind('dct', DCT)
    graph.parse(data=d, format='json-ld')
    return graph
    
def load_ontology(uri, uuid):
    return load_graph(uri, uuid, 'ontology')

def load_dataset(uri, uuid):
    return load_graph(uri, uuid, 'datasets')

def load_similarity(uri, uuid):
    return load_graph(uri, uuid, 'similarity')

def load_autotagged(uri, uuid):
    return load_graph(uri, uuid, 'autotag')


def save_log(uri, json):
    client = MongoClient(uri)
    db = client.ontodb
    db.log.insert_one(json)

def save_dataframe(uri, df):    
    client = MongoClient(uri)
    db = client.ontodb
    j = df.to_json(orient='split')
    return db.dataframe.insert_one({'df': j}).inserted_id

def load_dataframe(uri, uuid):
    client = MongoClient(uri)
    db = client.ontodb
    doc = db.dataframe.find_one({'_id': ObjectId(uuid)})
    js = json_loads(doc['df'])
    js['columns'] = list(map(lambda x: URIRef(x), js['columns']))
    js['index'] = list(map(lambda x: URIRef(x), js['index']))
    df = pd.DataFrame(data=js['data'], index=js['index'], columns=js['columns'])
    return df
