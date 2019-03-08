from collections.abc import Mapping
from otd.constants import SIMTYPE_AUTOTAG, SIMTYPE_SIMILARITY
from bson.errors import InvalidId
import warnings
from similarity.csv_parse import get_fragment
from utils.graph import RDF, OTD, DCAT, DCT
from otd.skosnavigate import SKOSNavigate
from otd.queryextractor import QueryExtractor
from otd.semscore import SemScore
import db.dataframe
import db.graph
from sklearn.metrics.pairwise import cosine_similarity
from collections import namedtuple

import pandas as pd
import numpy as np 
import clint.textui.progress


DatasetInfo = namedtuple('DatasetInfo', ('title', 'description', 'uri'))
SearchResult = namedtuple('SearchResult', ('score', 'info', 'concepts'))
ConceptSimilarity = namedtuple('ConceptSimilarity', ('concept', 'similarity'))


class MissingMatrixError(RuntimeError):
    """
    Error indicating that a matrix/DataFrame was expected, but was not found.
    This will only happen when matrices are set to not be generated, and
    indicate that the ontology or similarity tagging graph cannot be used before
    the matrices are (re)generated.
    """
    pass


class OpenDataSemanticFramework:
    def __init__(self, ontology_uuid, dataset_uuid, auto_compute=True):
        """
        The RDF library allows a set of rdf-files to be parsed into
        a graph representing RDF triples. The SKOSNavigate class is
        a tool for navigating between siblings, children and parents in
        a graph, and implements methods for calculating similarity based 
        on the relative position of two concepts.
        """
        self.auto_compute = auto_compute
        self.cds = dict()
        self.ccs = None

        # Set up variables needed for graph property setter
        self.__graph = None
        self.navigator = None
        self.concepts = []

        # Then set graph
        self.load_new_graph(ontology_uuid)

        # Other properties
        self.dataset_graph = db.graph.get_dataset(
            dataset_uuid,
            raise_on_no_uuid=False
        )

    @property
    def graph(self):
        return self.__graph

    @graph.setter
    def graph(self, new_graph):
        self.__graph = new_graph

        # Update dependent properties
        self.navigator = SKOSNavigate(new_graph)
        self.concepts = list(self.navigator.concepts())

    def load_new_graph(self, uuid):
        graph = db.graph.get_ontology(uuid, raise_on_no_uuid=False)
        self.graph = graph
        self.load_ccs(uuid)

    def compute_ccs(self):
        data = []
        for c1 in clint.textui.progress.bar(
            self.concepts,
            'Calculating concept-concept similarity… ',
        ):
            v = []
            for c2 in self.concepts:
                score = self.navigator.sim_wup(c1, c2)
                v.append(score)
            data.append(v)
        ccs = pd.DataFrame(columns=self.concepts, index=self.concepts, data=data)
        return ccs

    def add_similarity_graph(self, name, graph):
        self.cds[name] = self.compute_cds(graph, name)
        if 'all' in self.cds:
            self.cds['all'] = self.cds['all'].append(self.cds[name], sort=True)
        else:
            self.cds['all'] = self.cds[name]

            
    def get_cds(self, name):
        return self.cds[name]

    def get_ccs(self):
        return self.ccs

    # TODO: Clarify what is public and what is private
    # TODO: Make call graph more obvious with method ordering
    def load_ccs(self, uuid, **kwargs):
        graph_id = db.graph.get_dataframe_id('ontology', uuid, False, **kwargs)
        result = db.dataframe.get(graph_id, **kwargs)
        if result is None:
            if self.auto_compute:
                result = self.compute_ccs()
                db.dataframe.store(result, graph_id)
            else:
                raise MissingMatrixError(
                    f'No (up-to-date) existing concept-concept similarity '
                    f'matrix could be found for the ontology graph with UUID '
                    f'{uuid}, and not set to auto-create it.'
                )

        self.ccs = result

    def load_similarity_graph(self, name, key, uuid, **kwargs):
        graph_id = db.graph.get_dataframe_id(key, uuid, False, **kwargs)
        result = db.dataframe.get(graph_id, **kwargs)
        if result is None:
            if self.auto_compute:
                # Create matrix
                # TODO: Find a cleaner solution to using get_uuid_for_collection everywhere
                uuid = db.graph.get_uuid_for_collection(
                    key,
                    uuid,
                    False,
                    'load_similarity_graph'
                )
                sim_graph = db.graph.get(uuid, key)
                result = self.compute_cds(sim_graph, name)
                # Store for next time
                db.dataframe.store(result, graph_id)
            else:
                raise MissingMatrixError(
                    f'No (up-to-date) existing concept-dataset similarity '
                    f'matrix could be found for the {key} graph with '
                    f'UUID {uuid}, and not set to auto-create it.'
                )

        self.cds[name] = result

        self.add_to_all_cdsm(result)

    def add_to_all_cdsm(self, cdsm):
        if 'all' in self.cds:
            self.cds['all'] = self.cds['all'].append(cdsm, sort=True)
        else:
            self.cds['all'] = cdsm

    def compute_cds(self, sgraph, name):
        cds = pd.DataFrame(None, columns=self.concepts)

        # Create zero-vectors for each dataset
        for dataset in self.dataset_graph.subjects(RDF.type, DCAT.Dataset):
            cds.loc[dataset] = np.nan

        # Set similarity values in the cds
        similarities = tuple(sgraph.subjects(RDF.type, OTD.Similarity))
        for similarity in clint.textui.progress.bar(
            similarities,
            f'Constructing concept-dataset similarity matrix for "{name}"… ',
            every=1,
        ):
            dataset = next(sgraph.objects(similarity, OTD.dataset), None)
            concept = next(sgraph.objects(similarity, OTD.concept), None)
            score = (float)(next(sgraph.objects(similarity, OTD.score), np.nan))
            for cs in self.concepts:                
                simscore = (float)(self.ccs[cs][concept])*score
                cds.loc[dataset][cs] = np.nanmax([simscore, cds.loc[dataset][cs]])
        return cds.dropna(thresh=1)

    def datasets(self):
        ds = []
        for dataset in self.dataset_graph.subjects(RDF.type, DCAT.Dataset):
            title = next(self.dataset_graph.objects(dataset, DCT.title), None)
            if title:
                ds.append(title)
        return ds

    def similarities(self):
        ss = []
        for similarity in self.similarity_graph.subjects(RDF.type, OTD.Similarity):
            dataset = next(self.similarity_graph.objects(similarity, OTD.dataset), None)
            concept = next(self.similarity_graph.objects(similarity, OTD.concept), None)
            score = (float)(next(self.similarity_graph.objects(similarity, OTD.score), "0.0"))
            ss.append('{} {} : {}'.format(dataset, concept, score))
        return ss
        
    def calculate_query_sim_to_concepts(self, query):
        qe = QueryExtractor()
        sscore = SemScore(qe, self.navigator)
        scorevec = sscore.score_vector(query)        
        return scorevec

    def get_dataset_info(self, dataset):
        title = next(self.dataset_graph.objects(dataset, DCT.title), None)
        description = next(self.dataset_graph.objects(dataset, DCT.description), None)
        return DatasetInfo(str(title), str(description), str(dataset))

    def query_score_vec(self, query):
        return self.calculate_query_sim_to_concepts(query)

    def cos_sim(self, query):
        sv = self.calculate_query_sim_to_concepts(query)
        cds = self.cds[cds_name]
        cs = cosine_similarity(cds.append(sv))
        cols = ['query'] + list(cds.index)
        res = pd.DataFrame(cs, columns=cols, index=cols)
        return res

    def search_query(self, query, cds_name="all"):
        # Calculate the query's similarity to our concepts
        query_concept_sim = self.calculate_query_sim_to_concepts(query)

        # What were the most similar concepts?
        most_similar_concepts = self.sort_concept_similarities(
            self.get_concept_similarities_for_query(
                query_concept_sim
            )
        )[:5]

        # How similar are the datasets' similarity to the query's similarity?
        dataset_query_sim = self.calculate_dataset_query_sim(
            query_concept_sim,
            cds_name,
            query,
        )

        # Put together information for the search results page
        results = list()
        for dataset, similarity in dataset_query_sim.items():
            # Only consider the most relevant datasets
            if similarity <= 0.75:
                continue
            results.append(SearchResult(
                score=similarity,
                info=self.get_dataset_info(dataset),
                concepts=self.get_most_similar_concepts_for_dataset(
                    cds_name,
                    dataset
                ),
            ))
        return results, most_similar_concepts

    @staticmethod
    def get_concept_similarities_for_query(query_concept_similarity):
        return list(
            map(
                lambda concept, similarity: ConceptSimilarity(
                    concept,
                    similarity
                ),
                list(
                    map(
                        get_fragment,
                        query_concept_similarity.columns
                    )
                ),
                query_concept_similarity.values[0]
            )
        )

    def calculate_dataset_query_sim(self, query_concept_sim, cds_name, query):
        # Add in the datasets' similarity to the concepts
        entry_concept_sim = query_concept_sim.append(
            self.cds[cds_name],
            sort=True
        )

        # Do the similarity calculation
        sim_data = cosine_similarity(entry_concept_sim)

        # Convert into format used by the rest of the application
        entry_entry_sim = pd.DataFrame(
            sim_data,
            columns=entry_concept_sim.index,
            index=entry_concept_sim.index
        )

        # Extract the datasets' similarity to the query, sort most similar
        # datasets first, then remove the query's similarity to itself
        dataset_query_sim = entry_entry_sim \
            .loc[query] \
            .sort_values(ascending=False) \
            .drop(query)
        return dataset_query_sim

    def get_most_similar_concepts_for_dataset(self, cds_name, dataset):
        concepts_for_dataset = self.get_concepts_for_dataset(
            cds_name,
            dataset
        )
        closest_concepts_for_dataset = self.sort_concept_similarities(
            concepts_for_dataset
        )[:5]
        return closest_concepts_for_dataset

    def get_concepts_for_dataset(self, cds_name, dataset):
        return list(
            map(
                lambda concept, similarity: ConceptSimilarity(
                    concept,
                    similarity
                ),
                self.cds[cds_name].loc[dataset].index,
                self.cds[cds_name].loc[dataset].values
            )
        )

    @staticmethod
    def sort_concept_similarities(similarities):
        return sorted(
            similarities,
            key=lambda x: x.similarity,
            reverse=True
        )


