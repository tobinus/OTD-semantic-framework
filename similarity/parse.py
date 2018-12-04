import csv
import functools

from rdflib import URIRef

from db.graph import get_concepts, get_dataset
from utils.graph import create_bound_graph, RDF, DCAT
from similarity.generate import add_similarity_link


def csv2rdf(fn, dialect):
    graph = create_bound_graph()
    csv_reader = csv.reader(fn, dialect=dialect)
    concept_uris = set(get_concepts(None).values())
    dataset_uris = get_dataset_uris()
    first_row = next(csv_reader)

    dataset_index = find_dataset_index(first_row)

    if 'Concepts' in first_row or 'concepts' in first_row:
        analyzer = CsvSingleColumnAnalyzer(first_row, concept_uris)
    else:
        analyzer = CsvMultipleColumnAnalyzer(first_row, concept_uris)

    for row in csv_reader:
        dataset = row[dataset_index]
        if dataset not in dataset_uris:
            raise ValueError(f'Dataset {dataset} not recognized')

        relevant_concepts = analyzer.find_concepts_for(row)

        for concept in relevant_concepts:
            add_similarity_link(
                graph,
                URIRef(dataset),
                concept,
            )
    return graph


def get_dataset_uris():
    dataset_graph = get_dataset(raise_on_no_uuid=False)
    return set(
        map(
            str,
            dataset_graph.subjects(RDF.type, DCAT.Dataset)
        )
    )


def find_dataset_index(row):
    for i, cell in enumerate(row):
        if cell in ('Dataset', 'dataset'):
            return i
    else:
        raise ValueError('There is no designated column for "Dataset"')


class CsvSingleColumnAnalyzer:
    def __init__(self, first_row, concept_uris):
        self.concepts_index = \
            CsvSingleColumnAnalyzer.find_concepts_index(first_row)
        self.concepts_recognizer = ConceptRecognizer(concept_uris)

    @staticmethod
    def find_concepts_index(first_row):
        for i, cell in enumerate(first_row):
            if cell in ('Concepts', 'concept'):
                return i
        else:
            raise ValueError('There is no designated column for "Concepts"')

    def find_concepts_for(self, row):
        cell = row[self.concepts_index]
        concept_refs = cell.split(',')
        return map(self.concepts_recognizer.get_concept_from, concept_refs)


class CsvMultipleColumnAnalyzer:
    def __init__(self, first_row, concept_uris):
        self.concept_columns = CsvMultipleColumnAnalyzer.find_concept_columns(
            first_row,
            concept_uris
        )

    @staticmethod
    def find_concept_columns(first_row, concept_uris):
        concept_columns = dict()
        concept_recognizer = ConceptRecognizer(concept_uris)

        for index, label in enumerate(first_row):
            try:
                concept = concept_recognizer.get_concept_from(label)
            except ValueError:
                continue

            concept_columns[index] = concept
        return concept_columns

    def find_concepts_for(self, row):
        concepts = []

        for index, concept in self.concept_columns.items():
            if row[index].strip():
                concepts.append(concept)
        return concepts


def as_uriref(func):
    @functools.wraps(func)
    def add_uriref(*args, **kwargs):
        return URIRef(func(*args, **kwargs))

    return add_uriref


class ConceptRecognizer:
    def __init__(self, concepts):
        self.concepts = {
            get_fragment(str(uri).lower()): str(uri) for uri in concepts
        }
        self.concept_uris = set(str(uri) for uri in concepts)

    @as_uriref
    def get_concept_from(self, str_):
        str_ = str_.strip()

        if str_ in self.concept_uris:
            # We were handed a whole URI
            return str_

        if str_.lower() in self.concepts:
            return self.concepts[str_.lower()]

        raise ValueError(f'The concept "{str_}" was not recognized')


def equal_uris(one, another):
    # A more lenient check of URIs, allowing one of them to be only the last bit
    if one == another:
        return True

    one = str(one)
    another = str(another)

    if one == another:
        return True

    one_fragment = get_fragment(one)
    another_fragment = get_fragment(another)

    return one_fragment == another or one == another_fragment


def get_fragment(uri):
    fragment_delimiters = ('#', '/')
    alternatives = tuple(
        uri.rsplit(delimiter, maxsplit=1)[-1]
        for delimiter in fragment_delimiters
        if delimiter in uri
    )
    # Return whatever alternative is shortest
    return min(alternatives, key=len)





