import os
from abc import ABCMeta, abstractmethod
from collections import namedtuple
import datetime
import warnings
from bson.objectid import ObjectId
from rdflib import URIRef, BNode, Literal, Namespace

from similarity.generate import add_similarity_link
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


class MissingUuidWarning(Warning):
    pass


class DbCollection(metaclass=ABCMeta):
    def __init__(self, uuid=None):
        self.uuid = uuid

    @staticmethod
    @abstractmethod
    def _get_key():
        return ''

    @classmethod
    def from_uuid(cls, uuid=None, **kwargs):
        key = cls._key
        assert is_recognized_key(key)
        uuid = cls.find_uuid(uuid)

        criteria = None
        if uuid is not None:
            criteria = {'_id': ObjectId(uuid)}

        with MongoDBConnection(**kwargs) as client:
            db = client.ontodb
            collection = getattr(db, key)

            document = collection.find_one(criteria)

            if document is None:
                raise ValueError(
                    'No {} found with the UUID "{}"'
                        .format(key, uuid)
                )
        return cls.from_document(document)

    @classmethod
    @abstractmethod
    def from_document(cls, document):
        return cls(document['_id'])

    @classmethod
    def find_uuid(cls, uuid=None):
        key = cls._get_key()
        return cls._get_uuid_for(key, uuid)

    @staticmethod
    def _get_uuid_for(key, uuid=None):
        envvar = '{}_UUID'.format(key.upper())

        # No UUID given? Were we given one by environment variables?
        if uuid is None:
            ensure_loaded_dotenv()
            uuid = os.environ.get(envvar)

        if uuid is None:
            warnings.warn(
                'No UUID specified when fetching {}. Using '
                'whatever MongoDB returns first'.format(key),
                MissingUuidWarning,
                2
            )
        return uuid

    @classmethod
    def _force_get_uuid_for(cls, key, uuid=None, **kwargs):
        uuid = cls._get_uuid_for(key, uuid)
        if uuid is not None:
            return uuid

        # We're using whatever MongoDB returns first, so find that
        with MongoDBConnection(**kwargs) as client:
            db = client.ontodb
            collection = getattr(db, key)
            first_document = collection.fetch_one({})
            if first_document is None:
                return None
            return str(first_document['_id'])

    def prepare(self):
        pass

    def save(self, **kwargs):
        self.prepare()

        if self.uuid is None:
            uuid = self._save_as_new(**kwargs)
            self.uuid = uuid
            return uuid
        else:
            return self._save_with_uuid(self.uuid, **kwargs)

    def _save_as_new(self, **kwargs):
        document = self._get_as_document()
        with MongoDBConnection(**kwargs) as client:
            db = client.ontodb
            collection = getattr(db, self._get_key())
            assigned_id = collection.insert_one(document).inserted_id
        return str(assigned_id)

    def _save_with_uuid(self, uuid, **kwargs):
        document = self._get_as_document()
        with MongoDBConnection(**kwargs) as client:
            db = client.ontodb
            collection = getattr(db, self._get_key())
            collection.replace_one(
                {'_id': ObjectId(uuid)},
                document,
                upsert=True,
            )
        return uuid

    @abstractmethod
    def _get_as_document(self):
        return dict()


class Configuration(DbCollection):
    def __init__(
            self,
            uuid=None,
            similarity=None,
            autotag=None,
            dataset=None,
            ontology=None
    ):
        super().__init__(uuid)
        self.similarity_uuid = similarity
        self.autotag_uuid = autotag
        self.dataset_uuid = dataset
        self.ontology_uuid = ontology

    @classmethod
    def from_document(cls, document):
        return cls(
            document['_id'],
            document['similarity'],
            document['autotag'],
            document['dataset'],
            document['ontology']
        )

    @staticmethod
    def _get_key():
        return 'configuration'

    def get_similarity(self):
        return Similarity.from_uuid(self.similarity_uuid)

    def get_autotag(self):
        return Autotag.from_uuid(self.autotag_uuid)

    def get_dataset(self):
        return Dataset.from_uuid(self.dataset_uuid)

    def get_ontology(self):
        return Ontology.from_uuid(self.ontology_uuid)

    def prepare(self):
        # Ensure all mandatory fields are present
        if self.similarity_uuid is None:
            raise RuntimeError(
                'A configuration must be linked to a similarity graph'
            )

        if self.autotag_uuid is None:
            raise RuntimeError(
                'A configuration must be linked to an autotag graph'
            )

        # Examine the consistency of linked dataset and ontology graphs
        similarity = self.get_similarity()
        sim_dataset = similarity.dataset_uuid
        sim_ontology = similarity.ontology_uuid

        autotag = self.get_autotag()
        auto_dataset = autotag.dataset_uuid
        auto_ontology = autotag.ontology_uuid

        # Test whether the datasets are consistent (or not defined)
        if self.dataset_uuid not in (None, sim_dataset) or \
                sim_dataset != auto_dataset:
            raise RuntimeError(
                'Inconsistency detected in what dataset graph is used by the '
                'configuration, similarity graph and autotag graph'
            )

        # Do the same test for the linked ontology
        if self.ontology_uuid not in (None, sim_ontology) or \
                sim_ontology != auto_ontology:
            raise RuntimeError(
                'Inconsistency detected in what ontology graph is used by the '
                'configuration, similarity graph and autotag graph'
            )

        # If those are not defined for the configuration, fill in from any graph
        if self.dataset_uuid is None:
            self.dataset_uuid = sim_dataset
        if self.ontology_uuid is None:
            self.ontology_uuid = sim_ontology

    def _get_as_document(self):
        document = {
            'similarity': self.similarity_uuid,
            'autotag': self.autotag_uuid,
            'dataset': self.dataset_uuid,
            'ontology': self.ontology_uuid,
        }
        return document


