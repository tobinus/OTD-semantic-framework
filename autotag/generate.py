from sys import stderr
from uuid import uuid4
import clint.textui
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from rdflib import URIRef, Literal, XSD
import db.graph
from utils import word_similarity
from utils.graph import RDF, DCAT, DCT, SKOS, QEX, OTD, create_bound_graph
from utils.nlp import normalize, remove_stopwords_nb


def generate_autotag(
        quiet,
        language,
        semantic_threshold,
        min_concepts
):
    corpus = get_dataset_texts(quiet=quiet)
    concept_labels = get_concept_labels(
        quiet=quiet,
        language=language
    )
    similarity_graph = create_autotag_graph(
        corpus,
        concept_labels,
        quiet,
        language,
        semantic_threshold,
        min_concepts,
    )
    return similarity_graph


def get_dataset_texts(quiet):
    progress_print(quiet, 'Loading datasets from database…')
    dataset = db.graph.Dataset.from_uuid().graph

    progress_print(quiet, 'Checking how many datasets to process…')
    num_datasets = len(tuple(dataset.subjects(RDF.type, DCAT.Dataset)))

    corpus = dict()
    for dataset_ref in clint.textui.progress.bar(
        dataset.subjects(RDF.type, DCAT.Dataset),
        'Extracting text from datasets',
        hide=quiet or None,
        expected_size=num_datasets,
    ):
        properties = dict(dataset.predicate_objects(dataset_ref))
        title = properties.get(DCT.title, '')
        description = properties.get(DCT.description, '')
        if not (title and description):
            continue

        text = '. '.join((title, description))

        parsed_html = BeautifulSoup(text, 'html5lib')
        if bool(parsed_html.find()):
            text = parsed_html.text
        corpus[dataset_ref] = text
    dataset.close()
    return corpus


def get_concept_labels(quiet, language):
    progress_print(quiet, 'Loading ontology from database…')
    ontology = db.graph.Ontology.from_uuid().graph

    progress_print(quiet, 'Extracting ontology labels from graph…')

    concept_labels = dict()
    for concept in ontology.subjects(RDF.type, SKOS.Concept):
        pref = [
            o.value
            for o in ontology.objects(concept, SKOS.prefLabel)
            if o.language == language
        ]
        alt = [
            o.value
            for o in ontology.objects(concept, SKOS.altLabel)
            if o.language == language
        ]
        concept_labels[concept] = pref+alt

    return concept_labels


def create_autotag_graph(
        corpus,
        concept_labels,
        quiet,
        language,
        semantic_threshold,
        min_concepts,
):
    progress_print(quiet, 'Loading dictionary used to find similar words.')
    progress_print(quiet, 'This is known to take 7 minutes or more, hang on…')
    comparator = word_similarity.get_comparator(language)
    comparator.ensure_loaded_corpus()
    progress_print(quiet, 'Done loading dictionary.')

    similarity_graph = create_bound_graph()

    for dataset, text in clint.textui.progress.bar(
        corpus.items(),
        'Associating datasets to concepts',
        hide=quiet or None,
        expected_size=len(corpus),
    ):
        tokens = word_tokenize(text)
        tokens = tuple(normalize(remove_stopwords_nb(tokens)))

        # Compute the relevance for each concept
        scorelist = []
        for concept, labels in concept_labels.items():
            scores = tuple(map(
                lambda token: compute_score(token, labels, comparator),
                tokens
            ))
            score = max(scores, default=0.0)
            scorelist.append((concept, score))
        sorted_scores = sorted(scorelist, key=lambda x: x[1], reverse=True)
        filtered_score = [(c, s) for c, s in sorted_scores if
                          s >= semantic_threshold]
        if len(filtered_score) < min_concepts:
            filtered_score = sorted_scores[:min_concepts]

        # Add the scores to a graph
        for concept, score in filtered_score:
            add_similarity_link(similarity_graph, dataset, concept, score)
    return similarity_graph


def compute_score(word, concept_labels, comparator):
    scores = map(lambda label: comparator.compare(word, label), concept_labels)
    return max(scores, default=0.0)


# Helper method to create a link between a dataset and a concept with
# a given similarity-score
def add_similarity_link(graph, dataset, concept, score):
    uuid = uuid4().hex
    simlink = URIRef(QEX[uuid])
    graph.add((simlink, RDF.type, OTD.Similarity))
    graph.add((simlink, OTD.dataset, dataset))
    graph.add((simlink, OTD.concept, concept))
    graph.add((simlink, OTD.score, Literal(score, datatype=XSD.double)))
    return simlink


def progress_print(quiet, *args, **kwargs):
    if not quiet:
        print(*args, file=stderr, **kwargs)
