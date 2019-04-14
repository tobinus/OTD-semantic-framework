from time import sleep

from bson.errors import InvalidId
from flask import render_template, request, redirect, url_for, abort, jsonify
from rdflib import URIRef

import db.graph
from dataset_tagger.app import app
from dataset_tagger.app.forms import TagForm
from similarity.generate import add_similarity_link
from utils.graph import create_bound_graph, RDF, DCAT, OTD, DCT


@app.route('/')
def index():
    if request.args.get('submit_button'):
        uuid = request.args.get('similarity_uuid')
        return redirect(
            url_for('edit', uuid=uuid)
        )

    return render_template(
        'index.html'
    )

@app.route('/edit/<uuid>', methods=['GET', 'POST'])
def edit(uuid):
    form = TagForm()
    result = ''

    try:
        configuration = db.graph.Configuration.from_uuid(uuid)
    except (ValueError, InvalidId):
        # Mitigate against guessing the ID by bruteforce
        sleep(1)
        return abort(404)

    if request.method == 'POST':
        try:
            linked_dataset_url = request.form.get('dcatDataset')
            concept_label = request.form.get('tag')
            result = add_tagging(configuration, linked_dataset_url, concept_label)
        except Exception as e:
            result = str(e)
            pass

    return render_template(
        'edit.html',
        form=form,
        concepts=configuration.get_ontology().get_concepts(),
        result=result,
        configuration=configuration,
    )


@app.route('/api/v1/<uuid>/tagging', methods=['POST'])
def api_add_tagging(uuid):
    try:
        configuration = db.graph.Configuration.from_uuid(uuid)
    except (ValueError, InvalidId):
        # Mitigate against guessing the ID by bruteforce
        sleep(1)
        return abort(404)
    
    if not request.is_json:
        return abort(400)

    # TODO: Authorization

    data = request.json
    # TODO: Display error when fields are missing
    linked_dataset_url = data['dataset_url']
    concept_url = data['concept']

    try:
        new_id = add_tagging(configuration, linked_dataset_url, concept_url)
        # TODO: Handle case where dataset/concept is not recognized
        result = {'success': True, 'id': new_id}
    except Exception as e:
        # TODO: Print stacktrace of some kind, maybe don't leak exceptions
        result = {'success': False, 'message': str(e)}

    return jsonify(result)


def add_tagging(configuration, linked_dataset_url, concept_label):
    similarity = configuration.get_similarity()
    ontology = similarity.get_ontology()
    concepts = ontology.get_concepts()
    dataset = similarity.get_dataset()

    dataset_uri = URIRef(get_dataset_id_from_url(linked_dataset_url))

    # Do we already have this in our dataset graph?
    if (dataset_uri, RDF.type, DCAT.Dataset) not in dataset.graph:
        # Nope, add it
        dataset.graph.parse(linked_dataset_url)
        dataset.save()

    # Create the link
    if concept_label in concepts.values():
        # We have a complete URI already
        concept_uri = concept_label
    else:
        # We might have a label?
        concept_uri = concepts[concept_label]
    
    link_score = 1.0

    link_id = add_similarity_link(
        similarity.graph,
        dataset_uri,
        URIRef(concept_uri),
        link_score
    )
    similarity.save()
    return link_id


@app.route('/api/v1/<uuid>/tagging', methods=['GET'])
def api_get_tagging(uuid):
    try:
        configuration = db.graph.Configuration.from_uuid(uuid)
    except (ValueError, InvalidId):
        # Mitigate against guessing the ID by bruteforce
        sleep(1)
        return abort(404)

    chosen_dataset = get_dataset_id_from_request(is_get=True)

    concepts_by_label = configuration.get_ontology().get_concepts()
    labels_by_concept = {value: key for key, value in concepts_by_label.items()}

    tag_graph = configuration.get_similarity().graph
    dataset_graph = configuration.get_dataset().graph

    taggings_per_dataset = dict()
    for tagging in tag_graph.subjects(RDF.type, OTD.Similarity):
        dataset = tag_graph.value(tagging, OTD.dataset)
        dataset_str = str(dataset)

        if chosen_dataset is not None and chosen_dataset != dataset_str:
            continue

        concept = str(tag_graph.value(tagging, OTD.concept))
        concept_label = labels_by_concept[concept]

        concept_info = {
            'uri': concept,
            'label': concept_label,
        }

        if dataset_str not in taggings_per_dataset:
            title = dataset_graph.value(dataset, DCT.title)
            taggings_per_dataset[dataset_str] = {
                'title': title,
                'concepts': [concept_info],
            }
        else:
            taggings_per_dataset[dataset_str]['concepts'].append(concept_info)

    if chosen_dataset is not None:
        return jsonify(taggings_per_dataset.get(chosen_dataset))
    else:
        return jsonify(taggings_per_dataset)


