import httpx
import asyncio
import time


def fetch_with_manual_retry(
    client: httpx.Client | httpx.AsyncClient,
    method: str,
    url: str,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    retry_statuses: set = {429, 500, 502, 503, 504},
    **kwargs,
):
    """
    Fetch with manual retry - works with both sync and async clients.
    Returns a coroutine if AsyncClient is passed, otherwise executes synchronously.
    """
    if isinstance(client, httpx.AsyncClient):
        return _async_fetch_with_retry(
            client, method, url, max_retries, backoff_factor, retry_statuses, **kwargs
        )
    else:
        return _sync_fetch_with_retry(
            client, method, url, max_retries, backoff_factor, retry_statuses, **kwargs
        )


async def _async_fetch_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    max_retries: int,
    backoff_factor: float,
    retry_statuses: set,
    **kwargs,
):
    last_exception = None

    for attempt in range(max_retries):
        try:
            response = await client.request(method, url, **kwargs)

            if response.status_code in retry_statuses:
                retry_after = float(
                    response.headers.get("Retry-After", backoff_factor * (2**attempt))
                )
                await asyncio.sleep(retry_after)
                continue

            response.raise_for_status()
            return response

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            last_exception = e
            await asyncio.sleep(backoff_factor * (2**attempt))

    raise last_exception or Exception("Max retries exceeded")


def _sync_fetch_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    max_retries: int,
    backoff_factor: float,
    retry_statuses: set,
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
