from fastapi import Request
from mongomantic import BaseRepository
from libs.core.jsondecoder import convertFromBaseModel, convertFromMongo


def getPagination(request: Request):
    try:
        skip = int(request.query_params.get("skip", "0"))
    except Exception:
        skip = 0
    try:
        limit = int(request.query_params.get("limit", "50"))
    except Exception:
        limit = 50
    return skip, limit


def paginateData(
    model: BaseRepository, request: Request, mongo=False, order=None, **query
):
    try:
        page = int(request.query_params.get("page", "1"))
    except Exception:
        page = 1

    try:
        page_size = int(request.query_params.get("page_size", "50"))
    except Exception:
        page_size = 50
    if not order:
        order = [("_id", -1)]
    if mongo:
        projection = query.get("projection")
        query = query.get("query", {})
        data = (
            model._get_collection()
            .find(query, projection)
            .sort(order)
            .limit(page_size)
            .skip((page - 1) * page_size)
        )
        data = [convertFromMongo(d) for d in data]
        count = model._get_collection().count_documents(query)
    else:
        data = model.find(**query, limit=page_size, skip=(page - 1) * page_size)
        data = [convertFromBaseModel(d) for d in data]
        count = model.count(**query)
    return {"count": count, "data": data}
