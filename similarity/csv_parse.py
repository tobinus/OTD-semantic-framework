import csv
import functools
from rdflib import URIRef
from db.graph import Ontology, Dataset
from utils.graph import create_bound_graph, RDF, DCAT
from similarity.generate import add_similarity_link


def csv2rdf(fn, dialect):
    """
    Convert a CSV file into an RDF similarity graph.

    Args:
        fn: File handler for a file opened for reading, with newline=''
        dialect: CSV dialect to use when parsing fn.

    Returns:
        Similarity graph with the dataset-concept links named in the CSV file.
    """
    # Initialize what we need
    graph = create_bound_graph()
    csv_reader = csv.reader(fn, dialect=dialect)
    concept_uris = set(Ontology.from_uuid().get_concepts().values())
    dataset_uris = get_dataset_uris()
    first_row = next(csv_reader)

    # Which column tells us where datasets are found?
    dataset_index = find_dataset_index(first_row)

    # What kind of CSV do we have? One where concepts are listed in one column,
    # or one where different columns represent different concepts?
    if 'Concepts' in first_row or 'concepts' in first_row:
        analyzer = CsvSingleColumnAnalyzer(first_row, concept_uris)
    else:
        analyzer = CsvMultipleColumnAnalyzer(first_row, concept_uris)

    # Populate the graph, for each dataset in the CSV
    for row in csv_reader:
        # What dataset is this row about?
        dataset = row[dataset_index]
        if dataset not in dataset_uris:
            raise ValueError(f'Dataset {dataset} not recognized')

        # What concepts should this dataset be linked to?
        relevant_concepts = analyzer.find_concepts_for(row)

        # Perform the linking
        for concept in relevant_concepts:
            add_similarity_link(
                graph,
                URIRef(dataset),
                concept,
            )
    return graph


def get_dataset_uris():
    """
    Fetch the known datasets from the database.

    Returns:
        Set of dataset URIs, from the dataset graph in the DB.
    """
    dataset_graph = Dataset.from_uuid().graph
    return set(
        map(
            str,
            dataset_graph.subjects(RDF.type, DCAT.Dataset)
        )
    )


def find_dataset_index(row):
    """
    Find what column has the "Dataset" label.

    Args:
        row: The row with the headers for this table, typically the first.

    Returns:
        Index of the "Dataset" column.

    Raises:
        ValueError: If no dataset column can be found.
    """
    return find_index(
        'Dataset',
        row,
        'There is no designated column for "Dataset"'
    )


def find_index(column_name, row, error_msg):
    """
    Find what column has the specified label.

    The search is case insensitive.

    Args:
        column_name: Column label to search for
        row: The row with the headers for this table, typically the first.
        error_msg: Error message to raise with ValueError.

    Returns:
        Index of the column with the specified name.

    Raises:
        ValueError: If no column named column_name can be found.
    """
    for i, cell in enumerate(row):
        if cell.strip().lower() == column_name.lower():
            return i
    else:
        raise ValueError(error_msg)


class CsvSingleColumnAnalyzer:
    """
    Class used for finding what concepts each dataset is linked to, when the
    concepts are listed in a single cell for each dataset.
    """

    def __init__(self, first_row, concept_uris):
        """
        Initialize the class for finding concepts for datasets in one column.

        Args:
            first_row: The row with the column labels, used for figuring out
                which column contains the concepts.
            concept_uris: All known concepts, used for figuring out the whole
                URI of concepts where only the last part is in the CSV.
        """
        self.concepts_index = \
            CsvSingleColumnAnalyzer.find_concepts_index(first_row)
        self.concepts_recognizer = ConceptRecognizer(concept_uris)

    @staticmethod
    def find_concepts_index(first_row):
        """
        Find the index of the column where concepts are listed.

        Args:
            first_row: The row with the column labels.

        Returns:
            Index of the column where concepts are listed.
        """
        return find_index(
            'concepts',
            first_row,
            'There is no designated column for "Concepts"'
        )

    def find_concepts_for(self, row):
        """
        Find the concepts that this dataset should be linked to.

        Args:
            row: One row, representing one dataset.

        Returns:
            Concepts (URIRef) that should be linked to the given dataset.
        """
        concept_refs = self.get_user_concepts_for(row)
        return map(self.concepts_recognizer.get_concept_from, concept_refs)

    def get_user_concepts_for(self, row):
        """
        Find the concepts that user wrote for the corresponding row.

        These concepts do not need to exist, this is simply what the user wrote.

        Args:
            row: One row, representing one dataset.

        Returns:
            Concepts the user wants to connect with this dataset.
        """
        cell = row[self.concepts_index]
        concept_refs = filter(None, map(lambda s: s.strip(), cell.split(',')))
        return concept_refs


