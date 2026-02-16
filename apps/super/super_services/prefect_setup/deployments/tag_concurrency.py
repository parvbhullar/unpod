import copy
from tabulate import tabulate
from prefect import get_client


async def create_run_concurrency_tag(run_id: str, concurrency_limit: int = 8):
    """Create a dynamic concurrency tag for a specific run."""
    tag_name = f"run_{run_id}"
    async with get_client() as client:
        await client.create_concurrency_limit(
            tag=tag_name,
            concurrency_limit=concurrency_limit
        )
    return tag_name


async def delete_run_concurrency_tag(run_id: str):
    """Delete the dynamic concurrency tag after run completion."""
    tag_name = f"run_{run_id}"
    async with get_client() as client:
        await client.delete_concurrency_limit_by_tag(tag=tag_name)
    return tag_name


async def create_tag_concurrency_tasks(concurrency_entries):
    sum_headers = ['Tag Name', 'Concurrency Limit', 'Created/Updated', 'Exception']
    CHECK_MARK = "\u2714"
    CROSS_MARK = "\u2718"
    row_data = ['', '', CROSS_MARK, '']
    row_entries = list()
    async with get_client() as client:
        for entry in concurrency_entries:
            row_entry = copy.deepcopy(row_data)
            tag_name = entry.get("tag_name", None)
            concurrency_limit = entry.get("concurrency_limit", None)
            
            if tag_name and concurrency_limit is not None:
                try:
                    row_entry[0] = tag_name
                    row_entry[1] = concurrency_limit
                    # Create a concurrency limit for the specified tag
                    await client.create_concurrency_limit(
                        tag=tag_name, 
                        concurrency_limit=concurrency_limit
                    )
                    row_entry[2] = CHECK_MARK
                    # print(f"Created concurrency limit {limit_id} for tag '{tag_name}' with limit {concurrency_limit}.")
                except Exception as e:
                    # print(f"Failed to create concurrency limit for tag '{tag_name}': {e}")
                    row_entry[3] = str(e)
            row_entries.append(row_entry)

    print('Task Concurrency Info:')
    print(tabulate(row_entries, headers=sum_headers, tablefmt='fancy_grid'))
    
    return True