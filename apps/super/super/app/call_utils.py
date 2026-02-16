import httpx
import time


def fetch_with_manual_retry(
    client: httpx.Client,
    method: str,
    url: str,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    retry_statuses: set = {429, 500, 502, 503, 504},
    **kwargs,
):
    last_exception = None

    for attempt in range(max_retries):
        try:
            response = client.request(method, url, **kwargs)

            if response.status_code in retry_statuses:
                retry_after = float(
                    response.headers.get("Retry-After", backoff_factor * (2**attempt))
                )
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            return response

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            last_exception = e
            time.sleep(backoff_factor * (2**attempt))

    raise last_exception or Exception("Max retries exceeded")
