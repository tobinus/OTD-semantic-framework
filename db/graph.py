import os
from collections import namedtuple
import datetime
from bson.objectid import ObjectId
from rdflib import URIRef, BNode, Literal, Namespace
from utils.misc import first, second
from utils.db import MongoDBConnection
from utils.dotenv import ensure_loaded_dotenv
from utils.graph import create_bound_graph, RDF, XSD, SKOS, DCAT, QEX

DEFAULT_UUID = 'default'
"""
Special value which can be given as the UUID to any get function, in order to
not search using UUID but rather accept the first document retrieved by MongoDB
by default.
"""


DataFrameId = namedtuple(
    'DataFrameId', ('graph_type', 'graph_uuid', 'last_modified')
)


def get(uuid, key='ontology', **kwargs):
    """
    Read ontology given by 'uuid'
    """
    d = get_raw_json(uuid, key, **kwargs)
    graph = create_bound_graph()
    graph.parse(data=d, format='json-ld')
    return graph


def _get_for_collection(key, uuid=None, raise_on_no_uuid=True, **kwargs):
    """
    Fetch one graph from the named collection, matching the given UUID.

    This differs from the simple get() because it handles the case where a
    UUID is not given, by looking at environment variables.

    Args:
        key: Name of the collection to fetch a graph from.
        uuid: The UUID of the document to fetch. If not given, the
            environment variable <KEY>_UUID will be used, where <KEY> is the
            key argument put into uppercase.
        raise_on_no_uuid: By default, an exception is raised when None is given
            as uuid, and no environment variable value is found. However, by
            setting this to False, you can instead simply let MongoDB decide
            what to fetch in cases where no UUID is specified.
        **kwargs: Extra arguments to be given to MongoDBConnection
            constructor.

    Returns:
        The parsed graph from the named collection with the given UUID.

    Raises:
        ValueError: If UUID was neither given as an argument nor as the
            environment variable.
    """
    func_name = 'get_{}'.format(key)
    uuid = get_uuid_for_collection(key, uuid, raise_on_no_uuid, func_name)
    return get(uuid, key, **kwargs)


def get_uuid_for_collection(key, uuid, raise_on_no_uuid, func_name):
    envvar = '{}_UUID'.format(key.upper())

    # No uuid given? Were we given one by environment variables?
    if uuid is None:
        ensure_loaded_dotenv()
        uuid = os.environ.get(envvar)

        if uuid is None:
            if raise_on_no_uuid:
                # No UUID given by environment variables
                raise ValueError(
                    'No UUID specified as argument to {} or in environment '
                    'variable {}'.format(func_name, envvar)
                )
            else:
                uuid = DEFAULT_UUID
    return uuid


def get_ontology(*args, **kwargs):
    """
    Fetch one graph from the ontology collection, matching the given UUID.

    Args:
        uuid: The UUID of the document to fetch. If not given, the
            environment variable ONTOLOGY_UUID will be used.
        raise_on_no_uuid: By default, an exception is raised when None is given
            as uuid, and no environment variable value is found. However, by
            setting this to False, you can instead simply let MongoDB decide
            what to fetch in cases where no UUID is specified.
        **kwargs: Extra arguments to be given to MongoDBConnection
            constructor.

    Returns:
        The parsed graph from the ontology collection with the given UUID.

    Raises:
        ValueError: If UUID was neither given as an argument nor as the
            environment variable ONTOLOGY_UUID.
    """
    return _get_for_collection('ontology', *args, **kwargs)


def get_dataset(*args, **kwargs):
    """
    Fetch one graph from the dataset collection, matching the given UUID.

    Args:
        uuid: The UUID of the document to fetch. If not given, the
            environment variable DATASET_UUID will be used.
        raise_on_no_uuid: By default, an exception is raised when None is given
            as uuid, and no environment variable value is found. However, by
            setting this to False, you can instead simply let MongoDB decide
            what to fetch in cases where no UUID is specified.
        **kwargs: Extra arguments to be given to MongoDBConnection
            constructor.

    Returns:
        The parsed graph from the dataset collection with the given UUID.

    Raises:
        ValueError: If UUID was neither given as an argument nor as the
            environment variable DATASET_UUID.
    """
    return _get_for_collection('dataset', *args, **kwargs)


def get_similarity(*args, **kwargs):
    """
    Fetch one graph from the similarity collection, matching the given UUID.

    Args:
        uuid: The UUID of the document to fetch. If not given, the
            environment variable SIMILARITY_UUID will be used.
        raise_on_no_uuid: By default, an exception is raised when None is given
            as uuid, and no environment variable value is found. However, by
            setting this to False, you can instead simply let MongoDB decide
            what to fetch in cases where no UUID is specified.
        **kwargs: Extra arguments to be given to MongoDBConnection
            constructor.

    Returns:
        The parsed graph from the similarity collection with the given UUID.

    Raises:
        ValueError: If UUID was neither given as an argument nor as the
            environment variable SIMILARITY_UUID.
    """
    return _get_for_collection('similarity', *args, **kwargs)


