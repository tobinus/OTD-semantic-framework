import itertools
import json
from yaml import load
from sys import stderr
from tabulate import tabulate

from otd.constants import SIMTYPE_SIMILARITY, simtypes
from otd.opendatasemanticframework import ODSFLoader
from utils.common_cli import float_between_0_and_1


def do_multi_search(file):
    try:
        # Parse the file we were given
        document = load(file)

        # Load the variables we recognize, using defaults
        try:
            queries = document['query']
        except KeyError as e:
            raise RuntimeError(
                "Please specify the key 'query' in the given YAML document"
            ) from e
        except TypeError as e:
            raise RuntimeError(
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
        file.close()


def do_single_multi_search(
        configuration,
        t_s,
        t_c,
        t_q,
        simtype,
        query
):
    # Print the first line, with information about chosen variables
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


def do_search(args):
    include_dataset_info = not args.simple
    include_concepts = args.details

    results, query_concept_similarities = make_search(
        args.query,
        args.simtype,
        args.t_s,
        args.t_c,
        args.t_q,
        include_dataset_info=include_dataset_info,
        include_concepts=include_concepts,
    )

    if args.simple:
        print_func = print_results_simple
    elif args.details:
        print_func = print_results_detailed
    else:
        print_func = print_results_normally

    print_func(results, query_concept_similarities, args.query)


def do_matrix(_):
    odsf_loader = ODSFLoader(True)
    odsf_loader.ensure_all_loaded()


def make_search(query, simtype, t_s, t_c, t_q, configuration=None, **kwargs):
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
        **kwargs
    )


def print_results_simple(results, _1, _2):
    # Simply print URIs (for processing by other script)
    for result in results:
        print(result.info)


def print_results_detailed(results, query_concept_similarities, query):
    # Print all the information we have
    print(f'Your query for "{query}" matched the following concepts:')
    print(tabulate(
        _only_include_label_similarity(query_concept_similarities),
        headers=('Label', 'Similarity score'),
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
            _only_include_label_similarity(matched_concepts),
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


def _only_include_label_similarity(similarities):
    return map(
        lambda similarity: (similarity.label, similarity.similarity),
        similarities
    )


def print_results_normally(results, _, query):
    # Print information probably sought by the average user(?)
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
