from otd.opendatasemanticframework import OpenDataSemanticFramework
from otd.constants import SIMTYPE_SIMILARITY, SIMTYPE_AUTOTAG


def ensure_matrices_are_created():
    ontology = OpenDataSemanticFramework(None, None, True)
    ontology.load_similarity_graph(SIMTYPE_SIMILARITY, 'similarity', None)
    ontology.load_similarity_graph(SIMTYPE_AUTOTAG, 'autotag', None)
