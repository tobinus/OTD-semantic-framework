from flask import render_template, request, redirect, url_for
from dataset_tagger.app import app, app_path
from dataset_tagger.odt.ontology import fetch, create_new_graph, get_concepts, tag_dataset
from dataset_tagger.odt.ontology import tagged_datasets, get_graph, find_all_ids
from dataset_tagger.app.forms import TagForm


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/viz', methods=['GET'])
def viz():
    uid = request.args.get('uid', default=None, type=None)


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    form=TagForm()
    foo = ''
    uid = request.args.get('uid', default=None, type=None)
    if not uid:
        return redirect(url_for('about'))        
    
    if request.method == 'POST':
        try:
            dataset = request.form.get('dcatDataset')
            tag = request.form.get('tag')
            score = 1.0
            foo = str(tag_dataset(uid, dataset, tag, score))
            
        except Exception as e:
            foo = str(e)
            pass

    
    g = get_graph(uid)
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
    
        
    leketag = tagged_datasets(uid)
    return render_template('index.html', form=form, concepts=get_concepts(uid), tagged=leketag, uid=uid, foo=foo, edges=es, nodes=",".join(ns))
   

@app.route('/ontology/fetch/<string:uid>')
def ontology_fetch(uid):
    return fetch(uid)


@app.route('/ontology/delete/<string:uid>', methods=['GET'])
def ontology_delete(uid):
    pass


@app.route('/ontology/create', methods=['GET'])
def ontology_create():
    uid = create_new_graph()
    return str({'uid': uid})



@app.route('/ontology/list', methods=['GET'])
def ontology_list():
    return str({'ontologies': find_all_ids()})
#    path = os.path.join(app_path, 'db')
#    ontologies = [splitext(f)[0] for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
#    return str({'ontologies':ontologies})
