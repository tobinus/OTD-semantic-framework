import os
from bson.objectid import ObjectId
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL, DC, FOAF, XSD, SKOS
from utils.misc import first, second
from utils.db import MongoDBConnection


ODT = Namespace('http://www.quaat.com/ontologies#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')
ODTX = Namespace('http://www.quaat.com/ontology/ODTX#')
QEX = Namespace('http://www.quaat.com/extended_skos#')


def get(uid, key='ontology', **kwargs):
    """
    Read ontology given by 'uid'
    """
    d = get_raw_json(uid, key, **kwargs)
    graph = Graph()
    graph.bind('odt', ODT)
    graph.bind('dcat', DCAT)
    graph.bind('dct', DCT)
    graph.parse(data=d, format='json-ld')
    return graph


def get_ontology(uid, **kwargs):
    return get(uid, 'ontology', **kwargs)


def get_dataset(uid, **kwargs):
    return get(uid, 'dataset', **kwargs)


def get_similarity(uid, **kwargs):
    return get(uid, 'similarity', **kwargs)


def get_autotag(uid, **kwargs):
    return get(uid, 'autotag', **kwargs)


def get_raw_json(uid, key='ontology', **kwargs):
    assert is_recognized_key(key)

    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        doc = getattr(db, key).find_one({'_id': ObjectId(uid)})
        d = doc['rdf'].decode("utf-8")
        return d


def update(graph, uid, key='ontology', **kwargs):
    """
    Store graph data in the database
    """
    assert is_recognized_key(key)

    jld = graph.serialize(format='json-ld')
    ont = {"rdf": jld}

    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        getattr(db, key).replace_one({'_id': ObjectId(uid)}, ont, upsert=True)
    return True


def get_concepts(uid, **kwargs):
    g = get(uid, **kwargs)
    concept_dict = {}
    for concept in g.subjects(RDF.type, SKOS.Concept):
        label = str(second(first(g.preferredLabel(concept, lang='en'))))
        concept_dict[label] = concept
    return concept_dict


def find_all_ids(key='ontology', **kwargs):
    assert is_recognized_key(key)

    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        collection = getattr(db, key)
        ids = [str(i) for i in collection.distinct('_id')]

    return list(ids)


def create_new(filename=None, uid=None, key='ontology', **kwargs):
    g = create_graph_from_file(filename)

    if uid is None:
        return store(g, key, **kwargs)
    else:
        update(g, uid, key, **kwargs)
        return uid


def create_graph_from_file(filename=None):
    if filename is None:
        filename = os.path.join(
            os.path.dirname(__file__),
            '..',
            'resources',
            'skos-odt.owl'
        )

    g = Graph()
    g.bind('odt', ODT)
    g.bind('odtx', ODTX)
    g.bind('dcat', DCAT)
    g.bind('dct', DCT)
    g.bind('qex', QEX)
    g.parse(filename, format="xml")
    return g


def store(graph, key='ontology', **kwargs):
    assert is_recognized_key(key)
    # Prepare what we want to insert
    jld = graph.serialize(format='json-ld')
    ont = {"rdf": jld}

    # Insert
    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        ont_id = getattr(db, key).insert_one(ont).inserted_id

    # Return the ID of our newly created graph
    return str(ont_id)


def tag_dataset(uid, dataset_uri, tag, score, **kwargs):
    dataset_graph = Graph()
    dataset_graph.parse(dataset_uri, format="xml")
    ds = next(dataset_graph.subjects(RDF.type, DCAT.Dataset))
    graph = get(uid, **kwargs)
    graph.parse(dataset_uri, format="xml")
    concept_dict = get_concepts(uid)
    if tag in get_concepts(uid):
        node = concept_dict[tag]
        graph.add((ds, SKOS.relatedMatch, node))
        graph.add((ds, QEX.score, Literal(str(score), datatype=XSD.double)))
        store(graph, uid, **kwargs)
        #output = path.join(app_path + '/db', uid+'.rdf')
        #graph.serialize(destination=output, format='xml')
        graph.close()
        return True
    return False


def get_tagged_datasets(uid, **kwargs):
    graph = get(uid, **kwargs)
    datasets = []
    for s, p, o in graph.triples( (None, SKOS.relatedMatch, None) ):
        datasets.append((s, o))
    return datasets


def is_recognized_key(key):
    return key in ('ontology', 'autotag', 'dataset', 'similarity')
