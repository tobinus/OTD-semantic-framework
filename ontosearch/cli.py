from os.path import dirname
from utils.common_cli import make_subcommand_gunicorn


def register_subcommand(add_parser):
    register_serve(add_parser)
    register_search(add_parser)


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


def register_search(add_parser):
    help_text = 'Perform one search using DataOntoSearch.'
    parser = add_parser(
        'search',
        help=help_text,
        description=help_text,
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
        choices=('all', 'tagged', 'auto'),
        help='The set of dataset-concept links to use. "tagged" is the '
             'manually tagged similarity graph, "auto" is the automatically '
             'generated autotag graph, while "all" uses both.'
    )
    parser.add_argument(
        'query',
        help='The query to search with.',
    )

    parser.set_defaults(
        func=do_search,
    )


def do_search(args):
    results, query_concept_similarities = make_search(args.query, args.simtype)

    if args.simple:
        print_func = print_results_simple
    elif args.details:
        print_func = print_results_detailed
    else:
        print_func = print_results_normally

    print_func(results, query_concept_similarities, args.query)


def make_search(query, simtype):
    from otd.opendatasemanticframework import OpenDataSemanticFramework
    from sys import stderr

    print('Loading indices and matrices…', file=stderr)
    ontology = OpenDataSemanticFramework(None, None, True)
    # TODO: Use constants to refer to the different CDS matrices
    ontology.load_similarity_graph("tagged", 'similarity', None)
    ontology.load_similarity_graph("auto", 'autotag', None)

    print('Performing query…', file=stderr)
    return ontology.search_query(query, cds_name=simtype)


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
