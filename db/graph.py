import datetime
import os
import warnings
from abc import ABCMeta, abstractmethod
from collections import namedtuple

from bson.objectid import ObjectId

import db.dataframe
from utils.db import MongoDBConnection
from utils.dotenv import ensure_loaded_dotenv
from utils.graph import create_bound_graph, RDF, SKOS
from utils.misc import first, second


DataFrameId = namedtuple(
    'DataFrameId', (
        'graph_type',
        'graph_uuid',
        'last_modified',
        'other_parameters'
    )
)


class MissingUuidWarning(Warning):
    """
    No UUID has been specified by the user.

    This is not an error, since the first result returned by MongoDB will be
    used as a fallback/shortcut.

    This can be fine in some cases, but you'll usually want to specify UUIDs
    explicitly through environment variables or the use of a configuration, to
    avoid problems with unpredictable results once more than one entry exists.
    """
    pass


class NoSuchGraph(Exception):
    """
    No graph was found with the given UUID, or no graph exists.
    """
    pass


class DbCollection(metaclass=ABCMeta):
    """
    Generic class for any MongoDB collection in DataOntoSearch.
    """
    def __init__(self, uuid=None):
        """
        Create new instance of a class for any MongoDB collection.

        Args:
            uuid: UUID associated with this document.
        """
        self.uuid = uuid
        """The UUID associated with this document."""

    @staticmethod
    @abstractmethod
    def get_collection_name():
        """
        Get the name of the collection associated with this class.

        This is used to find out which collection to fetch and store documents
        in when interacting with this class.

        Returns:
            The name of the collection associated with this class.
        """
        return ''

    @classmethod
    def from_uuid(cls, uuid=None, **kwargs):
        """
        Fetch an instance of this class from the database.

        Args:
            uuid: UUID of the instance to fetch. If not given, an environment
                variable named <COLLECTION_NAME>_UUID will be used. If that one
                does not exist, a MissingUuidWarning will be emitted and the
                first instance returned from the database is used.
            **kwargs: Extra keyword arguments to give to MongoDBConnection.

        Returns:
            An instance of this class, filled with information from the
            database.

        Warnings:
            MissingUuidWarning: If no UUID is given as an argument or an
                environment variable.

        Raises:
            ValueError: If no document with the specified UUID can be found, or
                if no document exists when not specifying the UUID.
        """
        collection_name = cls.get_collection_name()
        uuid = cls.find_uuid(uuid)

        criteria = None
        if uuid is not None:
            criteria = {'_id': ObjectId(uuid)}

        with MongoDBConnection(**kwargs) as client:
            db = client.ontodb
            collection = getattr(db, collection_name)

            document = collection.find_one(criteria)

            if document is None:
                raise ValueError(
                    'No {} found with the UUID "{}"'
                        .format(collection_name, uuid)
                )
        return cls.from_document(document)

    @classmethod
    @abstractmethod
    def from_document(cls, document):
        """
        Create a new instance of this class, using the retrieved document.

        Args:
            document: Document retrieved from this class' collection in the DB.

        Returns:
            An instance of this class, filled with details from the document.
        """
        return cls(str(document['_id']))

    @classmethod
    def find_uuid(cls, uuid=None):
        """
        Find the UUID to look up, using the collection associated with this
        class.

        If the UUID has not been specified, it will be retrieved from an
        environment variable named <COLLECTION_NAME>_UUID.

        Args:
            uuid: Potentially a UUID, in which case it will be used as-is.

        Returns:
            The UUID to use, or None if the first result from MongoDB should be
            used.
        """
        collection_name = cls.get_collection_name()
        return cls._get_uuid_for(collection_name, uuid)

    @staticmethod
    def _get_uuid_for(collection_name, uuid=None):
        """
        Find the UUID to look up, using the given collection.

        If the UUID has not been specified, it will be retrieved from an
        environment variable named <COLLECTION_NAME>_UUID.

        Args:
            collection_name: Name of the MongoDB collection to find a UUID for.
            uuid: Potentially a UUID, in which case it will be used as-is.

        Returns:
            The UUID to use, or None if the first result from MongoDB should be
            used.
        """
        envvar = '{}_UUID'.format(collection_name.upper())

        # No UUID given? Were we given one by environment variables?
        if uuid is None:
            ensure_loaded_dotenv()
            uuid = os.environ.get(envvar)

        if uuid is None:
            warnings.warn(
                'No UUID specified when fetching {}. Using '
                'whatever MongoDB returns first'.format(collection_name),
                MissingUuidWarning,
                2
            )
        return uuid

    @classmethod
    def force_find_uuid(cls, uuid=None, **kwargs):
        """
        Do a look-up to find the UUID which would have been found when fetching
        an instance of this class using the given UUID.

        This goes one step further than find_uuid, since it will query the
        database to find the UUID. This is not necessary when simply wanting to
        fetch one entry.

        Args:
            uuid: Potentially a UUID, in which case it will be used as-is and
                not checked for validity.
            **kwargs: Extra keyword arguments to give to MongoDBConnection.

        Returns:
            The UUID of the document that would have been returned when calling
            from_uuid on this class.
        """
        return cls._force_get_uuid_for(cls.get_collection_name(), uuid, **kwargs)

    @classmethod
    def _force_get_uuid_for(cls, collection_name, uuid=None, **kwargs):
        """
        Do a look-up to find the UUID which would have been found when fetching
        a document for the given collection and UUID.

        This goes one step further than _get_uuid_for, since it will query the
        database to find the UUID. This is not necessary when simply wanting to
        fetch one entry.

        Args:
            collection_name: Name of the MongoDB collection to find a UUID for.
            uuid: Potentially a UUID, in which case it will be used as-is and
                not checked for validity.
            **kwargs: Extra keyword arguments to give to MongoDBConnection.

        Returns:
            The UUID of the document that would have been returned when fetching
            one document for the given collection and UUID.
        """
        uuid = cls._get_uuid_for(collection_name, uuid)
        if uuid is not None:
            return uuid

        # We're using whatever MongoDB returns first, so find that
        with MongoDBConnection(**kwargs) as client:
            db = client.ontodb
            collection = getattr(db, collection_name)
            first_document = collection.find_one({})
            if first_document is None:
                return None
            return str(first_document['_id'])

    def prepare(self):
        """
        Validate this object and set any automatically derived properties.

        This is called in preparation of saving the object.
        """
        pass

    def save(self, **kwargs):
        """
        Save this object to the database.

        If a UUID is associated with this object, any document in the database
        collection with the same UUID will be replaced.

        If no UUID is associated with this object, it will be inserted as a new
        document in the database collection. Its new UUID, assigned by MongoDB,
        will be associated with this object and returned.

        Args:
            **kwargs: Extra keyword arguments to give to MongoDBConnection.

        Returns:
            The UUID of the saved object.
        """
        self.prepare()

        if self.uuid is None:
            uuid = self._save_as_new(**kwargs)
            self.uuid = uuid
            return uuid
        else:
            return self._save_with_uuid(self.uuid, **kwargs)

    def _save_as_new(self, **kwargs):
        """
        Save this object to the database collection as a new document.
        """
        document = self._get_as_document()
        with MongoDBConnection(**kwargs) as client:
            db = client.ontodb
            collection = getattr(db, self.get_collection_name())
            assigned_id = collection.insert_one(document).inserted_id
        return str(assigned_id)

    def _save_with_uuid(self, uuid, **kwargs):
        """
        Save this object to the database collection using the given UUID.
        """
        document = self._get_as_document()
        with MongoDBConnection(**kwargs) as client:
            db = client.ontodb
            collection = getattr(db, self.get_collection_name())
            collection.replace_one(
                {'_id': ObjectId(uuid)},
                document,
                upsert=True,
            )
        return uuid

    def remove(self, **kwargs):
        """
        Remove this object from the database.

        Args:
            **kwargs: Extra keyword arguments to give to MongoDBConnection.

        Returns:
            True if an object was removed, False if not.

        Raises:
            RuntimeError: when this object has not been given a UUID.
        """
        if self.uuid is None:
            raise RuntimeError('Cannot remove document that has not been put '
                               'into the database (UUID is missing)')

        return self.remove_by_uuid(self.uuid, **kwargs)

    @classmethod
    def remove_by_uuid(cls, uuid, **kwargs):
        """
        Remove the document with the given UUID from the database collection.

        Args:
            uuid: The UUID of the document to remove from the database.
            **kwargs: Extra keyword arguments to give to MongoDBConnection.

        Returns:
            True if a document was actually removed, False if not.
        """
        with MongoDBConnection(**kwargs) as client:
            db = client.ontodb
            collection = getattr(db, cls.get_collection_name())
            r = collection.delete_one({'_id': ObjectId(uuid)})
            num_deleted = r.deleted_count
        return num_deleted > 0

    @classmethod
    def find_all_ids(cls, **kwargs):
        """
        Return the UUIDs of all documents in the database collection.

        Args:
            **kwargs: Extra keyword arguments to give to MongoDBConnection.

        Returns:
            List of UUIDs, one for each document in the database collection.
        """
        with MongoDBConnection(**kwargs) as client:
            db = client.ontodb
            collection = getattr(db, cls.get_collection_name())
            ids = [str(i) for i in collection.distinct('_id')]
        return ids

    @abstractmethod
    def _get_as_document(self):
        """
        Create a document out of this object that can be saved to the database.

        Returns:
            A dictionary with the data that will be saved to the database.
        """
        return dict()