def check_csv_for_unknown_concepts(fn, dialect):
    csv_reader = csv.reader(fn, dialect=dialect)
    concept_uris = set(Ontology.from_uuid().get_concepts().values())
    first_row = next(csv_reader)

    analyzer = CsvSingleColumnAnalyzer(first_row, concept_uris)

    concept_column = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[analyzer.concepts_index]

    errors = dict()

    # Check for each row
    for i, row in enumerate(csv_reader, start=2):
        # What concepts did the user write?
        user_concepts = analyzer.get_user_concepts_for(row)
        for concept in user_concepts:
            try:
                analyzer.concepts_recognizer.get_concept_from(concept)
            except ValueError:
                errors.setdefault(concept, []).append(i)

    for unrecognized_concept, rows in errors.items():
        cells = map(lambda r: concept_column + str(r), rows)
        print(unrecognized_concept + ":", ", ".join(cells))
    return errors


class CsvMultipleColumnAnalyzer:
    """
    Class used for finding what concepts each dataset is linked to, when each
    concept has a column of its own.
    """

    def __init__(self, first_row, concept_uris):
        """
        Initialize the class for finding concepts for datasets in multiple
        columns.

        Args:
            first_row: The row with the column labels, used for figuring out
                which columns map to which concepts.
            concept_uris: All known concepts, used for figuring out what
                concept each column refers to, if any.
        """
        self.concept_columns = CsvMultipleColumnAnalyzer.find_concept_columns(
            first_row,
            concept_uris
        )

    @staticmethod
    def find_concept_columns(first_row, concept_uris):
        """
        Create mapping between column and the concept it refers to.

        Args:
            first_row: The row with the column labels.
            concept_uris: All known concepts.

        Returns:
            Dictionary where the column index is the key, and the concept
            associated with that column is the value.
        """
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
        """
        Find the concepts that this dataset should be linked to.

        Args:
            row: One row, representing one dataset.

        Returns:
            Concepts (URIRef) that should be linked to the given dataset.
        """
        concepts = []

        for index, concept in self.concept_columns.items():
            if row[index].strip():
                concepts.append(concept)
        return concepts


def as_uriref(func):
    """
    Decorator which ensures that the decorated function returns a URIRef.

    Args:
        func: Function whose return value should always be converted into
            a URIRef.

    Returns:
        Function which is exactly like the given function, except its return
        value is converted into a URIRef.
    """
    @functools.wraps(func)
    def add_uriref(*args, **kwargs):
        return URIRef(func(*args, **kwargs))

    return add_uriref


class ConceptRecognizer:
    """
    Class for finding out what concept any given string refers to.
    """

    def __init__(self, concepts):
        """
        Initialize class for finding out what concept any string refers to.

        Args:
            concepts: All concepts to recognize, as their fully qualified URIs.
        """
        self.concepts = {
            get_fragment(str(uri).lower()): str(uri) for uri in concepts
        }
        self.concept_uris = set(str(uri) for uri in concepts)

    @as_uriref
    def get_concept_from(self, str_):
        """
        Find the full URI of the concept referred to by the given string.

        Args:
            str_: Either the full URI of a concept, or the final part of such a
                URI.

        Returns:
            Full URI of the concept recognized from the given string.

        Raises:
            ValueError: When no matching concept can be found.
        """
        str_ = str_.strip()

        if str_ in self.concept_uris:
            # We were handed a whole URI
            return str_

        if str_.lower() in self.concepts:
            return self.concepts[str_.lower()]

        raise ValueError(f'The concept "{str_}" was not recognized')


def get_fragment(uri):
    """
    Get the final part of the URI.

    The final part is the text after the last hash (#) or slash (/), and is
    typically the part that varies and is appended to the namespace.

    Args:
        uri: The full URI to extract the fragment from.

    Returns:
        The final part of the given URI.
    """
    fragment_delimiters = ('#', '/')
    alternatives = tuple(
        uri.rsplit(delimiter, maxsplit=1)[-1]
        for delimiter in fragment_delimiters
        if delimiter in uri
    )
    # Return whatever alternative is shortest
    return min(alternatives, key=len)
