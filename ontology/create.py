from utils.graph import create_bound_graph, SKOS
from db import graph


def parse_graph(location, format, skos):
    g = create_bound_graph()
    g.parse(location, format=format)

    # Using SKOS.prefLabel as a substitute for checking for all SKOS subjects
    has_skos = (SKOS.prefLabel, None, None) in g
    if skos and not has_skos:
        g.parse(skos)
    elif not has_skos:
        raise ValueError("The parsed graph does not contain SKOS triples and "
                         "no SKOS location has been provided.")

    return g


def insert_graph(uuid, location, format, skos):
    g = parse_graph(location, format, skos)
    uuid = graph.get_uuid_for_collection(
        'ontology', uuid, True, 'create_graph()'
    )
    graph.update(g, uuid, 'ontology')
    return uuid


def insert_new_graph(location, format, skos):
    g = parse_graph(location, format, skos)
    return graph.store(g, 'ontology')
