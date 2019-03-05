from ontology import SKOS_RDF_LOCATION
from utils.common_cli import GraphSubcommand


def adjust_loaded_graph(self, g, args):
    skos = args.skos
    # Using SKOS.prefLabel as a substitute for checking for all SKOS subjects
    has_skos = (self._utils_graph.SKOS.prefLabel, None, None) in g
    if skos and not has_skos:
        g.parse(skos)
    elif not has_skos:
        raise ValueError("The parsed graph does not contain SKOS triples and "
                         "no SKOS location has been provided.")


def adjust_parsers(subparsers):
    generate_parser = subparsers['generate']
    create_parser = subparsers['create']

    generate_parser.add_argument(
        '--skos',
        '-s',
        help="Embed triples defining SKOS in the serialization. You can "
             "optionally provide a URL or location for file with RDF XML for "
             "SKOS. (Default: %(const)s)",
        nargs='?',
        const=SKOS_RDF_LOCATION,
        default=False
    )

    create_parser.add_argument(
        '--skos',
        '-s',
        help="Location where SKOS RDF XML can be found. (Default: %(default)s)",
        default=SKOS_RDF_LOCATION
    )


def do_generate(args):
    from ontology.generate import create_graph
    return create_graph(args.skos)


def do_show_hier(args):
    from ontology.show_hier import get_concept_list
    print(get_concept_list(args.uuid))


def register_show_hier(add_parser):
    help_text = (
        'Print HTML for a hierarchical list of concepts.'
    )
    parser = add_parser(
        'show_hier',
        help=help_text,
        description=help_text,
    )
    parser.add_argument(
        'uuid',
        nargs='?',
        default=None,
        help='UUID of the ontology graph to use. When not given, the '
             'environment variable ONTOLOGY_UUID will be used, or the first '
             'graph returned by MongoDB.',
    )
    parser.set_defaults(
        func=do_show_hier
    )


def register_sort_turtle(add_parser):
    help_text = (
        'Sort a SKOS turtle file in order of hierarchy.'
    )
    parser = add_parser(
        'sort_turtle',
        help=help_text,
        description=help_text,
    )
    parser.add_argument(
        '--prefix',
        '-p',
        help='Prefix used before each concept name in turtle file. '
             '(Default: %(default)s)',
        default='otd:',
    )
    parser.add_argument(
        'source',
        help='Path to turtle file to sort.',
    )
    parser.add_argument(
        'destination',
        help='Where to save the sorted turtle file.',
    )
    parser.set_defaults(
        func=do_sort_turtle
    )


def do_sort_turtle(args):
    from ontology.sort_turtle import sort_turtle, get_concepts_sorted
    identifiers = get_concepts_sorted(args.source)
    sort_turtle(args.prefix, identifiers, args.source, args.destination)


subcommand = GraphSubcommand(
    'Ontology',
    'ontologies',
    adjust_loaded_graph,
    adjust_parsers,
    do_generate,
    "Each ontology graph represents one ontology, with concepts and their "
    "labels and connections to one another. The SKOS vocabulary is used to "
    "describe them."
)


def register_subcommand(add_parser):
    _, subcommands = subcommand.register_subcommand(add_parser)
    register_show_hier(subcommands.add_parser)
    register_sort_turtle(subcommands.add_parser)
