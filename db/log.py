from utils.db import MongoDBConnection


def store(json, **kwargs):
    with MongoDBConnection(**kwargs) as client:
        db = client.ontodb
        db.log.insert_one(json)
