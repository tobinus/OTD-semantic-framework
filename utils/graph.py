"""
Module with project-wide RDF namespaces and helper-functions for graphs.
"""
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery, sparql

# Namespaces we use in our application
from rdflib.namespace import RDF, SKOS, OWL, RDFS, FOAF, DC


# Custom namespaces for our purposes
OTD = Namespace('http://www.quaat.com/ontologies#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')
QEX = Namespace('http://www.quaat.com/extended_skos#')
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')
WN20SCHEMA = Namespace('http://www.w3.org/2006/03/wn/wn20/schema/')
DN = Namespace('http://www.wordnet.dk/owl/instance/2009/03/instances/')
DN_SCHEMA = Namespace('http://www.wordnet.dk/owl/instance/2009/03/schema/')


bindings = {
    'otd': OTD,
    'dcat': DCAT,
    'dct': DCT,
    'qex': QEX,
    'owl': OWL,
    'rdf': RDF,
    'rdfs': RDFS,
    'foaf': FOAF,
    'dc': DC,
    'skos': SKOS,
}


def create_bound_graph(*args, bindings_to_apply: set =None, **kwargs) -> Graph:
    """
    Create a new rdflib.Graph which has application-specific prefixes bound.

    Args:
        *args: Positional arguments to give to rdflib.Graph constructor.
        **kwargs: Keyword arguments to give to rdflib.Graph constructor.
        bindings_to_apply: Set of Namespace instances imported from this module,
            which should be bound. By default, all known namespaces are bound.

    Returns:
        New instance of rdflib.Graph, with prefixes already bound to namespaces.
    """
    g = Graph(*args, **kwargs)
    bind_graph(g, bindings_to_apply=bindings_to_apply)
    return g


def bind_graph(g: Graph, bindings_to_apply: set =None):
    """
    Bind the rdflib.Graph instance's prefixes to namespaces for DataOntoSearch.

    The namespaces named in the bindings module variable will be bound.

    Args:
        g: Graph whose prefixes should be bound to namespaces.
        bindings_to_apply: Set of Namespace instances imported from this module,
            which should be bound. By default, all known namespaces are bound.
    """
    if bindings_to_apply is None:
        relevant_bindings = bindings
    else:
        bindings_by_namespace = {
            namespace: prefix for prefix, namespace in bindings.items()
        }
        relevant_bindings = dict()
        for namespace in bindings_to_apply:
            # By looking up this way, we ensure we throw an error if a
            # namespace was not recognized
            prefix = bindings_by_namespace[namespace]
            relevant_bindings[prefix] = namespace

    for prefix, namespace in relevant_bindings.items():
        g.bind(prefix, namespace)


def prepare_query(query):
    """
    Prepare a SparQL query for later use, adding the needed namespaces.

    Args:
        query: The query to prepare.

    Returns:
        The prepared query, with namespaces already bound.
    """
    return prepareQuery(query, initNs=bindings)


def query(g: Graph, query, **kwargs):
    """
    Perform a SparQL query against the given graph.

    When given a string as query, namespaces will automatically be bound.

    Args:
        g: Graph to perform the query on.
        query: The query to perform. Can be a prepared query.
        **kwargs: Initial bindings for variables in the query.

    Returns:
        QueryResult from rdflib (same as g.query).
    """
    if isinstance(query, sparql.Query):
        # Prepared query, don't add namespaces
        return g.query(query, initBindings=kwargs)
    else:
        return g.query(query, initNs=bindings, initBindings=kwargs)


def update(g: Graph, query, **kwargs):
    """
    Perform a SparQL data update query against the given graph.

    Namespaces will be automatically bound.

    Args:
        g: Graph to perform the query on.
        query: The query to perform, as a string.
        **kwargs: Initial bindings for variables in the query.

    Returns:
        Whatever g.update returns, which I think is nothing.
    """
    return g.update(query, initNs=bindings, initBindings=kwargs)
