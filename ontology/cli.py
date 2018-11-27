import argparse

from bson.errors import InvalidId

from ontology import SKOS_RDF_LOCATION
from utils.common_cli import register_arguments_for_rdf_output, with_rdf_output


def register_subcommand(add_parser):
    parser = add_parser(
        'ontology',
        help="Collection of helper commands for dealing with ontologies."
    )
    subcommands = parser.add_subparsers(
        title="actions",
        description="These actions are available to manipulate ontologies.",
        dest="action"
    )
    register_generate(subcommands.add_parser)
    register_create(subcommands.add_parser)
    register_remove(subcommands.add_parser)
    register_list(subcommands.add_parser)
    register_show(subcommands.add_parser)


def register_generate(add_parser):
    parser = add_parser(
        'generate',
        help="Create a serialization of the Open Transport Ontology.",
        description="Create a serialization of the Open Transport Ontology."
    )
    register_arguments_for_rdf_output(parser)
    parser.add_argument(
        '--skos',
        '-s',
        help="Embed triples defining SKOS in the serialization. You can "
             "optionally provide a URL or location for file with RDF XML for "
             "SKOS. (Default: %(const)s)",
        nargs='?',
        const=SKOS_RDF_LOCATION,
        default=False
    )
    parser.set_defaults(
        func=do_generate
    )


@with_rdf_output
def do_generate(args):
    from ontology.generate import create_graph
    return create_graph(args.skos)


def register_create(add_parser):
    parser = add_parser(
        'create',
        help="Create new ontology in the database, using an ontology as the "
             "basis. The UUID of the new ontology entry is printed.",
        description="Create new ontology in the database, using an ontology as "
                    "the basis. The UUID of the new ontology entry is printed."
    )
    parser.add_argument(
        '--ontology',
        '-o',
        help="Location and format of ontology to load into the database. By "
             "default, the authoritative version of the OTD ontology will be "
             "used.",
        nargs=2,
        metavar=('LOCATION', 'FORMAT')
    )
    parser.add_argument(
        '--uuid',
        '-i',
        help="Force the UUID for the new ontology, potentially overwriting an "
             "existing ontology with the same UUID. If you do not provide a "
             "UUID, it will be read from the ONTOLOGY_UUID environment "
             "variable. When this flag is not given, a new UUID is generated "
             "and printed.",
        nargs='?',
        const=None,
        default=False
    )
    parser.add_argument(
        '--skos',
        '-s',
        help="Location where SKOS RDF XML can be found. (Default: %(default)s)",
        default=SKOS_RDF_LOCATION
    )
    parser.set_defaults(
        func=do_create
    )


def do_create(args):
    from ontology.create import insert_potentially_new_graph

    if args.ontology:
        ontology, ont_format = args.ontology
    else:
        ontology, ont_format = None, None

    uuid = insert_potentially_new_graph(
        args.uuid,
        ontology,
        ont_format,
        args.skos
    )
    print(uuid)


def register_remove(add_parser):
    help_text = (
        "Remove the ontology with the specified UUID(s), no questions asked."
    )
    parser = add_parser(
        'remove',
        help=help_text,
        description=help_text,
    )
    parser.add_argument(
        'uuid',
        help="UUID of ontology document(s) to remove",
        nargs="+"
    )
    parser.set_defaults(
        func=do_remove
    )


def do_remove(args):
    from db import graph

    success = True
    for uuid in args.uuid:
        try:
            result = graph.remove(uuid, 'ontology')
            if not result:
                success = False
                print('No document with UUID', uuid, 'found')
        except InvalidId:
            success = False
            print('The UUID', uuid, 'is invalid')

    return 0 if success else 1


def register_list(add_parser):
    help_text = (
        "List all ontologies in the database."
    )
    parser = add_parser(
        'list',
        help=help_text,
        description=help_text,
    )
    parser.set_defaults(
        func=do_list
    )


def do_list(args):
    from db import graph
    ontologies = graph.find_all_ids('ontology')
    for ontology in ontologies:
        print(ontology)


def register_show(add_parser):
    help_text = (
        "Display the contents of an ontology in the database."
    )
    parser = add_parser(
        'show',
        help=help_text,
        description=help_text,
    )
    register_arguments_for_rdf_output(parser)
    parser.add_argument(
        'uuid',
        help='The UUID of the ontology to show. If not given, then the UUID '
             'named in the ONTOLOGY_UUID environment variable is used. If no '
             'such variable is found, whatever MongoDB returns first is shown.',
        nargs='?',
        default=None
    )
    parser.set_defaults(
        func=do_show
    )


@with_rdf_output
def do_show(args):
    from db import graph
    return graph.get_ontology(args.uuid, False)