@app.route('/api/v1/<uuid>/tagging', methods=['DELETE'])
def api_delete_tagging(uuid):
    try:
        configuration = db.graph.Configuration.from_uuid(uuid)
    except (ValueError, InvalidId):
        # Mitigate against guessing the ID by bruteforce
        sleep(1)
        return abort(404)

    if not request.is_json:
        return abort(400)

    # TODO: Authorization

    linked_dataset = get_dataset_id_from_request(required=True)

    # TODO: Handle missing data better
    data = request.json
    concept_url = data['concept']

    # TODO: Handle case where dataset/concept is not recognized
    remove_tagging(configuration, linked_dataset, concept_url)
    return jsonify({'success': True})


@app.route('/api/v1/<uuid>/dataset', methods=['DELETE'])
def api_delete_dataset(uuid):
    try:
        configuration = db.graph.Configuration.from_uuid(uuid)
    except (ValueError, InvalidId):
        # Mitigate against guessing the ID by bruteforce
        sleep(1)
        return abort(404)

    if not request.is_json:
        return abort(400)

    # TODO: Authorization

    # TODO: Handle missing data better
    linked_dataset = get_dataset_id_from_request(required=True)
    # Fetch information about this dataset
    # TODO: Refactor some of the duplication

    # What taggings do we need to remove?
    query = """
        SELECT DISTINCT ?concept 
        WHERE {
            ?tagging a           otd:Similarity ;
                     otd:dataset ?dataset ;
                     otd:concept ?concept .
        }
    """
    r = configuration.get_similarity().graph.query(
        query,
        initBindings={
            'dataset': URIRef(linked_dataset)
        }
    )
    removed_something = False
    for result in r:
        removed_something = True
        concept = result['concept']
        # TODO: Only do the common work once, instead of for each tagging
        remove_tagging(configuration, linked_dataset, str(concept))

    if removed_something:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Dataset not found in DB'})


def remove_tagging(configuration, linked_dataset, concept_label):
    similarity = configuration.get_similarity()
    ontology = similarity.get_ontology()
    concepts = ontology.get_concepts()
    dataset = similarity.get_dataset()

    # Create the link
    if concept_label in concepts.values():
        # We have a complete URI already
        concept_uri = concept_label
    else:
        # We might have a label?
        concept_uri = concepts[concept_label]

    # So, what is the URI for the tagging we're removing?
    r = similarity.graph.query(
        """
        SELECT DISTINCT ?uri
        WHERE {
            ?uri a otd:Similarity .
            ?uri otd:dataset ?dataset .
            ?uri otd:concept ?concept .
        }
        """,
        initBindings={
            'dataset': URIRef(linked_dataset),
            'concept': URIRef(concept_uri)
        }
    )
    # Get first row of results, and extract the only variable assigned there
    # (?uri)
    try:
        tagging = next(iter(r))['uri']
    except StopIteration as e:
        # No binding found
        # TODO: Report this nicely to the user
        raise RuntimeError('No tagging found for the specified dataset and '
                           'concept') from e

    # Remove all triples pertaining to this tagging
    similarity.graph.remove((tagging, None, None))

    # Are there any taggings left for this dataset?
    if (None, OTD.dataset, URIRef(linked_dataset)) not in similarity.graph:
        # Nope, remove the dataset itself
        dataset.graph.remove((URIRef(linked_dataset), None, None))
        dataset.save()

    similarity.save()
    return True


@app.route('/api/v1/<uuid>/concept', methods=['GET'])
def api_get_concept(uuid):
    try:
        configuration = db.graph.Configuration.from_uuid(uuid)
    except (ValueError, InvalidId):
        # Mitigate against guessing the ID by bruteforce
        sleep(1)
        return abort(404)

    concepts_by_label = configuration.get_ontology().get_concepts()
    labels_by_concept = {value: key for key, value in concepts_by_label.items()}

    return jsonify(labels_by_concept)


def get_dataset_id_from_request(is_get=False, required=False):
    if not is_get:
        data = request.json

        dataset_id = data.get('dataset_id')
        dataset_url = data.get('dataset_url')
    else:
        dataset_id = request.args.get('dataset_id')
        dataset_url = request.args.get('dataset_url')

    if dataset_id:
        # The user provided the RDF IRI directly
        return dataset_id
    elif not dataset_url:
        # The user provided no dataset information. Is this an error?
        if required:
            raise RuntimeError(
                'No dataset was specified. Please specify either dataset_id or '
                'dataset_url.'
            )
        else:
            return None

    # Fetch information about this dataset using the URL
    return get_dataset_id_from_url(dataset_url)


def get_dataset_id_from_url(dataset_url):
    linked_dataset_graph = create_bound_graph()
    linked_dataset_graph.parse(dataset_url, format='xml')
    try:
        return str(next(linked_dataset_graph.subjects(RDF.type, DCAT.Dataset)))
    except StopIteration:
        raise ValueError(f'No dataset information was found at the specified '
                         f'URL ({dataset_url})')
