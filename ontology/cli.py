import argparse
from ontology import SKOS_RDF_LOCATION


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


def register_generate(add_parser):
    parser = add_parser(
        'generate',
        help="Create a serialization of the Open Transport Ontology.",
        description="Create a serialization of the Open Transport Ontology."
    )
    parser.add_argument(
        'outfile',
        help="Where to save the serialized ontology graph",
        type=argparse.FileType('wb')
    )
    parser.add_argument(
        '--format',
        '-f',
        help="Format to use when serializing the graph. See "
             "https://rdflib.readthedocs.io/en/stable/plugin_serializers.html "
             "for available options, plus json-ld. (Default: %(default)s)",
        choices=(
            'n3',
            'nquads',
            'nt',
            'pretty-xml',
            'trig',
            'trix',
            'turtle',
            'xml',
            'json-ld',
        ),
        default='xml'
    )
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


def do_generate(args):
    from ontology.generate import create_graph
    g = create_graph(args.skos)
    g.serialize(destination=args.outfile, format=args.format)


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

