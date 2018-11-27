from utils.graph import RDF, OTD, DCAT, DCT
from otd.skosnavigate import SKOSNavigate
from otd.queryextractor import QueryExtractor
from otd.semscore import SemScore
import db.dataframe
from scipy.spatial.distance import cosine
from sklearn.metrics.pairwise import cosine_similarity
from math import isnan

import pandas as pd
import numpy as np 
from os.path import isfile


class OpenDataSemanticFramework:
    def __init__(self, ontology, dataset_graph, compute_ccs=True):
        """
        The RDF library allows a set of rdf-files to be parsed into
        a graph representing RDF triples. The SKOSNavigate class is
        a tool for navigating between siblings, children and parents in
        a graph, and implements methods for calculating similarity based 
        on the relative position of two concepts.
        """
        self.graph            = ontology
        self.dataset_graph    = dataset_graph        
        self.navigator        = SKOSNavigate(self.graph)
        self.concepts         = list(self.navigator.concepts())

        if compute_ccs:
            self.ccs = self.compute_ccs()
        else:
            self.ccs = None

        self.cds = {}

    def compute_ccs(self):
        data = []
        for c1 in self.concepts:
            v = []
            for c2 in self.concepts:
                score = self.navigator.sim_wup(c1, c2)
                v.append(score)
            data.append(v)
        ccs = pd.DataFrame(columns=self.concepts, index=self.concepts, data=data)
        return ccs

    def add_similarity_graph(self, name, graph):
        self.cds[name] = self.compute_cds(graph)
        if 'all' in self.cds:
            self.cds['all'] = self.cds['all'].append(self.cds[name])
        else:
            self.cds['all'] = self.cds[name]

            
    def get_cds(self, name):
        return self.cds[name]

    def get_ccs(self):
        return self.ccs
    
    def load_ccs(self, uuid, **kwargs):
        self.ccs = db.dataframe.get(uuid, **kwargs)

    def load_similarity_graph(self, name, uuid, **kwargs):
        self.cds[name] = db.dataframe.get(uuid, **kwargs)

    def compute_cds(self, sgraph):
        cds = pd.DataFrame(None, columns=self.concepts)

        # Create zero-vectors for each dataset
        for dataset in self.dataset_graph.subjects(RDF.type, DCAT.Dataset):
            cds.loc[dataset] = np.nan

        # Set similarity values in the cds
        for similarity in sgraph.subjects(RDF.type, OTD.Similarity):
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
