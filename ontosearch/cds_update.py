from otd.opendatasemanticframework import OpenDataSemanticFramework


def ensure_matrices_are_created():
    ontology = OpenDataSemanticFramework(None, None, True)
    ontology.load_similarity_graph("tagged", 'similarity', None)
    ontology.load_similarity_graph("auto", 'autotag', None)