class Graph(DbCollection):
    def __init__(self, uuid=None, graph=None, last_modified=None):
        super().__init__(uuid)
        self.graph = graph
        self.last_modified = last_modified

    @classmethod
    def from_document(cls, document):
        graph = cls._create_graph_from_document(document)

        return cls(
            document['_id'],
            graph,
            document['lastModified']
        )

    @classmethod
    def _create_graph_from_document(cls, document):
        raw_graph = document['rdf'].decode('utf-8')
        graph = create_bound_graph()
        graph.parse(data=raw_graph, format='json-ld')
        return graph

    def prepare(self):
        super().prepare()

        # Ensure all mandatory fields are present
        if self.graph is None:
            raise RuntimeError('The graph itself is missing')

        # Update when this was last modified
        self.last_modified = datetime.datetime.utcnow()

    def _get_as_document(self):
        serialized_graph = self.graph.serialize(format='json-ld')
        return {
            'rdf': serialized_graph,
            'lastModified': self.last_modified,
        }


class Ontology(Graph):
    @staticmethod
    def _get_key():
        return 'ontology'


class Dataset(Graph):
    @staticmethod
    def _get_key():
        return 'dataset'


class DatasetTagging(Graph):
    def __init__(
            self,
            uuid=None,
            graph=None,
            last_modified=None,
            dataset=None,
            ontology=None
    ):
        super().__init__(uuid, graph, last_modified)
        self.dataset_uuid = dataset
        self.ontology_uuid = ontology

    def get_dataset(self):
        return Dataset.from_uuid(self.dataset_uuid)

    def get_ontology(self):
        return Ontology.from_uuid(self.ontology_uuid)

    @classmethod
    def from_document(cls, document):
        graph = cls._create_graph_from_document(document)

        return cls(
            document['_id'],
            graph,
            document['lastModified'],
            document['dataset'],
            document['ontology'],
        )

    def prepare(self):
        super().prepare()

        # Check validity
        dataset_uuid = self._force_get_uuid_for('dataset', self.dataset_uuid)
        if dataset_uuid is None:
            raise RuntimeError(
                'A dataset tagging graph must be associated with a dataset '
                'graph'
            )

        ontology_uuid = self._force_get_uuid_for('ontology', self.ontology_uuid)
        if ontology_uuid is None:
            raise RuntimeError(
                'A dataset tagging graph must be associated with an ontology '
                'graph'
            )

        # Now we can update with any inferred dataset or ontology UUIDs
        self.dataset_uuid = dataset_uuid
        self.ontology_uuid = ontology_uuid

    def _get_as_document(self):
        document = super()._get_as_document()
        document.update({
            'dataset': self.dataset_uuid,
            'ontology': self.ontology_uuid,
        })
        return document


class Similarity(DatasetTagging):
    @staticmethod
    def _get_key():
        return 'similarity'


class Autotag(DatasetTagging):
    @staticmethod
    def _get_key():
        return 'autotag'


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
    if tag not in concept_dict:
        return False

    add_similarity_link()
    node = concept_dict[tag]
    graph.add((ds, SKOS.relatedMatch, node))
    graph.add((ds, QEX.score, Literal(str(score), datatype=XSD.double)))
    update(graph, uuid, **kwargs)
    #output = path.join(app_path + '/db', uuid+'.rdf')
    #graph.serialize(destination=output, format='xml')
    graph.close()
    return True


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
