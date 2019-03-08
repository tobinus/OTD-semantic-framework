from flask import render_template, redirect, url_for
from flask import request, flash, abort, json
from flask import Response
from flask.json import jsonify
from ontosearch.app import app
from ontosearch.app import odsf_loader
from ontosearch.app.forms import SearchForm, ScoreForm
from time import time
from datetime import datetime
import db.log
from otd.constants import SIMTYPE_AUTOTAG, SIMTYPE_SIMILARITY
from otd.opendatasemanticframework import ODSFLoader, MissingMatrixError


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = SearchForm()
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
    form = ScoreForm()

    most_similar_concepts = []

    ontology = odsf_loader.get_default()

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


@app.route('/api/v1/search')
def api_search():
    if 'q' not in request.args:
        abort(400)

    query = request.args.get('q')
    autotag = request.args.get('a') == '1'
    configuration_uuid = request.args.get('c', ODSFLoader.DEFAULT_KEY)

    try:
        odsf = odsf_loader[configuration_uuid]
    except KeyError:
        return jsonify({'errors': ['Unrecognized configuration UUID']}), 404
    except MissingMatrixError:
        return jsonify({
            'errors': ['Chosen configuration does not have generated matrices']
        }), 500

    results, concept_similarities = odsf.search_query(
        query,
        SIMTYPE_AUTOTAG if autotag else SIMTYPE_SIMILARITY,
    )

    # namedtuples are treated as tuples, so we must create a comprehensible
    # structure ourself
    return jsonify({
        'concepts': [
            {
                'concept': c.concept,
                'similarity': c.similarity
            }
            for c in concept_similarities
        ],
        'results': [
            {
                'score': d.score,
                'title': d.info.title,
                'description': d.info.description,
                'uri': d.info.uri,
                'concepts': [
                    {
                        'concept': c.concept,
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
