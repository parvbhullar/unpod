import asyncio
from super_services.voice.models.threads import ThreadHandler
from super_services.db.services.models.task import TaskModel


def create_thread_post(task_id):
    """Synchronous thread creation (legacy)."""
    task = TaskModel.get(task_id=task_id)

    if task.thread_id:
        return task.thread_id

    thread_handler = ThreadHandler()
    thread_id = thread_handler.create_thread(task)

    TaskModel.update_one({"task_id": task_id}, {"thread_id": str(thread_id)})
    print(
        f"\n{'='*50 } \n no thread id available create thread with id  thread_id: {thread_id} \n  {'='*50 } \n"
    )

    if not isinstance(thread_id, str):
        thread_id = str(thread_id)

    return thread_id


async def create_thread_async(task_id: str) -> str:
    """
    Asynchronous thread creation - optimized for non-blocking operation.

    Uses:
    - asyncio.to_thread for DB operations
    - aiohttp for HTTP requests
    """
    # Get task from DB in thread pool
    task = await asyncio.to_thread(TaskModel.get, task_id=task_id)

    if task.thread_id:
        return task.thread_id

    thread_handler = ThreadHandler()
    thread_id = await thread_handler.create_thread_async(task)

    # Update task with thread_id in background (don't wait)
    asyncio.create_task(
        asyncio.to_thread(
            TaskModel.update_one, {"task_id": task_id}, {"thread_id": str(thread_id)}
        )
    )

    print(
        f"\n{'='*50 } \n [ASYNC] created thread with id: {thread_id} \n  {'='*50 } \n"
    )

    if not isinstance(thread_id, str):
        thread_id = str(thread_id)

    return thread_id


async def create_thread_without_task(
    space_id: str,
    user_id: str,
    title: str = "SDK Conversation",
    collection_ref: str = "",
    ref_doc_id: str = "",
) -> str:
    """
    Create thread directly without creating a task.
    Used for SDK Conversation (SuperKik) flow.

    Args:
        space_id: Space ID for the thread
        user_id: User ID for the thread
        title: Thread title (default: "SDK Conversation")
        collection_ref: Optional collection reference
        ref_doc_id: Optional document reference ID

    Returns:
        Thread ID string
    """
    thread_handler = ThreadHandler()
    thread_id = await thread_handler.create_thread_directly(
        space_id=space_id,
        user_id=user_id,
        title=title,
        collection_ref=collection_ref,
        ref_doc_id=ref_doc_id,
    )

    print(
        f"\n{'='*50 } \n [SDK] created thread directly with id: {thread_id} \n  {'='*50 } \n"
    )

    if not isinstance(thread_id, str):
        thread_id = str(thread_id)

    return thread_id


def update_thread(task_id, data):
    thread_handler = ThreadHandler()
    task = TaskModel.get(task_id=task_id)
    res = thread_handler.update_thread(task.thread_id, data)

    print(f"\n\n {res} \n\n ")


def get_user_id(task_id):
    task = TaskModel.get(task_id=task_id)
    if task.user:
        return task.user

    return None
