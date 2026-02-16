import requests
import aiohttp
from dotenv import load_dotenv
from super.core.voice.common.services import save_execution_log

load_dotenv()
import os
from super_services.db.services.schemas.task import TaskStatusEnum
import asyncio


class ThreadHandler:
    def __init__(self):
        pass

    def get_headers(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {os.environ.get('UNPOD_API_KEY')}",
            "Product-Id": "unpod.ai",
        }
        return headers

    def create_thread(self, task):
        """Synchronous thread creation (legacy)."""
        url = f"{os.environ.get('UNPOD_BASE')}/threads/public/create-thread/"

        payload = {
            "user_id": task.user,
            "space_id": task.space_id,
            "title": task.task.get("objective", "test"),
            "post_type": "post",
            "content": "hello",
            "scheduled": False,
            "privacy_type": "private",
            "user_list": [],
            "content_type": "text",
            "ref_collection": task.collection_ref,
            "ref_doc_id": task.ref_id,
        }

        for i in range(3):
            try:
                res = requests.post(url=url, headers=self.get_headers(), json=payload)

                if res.status_code == 201:
                    thread_id = res.json().get("data", {}).get("post_id", None)
                    return thread_id

                else:
                    print(res.text)
                    continue

            except Exception as e:
                print(f"exception occured while creating thread: {e}")
                return "unable to create thread"

        return ""

    async def create_thread_async(self, task) -> str:
        """
        Create thread asynchronously using aiohttp.
        Much faster than sync requests for non-blocking operation.
        """
        url = f"{os.environ.get('UNPOD_BASE')}/threads/public/create-thread/"

        payload = {
            "user_id": task.user,
            "space_id": task.space_id,
            "title": task.task.get("objective", "test"),
            "post_type": "post",
            "content": "hello",
            "scheduled": False,
            "privacy_type": "private",
            "user_list": [],
            "content_type": "text",
            "ref_collection": task.collection_ref,
            "ref_doc_id": task.ref_id,
        }

        return await self._create_thread_request(url, payload)

    async def create_thread_directly(
        self,
        space_id: str,
        user_id: str,
        title: str = "SDK Conversation",
        collection_ref: str = "",
        ref_doc_id: str = "",
    ) -> str:
        """
        Create thread directly without requiring a task object.
        Used for SDK Conversation flow where no task is created.
        """
        url = f"{os.environ.get('UNPOD_BASE')}/threads/public/create-thread/"

        payload = {
            "user_id": user_id,
            "space_id": space_id,
            "title": title,
            "post_type": "post",
            "content": "hello",
            "scheduled": False,
            "privacy_type": "private",
            "user_list": [],
            "content_type": "text",
            "ref_collection": collection_ref,
            "ref_doc_id": ref_doc_id,
        }

        return await self._create_thread_request(url, payload)

    async def _create_thread_request(self, url: str, payload: dict) -> str:
        """Common method to make thread creation request."""

        for i in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        headers=self.get_headers(),
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as res:
                        if res.status == 201:
                            data = await res.json()
                            thread_id = data.get("data", {}).get("post_id", None)
                            return thread_id
                        else:
                            text = await res.text()
                            print(f"Thread creation failed (attempt {i+1}): {text}")
                            continue

            except asyncio.TimeoutError:
                print(f"Thread creation timeout (attempt {i+1})")
                continue
            except Exception as e:
                print(f"Exception in async thread creation (attempt {i+1}): {e}")
                if i == 2:  # Last attempt
                    return "unable to create thread"
                continue

        return ""

    def update_thread(self, thread_id, data):
        url = f"{os.environ.get('UNPOD_BASE')}/threads/public/thread/{thread_id}/"

        payload = {
            "content": data.get("post_call_data", {})
            .get("classification", {})
            .get("summary", ""),
            "tags": data.get("post_call_data", {})
            .get("classification", {})
            .get("labels", []),
        }

        for i in range(3):
            try:
                res = requests.patch(url=url, headers=self.get_headers(), json=payload)

                if res.status_code == 200:
                    asyncio.create_task(
                        save_execution_log(
                            task.task_id,
                            "thread updated",
                            TaskStatusEnum.completed,
                            thread_id,
                        )
                    )

                    return "thread updated successfully"

                else:
                    continue

            except Exception as e:
                asyncio.create_task(
                    save_execution_log(
                        task.task_id,
                        "thread_created",
                        TaskStatusEnum.failed,
                        "",
                        str(e),
                    )
                )

                print(f"exception occured while creating thread: {e}")
                continue

        return "unable to update thread"


if __name__ == "__main__":
    thread = ThreadHandler()
    from super_services.db.services.models.task import TaskModel

    task = TaskModel.get(task_id="Tefe4015f78de11f082ac156368e7acc4")
    id = thread.create_thread(task)

    print(id)
