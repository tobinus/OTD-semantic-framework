import argparse
import textwrap
from otd.constants import SIMTYPE_SIMILARITY


def register_subcommand(add_parser):
    register_evaluate(add_parser)


def register_evaluate(add_parser):
    help_text = (
        "Compare the search engine's performance against a ground truth and "
        "report the achieved precision and recall."
    )

    epilog = (f"""
format of YAML file:
  query:        A mapping. The key is the query to run. The value is a list
                consisting of RDF URIs that indicate relevant datasets. They can
                either refer to concepts, in which case the ground-truth
                parameter below is used, or to datasets, in which case they are
                regarded as relevant datasets. You may combine the two however
                you like.
  ground-truth: A mapping with the following keys, influencing how the ground
                truth is derived from the concepts mentioned.
    threshold:  When looking at datasets that are tagged with a mentioned
                concept, this parameter decides how high the tagging score must
                be for this dataset to be considered relevant. Defaults to 0.8.
    simtype:    The dataset tagging used to find connections from concepts to
                datasets. Defaults to {SIMTYPE_SIMILARITY}.
  See the help text for the 'multisearch' subcommand for the other parameters 
  available.
""")

    parser = add_parser(
        'evaluate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help=help_text,
        description=textwrap.fill(help_text, width=80),
        epilog=epilog
    )

    parser.add_argument(
        'file',
        type=argparse.FileType('r'),
        help='YAML file used to find the queries to use and determine the '
             'ground truth for what is relevant to each query. Specify a dash '
             '(-) to use stdin.',
    )

    parser.add_argument(
        '--format',
        '-f',
        help='Choose a format to use when pretty-printing the results. See the '
             'documentation of python-tabulate for available options. '
             'Additionally, you may use the "csv" format to output a CSV file. '
             '(Default: %(default)s)',
        default='psql',
    )

    parser.set_defaults(
        func=do_evaluate,
    )


def do_evaluate(args):
    from evaluation.evaluate import evaluate_using_file, print_results
    results = evaluate_using_file(args.file)
    print_results(results, args.format)
