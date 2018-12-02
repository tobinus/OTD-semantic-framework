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
    # TODO: Split up into more re-usable functions
    from otd.opendatasemanticframework import OpenDataSemanticFramework
    from tabulate import tabulate
    from sys import stderr

    print('Loading indices and matrices…', file=stderr)
    ontology = OpenDataSemanticFramework(None, None, True)
    # TODO: Use constants to refer to the different CDS matrices
    ontology.load_similarity_graph("tagged", 'similarity', None)
    ontology.load_similarity_graph("auto", 'autotag', None)

    print('Performing query…', file=stderr)
    # TODO: Find proper names for xs and sv variables
    results, sv = ontology.search_query(args.query, cds_name=args.simtype)
    del ontology

    print('Formatting output…', file=stderr)
    if args.simple:
        # Simply print URIs (for processing by other script)
        for result in results:
            print(result[1].uri)

    elif args.details:
        # Print all the information we have
        print('Your query matched the following concepts:')
        print(tabulate(
            sv,
            headers=('Concept', 'Similarity score'),
            tablefmt='psql'
        ))
        print()

        print('Your query matched the following datasets:')

        formatted_results = []
        for result in results:
            score = result[0]
            dataset_info = result[1]
            matched_concepts = result[2]

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
            tablefmt='psql',
        ))

    else:
        # Print information probably sought by the average user(?)
        print('The following datasets matched your query:')

        formatted_results = []
        for result in results:
            score = result[0]
            dataset_info = result[1]

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

