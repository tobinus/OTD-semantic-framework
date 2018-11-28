from ontology import SKOS_RDF_LOCATION
from utils.common_cli import GraphSubcommand


def adjust_loaded_graph(self, g, args):
    skos = args.skos
    # Using SKOS.prefLabel as a substitute for checking for all SKOS subjects
    has_skos = (self.utils_graph.SKOS.prefLabel, None, None) in g
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


subcommand = GraphSubcommand(
    'ontology',
    'ontologies',
    adjust_loaded_graph,
    adjust_parsers,
    do_generate
)


def register_subcommand(add_parser):
    return subcommand.register_subcommand(add_parser)