class ODSFLoader(Mapping):
    """
    Dictionary where keys are Configuration UUID, while values are instances of
    OpenDataSemanticFramework loaded with the graphs specified by the
    Configuration.

    The OpenDataSemanticFramework instances are lazy loaded, meaning they are
    loaded the first time you access them. Subsequent accesses will re-use the
    existing instance.

    Updates to Configuration will also be picked up, since they will be loaded
    again when their last-modified field changes. This process means you may
    need to run the matrix command periodically to re-generate the matrices.

    Note that updates to the similarity and autotag sets are not currently
    picked up automatically.
    """
    DEFAULT_KEY = 'default'

    def __init__(self, compute_matrices=False):
        self.compute_matrices = compute_matrices
        self.__instances = dict()
        self.__configurations = dict()

    def __getitem__(self, k):
        if k is None:
            raise KeyError(k)

        if k == self.DEFAULT_KEY:
            k = db.graph.Configuration.force_find_uuid(None)

        if k in self.__configurations:
            # Are we up to date?
            our_c = self.__configurations[k]
            newest_c = self._get_config_for(k)
            update_available = our_c == newest_c
        else:
            update_available = False

        if k not in self.__instances or update_available:
            try:
                configuration = self._get_config_for(k)
                self.__instances[k] = self._create_from_configuration(
                    configuration
                )
                self.__configurations[k] = configuration
            except (db.graph.NoSuchGraph, InvalidId):
                raise KeyError(k)
            except MissingMatrixError:
                if update_available:
                    # De-escalate to warning, since we have the old version
                    warnings.warn(
                        'New Configuration instance for {} is missing one or '
                        'more matrices. Falling back to previously loaded '
                        'version.'.format(k)
                    )
                else:
                    raise

        return self.__instances[k]

    def __len__(self) -> int:
        return len(db.graph.Configuration.find_all_ids())

    def __iter__(self):
        return iter(db.graph.Configuration.find_all_ids())

    def _get_config_for(self, key):
        return db.graph.Configuration.from_uuid(key)

    def _create_from_configuration(self, c):
        odsf = OpenDataSemanticFramework(
            c.ontology_uuid,
            c.dataset_uuid,
            self.compute_matrices
        )
        odsf.load_similarity_graph(
            SIMTYPE_SIMILARITY,
            'similarity',
            c.similarity_uuid
        )
        odsf.load_similarity_graph(
            SIMTYPE_AUTOTAG,
            'autotag',
            c.autotag_uuid
        )
        return odsf

    def get_default(self) -> OpenDataSemanticFramework:
        """
        Get the ODSF using the configuration named in the CONFIGURATION_UUID
        environment variable (referred to as the default configuration).

        Returns:
            The ODSF instance loaded using the default configuration.
        """
        return self[self.DEFAULT_KEY]

    def ensure_default_is_loaded(self):
        """
        Ensure the ODSF with the default configuration is loaded.

        Returns:
            Nothing.
        """
        _ = self.get_default()

    def ensure_all_loaded(self):
        """
        Ensure all available configurations are loaded.

        This is useful when generating matrices, since it will ensure all
        matrices are generated.

        Otherwise, note that new configurations may be added between this being
        called and that configuration being put into use, thus they may be
        dynamically loaded at that time.

        Only call this when strictly necessary.

        Returns:
            Nothing.
        """
        for uuid, odsf in self.items():
            # We just wanted to load the odsf instance, so do nothing
            pass
