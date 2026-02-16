import json
from django.conf import settings
from django.core.cache import cache
import requests


def fetch_block(post_id):
    key = f"answer_block_{post_id}"
    data = cache.get(key)
    if data:
        return json.loads(data)
    url = f"{settings.API_SERVICE_URL}/conversation/{post_id}/answer/"
    try:
        hit = requests.get(url=url, timeout=30)

        # Check if request was successful
        if hit.status_code != 200:
            print(f"fetch_block: HTTP {hit.status_code} for post_id {post_id}")
            return {}

        # Check if response is empty
        if not hit.text or not hit.text.strip():
            print(f"fetch_block: Empty response for post_id {post_id}")
            return {}

        # Try to parse JSON
        data = hit.json()
        if data.get("data") and len(data.get("data", {})):
            block_data = data.get("data")
            cache.set(key, json.dumps(block_data), 60 * 60 * 24)
            return block_data
    except requests.exceptions.RequestException as e:
        print(f"fetch_block: Request error for post_id {post_id}: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"fetch_block: JSON decode error for post_id {post_id}: {str(e)}")
        print(f"fetch_block: Response text: {hit.text[:200]}")
    except Exception as e:
        print(f"fetch_block: Unexpected error for post_id {post_id}: {str(e)}")

    return {}
