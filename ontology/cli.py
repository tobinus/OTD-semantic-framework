import argparse


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


def register_generate(add_parser):
    parser = add_parser(
        'generate',
        help="Create a serialization of the Open Transport Ontology."
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
        const='https://www.w3.org/2009/08/skos-reference/skos.rdf',
        default=False
    )
    parser.set_defaults(
        func=do_generate
    )


def do_generate(args):
    from ontology.generate import create_graph
    g = create_graph(args.skos)
    g.serialize(destination=args.outfile, format=args.format)
