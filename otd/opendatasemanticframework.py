import os
from utils.graph import RDF, OTD, DCAT, DCT
from otd.skosnavigate import SKOSNavigate
from otd.queryextractor import QueryExtractor
from otd.semscore import SemScore
import db.dataframe
import db.graph
from scipy.spatial.distance import cosine
from sklearn.metrics.pairwise import cosine_similarity
from math import isnan

import pandas as pd
import numpy as np 
from os.path import isfile
import clint.textui.progress


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
            self.cds['all'] = self.cds['all'].append(self.cds[name])
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
                raise RuntimeError(
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
                raise RuntimeError(
                    f'No (up-to-date) existing concept-dataset similarity '
                    f'matrix could be found for the {key} graph with '
                    f'UUID {uuid}, and not set to auto-create it.'
                )

        self.cds[name] = result

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
        
    def get_scorevec(self, query):
        qe = QueryExtractor()
        sscore = SemScore(qe, self.navigator)
        scorevec = sscore.score_vector(query)        
        return scorevec

    def get_dataset_info(self, dataset):
        title = next(self.dataset_graph.objects(dataset, DCT.title), None)
        description = next(self.dataset_graph.objects(dataset, DCT.description), None)
        return (str(title), str(description), str(dataset))

    def query_score_vec(self, query):
        return self.get_scorevec(query)

    def cos_sim(self, query):
        sv = self.get_scorevec(query)
        cds = self.cds[cds_name]
        cs = cosine_similarity(cds.append(sv))
        cols = ['query'] + list(cds.index)
        res = pd.DataFrame(cs, columns=cols, index=cols)
        return res

    def search_query(self, query, cds_name="all"):
        sv = self.get_scorevec(query)
        significant = sorted(list(zip(list(sv.columns),sv.as_matrix()[0])), key=lambda x : x[1], reverse=True)[:5]
        df = sv.append(self.cds[cds_name])
        data = cosine_similarity(df)
        df1 = pd.DataFrame(data, columns=df.index, index=df.index)
        f =  df1.loc[query].sort_values(ascending=False)[1:]
        relvec = []
        for x in f.index:
            data = (list(zip(self.cds[cds_name].loc[x].index, self.cds[cds_name].loc[x].as_matrix())))
            data = sorted(data, key=lambda x:x[1], reverse=True)[:5]
            relvec.append(data)
        xs = zip(f.tolist(), map(self.get_dataset_info, list(f.index)), relvec)
        return ([x for x in xs if x[0] > 0.75], significant)
