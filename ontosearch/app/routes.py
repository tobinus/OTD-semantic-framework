from flask import render_template, redirect, url_for
from flask import request, flash, abort, json
from flask import Response
from flask.json import jsonify
from ontosearch.app import app
from ontosearch.app import ontology
from ontosearch.app.forms import SearchForm, ScoreForm
from time import time
from datetime import datetime
import db.log


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    xs = []
    sv = []
    if form.validate_on_submit():
        xs, sv = ontology.search_query(form.query.data, cds_name=form.simtype.data)
        timestamp = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
        log = {'ip':request.remote_addr, 'time':timestamp, 'query':form.query.data, 'type':form.simtype.data, 'res':[x[1][2] for x in xs]}
        db.log.store(log)
    return render_template(
        "search.html",
        form=form,
        results=xs,
        scorevec=sv,
        concept_labels=get_concept_labels(),
    )


@app.route('/scores', methods=['GET', 'POST'])
def scores():
    form = ScoreForm()

    most_similar_concepts = []

    if form.validate_on_submit():
        query_concept_sim = ontology.calculate_query_sim_to_concepts(form.query.data)

        # What were the most similar concepts?
        most_similar_concepts = ontology.sort_concept_similarities(
            ontology.get_concept_similarities_for_query(
                query_concept_sim
            )
        )

    return render_template(
        "scores.html",
        form=form,
        scorevec=most_similar_concepts,
        concept_labels=get_concept_labels(),
    )


@app.route('/message')
def message():
    flash('This is an example message.')
    return redirect('/')


def get_concept_labels():
    return list(ontology.navigator.all_concept_labels())


@app.route('/dataset/register', methods=['POST'])
def dataset_register():
    if not request.json or not 'uri' in request.json:
        abort(400)
    ontology.register_dataset(request.json['uri'])
    return jsonify({'status':'ok'}), 201

@app.route('/similarity/register', methods=['POST'])
def similarity_register():    
    if request.headers['Content-Type'] == 'application/json':
        data = json.dumps(request.json)
        ontology.register_similarity(data)
        return jsonify({'status':'ok'}), 201    
    abort(400)

@app.route('/status')
def status():
    datasets = ontology.datasets()
    similarities = ontology.similarities()
    if (datasets):
        flash('<p>'.join(datasets) + '<br/>' + '<p>'.join(similarities))
    return redirect(url_for('index'))

@app.route('/ontology/fetch')
def fetch_ontology():
    
    return Response(ontology.graph.serialize(format='xml'), mimetype='text/xml')