class Configuration(DbCollection):
    """
    A set of associated similarity, autotag, ontology and dataset graphs.

    This is generally used for public-facing parts of the application, like the
    dataset tagger and the search.
    """
    def __init__(
            self,
            uuid=None,
            label=None,
            similarity=None,
            autotag=None,
            dataset=None,
            ontology=None
    ):
        """
        Create a new set of associated graphs that go together.

        Args:
            uuid: UUID of this configuration.
            label: Human-readable label for this configuration.
            similarity: UUID of the associated similarity graph.
            autotag: UUID of the associated autotag graph.
            dataset: UUID of the associated dataset graph.
            ontology: UUID of the associated ontology graph.
        """
        super().__init__(uuid)

        self.label = label
        """
        Human-readable label for this configuration.
        """

        self.similarity_uuid = similarity
        """
        UUID of the associated similarity graph.
        """

        self.autotag_uuid = autotag
        """
        UUID of the associated autotag graph.
        """

        self.dataset_uuid = dataset
        """
        UUID of the associated dataset graph.
        """

        self.ontology_uuid = ontology
        """
        UUID of the associated ontology graph.
        """

    @classmethod
    def from_document(cls, document):
        return cls(
            str(document['_id']),
            document.get('label'),
            document['similarity'],
            document['autotag'],
            document['dataset'],
            document['ontology']
        )

    @staticmethod
    def get_collection_name():
        return 'configuration'

    def get_similarity(self):
        """
        Get the Similarity instance linked by this configuration.

        Returns:
            Instance of the Similarity graph associated with this configuration.
        """
        return Similarity.from_uuid(self.similarity_uuid)

    def get_autotag(self):
        """
        Get the Autotag instance linked by this configuration.

        Returns:
            Instance of the Autotag graph associated with this configuration.
        """
        return Autotag.from_uuid(self.autotag_uuid)

    def get_dataset(self):
        """
        Get the Dataset instance linked by this configuration.

        Returns:
            Instance of the Dataset graph associated with this configuration.
        """
        return Dataset.from_uuid(self.dataset_uuid)

    def get_ontology(self):
        """
        Get the Ontology instance linked by this configuration.

        Returns:
            Instance of the Ontology graph associated with this configuration.
        """
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
            'label': self.label,
            'similarity': self.similarity_uuid,
            'autotag': self.autotag_uuid,
            'dataset': self.dataset_uuid,
            'ontology': self.ontology_uuid,
        }
        return document

    def __eq__(self, other):
        return (
            isinstance(other, Configuration) and
            # Are the UUIDs the same?
            self.similarity_uuid == other.similarity_uuid and
            self.autotag_uuid == other.autotag_uuid and
            self.dataset_uuid == other.dataset_uuid and
            self.ontology_uuid == other.ontology_uuid
        )

    def has_available_update(self, last_modified):
        """
        Check whether there have been any changes to any of the graphs after the
        given last_modified time.

        Args:
            last_modified: Check if any graph has been changed since this date.

        Returns:
            True if there have been updates, False if not.
        """
        return

    def get_latest_modified_date(self):
        return max([
            self.get_similarity().last_modified,
            self.get_autotag().last_modified,
            self.get_dataset().last_modified,
            self.get_ontology().last_modified,
        ])


