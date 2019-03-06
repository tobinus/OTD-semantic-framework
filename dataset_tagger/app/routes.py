from bson.errors import InvalidId
from flask import render_template, request, redirect, url_for, abort, jsonify
from dataset_tagger.app import app, app_path
from dataset_tagger.app.forms import TagForm
from time import sleep

import db.graph
from similarity.generate import add_similarity_link
from utils.graph import create_bound_graph, RDF, DCAT
from rdflib import URIRef


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
        return abort(401)

    data = request.json
    linked_dataset_url = data['dataset']
    concept_url = data['concept']

    try:
        new_id = add_tagging(configuration, linked_dataset_url, concept_url)
        result = {'success': True, 'id': new_id}
    except Exception as e:
        result = {'success': False, 'message': str(e)}

    return jsonify(result)
    
def add_tagging(configuration, linked_dataset_url, concept_label):
    similarity = configuration.get_similarity()
    ontology = similarity.get_ontology()
    concepts = ontology.get_concepts()
    dataset = similarity.get_dataset()

    # Fetch information about this dataset
    linked_dataset_graph = create_bound_graph()
    linked_dataset_graph.parse(linked_dataset_url, format='xml')
    dataset_uri = next(linked_dataset_graph.subjects(RDF.type, DCAT.Dataset))

    # Do we already have this in our dataset graph?
    if (dataset_uri, RDF.type, DCAT.Dataset) not in dataset.graph:
        # Nope, add it
        dataset.graph.parse(linked_dataset_url)
        dataset.save()

    # Create the link
    if concept_label in concepts.items():
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

