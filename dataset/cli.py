from utils.common_cli import GraphSubcommand


def adjust_parsers(subparsers):
    generate_parser = subparsers['generate']
    create_parser = subparsers['create']

    generate_parser.add_argument(
        'ckan',
        help='URL of CKAN instance to import datasets from, or URL to API call '
             'using package_search, for limiting datasets to import.',
    )
    create_parser.add_argument(
        '--ckan',
        help='URL of CKAN instance to import datasets from, or URL to API call '
             'using package_search, for limiting datasets to import. Mandatory '
             'if not importing from file.',
        dest='ckan',
    )


def do_generate(args):
    if not args.ckan:
        raise ValueError('Please provide a CKAN instance when generating!')
    from dataset.generate import generate_dataset
    return generate_dataset(args.ckan)


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
    return subcommand.register_subcommand(add_parser)
