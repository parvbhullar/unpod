import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict

from prefect import flow, task, get_run_logger
from prefect.client.orchestration import get_client
from prefect.client.schemas.filters import (
    FlowRunFilter,
    FlowRunFilterState,
    FlowRunFilterStateType,
    FlowRunFilterStartTime,
)
from prefect.client.schemas.objects import StateType
from prefect.exceptions import ObjectNotFound
from pymongo import MongoClient

from super_services.libs.config import settings


def save_cleanup_stats(stats: Dict) -> None:
    """Save cleanup statistics to MongoDB."""
    client = MongoClient(settings.MONGO_DSN)
    db = client[settings.MONGO_DB]
    collection = db["cleanup_stats"]
    collection.insert_one(stats)
    client.close()


@task
async def delete_old_flow_runs(days_to_keep: int = 10, batch_size: int = 100):
    """Delete completed flow runs older than specified days."""
    logger = get_run_logger()

    deleted_by_state: Dict[str, int] = defaultdict(int)
    deleted_by_flow: Dict[str, int] = defaultdict(int)
    failed_deletes_count = 0

    async with get_client() as client:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        flow_run_filter = FlowRunFilter(
            start_time=FlowRunFilterStartTime(before_=cutoff),
            state=FlowRunFilterState(
                type=FlowRunFilterStateType(
                    any_=[StateType.COMPLETED, StateType.FAILED, StateType.CANCELLED]
                )
            ),
        )

        flow_runs = await client.read_flow_runs(
            flow_run_filter=flow_run_filter, limit=batch_size
        )

        deleted_total = 0
        flow_cache: Dict[str, str] = {}

        while flow_runs:
            batch_deleted = 0
            failed_deletes = []

            for flow_run in flow_runs:
                try:
                    state_name = (
                        flow_run.state.type.value if flow_run.state else "UNKNOWN"
                    )
                    flow_id_str = str(flow_run.flow_id)

                    if flow_id_str not in flow_cache:
                        try:
                            flow_obj = await client.read_flow(flow_run.flow_id)
                            flow_cache[flow_id_str] = flow_obj.name
                        except Exception:
                            flow_cache[flow_id_str] = flow_id_str

                    flow_name = flow_cache[flow_id_str]

                    await client.delete_flow_run(flow_run.id)
                    deleted_total += 1
                    batch_deleted += 1
                    deleted_by_state[state_name] += 1
                    deleted_by_flow[flow_name] += 1
                except ObjectNotFound:
                    deleted_total += 1
                    batch_deleted += 1
                except Exception as e:
                    logger.warning(f"Failed to delete flow run {flow_run.id}: {e}")
                    failed_deletes.append(flow_run.id)
                    failed_deletes_count += 1

                if batch_deleted % 10 == 0:
                    await asyncio.sleep(0.5)

            logger.info(
                f"Deleted {batch_deleted}/{len(flow_runs)} flow runs (total: {deleted_total})"
            )
            if failed_deletes:
                logger.warning(f"Failed to delete {len(failed_deletes)} flow runs")

            flow_runs = await client.read_flow_runs(
                flow_run_filter=flow_run_filter, limit=batch_size
            )

            await asyncio.sleep(1.0)

        logger.info(f"Retention complete. Total deleted: {deleted_total}")

    cleanup_stats = {
        "run_date": datetime.now(timezone.utc),
        "days_to_keep": days_to_keep,
        "total_deleted": deleted_total,
        "deleted_by_state": dict(deleted_by_state),
        "deleted_by_flow": dict(deleted_by_flow),
        "failed_deletes": failed_deletes_count,
    }
    save_cleanup_stats(cleanup_stats)
    logger.info(f"Saved cleanup stats to MongoDB: {cleanup_stats}")


@flow(name="database-retention")
async def retention_flow():
    """Run database retention tasks."""
    await delete_old_flow_runs(days_to_keep=30, batch_size=100)


if __name__ == "__main__":
    asyncio.run(retention_flow())
