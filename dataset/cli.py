from utils.common_cli import GraphSubcommand


def adjust_parsers(subparsers):
    generate_parser = subparsers['generate']
    create_parser = subparsers['create']

    generate_parser.add_argument(
        'ckan_instance',
        help='URL of CKAN instance to import datasets from.',
    )
    create_parser.add_argument(
        '--ckan',
        help='URL of CKAN instance to import datasets from. Mandatory if not '
             'importing from file.',
        dest='ckan_instance',
    )


def do_generate(args):
    if not args.ckan_instance:
        raise ValueError('Please provide a CKAN instance when generating!')
    from dataset.generate import generate_dataset
    return generate_dataset(args.ckan_instance)


subcommand = GraphSubcommand(
    'dataset',
    'datasets',
    None,
    adjust_parsers,
    do_generate,
    'Each dataset graph represents one collection of datasets, and is used to '
    'avoid querying the CKAN instance more than once. DCAT is used to describe '
    'them.'
)


def register_subcommand(add_parser):
    parser, subcommand_parser = subcommand.register_subcommand(add_parser)
    register_append(subcommand_parser.add_parser)


def register_append(add_parser):
    parser = add_parser(
        'append',
        help='Add more datasets to an existing dataset graph.',
        description='Add one or more datasets to an existing dataset graph.'
    )
    parser.add_argument(
        '--package-list',
        help='Import all datasets matching a certain search in a CKAN API. '
             'The URL you use here should be '
    )
    parser.add_argument(
        'dataset',
        help=''
    )

