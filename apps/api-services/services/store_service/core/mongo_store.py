import pandas as pd
from mongomantic.core.database import MongomanticClient


def get_mongo_default():
    return MongomanticClient.db


class MongoStore:
    def __init__(self, collection=None, client=None):
        if client is None:
            self.client = get_mongo_default()
        if collection is None:
            raise ValueError("Collection name is required")
        self.collection = collection
        if isinstance(self.collection, str):
            self.collection = self.client[self.collection]

    def create_store(self, schema=None):
        if schema is None:
            return
        for field in schema.get("CollectionFields", []):
            if field.get("Indexed", False):
                self.collection.create_index(field["Name"])
        return "MongoDB collection created successfully"

    def save_data(self, data=None):
        if isinstance(data, pd.DataFrame):
            records = data.to_dict("records")
        else:
            records = data
        res = self.collection.insert_many(records)
        return f"Data saved to MongoDB successfully, Inserted Count - {len(res.inserted_ids)}"

    def fetch_data(self, *args, **kwargs):
        return list(self.collection.find(*args, **kwargs))

    def count_data(self, *args, **kwargs):
        return self.collection.count_documents(*args, **kwargs)
