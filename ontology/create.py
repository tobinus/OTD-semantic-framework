from io import BytesIO
from utils.graph import create_bound_graph, SKOS
from db import graph
from ontology import SKOS_RDF_LOCATION


def insert_potentially_new_graph(uuid=False, location=None, format=None, skos=None):
    if uuid is not False:
        return insert_graph(uuid, location, format, skos)
    else:
        return insert_new_graph(location, format, skos)


def insert_graph(uuid, location=None, format=None, skos=None):
    g = parse_graph_or_use_authoritative(location, format, skos)
    uuid = graph.get_uuid_for_collection(
        'ontology', uuid, True, 'create_graph()'
    )
    graph.update(g, uuid, 'ontology')
    return uuid


def insert_new_graph(location=None, format=None, skos=None):
    g = parse_graph_or_use_authoritative(location, format, skos)
    return graph.store(g, 'ontology')


def parse_graph_or_use_authoritative(location=None, format=None, skos=None):
    if skos is None:
        skos = SKOS_RDF_LOCATION

    if location and format:
        return parse_graph(location, format, skos)
    else:
        from ontology.generate import get_authoritative_ontology
        return get_authoritative_ontology(skos)


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
