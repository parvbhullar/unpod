from bson import ObjectId


def get_document_id_query(document_id):
    query = {}
    try:
        obj = ObjectId(document_id)
        query = {"_id": obj}
    except Exception as ex:
        query = {"document_id": document_id}
    return query
