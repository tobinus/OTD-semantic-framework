import argparse
import textwrap
from os.path import dirname
from utils.common_cli import make_subcommand_gunicorn
from otd.constants import SIMTYPE_ALL, SIMTYPE_AUTOTAG, SIMTYPE_SIMILARITY, simtypes


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
        'Perform multiple searches using DataOntoSearch, potentially varying '
        'variables.'
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
  search-result-threshold:     List of search result thresholds to apply.
  concept-relevance-threshold: List of concept relevance thresholds to apply.
  query-concept-threshold:     List of query concept similarity thresholds to
                               apply.
  simtype:                     List of dataset taggings to use. Possible values
                               are {simtypes}.
  query:                       Either list of queries, or a mapping where the
                               queries are used as keys. The values of the
                               mapping are ignored by this script.
  See the help documentation for the 'search' subcommand for more information on
  these variables.
  All items, except for query, have a default value and can be left out. For all
  items, you can also specify a single value directly instead of a list, which
  will be interpreted as a list with just that one value.

output format:
  A streamable format is used, so that the processing can be pipelined. Queries
  are created using the cartesian product of all variables and their defined
  values, so if there are two values for search-result-threshold,
  concept-relevance-threshold, query-concept-threshold and simtype, and there
  are four queries defined, then the number of queries will be 2*2*2*2*4=64. The
  results of each query is reported separately.
  
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
    from yaml import load
    import itertools

    try:
        # Parse the file we were given
        document = load(args.file)

        # Load the variables we recognize, using defaults
        try:
            queries = document['query']
        except KeyError as e:
            raise ValueError(
                "Please specify the key 'query' in the given YAML document"
            ) from e
        except TypeError as e:
            raise ValueError(
                "Please provide a non-empty YAML document"
            ) from e

        configurations = document.get('configuration', [None])
        t_s = document.get('search-result-threshold', [0.75])
        t_c = document.get('concept-relevance-threshold', [0.0])
        t_q = document.get('query-concept-threshold', [0.0])
        chosen_simtypes = document.get(
            'simtype',
            [SIMTYPE_SIMILARITY]
        )

        # Implement shortcut so you don't need to use lists for single values.
        # Also validate/transform values.
        if isinstance(queries, str):
            queries = [queries]

        if isinstance(configurations, str) or configurations is None:
            configurations = [configurations]

        if isinstance(t_s, float):
            t_s = [t_s]
        t_s = map(float_between_0_and_1, t_s)

        if isinstance(t_c, float):
            t_c = [t_c]
        t_c = map(float_between_0_and_1, t_c)

        if isinstance(t_q, float):
            t_q = [t_q]
        t_q = map(float_between_0_and_1, t_q)

        if isinstance(chosen_simtypes, str):
            chosen_simtypes = [chosen_simtypes]
        unrecognized_simtypes = set(chosen_simtypes) - set(simtypes)
        if unrecognized_simtypes:
            raise ValueError(
                f'Did not recognize the simtypes {unrecognized_simtypes}'
            )

        # Iterate through the instantiated queries
        is_first_result = True
        for arguments in itertools.product(
                configurations,
                t_s,
                t_c,
                t_q,
                chosen_simtypes,
                queries
        ):
            # Use empty lines between results, but not before first or after
            # last
            if not is_first_result:
                print()
            else:
                is_first_result = False

            do_single_multi_search(*arguments)

    finally:
        args.file.close()


def do_single_multi_search(
        configuration,
        t_s,
        t_c,
        t_q,
        simtype,
        query
):
    # Print the first line, with information about chosen variables
    import json
    document = {
        'configuration': configuration,
        'search-result-threshold': t_s,
        'concept-relevance-threshold': t_c,
        'query-concept-threshold': t_q,
        'simtype': simtype,
        'query': query,
    }
    print(json.dumps(document))

    # Perform query
    results, _ = make_search(query, simtype, t_s, t_c, t_q, configuration)

    # Print the datasets we found
    print_results_simple(results, None, None)


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


def float_between_0_and_1(s):
    try:
        value = float(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f'{s} is not a float')

    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError(
            f'{s} is not between 0.0 and 1.0 inclusive'
        )

    return value


def do_search(args):
    results, query_concept_similarities = make_search(
        args.query,
        args.simtype,
        args.t_s,
        args.t_c,
        args.t_q,
    )

    if args.simple:
        print_func = print_results_simple
    elif args.details:
        print_func = print_results_detailed
    else:
        print_func = print_results_normally

    print_func(results, query_concept_similarities, args.query)


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


def do_matrix(_):
    from otd.opendatasemanticframework import ODSFLoader

    odsf_loader = ODSFLoader(True)
    odsf_loader.ensure_all_loaded()


def make_search(query, simtype, t_s, t_c, t_q, configuration=None):
    from otd.opendatasemanticframework import ODSFLoader
    from sys import stderr

    print('Loading indices and matrices…', file=stderr)
    odsf_loader = ODSFLoader(True, t_c)
    if configuration is None:
        odsf = odsf_loader.get_default()
    else:
        odsf = odsf_loader[configuration]

    print('Performing query…', file=stderr)
    return odsf.search_query(
        query,
        cds_name=simtype,
        qc_sim_threshold=t_q,
        score_threshold=t_s,
    )


def print_results_simple(results, _1, _2):
    # Simply print URIs (for processing by other script)
    for result in results:
        print(result.info.uri)


def print_results_detailed(results, query_concept_similarities, query):
    # Print all the information we have
    from tabulate import tabulate
    print(f'Your query for "{query}" matched the following concepts:')
    print(tabulate(
        query_concept_similarities,
        headers=('Concept', 'Similarity score'),
        tablefmt='psql'
    ))
    print()

    print(f'Your query for "{query}" matched the following datasets:')

    formatted_results = []
    for result in results:
        score = result.score
        dataset_info = result.info
        matched_concepts = result.concepts

        formatted_concepts = tabulate(
            matched_concepts,
            tablefmt='plain',
        )
        formatted_results.append((
            dataset_info.uri,
            score,
            dataset_info.title,
            dataset_info.description,
            formatted_concepts,
        ))
    print(tabulate(
        formatted_results,
        headers=(
            'URI',
            'Score',
            'Title',
            'Description',
            'Matching concepts+score',
        ),
        tablefmt='grid',
    ))


def print_results_normally(results, _, query):
    # Print information probably sought by the average user(?)
    from tabulate import tabulate
    print(f'The following datasets matched your query for {query}:')

    formatted_results = []
    for result in results:
        score = result.score
        dataset_info = result.info

        formatted_results.append((
            dataset_info.title,
            score,
            dataset_info.description,
        ))
    print(tabulate(
        formatted_results,
        headers=(
            'Title',
            'Score',
            'Description',
        ),
        tablefmt='psql',
    ))
