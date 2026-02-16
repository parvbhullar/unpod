import json
from django.conf import settings
from django.core.cache import cache
import requests


def fetch_notebook_data(thread_id, pilot_handle):
    key = f"notebook_data_{thread_id}_{pilot_handle}"
    data = cache.get(key)
    if data:
        return json.loads(data)
    url = f"{settings.API_SERVICE_URL}/book/{thread_id}/data/{pilot_handle}/"
    try:
        hit = requests.get(url=url, timeout=30)
        data = hit.json()
        if data.get("data") and len(data.get("data", {})):
            block_data = data.get("data")
            cache.set(key, json.dumps(block_data), 20)
            return block_data
    except requests.exceptions.Timeout:
        print(f"Timeout fetching notebook data for thread {thread_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching notebook data: {e}")
    return {}


def fetch_notebook_collection_org(org_id, pilot_handle):
    key = f"notebook_data_org_{org_id}_{pilot_handle}"
    data = cache.get(key)
    if data:
        return json.loads(data)
    url = (
        f"{settings.API_SERVICE_URL}/book/{org_id}/collection-org/{pilot_handle}/"
    )
    try:
        hit = requests.get(url=url, timeout=30)
        data = hit.json()
        if data.get("data") and len(data.get("data", {})):
            block_data = data.get("data")
            cache.set(key, json.dumps(block_data), 20)
            return block_data
    except requests.exceptions.Timeout:
        print(f"Timeout fetching notebook collection for org {org_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching notebook collection: {e}")
    return {}
