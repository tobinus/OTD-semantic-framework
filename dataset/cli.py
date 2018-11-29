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
    do_generate
)


def register_subcommand(add_parser):
    return subcommand.register_subcommand(add_parser)