import os.path
from utils.graph import create_bound_graph


def get_authoritative_ontology(skos_location):
    return create_graph(skos_location)


def create_graph(skos_location):
    g = create_bound_graph()

    # The ontology file is in the same folder as this file, called 'otd.ttl'.
    # That file is the canonical description of the ontology.
    otd_ontology = os.path.join(
        os.path.dirname(__file__),
        'otd.ttl'
    )

    g.parse(location=otd_ontology, format='turtle')

    if skos_location:
        g.parse(location=skos_location)

    return g
