import argparse
import textwrap
from os.path import dirname
from utils.common_cli import make_subcommand_gunicorn, float_between_0_and_1
from otd.constants import SIMTYPE_ALL, SIMTYPE_AUTOTAG, SIMTYPE_SIMILARITY, simtypes, DATAONTOSEARCH_ENGINE, GOOGLE_ENGINE, engines


def register_subcommand(add_parser):
    register_serve(add_parser)
    register_search(add_parser)
    register_multi_search(add_parser)
    register_matrix(add_parser)


def register_serve(add_parser):
    help_text = 'Start the webserver for searching ontologies.'
    parser = add_parser(
        'serve',
        help=help_text,
        description=help_text,
    )
    parser.add_argument(
        '--skip-matrix',
        '-s',
        help='Do not create missing concept-concept and concept-dataset '
             'similarity matrices before starting the webserver. This saves '
             'time when they are already up-to-date, but crashes if not.',
        action='store_true',
    )
    make_subcommand_gunicorn(parser, dirname(dirname(__file__)), 'ontosearch.app:app', ensure_server_ready)


def ensure_server_ready(args):
    if not args.skip_matrix:
        from ontosearch.cds_update import ensure_matrices_are_created
        ensure_matrices_are_created()


def register_multi_search(add_parser):
    help_text = (
        'Perform multiple searches using DataOntoSearch among others, '
        'potentially varying variables.'
    )

    description = textwrap.fill(
        help_text + ' You do this by creating a YAML file where all parameters '
                    'and queries are specified.',
        width=80
    )

    epilog = (f"""
format of YAML file:
  configuration:               List of UUID of the configurations to use when
                               running the queries.
  query:                       Either list of queries, or a mapping where the
                               queries are used as keys. The values of the
                               mapping are ignored by this script.
  engine:                      Name of search engine to use. Note: Only one
                               engine can be chosen. Defaults to
                               {DATAONTOSEARCH_ENGINE}. Available options:
                               {engines}.

  For the '{DATAONTOSEARCH_ENGINE}' engine, available options are described
  below. For all other engines, their options are put into a key with the same
  name as the engine.

  All items, except for query, have a default value and can be left out. For all
  items, you can also specify a single value directly instead of a list, which
  will be interpreted as a list with just that one value. This also applies to
  the additional options for '{DATAONTOSEARCH_ENGINE}' below.

additional options for '{DATAONTOSEARCH_ENGINE}':
  search-result-threshold:     List of search result thresholds to apply.
  concept-relevance-threshold: List of concept relevance thresholds to apply.
  query-concept-threshold:     List of query concept similarity thresholds to
                               apply.
  simtype:                     List of dataset taggings to use. Possible values
                               are {simtypes}.
  See the help documentation for the 'search' subcommand for more information on
  these variables.

additional options for '{GOOGLE_ENGINE}':
  {GOOGLE_ENGINE}:
    site:                      Restrict returned datasets to this provider.
                               Analog to the site: operator in regular Google
                               search. Examples include data.ny.gov and
                               data.gov. No restriction is applied by default.

output format:
  A streamable format is used, so that the processing can be pipelined. For 
  the '{DATAONTOSEARCH_ENGINE}' engine, queries are created using the cartesian
  product of all variables and their defined values, so if there are two values
  for search-result-threshold, concept-relevance-threshold,
  query-concept-threshold and simtype, and there are four queries defined, then
  the number of queries will be 2*2*2*2*4=64. The results of each query is
  reported separately. For other engines, only the cartesian product of the
  configurations and queries is used.
  
  The first line of a query's results is a single-line JSON listing the chosen
  values for all variables. The next lines simply list the RDF URI of the
  datasets that were retrieved in order of decreasing relevance, one URI on each
  line. A blank line or end of file indicates the end of the result list, after
  which the next query's results may start (in the case of a blank line).
""")

    parser = add_parser(
        'multisearch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help=help_text,
        description=description,
        epilog=epilog
    )
    parser.add_argument(
        'file',
        type=argparse.FileType('r'),
        help='YAML file used to derive the queries and configurations to use. '
             'Specify a dash (-) to use stdin.'
    )
    parser.set_defaults(
        func=do_multi_search
    )


def do_multi_search(args):
    from ontosearch.search import do_multi_search
    return do_multi_search(args.file)


def register_search(add_parser):
    help_text = 'Perform one search using DataOntoSearch.'
    parser = add_parser(
        'search',
        help=help_text,
        description=help_text,
    )

    parser.add_argument(
        '--search-result-threshold',
        '-t',
        help='Adjust the lower threshold for how similar a dataset vector must '
             'be to the query vector in order to be included in the results '
             '(Ts). (Default: %(default)s, Type: float between 0.0 and 1.0)',
        type=float_between_0_and_1,
        default=0.75,
        dest='t_s',
        metavar='THRESHOLD',
    )

    parser.add_argument(
        '--concept-relevance-threshold',
        '-c',
        help='Adjust the lower threshold of similarity between a dataset and '
             'concepts, used to decide which concepts are relevant (Tc). ' 
             '(Default: %(default)s, Type: float between 0.0 and 1.0)',
        type=float_between_0_and_1,
        default=0.0,
        dest='t_c',
        metavar='THRESHOLD',
    )

    parser.add_argument(
        '--query-concept-threshold',
        '-q',
        help='Adjust the lower threshold for how similar a concept must be to '
             'the search query in order to be picked to represent it. '
             '(Default: %(default)s, Type: float between 0.0 and 1.0)',
        type=float_between_0_and_1,
        default=0.0,
        dest='t_q',
        metavar='THRESHOLD',
    )

    format_option = parser.add_mutually_exclusive_group()
    format_option.add_argument(
        '--details',
        '-d',
        help='Print extra details about returned results, including URI, '
             'matched concepts and their similarity score.',
        action='store_true',
    )
    format_option.add_argument(
        '--simple',
        '-s',
        help='Print only the URI of matched datasets, for consumption by other '
             'scripts etc.',
        action='store_true',
    )

    parser.add_argument(
        'simtype',
        choices=simtypes,
        help=f'The set of dataset-concept links to use. "{SIMTYPE_SIMILARITY}" '
        f'is the manually tagged similarity graph, "{SIMTYPE_AUTOTAG}" is the '
        f'automatically generated autotag graph, while "{SIMTYPE_ALL}" uses '
        f'both.'
    )
    parser.add_argument(
        'query',
        help='The query to search with.',
    )

    parser.set_defaults(
        func=do_search,
    )


def do_search(args):
    from ontosearch.search import do_search
    return do_search(args)


def register_matrix(add_parser):
    help_text = 'Generate all CDS and CCS matrices for all configurations.'
    parser = add_parser(
        'matrix',
        help=help_text,
        description=help_text,
    )
    parser.set_defaults(
        func=do_matrix
    )


def do_matrix(args):
    from ontosearch.search import do_matrix
    return do_matrix(args)
