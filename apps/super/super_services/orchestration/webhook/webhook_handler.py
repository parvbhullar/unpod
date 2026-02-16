import requests
from super_services.libs.core.db import executeQuery
from super_services.db.services.models.task import (
    TaskModel,
    TaskExecutionLogModel,
)
from super_services.db.services.schemas.task import TaskStatusEnum

import json
from datetime import datetime, date
import uuid


def sanitize(obj):
    if isinstance(obj, (datetime, date)):
        return str(obj)

    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}

    return obj


class WebhookHandler:
    def __init__(self):
        self.task = None
        self.task_data = None
        self.task_id = None
        self.webhook_plan = None

    async def save_execution_log(self, status, output, error=None):
        if isinstance(output, str):
            output = {"data": output}
        exec_id = f"TE{uuid.uuid1().hex}"
        exec_log_data = {
            "task_exec_id": exec_id,
            "task_id": self.task.task_id,
            "run_id": self.task.run_id,
            "executor_id": "default",
            "status": status,
            "input": self.task.input,
            "output": {
                "step": "webhook",
                "data": output,
            },
            "space_id": self.task.space_id,
            "data": {},
        }
        if error:
            exec_log_data["output"] = {"error": str(error)}
        try:
            print("creating execution log")
            exec_status = TaskExecutionLogModel.save_single_to_db(exec_log_data)
        except Exception as e:
            print("creating execution log", str(e))

    def get_task(self):
        task = TaskModel.get(task_id=self.task_id)
        if task:
            self.task = task
            data = task.dict()
            data.pop("id")
            data = sanitize(data)

            self.task_data = data

    def get_webhook_plan(self):
        if not self.task:
            return {}

        agent = self.task.assignee
        query = """
         SELECT dfv.values
            FROM dynamic_form_values dfv
            JOIN dynamic_forms df
              ON dfv.form_id = df.id
            WHERE dfv.parent_id =  %(agent)s
              AND df.slug = 'webhook-integration';
          """

        params = {"agent": agent}

        res = executeQuery(query=query, params=params)

        try:
            if isinstance(res.get("values"), str):
                res = json.loads(res.get("values"))
            else:
                res = res.get("values")
        except Exception as e:
            res = {}

        return res

    def get_headers(self):
        headers = {
            "Content-Type": "application/json",
        }
        webhook_headers = self.webhook_plan.get("headers") or {}

        if isinstance(webhook_headers, dict):
            headers.update(webhook_headers)
        elif isinstance(webhook_headers, list):
            for i in webhook_headers:
                headers[i["header_name"]] = i["header_value"]

        return headers

    async def execute(self, task_id):
        self.task_id = task_id
        self.get_task()
        self.webhook_plan = self.get_webhook_plan()
        res = None
        if (
            self.webhook_plan
            and self.task_data
            and self.webhook_plan.get("enable_webhook", False)
        ):
            headers = self.get_headers()
            url = self.webhook_plan.get("webhook_url")

            if not url:
                await self.save_execution_log(
                    TaskStatusEnum.failed,
                    "",
                    error={"error": "skipping webhook request as url not available"},
                )

            for i in range(3):
                try:
                    res = requests.post(url, json=self.task_data, headers=headers)
                    if res.status_code == 200:
                        print("webhook request successful")
                        await self.save_execution_log(
                            TaskStatusEnum.completed, output=res.json()
                        )
                        return "Success"
                    else:
                        print("webhook request failed %s", res)
                        continue

                except Exception as e:
                    await self.save_execution_log(
                        TaskStatusEnum.failed, output="error", error=e
                    )
                    print("webhook request failed", str(e))
                    return "Failed to process webhook request"
            await self.save_execution_log(
                TaskStatusEnum.completed, output=res.json() if res else {}
            )
            return f"Failed to process webhook request"

        elif not self.webhook_plan.get("enable_webhook"):
            await self.save_execution_log(
                TaskStatusEnum.completed,
                output={"status": "skipping event as webhook request not enabled"},
            )
            return "skipping event as webhook request not enabled"

        return "Failed to process webhook request"


if __name__ == "__main__":
    import asyncio

    webhook_handler = WebhookHandler()
    asyncio.run(webhook_handler.execute(task_id="Tefe4015f78de11f082ac156368e7acc4"))
