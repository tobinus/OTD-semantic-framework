from bson.errors import InvalidId
from flask import render_template, request, redirect, url_for, abort
from dataset_tagger.app import app, app_path
from dataset_tagger.app.forms import TagForm
import db.graph
from db.graph import NoSuchGraph


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/viz', methods=['GET'])
def viz():
    uuid = request.args.get('uuid', default=None, type=None)


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    form=TagForm()
    foo = ''
    uuid = request.args.get('uuid', default=None, type=None)
    if not uuid:
        return redirect(url_for('about'))        
    
    if request.method == 'POST':
        try:
            dataset = request.form.get('dcatDataset')
            tag = request.form.get('tag')
            score = 1.0
            foo = str(db.graph.tag_dataset(uuid, dataset, tag, score))
            
        except Exception as e:
            foo = str(e)
            pass

    try:
        g = db.graph.get(uuid)
    except (NoSuchGraph, InvalidId):
        abort(404)

    edges = []
    nodes = []
    for s, _, o in g.triples( (None, None, None)):
        if (s.find('#') >= 0):
            x = s[s.index('#')+1:]
        else:
            x = s
        if (o.find('#') >= 0):
            y = o[o.index('#')+1:]
        else:
            y = o
        nodes.append(x)
        nodes.append(y)
        edges.append((x, y))

    nodeset = set(nodes)
    ns = []
    for n in nodeset:
        if n != 'Class':
            ns.append("{"+ "id :'{}',label:'{}'".format(n,n)+ "}")
    es = ",".join(["{"+ "from:'{}',to:'{}'".format(a,b) +"}" for (a,b) in edges])
    
        
    leketag = db.graph.get_tagged_datasets(uuid)
    return render_template(
        'index.html',
        form=form,
        concepts=db.graph.get_concepts(uuid),
        tagged=leketag,
        uuid=uuid,
        foo=foo,
        edges=es,
        nodes=",".join(ns)
    )
   

@app.route('/ontology/fetch/<string:uuid>')
def ontology_fetch(uuid):
    try:
        return db.graph.get_raw_json(uuid)
    except (NoSuchGraph, InvalidId):
        abort(404)


@app.route('/ontology/delete/<string:uuid>', methods=['GET'])
def ontology_delete(uuid):
    pass


@app.route('/ontology/create', methods=['GET'])
def ontology_create():
    uuid = db.graph.create_new()
    return str({'uuid': uuid})


@app.route('/ontology/list', methods=['GET'])
def ontology_list():
    return str({'ontologies': db.graph.find_all_ids()})
#    path = os.path.join(app_path, 'db')
#    ontologies = [splitext(f)[0] for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
#    return str({'ontologies':ontologies})
