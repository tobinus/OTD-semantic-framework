from datetime import datetime
from time import time

from flask import render_template, redirect
from flask import request, flash, abort
from flask.json import jsonify

import db.log
from ontosearch.app import app
from ontosearch.app import odsf_loader
from ontosearch.app.forms import SearchForm, ScoreForm
from otd.constants import SIMTYPE_AUTOTAG, SIMTYPE_SIMILARITY
from otd.opendatasemanticframework import ODSFLoader, MissingMatrixError


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    # Disabling CSRF because it does not play nice with multiple workers, plus
    # users are not authenticated so CSRF does not protect against anything
    form = SearchForm(meta={'csrf': False})
    xs = []
    sv = []
    if form.validate_on_submit():
        xs, sv = odsf_loader.get_default().search_query(form.query.data, cds_name=form.simtype.data)
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
    # Disabling CSRF because it does not play nice with multiple workers, plus
    # users are not authenticated so CSRF does not protect against anything
    form = ScoreForm(meta={'csrf': False})

    most_similar_concepts = []

    odsf = odsf_loader.get_default()

    if form.validate_on_submit():
        query_concept_sim = odsf.calculate_query_sim_to_concepts(
            form.query.data,
            0.0
        )

        # What were the most similar concepts?
        most_similar_concepts = odsf.sort_concept_similarities(
            odsf.get_concept_similarities_for_query(
                query_concept_sim
            )
        )

    return render_template(
        "scores.html",
        form=form,
        scorevec=most_similar_concepts,
        concept_labels=get_concept_labels(),
    )


@app.route('/api/v1/search')
def api_search():
    # Ensure mandatory query parameters are present
    if 'q' not in request.args:
        abort(400)

    # Collect parameters from the user
    query = request.args.get('q')
    autotag = request.args.get('a') == '1'
    include_dataset_info = request.args.get('d') != '0'
    include_concepts = request.args.get('ic') != '0'
    configuration_uuid = request.args.get('c', ODSFLoader.DEFAULT_KEY)
    query_concept_sim = request.args.get('qcs', '0.0')
    query_dataset_sim = request.args.get('qds', '0.75')

    # Convert to correct format
    try:
        query_concept_sim = float(query_concept_sim)
    except ValueError:
        return jsonify({'errors': ['qcs value is not a float']}), 400

    try:
        query_dataset_sim = float(query_dataset_sim)
    except ValueError:
        return jsonify({'errors': ['qds value is not a float']}), 400

    # Load the configuration
    try:
        odsf = odsf_loader[configuration_uuid]
    except KeyError:
        return jsonify({'errors': ['Unrecognized configuration UUID']}), 404
    except MissingMatrixError:
        return jsonify({
            'errors': ['Chosen configuration does not have generated matrices']
        }), 500

    # Perform the query
    results, concept_similarities = odsf.search_query(
        query,
        SIMTYPE_AUTOTAG if autotag else SIMTYPE_SIMILARITY,
        query_concept_sim,
        query_dataset_sim,
        include_dataset_info=include_dataset_info,
        include_concepts=include_concepts,
    )

    # Create a representation of the results.
    # namedtuples are treated as tuples, so we must create a comprehensible
    # structure ourself
    return jsonify({
        'concepts': [
            {
                'uri': c.uri,
                'label': c.label,
                'similarity': c.similarity
            }
            for c in concept_similarities
        ],
        'results': [
            {
                'score': d.score,
                'title': d.info.title if include_dataset_info else None,
                'description': d.info.description if include_dataset_info else
                None,
                'uri': d.info.uri if include_dataset_info else d.info,
                'concepts': [
                    {
                        'uri': c.uri,
                        'label': c.label,
                        'similarity': c.similarity,
                    }
                    for c in d.concepts
                ]
            }
            for d in results
        ],
    })


@app.route('/message')
def message():
    flash('This is an example message.')
    return redirect('/')


def get_concept_labels():
    return list(odsf_loader.get_default().navigator.all_concept_labels())
