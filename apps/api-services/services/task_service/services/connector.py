from libs.core.exceptions import APICommonException


async def fetch_contact_data(filters, space_token):
    from services.store_service.views.connector import fetch_collector_based_data

    if "fetch_all" not in filters and len(filters) > 0:
        filters["fetch_all"] = "1"
    data = await fetch_collector_based_data(
        space_token, limit=0, skip=0, query_params=filters
    )
    if data.get("success") is False:
        raise APICommonException({"message": data.get("message"), "status_code": 206})
    count = data.get("count", 0)
    if count <= 0:
        return []
    return data.get("data", {}).get("data", [])