class Graph(DbCollection):
    """A class representing a generic RDF graph."""

    def __init__(self, uuid=None, graph=None, last_modified=None, raw_graph=None):
        """
        Create a new instance of an RDF graph from the database.

        Args:
            uuid: UUID of this RDF graph.
            graph: The instantiated RDF graph.
            last_modified: Date of when this graph was last modified.
            raw_graph: Raw JSON-ld graph returned by MongoDB. Used to lazy load
                the graph later and not at instantiation time.
        """
        super().__init__(uuid)

        self.__graph = graph
        """The instantiated RDF graph."""

        self.last_modified = last_modified
        """The time when this graph was last modified."""

        self.__raw_graph = raw_graph

    @property
    def graph(self):
        """The instantiated RDF graph. Is lazy loaded upon access."""
        # Return the lazily loaded graph if it is loaded, or load it now
        if self.__graph is None:
            # Is there even any graph to load?
            if self.__raw_graph is None:
                # Nope
                return None
            # Load the graph lazily
            self.__graph = self._create_graph(self.__raw_graph)
            # Don't keep the raw graph in memory
            self.__raw_graph = None
        return self.__graph

    @graph.setter
    def graph(self, value):
        self.__graph = value

    @classmethod
    def from_document(cls, document):
        return cls(
            str(document['_id']),
            last_modified=document['lastModified'],
            raw_graph=document['rdf'],
        )

    @classmethod
    def _create_graph(cls, raw_graph):
        """
        Helper method for parsing and instantiating a graph from RDF JSON-ld.

        Args:
            raw_graph: Raw JSON-ld graph returned by MongoDB.

        Returns:
            An RDF-lib graph with its contents taken from the given RDF JSON-ld.
        """
        raw_graph = raw_graph.decode('utf-8')
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
            # TODO: Parse last_modified in a way, so it is native Python datetime
            'lastModified': self.last_modified,
        }


