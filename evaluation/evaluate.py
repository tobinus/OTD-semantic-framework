import csv
import collections.abc
import io
import itertools
import json
import sys
import subprocess
from tabulate import tabulate
import yaml
from rdflib import URIRef

from db.graph import Configuration
from utils.graph import RDF, OTD, DCAT, SKOS
from otd.constants import SIMTYPE_SIMILARITY, SIMTYPE_AUTOTAG, simtypes
from utils.common_cli import float_between_0_and_1


def evaluate_using_file(filename):
    if filename == '-':
        in_document = io.StringIO()
        in_document.write(sys.stdin.read())
        file_contents = in_document.getvalue()
        document = yaml.load(file_contents)
    else:
        with open(filename) as fp:
            file_contents = None
            document = yaml.load(fp)

    try:
        queries = document['query']
    except KeyError as e:
        raise RuntimeError(
            "Please specify the key 'query' in the given YAML document"
        ) from e
    except TypeError as e:
        if document is None:
            raise RuntimeError(
                'Please provide a non-empty YAML document'
            ) from e
        else:
            raise RuntimeError(
                'Please ensure the YAML document has a mapping at the top level'
            ) from e

    if not isinstance(queries, collections.abc.Mapping):
        raise RuntimeError(
            "'query' must be a mapping between queries and relevant concepts "
            "and datasets"
        )

    if not all(
            map(
                lambda q: isinstance(q, list),
                queries.values()
            )
    ):
        raise RuntimeError(
            "Please ensure all values in the 'query' mapping are lists of "
            "datasets and concepts related to that query"
        )

    ground_truth = document.get('ground-truth', dict())

    ground_simtype = ground_truth.get('simtype', SIMTYPE_SIMILARITY)
    if ground_simtype not in simtypes:
        raise RuntimeError(
            f'Ground truth simtype "{ground_simtype}" was not recognized'
        )

    ground_threshold = ground_truth.get('threshold', 0.8)
    ground_threshold = float_between_0_and_1(ground_threshold)

    return evaluate(
        queries,
        ground_simtype,
        ground_threshold,
        filename,
        file_contents
    )


def evaluate(queries, ground_simtype, ground_threshold, filename, file_contents):
    command = [
        sys.executable or 'python',
        sys.argv[0],
        'multisearch',
        filename,
    ]

    input_text = None
    if file_contents is not None:
        input_text = file_contents

    process_info = subprocess.run(
        command,
        universal_newlines=True,
        input=input_text,
        stdout=subprocess.PIPE,
        check=True,
    )

    results = process_info.stdout.split('\n\n')
    results = map(lambda s: s.split('\n'), results)
    results = map(
        lambda lines: process_results(
            lines,
            queries,
            ground_simtype,
            ground_threshold
        ),
        results
    )
    return tuple(results)


def process_results(lines, queries, ground_simtype, ground_threshold):
    metadata = json.loads(lines[0])
    matching_datasets = lines[1:]

    query = metadata['query']
    configuration = metadata['configuration']
    raw_relevant_datasets = queries[query]
    relevant_datasets = find_relevant_datasets(
        raw_relevant_datasets,
        configuration,
        ground_simtype,
        ground_threshold
    )

    metrics = calculate_metrics(matching_datasets, relevant_datasets)

    # Return combination of the metadata for the query, and calculated metrics
    metadata.update(metrics)
    return metadata


def find_relevant_datasets(relevant_spec, configuration, simtype, threshold):
    # Load necessary graphs
    config = Configuration.from_uuid(configuration)
    dataset_graph = config.get_dataset().graph
    ontology_graph = config.get_ontology().graph
    if simtype == SIMTYPE_SIMILARITY:
        similarity_graph = config.get_similarity().graph
    elif simtype == SIMTYPE_AUTOTAG:
        similarity_graph = config.get_autotag().graph
    else:
        raise ValueError(f'Simtype {simtype} not supported')

    # We will be creating a list of relevant datasets
    relevant_datasets = list()

    # Go through all relevant datasets/concepts named in the YAML file
    for spec in relevant_spec:
        # We are assuming concepts or datasets are RDF URIs
        spec = URIRef(spec)
        # Are we dealing with a dataset or concept?
        if (spec, RDF.type, DCAT.Dataset) in dataset_graph:
            # We are naming a relevant dataset, simply add it
            relevant_datasets.append(str(spec))
        elif (spec, RDF.type, SKOS.Concept) in ontology_graph:
            # We are naming a relevant concept, add all datasets connected to it
            # Start with navigating dataset taggings related to this concept
            similarities = similarity_graph.subjects(OTD.concept, spec)
            for sim in similarities:
                # What is the similarity score for this dataset-concept tag?
                score = similarity_graph.value(sim, OTD.score, None)
                # Is it above our threshold?
                if float(score) < threshold:
                    # Nope, skip
                    continue
                # Add this dataset
                dataset = similarity_graph.value(sim, OTD.dataset, None)
                relevant_datasets.append(str(dataset))
        else:
            raise ValueError(
                f'Did not recognize {spec} as a concept or dataset for '
                f'configuration {configuration}'
            )
    return relevant_datasets


def calculate_metrics(matching_datasets, relevant_datasets):
    # Create array with relevant/irrelevant for each retrieved dataset
    result_relevance = tuple(
        map(
            lambda r: r in relevant_datasets,
            matching_datasets
        )
    )
    num_fetched = len(matching_datasets)
    num_relevant_existing = len(relevant_datasets)
    num_relevant_fetched = num_true(result_relevance)
    num_r_relevant_fetched = num_true(result_relevance[:num_relevant_existing])

    precision = num_relevant_fetched / num_fetched
    recall = num_relevant_fetched / num_relevant_existing
    f1_measure = (2 * precision * recall) / (precision + recall)
    r_precision = num_r_relevant_fetched / num_relevant_existing

    return {
        'precision': precision,
        'recall': recall,
        'f1-measure': f1_measure,
        'r-precision': r_precision,
    }


def num_true(iterable):
    return len(
        tuple(
            filter(
                None,
                iterable
            )
        )
    )


def print_results(results, table_format='psql', destination=None):
    if destination is None:
        destination = sys.stdout

    if table_format.lower() == 'csv':
        output = format_as_csv(results)
    else:
        output = format_using_tabulate(results, table_format)
    print(output, file=destination)


def format_as_csv(results):
    stream = io.StringIO(newline='')
    csv_writer = csv.DictWriter(stream, fieldnames=results[0].keys())
    csv_writer.writeheader()

    for r in results:
        csv_writer.writerow(r)
    return stream.getvalue().strip()


def format_using_tabulate(results, table_format):
    return tabulate(
        results,
        headers='keys',
        tablefmt=table_format,
    )
