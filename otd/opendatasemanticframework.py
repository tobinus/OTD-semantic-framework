import itertools
from collections.abc import Mapping
from otd.constants import SIMTYPE_AUTOTAG, SIMTYPE_SIMILARITY
from bson.errors import InvalidId
import logging
from rdflib import URIRef
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

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
sh = logging.StreamHandler()
log.addHandler(sh)
sh.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))


DatasetInfo = namedtuple('DatasetInfo', ('title', 'description', 'uri', 'href'))
SearchResult = namedtuple('SearchResult', ('score', 'info', 'concepts'))
# Note: 'info' is just dataset RDF IRI when dataset_info is disabled
ConceptSimilarity = namedtuple(
    'ConceptSimilarity',
    ('uri', 'label', 'similarity')
)


class MissingMatrixError(RuntimeError):
    """
    Error indicating that a matrix/DataFrame was expected, but was not found.
    This will only happen when matrices are set to not be generated, and
    indicate that the ontology or similarity tagging graph cannot be used before
    the matrices are (re)generated.
    """
    pass


class OpenDataSemanticFramework:
    def __init__(self, ontology_uuid, dataset_uuid, auto_compute=True,
                 concept_similarity=0.0):
        """
        The RDF library allows a set of rdf-files to be parsed into
        a graph representing RDF triples. The SKOSNavigate class is
        a tool for navigating between siblings, children and parents in
        a graph, and implements methods for calculating similarity based 
        on the relative position of two concepts.
        """
        self.auto_compute = auto_compute
        self.cds = dict()
        self.cds_df_id = dict()
        self.ccs = None
        self.concept_similarity = concept_similarity

        # Set up variables needed for graph property setter
        self.__graph = None
        self.navigator = None
        self.concepts = []
        self.ontology = None
        self.dataset = None
        self._qe = QueryExtractor()
        self._semscore = None

        # Then set graph
        self.load_new_graph(ontology_uuid)

        # Other properties
        self.dataset_graph = db.graph.Dataset.from_uuid(dataset_uuid).graph

    @property
    def graph(self):
        return self.__graph

    @graph.setter
    def graph(self, new_graph):
        self.__graph = new_graph

        # Update dependent properties
        self.navigator = SKOSNavigate(new_graph)
        self.concepts = list(self.navigator.concepts())
        self._semscore = SemScore(self._qe, self.navigator)

    def load_new_graph(self, uuid):
        self.ontology = db.graph.Ontology.from_uuid(uuid)
        graph = self.ontology.graph
        self.graph = graph
        self.load_ccs(self.ontology)

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
        ccs = pd.DataFrame(
            columns=self.concepts,
            index=self.concepts,
            data=data
        )
        return ccs

    def get_cds(self, name):
        return self.cds[name]

    def get_ccs(self):
        return self.ccs

    # TODO: Clarify what is public and what is private
    # TODO: Make call graph more obvious with method ordering
    def load_ccs(self, ontology, **kwargs):
        result = ontology.get_dataframe(**kwargs)
        if result is None:
            if self.auto_compute:
                result = self.compute_ccs()
                ontology.save_dataframe(result)
            else:
                raise MissingMatrixError(
                    f'No (up-to-date) existing concept-concept similarity '
                    f'matrix could be found for the ontology graph with UUID '
                    f'{ontology.uuid}, and not set to auto-create it.'
                )

        self.ccs = result

    def load_similarity_graph(
            self,
            name,
            dataset_tagging: db.graph.DatasetTagging,
            **kwargs
    ):
        similarity_threshold = float(self.concept_similarity)
        result = dataset_tagging.get_dataframe(
            similarity_threshold,
            **kwargs
        )

        if result is None:
            if self.auto_compute:
                # Create matrix
                sim_graph = dataset_tagging.graph
                result = self.compute_cds(sim_graph, name, similarity_threshold)
                # Store for next time
                dataset_tagging.save_dataframe(
                    result,
                    similarity_threshold,
                    **kwargs
                )
            else:
                raise MissingMatrixError(
                    f'No (up-to-date) existing concept-dataset similarity '
                    f'matrix (Tc={similarity_threshold}) could be found for '
                    f'the {dataset_tagging.get_collection_name()} graph with UUID '
                    f'{dataset_tagging.uuid}, and not set to auto-create it.'
                )

        self.cds[name] = result
        self.cds_df_id[name] = dataset_tagging.get_df_id(
            similarity_threshold
        )

        self.add_to_all_cdsm(result)

    def add_to_all_cdsm(self, cdsm):
        if 'all' in self.cds:
            self.cds['all'] = self.cds['all'].append(cdsm, sort=True)
        else:
            self.cds['all'] = cdsm

    def compute_cds(self, sgraph, name, similarity_threshold):
        cds = pd.DataFrame(None, columns=self.concepts)

        # Create zero-vectors for each dataset
        for dataset in self.dataset_graph.subjects(RDF.type, DCAT.Dataset):
            cds.loc[dataset] = np.nan

        # Set similarity values in the cds
        similarities = tuple(sgraph.subjects(RDF.type, OTD.Similarity))
        for similarity in clint.textui.progress.bar(
                similarities,
                f'Constructing concept-dataset similarity matrix for '
                f'"{name}"… ',
                every=1,
        ):
            dataset = next(sgraph.objects(similarity, OTD.dataset), None)
            concept = next(sgraph.objects(similarity, OTD.concept), None)
            score = (float)(next(sgraph.objects(similarity, OTD.score), np.nan))
            for cs in self.concepts:
                simscore = (float)(self.ccs[cs][concept]) * score

                # Only associate dataset with concepts above Tc (concept-dataset
                # similarity threshold)
                if simscore < similarity_threshold:
                    simscore = 0.0
                cds.loc[dataset][cs] = np.nanmax(
                    [simscore, cds.loc[dataset][cs]]
                )
        return cds.dropna(thresh=1)

    def enrich_query_with_ccs(self, score_vec, query, similarity_threshold):
        new_score_vec = score_vec.copy()
        print('Index for score_vec:', new_score_vec.index)
        query_row = score_vec.loc[query]
        new_query_row = new_score_vec.loc[query]

        for c1, c2 in itertools.permutations(self.concepts, 2):
            simscore = (float)(self.ccs[c1][c2]) * query_row[c1]

            if simscore < similarity_threshold:
                simscore = 0.0

            new_query_row[c2] = np.nanmax(
                [simscore, new_query_row[c2]]
            )
        return new_score_vec


    def datasets(self):
        ds = []
        for dataset in self.dataset_graph.subjects(RDF.type, DCAT.Dataset):
            title = next(self.dataset_graph.objects(dataset, DCT.title), None)
            if title:
                ds.append(title)
        return ds

    def calculate_query_sim_to_concepts(self, query, sim_threshold):
        scorevec = self._semscore.score_vector(query, sim_threshold)
        scorevec = self.enrich_query_with_ccs(scorevec, query, self.concept_similarity)
        return scorevec

    def get_dataset_info(self, dataset):
        title = next(self.dataset_graph.objects(dataset, DCT.title), None)
        description = next(
            self.dataset_graph.objects(dataset, DCT.description),
            None
        )
        href = next(
            self.dataset_graph.objects(dataset, DCAT.landingPage),
            dataset
        )
        return DatasetInfo(
            str(title),
            str(description),
            str(dataset),
            str(href)
        )

    def search_query(
            self,
            query,
            cds_name="all",
            qc_sim_threshold=0.0,
            score_threshold=0.75,
            include_dataset_info=True,
            include_concepts=True,
    ):
        """
        Perform a search query.

        Args:
            query: Search query to use.
            cds_name: Name of concept-dataset tagging to use when retrieving
                datasets.
            qc_sim_threshold: Lower threshold for how similar a word in the
                query must be to a concept label in order for that concept to
                be considered relevant to the query.
            score_threshold: Lower threshold for how similar a dataset must
                be to the query to be included in the result. This effectively
                decides how many datasets are included.
            include_dataset_info: Set to False to disable collection of dataset
                information. Should save some time in situations where that
                information is not needed.
            include_concepts: Set to False to disable collection of concepts
                related to the query and to each returned dataset. Should save
                some time in situations where that information is not needed.

        Returns:
            A tuple. The first item is a list of SearchResult that matched,
            sorted with the most similar results first. The second item is a
            list of the top five concepts that were matched with the query.
        """
        log.info('Binding query to concepts…')
        # Calculate the query's similarity to our concepts
        query_concept_sim = self.calculate_query_sim_to_concepts(
            query,
            qc_sim_threshold
        )

        log.info('Extracting most similar concepts…')
        # What were the most similar concepts?
        if include_concepts:
            most_similar_concepts = self.sort_concept_similarities(
                self.get_concept_similarities_for_query(
                    query_concept_sim
                )
            )[:5]
        else:
            most_similar_concepts = []

        log.info('Comparing datasets to the concepts extracted from the query…')
        # How similar are the datasets' similarity to the query's similarity?
        dataset_query_sim = self.calculate_dataset_query_sim(
            query_concept_sim,
            cds_name,
            query,
        )

        log.info('Putting together information for the result…')
        # Put together information for the search results page
        results = list()
        for dataset, similarity in dataset_query_sim.items():
            # Only consider the most relevant datasets
            if similarity < float(score_threshold):
                continue
            results.append(SearchResult(
                score=similarity,
                info=self.get_dataset_info(dataset)
                if include_dataset_info else dataset,
                concepts=self.get_most_similar_concepts_for_dataset(
                    cds_name,
                    dataset
                ) if include_concepts else [],
            ))
        log.info('Done with query processing!')
        return results, most_similar_concepts

    def get_concept_similarities_for_query(self, query_concept_similarity):
        return self._create_concept_similarities(
            query_concept_similarity.columns,
            query_concept_similarity.values[0]
        )

    def _create_concept_similarities(self, concepts, similarity_scores):
        processed_similarities = []

        concept_similarities = zip(
            concepts,
            similarity_scores,
        )

        for concept, similarity in concept_similarities:
            labels = self.navigator.pref_and_alt_labels(URIRef(concept))
            label = labels[0]

            processed_similarities.append(ConceptSimilarity(
                concept, label, similarity
            ))

        return processed_similarities

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
        location = self.cds[cds_name].loc[dataset]
        return self._create_concept_similarities(
            location.index,
            location.values
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

    Updates to Configuration and autotag and similarity graphs will be picked
    up, since they will be loaded again when their last-modified field changes.
    This process means you may need to run the matrix command periodically to
    re-generate the matrices.
    """
    DEFAULT_KEY = 'default'

    def __init__(
            self,
            compute_matrices=False,
            concept_similarity=0.0,
            simtypes=None,
    ):
        """
        Create new ODSF loader.

        Args:
            compute_matrices: Flag indicating whether new CCS and CDS matrices
                should be generated when missing.
            concept_similarity: A lower threshold for how similar a concept must
                be to a dataset in order to be associated with it.
            simtypes: List of simtypes to load. Can also be just the name of one
                simtype. By default, all available simtypes are loaded.
        """
        self.compute_matrices = compute_matrices
        self._concept_similarity = concept_similarity

        self.__simtypes = None
        if simtypes is None:
            simtypes = (SIMTYPE_SIMILARITY, SIMTYPE_AUTOTAG)
        self.simtypes = simtypes

        self.__instances = dict()
        self.__configurations = dict()

    @property
    def simtypes(self):
        return self.__simtypes

    @simtypes.setter
    def simtypes(self, value):
        # Normalize so it's always an iterable
        if isinstance(value, str):
            value = [value]

        # Are there any unrecognized simtypes? Report them now, to avoid subtle
        # bugs later on
        available_simtypes = {SIMTYPE_SIMILARITY, SIMTYPE_AUTOTAG}
        chosen_simtypes = set(value)
        unrecognized_simtypes = chosen_simtypes - available_simtypes
        if unrecognized_simtypes:
            raise ValueError(
                f'Unrecognized simtypes {unrecognized_simtypes} detected, '
                f'please only use simtypes among these: {available_simtypes}'
            )

        # All fine
        self.__simtypes = value

    def __getitem__(self, k):
        if k is None:
            raise KeyError(k)

        if k == self.DEFAULT_KEY:
            k = db.graph.Configuration.force_find_uuid(None)

        odsf_exists = k in self.__configurations

        if odsf_exists:
            # Are we up to date?
            our_c = self.__configurations[k]
            newest_c = self._get_config_for(k)
            update_available = our_c != newest_c
        else:
            update_available = False

        if (not odsf_exists) or update_available:
            try:
                configuration = self._get_config_for(k)
                self.__instances[k] = self._create_from_configuration(
                    configuration
                )
                self.__configurations[k] = configuration
            except (db.graph.NoSuchGraph, InvalidId):
                raise KeyError(k)
            except MissingMatrixError:
                if odsf_exists:
                    # De-escalate to warning, since we have the old version
                    log.warning(
                        'New Configuration instance for {} is missing one or '
                        'more matrices. Falling back to previously loaded '
                        'version.'.format(k)
                    )
                else:
                    raise
        else:
            # The ODSF instance exists, and the configuration is unchanged.
            # Ensure the dataset tagging graphs are up-to-date
            configuration = self._get_config_for(k)
            try:
                self._ensure_updated_dataset_taggings(
                    self.__instances[k],
                    configuration
                )
            except MissingMatrixError:
                # De-escalate to warning, since we have the existing dataset tag
                log.warning(
                    'There have been made changes to one of the dataset '
                    'taggings (similarity or autotag) after the Configuration '
                    'for {} was loaded, but the matrices have not been updated '
                    'yet. The changes can only be taken into effect once the '
                    'matrices are updated through the matrix subcommand.'
                    .format(k)
                )

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
            self.compute_matrices,
            self._concept_similarity,
        )
        if SIMTYPE_SIMILARITY in self.simtypes:
            odsf.load_similarity_graph(
                SIMTYPE_SIMILARITY,
                c.get_similarity(),
            )
        if SIMTYPE_AUTOTAG in self.simtypes:
            odsf.load_similarity_graph(
                SIMTYPE_AUTOTAG,
                c.get_autotag(),
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

    def _ensure_updated_dataset_taggings(
            self,
            odsf: OpenDataSemanticFramework,
            configuration,
    ):
        """
        Ensure the ODSF instance has up-to-date dataset taggings (sim graphs).

        Args:
            odsf: ODSF instance to ensure has up-to-date dataset tags.
            configuration: Up-to-date Configuration instance which can be used
                to find the relevant dataset taggings.

        Returns:
            Nothing.
        """

        for dataset_tagging, name in (
                (configuration.get_similarity(), SIMTYPE_SIMILARITY),
                (configuration.get_autotag(), SIMTYPE_AUTOTAG)
        ):
            existing_df_id = odsf.cds_df_id.get(name)
            current_df_id = dataset_tagging.get_df_id(self._concept_similarity)

            if existing_df_id != current_df_id:
                # Update is required! Simply try loading the new graph
                odsf.load_similarity_graph(
                    name,
                    dataset_tagging,
                )
