import csv
from db import graph
from utils.graph import RDF, DCAT, DCT, SKOS
from similarity.parse import get_fragment


def prepare_csv(csv_fn, dialect):
    writer = csv.writer(csv_fn, dialect)
    concepts = get_concepts_in_dfs_order()
    dataset = graph.get_dataset(raise_on_no_uuid=False)

    headers = ('Dataset', 'Title', 'Description') + tuple(concepts)
    writer.writerow(headers)

    for this_dataset in dataset.subjects(RDF.type, DCAT.Dataset):
        uri = str(this_dataset)
        title = dataset.value(subject=this_dataset, predicate=DCT.title)
        description = dataset.value(
            subject=this_dataset,
            predicate=DCT.description
        )

        writer.writerow((uri, title, description))


def get_concepts_in_dfs_order():
    ontology = graph.get_ontology(raise_on_no_uuid=False)

    # Assuming only one top concept
    top_concept = next(ontology.subjects(SKOS.topConceptOf))

    concepts = ontology.transitive_subjects(SKOS.broader, top_concept)

    return map(get_fragment, map(str, concepts))