def get_autotag(*args, **kwargs):
    """
    Fetch one graph from the autotag collection, matching the given UUID.

    Args:
        uuid: The UUID of the document to fetch. If not given, the
            environment variable AUTOTAG_UUID will be used.
        raise_on_no_uuid: By default, an exception is raised when None is given
            as uuid, and no environment variable value is found. However, by
            setting this to False, you can instead simply let MongoDB decide
            what to fetch in cases where no UUID is specified.
        **kwargs: Extra arguments to be given to MongoDBConnection
            constructor.

    Returns:
        The parsed graph from the autotag collection with the given UUID.

    Raises:
        ValueError: If UUID was neither given as an argument nor as the
            environment variable AUTOTAG_UUID.
    """
    return _get_for_collection('autotag', *args, **kwargs)


def get_raw_json(uuid, key='ontology', **kwargs):
    doc = get_document(uuid, key, **kwargs)
    d = doc['rdf'].decode("utf-8")
    return d


def get_document(uuid, key='ontology', **kwargs):
    assert is_recognized_key(key)

    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        collection = getattr(db, key)

        if uuid == DEFAULT_UUID:
            criteria = None
        else:
            criteria = {'_id': ObjectId(uuid)}

        doc = collection.find_one(criteria)

        if doc is None:
            raise NoSuchGraph(
                'No graph found in collection "{}" with UUID "{}"'
                    .format(key, uuid)
            )
        return doc


def update(graph, uuid, key='ontology', **kwargs):
    """
    Store graph data in the database
    """
    assert is_recognized_key(key)

    jld = graph.serialize(format='json-ld')
    ont = {
        "rdf": jld,
        "lastModified": datetime.datetime.utcnow(),
    }

    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        getattr(db, key).replace_one({'_id': ObjectId(uuid)}, ont, upsert=True)
    return True


def get_concepts(uuid, **kwargs):
    g = get_ontology(uuid, raise_on_no_uuid=False, **kwargs)
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


def store(graph, key='ontology', **kwargs):
    assert is_recognized_key(key)
    # Prepare what we want to insert
    jld = graph.serialize(format='json-ld')
    ont = {
        "rdf": jld,
        "lastModified": datetime.datetime.utcnow(),
    }

    # Insert
    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        ont_id = getattr(db, key).insert_one(ont).inserted_id

    # Return the ID of our newly created graph
    return str(ont_id)


def remove(uuid, key='ontology', **kwargs):
    assert is_recognized_key(key)

    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        collection = getattr(db, key)
        r = collection.delete_one({'_id': ObjectId(uuid)})
        num_deleted = r.deleted_count
    return num_deleted > 0


def tag_dataset(uuid, dataset_uri, tag, score, **kwargs):
    dataset_graph = create_bound_graph()
    dataset_graph.parse(dataset_uri, format="xml")
    ds = next(dataset_graph.subjects(RDF.type, DCAT.Dataset))
    graph = get(uuid, **kwargs)
    graph.parse(dataset_uri, format="xml")
    concept_dict = get_concepts(uuid)
    if tag in get_concepts(uuid):
        node = concept_dict[tag]
        graph.add((ds, SKOS.relatedMatch, node))
        graph.add((ds, QEX.score, Literal(str(score), datatype=XSD.double)))
        update(graph, uuid, **kwargs)
        #output = path.join(app_path + '/db', uuid+'.rdf')
        #graph.serialize(destination=output, format='xml')
        graph.close()
        return True
    return False


def get_tagged_datasets(uuid, **kwargs):
    graph = get(uuid, **kwargs)
    datasets = []
    for s, p, o in graph.triples( (None, SKOS.relatedMatch, None) ):
        datasets.append((s, o))
    return datasets


def is_recognized_key(key):
    return key in ('ontology', 'autotag', 'dataset', 'similarity')


def get_dataframe_id(key, uuid, raise_on_no_uuid, **kwargs):
    assert is_recognized_key(key)
    uuid = get_uuid_for_collection(
        key,
        uuid,
        raise_on_no_uuid,
        'get_dataframe_id'
    )

    doc = get_document(uuid, key, **kwargs)
    last_modified = doc['lastModified']
    return DataFrameId(key, uuid, last_modified)


class NoSuchGraph(Exception):
    pass
