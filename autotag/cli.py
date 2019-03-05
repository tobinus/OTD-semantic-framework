from utils.common_cli import GraphSubcommand


def adjust_parsers(subparsers):
    generate_parser = subparsers['generate']
    create_parser = subparsers['create']
    relevant_parsers = (generate_parser, create_parser)

    for parser in relevant_parsers:
        parser.add_argument(
            '--ontology',
            '-n',
            help='UUID of ontology graph with the concepts you want to connect '
                 'datasets to (when generating anew). By default, the '
                 'ONTOLOGY_UUID environment variable will be used, falling '
                 'back to the first ontology graph returned by MongoDB.',
            default=None
        )
        parser.add_argument(
            '--dataset',
            '-d',
            help='UUID of dataset graph with the datasets you want to connect '
                 'to concepts (when generating anew). By default, the '
                 'DATASET_UUID environment variable will be used, falling back '
                 'to the first dataset graph returned by MongoDB.',
            default=None
        )
        parser.add_argument(
            '--language',
            '-l',
            help='Language to use to select concept labels and compute word '
                 'similarity. Must match the language of the dataset metadata.',
            choices=('nb', 'en'),
            default='nb'
        )
        parser.add_argument(
            '--min-sim',
            '-m',
            help='The threshold for semantic similarity. Concepts with a '
                 'similarity score below this won\'t be associated with that '
                 'dataset. (Default: %(default)s)',
            default=0.8,
            type=float,
        )
        parser.add_argument(
            '--min-concepts',
            '-c',
            help='The minimum number of concepts to associate each dataset '
                 'with. Even if concepts fall below the --min-sim threshold, '
                 'they will be included if they are among the N top ranked '
                 'concepts for that dataset (N being this value). '
                 '(Default: %(default)s)',
            default=4,
            type=int,
        )
        parser.add_argument(
            '--quiet',
            '-q',
            help='Do not output progress information to stderr.',
            action='store_true'
        )


def do_generate(args):
    from autotag.generate import generate_autotag
    return generate_autotag(
        args.dataset,
        args.ontology,
        args.quiet,
        args.language,
        args.min_sim,
        args.min_concepts
    )


subcommand = GraphSubcommand(
    'Autotag',
    'autotags',
    None,
    adjust_parsers,
    do_generate,
    'Autotag and similarity graphs both represent a set of connections between '
    'concepts and datasets. Autotag graphs represent the automatically created '
    'tags, created through analysis of the existing dataset metadata. '
    'WARNING: Generating autotag may take around 40 minutes. Make sure you '
    'don\'t just feed the result to the birds.'
)


def register_subcommand(add_parser):
    return subcommand.register_subcommand(add_parser)
