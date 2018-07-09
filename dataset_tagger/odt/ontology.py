import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from os import path, environ
from app import app, app_path
import uuid
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL, DC, FOAF, XSD, SKOS
from rdflib.plugins.sparql import prepareQuery
from dcat.dataset import Catalog, Distribution, Dataset, CatalogRecord

ODT = Namespace('http://www.quaat.com/ontologies#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')
ODTX = Namespace('http://www.quaat.com/ontology/ODTX#')
QEX = Namespace('http://www.quaat.com/extended_skos#')

dburi = 'mongodb://{0}:{1}@ds119969.mlab.com:19969/ontodb'.format(app.config['DB_USERNAME'],app.config['DB_PASSWD'])

def first(xs):
    """
    Returns the first element of a list, or None if the list is empty
    """
    if not xs:
        return None
    return xs[0]


def second(xs):
    """
    Returns the second element of a list, or None if the list is empty
    """
    if not xs:
        return None
    return xs[1]


def get_graph(uid):
    """
    Read ontology given by 'uid'
    """
    client = MongoClient(dburi)
    db = client.ontodb
    doc = db.ontologies.find_one({'_id': ObjectId(uid)})
    d = doc['ontology'].decode("utf-8")    
    graph = Graph()
    graph.parse(data=d, format='json-ld')
    client.close()
    return graph


def store_graph(graph, uid):
    """
    Store graph data in the database
    """
    client = MongoClient(dburi)
    db = client.ontodb
    jld = graph.serialize(format='json-ld')
    ont = {"ontology": jld}
    db.ontologies.replace_one({'_id':ObjectId(uid)}, ont, upsert=True)
    client.close()
    return True


def get_concepts(uid):
    g = get_graph(uid)
    concept_dict = {}
    for concept in g.subjects(RDF.type, SKOS.Concept):
        label = str(second(first(g.preferredLabel(concept, lang='en'))))
        concept_dict[label] = concept
    return concept_dict


def find_all_ids():
    client = MongoClient(dburi)
    db = client.ontodb
    collection = db.ontologies
    ids = [str(i) for i in collection.distinct('_id')]
    client.close()
    return list(ids)


def create_new_graph():
    uid = uuid.uuid4().hex
    rdf_storage = path.join(app_path, uid)
    g = Graph()
    g.bind('odt', ODT)
    g.bind('odtx', ODTX)
    g.bind('dcat', DCAT)
    g.bind('dct', DCT)
    g.bind('qex', QEX)
    o = path.join(app_path + '/resources', 'skos-odt.owl')
    g.parse(o, format="xml")

    client = MongoClient(dburi)
    db = client.ontodb
    jld = g.serialize(format='json-ld')
    ont = {"ontology": jld}
    ont_id = db.ontologies.insert_one(ont).inserted_id
    client.close()
    return str(ont_id)


def fetch(uid):
    g = get_graph(uid)
    return g.serialize(format='json-ld')


def tag_dataset(uid, dataset_uri, tag, score):
    dataset_graph = Graph()
    dataset_graph.parse(dataset_uri, format="xml")
    ds = next(dataset_graph.subjects(RDF.type, DCAT.Dataset))
    graph = get_graph(uid)
    graph.parse(dataset_uri, format="xml")
    concept_dict = get_concepts(uid)
    if tag in get_concepts(uid):
        node = concept_dict[tag]
        graph.add((ds, SKOS.relatedMatch, node))
        graph.add((ds, QEX.score, Literal(str(score), datatype=XSD.double)))
        store_graph(graph,uid)
        #output = path.join(app_path + '/db', uid+'.rdf')
        #graph.serialize(destination=output, format='xml')
        graph.close()
        return True
    return False


def tagged_datasets(uid):
    graph = get_graph(uid)
    datasets = []
    for s, p, o in graph.triples( (None, SKOS.relatedMatch, None) ):
       datasets.append((s, o))
    return datasets    