class Ontology(Graph):
    """
    An RDF graph detailing the concepts and their hierarchy.
    """

    @staticmethod
    def get_collection_name():
        return 'ontology'

    def get_concepts(self):
        concepts = dict()

        for concept_uri in self.graph.subjects(RDF.type, SKOS.Concept):
            label = str(second(first(
                self.graph.preferredLabel(concept_uri, lang='en')
            )))
            concepts[label] = concept_uri
        return concepts

    def get_dataframe(self, **kwargs):
        identifier = self._get_df_id()
        return db.dataframe.get(identifier, **kwargs)

    def save_dataframe(self, df, **kwargs):
        identifier = self._get_df_id()
        return db.dataframe.store(df, identifier, **kwargs)

    def _get_df_id(self):
        return DataFrameId(
            self.get_collection_name(),
            self.uuid,
            self.last_modified,
            tuple(),
        )


class Dataset(Graph):
    """
    An RDF graph detailing the datasets that can be searched for.
    """
    @staticmethod
    def get_collection_name():
        return 'dataset'


class DatasetTagging(Graph):
    """
    Any RDF graph whose purpose is to associate datasets with concepts in the
    ontology.
    """
    def __init__(
            self,
            uuid=None,
            graph=None,
            last_modified=None,
            raw_graph=None,
            dataset=None,
            ontology=None
    ):
        """
        Create a new instance of any RDF graph used to tag datasets with
        concepts.

        Args:
            uuid: UUID of this RDF graph.
            graph: The instantiated RDF graph.
            last_modified: Date of when this graph was last modified.
            raw_graph: Raw JSON-ld graph returned by MongoDB. Used to lazy load
                the graph later and not at instantiation time.
            dataset: UUID of the associated dataset graph.
            ontology: UUID of the associated ontology graph.
        """
        super().__init__(uuid, graph, last_modified, raw_graph)

        self.dataset_uuid = dataset
        """UUID of the associated dataset graph."""

        self.ontology_uuid = ontology
        """UUID of the associated ontology graph."""

    def get_dataset(self):
        """
        Get the Dataset instance linked by this configuration.

        Returns:
            Instance of the Dataset graph associated with this configuration.
        """
        return Dataset.from_uuid(self.dataset_uuid)

    def get_ontology(self):
        """
        Get the Ontology instance linked by this configuration.

        Returns:
            Instance of the Ontology graph associated with this configuration.
        """
        return Ontology.from_uuid(self.ontology_uuid)

    @classmethod
    def from_document(cls, document):
        return cls(
            str(document['_id']),
            None,
            document['lastModified'],
            document['rdf'],
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

    def get_dataframe(self, concept_similarity, **kwargs):
        identifier = self._get_df_id(concept_similarity)
        return db.dataframe.get(identifier, **kwargs)

    def save_dataframe(self, df, concept_similarity, **kwargs):
        identifier = self._get_df_id(concept_similarity)
        return db.dataframe.store(df, identifier, **kwargs)

    def _get_df_id(self, concept_similarity):
        return DataFrameId(
            self.get_collection_name(),
            self.uuid,
            self.last_modified,
            (concept_similarity, )
        )


class Similarity(DatasetTagging):
    """
    RDF graph with manually created links between datasets and relevant
    concepts.
    """
    @staticmethod
    def get_collection_name():
        return 'similarity'


class Autotag(DatasetTagging):
    """
    RDF graph with automatically created links between datasets and relevant
    concepts.
    """
    @staticmethod
    def get_collection_name():
        return 'autotag'
