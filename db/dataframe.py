import json
from rdflib import URIRef
import pandas as pd
from utils.db import MongoDBConnection


def store(df, graph_identifier, **kwargs):
    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        j = df.to_json(orient='split')
        doc = {
            'df': j,
            'graphType': graph_identifier.graph_type,
            'graphUuid': graph_identifier.graph_uuid,
            'lastModified': graph_identifier.last_modified,
        }
        existing_id = _get_uuid_for_outdated(graph_identifier, **kwargs)
        is_update = existing_id is not None
        if is_update:
            db.dataframe.replace_one(
                {'_id': existing_id},
                doc,
            )
            return str(existing_id)
        else:
            return str(db.dataframe.insert_one(doc).inserted_id)


def get(graph_identifier, **kwargs):
    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        doc = db.dataframe.find_one({
            'graphType': graph_identifier.graph_type,
            'graphUuid': graph_identifier.graph_uuid,
            'lastModified': graph_identifier.last_modified,
        })
        if doc is None:
            return None
        js = json.loads(doc['df'])
    js['columns'] = list(map(lambda x: URIRef(x), js['columns']))
    js['index'] = list(map(lambda x: URIRef(x), js['index']))
    df = pd.DataFrame(data=js['data'], index=js['index'], columns=js['columns'])
    return df


def _get_uuid_for_outdated(graph_identifier, **kwargs):
    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        doc = db.dataframe.find_one({
            'graphType': graph_identifier.graph_type,
            'graphUuid': graph_identifier.graph_uuid,
        })
        if doc is None:
            return None
        return doc['_id']
