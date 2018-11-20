import json
from rdflib import URIRef
from bson.objectid import ObjectId
import pandas as pd
from utils.db import MongoDBConnection


def store(df, **kwargs):
    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        j = df.to_json(orient='split')
        return db.dataframe.insert_one({'df': j}).inserted_id


def get(uid, **kwargs):
    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        doc = db.dataframe.find_one({'_id': ObjectId(uid)})
        js = json.loads(doc['df'])
    js['columns'] = list(map(lambda x: URIRef(x), js['columns']))
    js['index'] = list(map(lambda x: URIRef(x), js['index']))
    df = pd.DataFrame(data=js['data'], index=js['index'], columns=js['columns'])
    return df
