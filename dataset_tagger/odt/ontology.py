import json
from bson.objectid import ObjectId
from os import path, environ
from dataset_tagger.app import app, app_path
import uuid
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL, DC, FOAF, XSD, SKOS
from rdflib.plugins.sparql import prepareQuery
from dataset_tagger.dcat.dataset import Catalog, Distribution, Dataset, CatalogRecord
from dotenv import load_dotenv, find_dotenv
from utils.misc import first, second
from utils.db import MongoDBConnection


ODT = Namespace('http://www.quaat.com/ontologies#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')
ODTX = Namespace('http://www.quaat.com/ontology/ODTX#')
QEX = Namespace('http://www.quaat.com/extended_skos#')


def get_graph(uid):
    """
    Read ontology given by 'uid'
    """
    with MongoDBConnection() as client:
        db = client.ontodb
        doc = db.ontologies.find_one({'_id': ObjectId(uid)})
        d = doc['ontology'].decode("utf-8")
        graph = Graph()
        graph.parse(data=d, format='json-ld')
    return graph


def store_graph(graph, uid):
    """
    Store graph data in the database
    """
    jld = graph.serialize(format='json-ld')
    ont = {"ontology": jld}

    with MongoDBConnection() as client:
        db = client.ontodb
        db.ontologies.replace_one({'_id':ObjectId(uid)}, ont, upsert=True)
    return True


def get_concepts(uid):
    g = get_graph(uid)
    concept_dict = {}
    for concept in g.subjects(RDF.type, SKOS.Concept):
        label = str(second(first(g.preferredLabel(concept, lang='en'))))
        concept_dict[label] = concept
    return concept_dict


def find_all_ids():
    with MongoDBConnection() as client:
        db = client.ontodb
        collection = db.ontologies
        ids = [str(i) for i in collection.distinct('_id')]
    return list(ids)


def create_new_graph(filename=None, uid=None):
    g = create_graph_from_file(filename)

    if uid is None:
        return store_new_graph(g)
    else:
        store_graph(g, uid)
        return uid


def create_graph_from_file(filename=None):
    if filename is None:
        filename = path.join(app_path, 'resources', 'skos-odt.owl')

    g = Graph()
    g.bind('odt', ODT)
    g.bind('odtx', ODTX)
    g.bind('dcat', DCAT)
    g.bind('dct', DCT)
    g.bind('qex', QEX)
    g.parse(filename, format="xml")
    return g


def store_new_graph(graph):
    # Prepare what we want to insert
    jld = graph.serialize(format='json-ld')
    ont = {"ontology": jld}

    # Insert
    with MongoDBConnection() as client:
        db = client.ontodb
        ont_id = db.ontologies.insert_one(ont).inserted_id

    # Return the ID of our newly created graph
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
        store_graph(graph, uid)
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
