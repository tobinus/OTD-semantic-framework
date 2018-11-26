"""
Module with project-wide RDF namespaces and helper-functions for graphs.
"""
from rdflib import Graph, Namespace

# Namespaces we use in our application
from rdflib.namespace import RDF, XSD, SKOS


# Custom namespaces for our purposes
ODT = Namespace('http://www.quaat.com/ontologies#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')
ODTX = Namespace('http://www.quaat.com/ontology/ODTX#')
QEX = Namespace('http://www.quaat.com/extended_skos#')
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')
WN20SCHEMA = Namespace('http://www.w3.org/2006/03/wn/wn20/schema/')
DN = Namespace('http://www.wordnet.dk/owl/instance/2009/03/instances/')
DN_SCHEMA = Namespace('http://www.wordnet.dk/owl/instance/2009/03/schema/')


bindings = {
    'odt': ODT,
    'dcat': DCAT,
    'dct': DCT,
    'odtx': ODTX,
    'qex': QEX,
}


def create_bound_graph(*args, **kwargs) -> Graph:
    """
    Create a new rdflib.Graph which has application-specific prefixes bound.

    Args:
        *args: Positional arguments to give to rdflib.Graph constructor.
        **kwargs: Keyword arguments to give to rdflib.Graph constructor.

    Returns:
        New instance of rdflib.Graph, with prefixes already bound to namespaces.
    """
    g = Graph(*args, **kwargs)
    bind_graph(g)
    return g


def bind_graph(g: Graph):
    """
    Bind the rdflib.Graph instance's prefixes to namespaces for DataOntoSearch.

    The namespaces named in the bindings module variable will be bound.

    Args:
        g: Graph whose prefixes should be bound to namespaces.
    """
    for prefix, namespace in bindings.items():
        g.bind(prefix, namespace)
