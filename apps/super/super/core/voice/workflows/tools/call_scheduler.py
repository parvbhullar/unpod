import re
from datetime import datetime
from typing import Optional

import dspy
from dspy import ChainOfThought

from super.core.voice.prompts.evalution_prompts.followup_eval import (
    BASE_PROMPT as FOLLOWUP_BASE_PROMPT,
)
from super_services.db.services.models.task import TaskModel

from ..dspy_config import get_dspy_lm
from .config import get_now


class CallFollowUpSignatures(dspy.Signature):
    # --- Inputs (all before outputs) ---
    prompt = dspy.InputField(
        desc="system prompt based on which agent will decide whether to have follow up or not"
    )
    transcript = dspy.InputField(desc="transcript of current call")
    logs = dspy.InputField(
        desc="past calls with the user along with datetime, status of the call and transcript of previous calls"
    )
    current_date = dspy.InputField(desc="current date and time (timezone-aware)")
    available_slots = dspy.InputField(
        desc=(
            "JSON with 'time_range' (list of {start, end} ISO strings) and "
            "'days_range' (list of day names like 'Mon','Tue'). "
            "Schedule within these windows only. If empty, use weekdays 8am-8pm."
        )
    )
    # --- Outputs ---
    requires_followup = dspy.OutputField(
        desc="whether the follow up call is required or not, must be either true or false",
        type=bool,
    )
    followup_time = dspy.OutputField(
        desc="precise datetime to schedule the follow up call if required",
        type=datetime,
    )
    reason = dspy.OutputField(
        desc="detailed explanation of the decision including followup count logic"
    )


class FollowUpAnalyzer(dspy.Module):
    def __init__(self, lm=None):
        super().__init__()
        self.lm = lm or get_dspy_lm()
        self.analyzer = ChainOfThought(CallFollowUpSignatures)

    def _get_logs(
        self,
        token: str,
        document_id: str,
        task_id: Optional[str],
        assignee: Optional[str] = None,
    ) -> list:
        try:
            from bson import ObjectId
            from pymongo import MongoClient
            from super_services.libs.config import settings

            client = MongoClient(settings.MONGO_DSN)

            if not task_id:
                return []

            task = TaskModel.get(task_id=task_id)

            task_output = task.output if isinstance(task.output, dict) else {}
            task_followup_count = task_output.get("followup_count")
            task_limit = max(5, int(task_followup_count or 0))

            db = client[settings.MONGO_DB]

            query = {"ref_id": document_id}
            if assignee:
                query["assignee"] = assignee

            logs = list(
                TaskModel._get_collection()
                .find(
                    query,
                    {
                        "_id": 0,
                        "output.call_status": 1,
                        "modified": 1,
                        "output.transcript": 1,
                        "output.followup_count": 1,
                    },
                )
                .sort([("created", -1)])
                .limit(task_limit)
            )

            if not logs:
                collection = db[f"collection_data_{token}"]

                result = collection.find_one(
                    {"_id": ObjectId(document_id)}, {"contact_number": 1, "_id": 0}
                )

                if not result:
                    client.close()
                    return []

                raw_contact_number = str(result.get("contact_number", "") or "")
                contact_number = [raw_contact_number]

                if not raw_contact_number.startswith("91") and not raw_contact_number.startswith("0"):
                    contact_number.append("91" + raw_contact_number)
                elif raw_contact_number.startswith("91"):
                    contact_number.append(raw_contact_number[2:])

                query = {
                    "$or": [
                        {"input.contact_number": {"$in": contact_number}},
                        {"output.contact_number": {"$in": contact_number}},
                        {"input.number": {"$in": contact_number}},
                        {"output.customer": {"$in": contact_number}},
                    ]
                }

                # Scope to same agent to avoid mixing campaign histories
                if assignee:
                    query["assignee"] = assignee

                logs = list(
                    TaskModel._get_collection()
                    .find(
                        query,
                        {
                            "_id": 0,
                            "output.call_status": 1,
                            "modified": 1,
                            "output.transcript": 1,
                            "output.followup_count": 1,
                        },
                    )
                    .sort([("created", -1)])
                    .limit(task_limit)
                )

            client.close()

            return logs

        except Exception as e:
            print(f"could not get recent conversations {str(e)}")
            return []

    def _coerce_followup_required(self, value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        normalized = re.sub(r"[^a-z0-9]+", "", str(value).lower())
        return normalized in {"true", "yes", "y", "1", "required"}

    def _extract_max_calls(self, prompt: str) -> int:
        default_max_calls = 3
        if not prompt:
            return default_max_calls

        normalized_prompt = prompt.lower()
        patterns = [
            r"\bup to\s+(\d+)\s+times?\b",
            r"\bmaximum\s+of\s+(\d+)\s+times?\b",
            r"\bmax(?:imum)?\s+(\d+)\s+calls?\b",
            r"\b(\d+)\s+maximum\s+calls?\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, normalized_prompt)
            if match:
                return max(1, int(match.group(1)))

        retry_match = re.search(
            r"initial call\s*\+\s*(\d+)\s+retries", normalized_prompt
        )
        if retry_match:
            return max(1, int(retry_match.group(1)) + 1)

        return default_max_calls

    def _get_current_followup_count(self, logs: list) -> int:
        max_followup_count = 0
        for log in logs:
            output = log.get("output", {})
            followup_count = output.get("followup_count")
            if isinstance(followup_count, int):
                max_followup_count = max(max_followup_count, followup_count)
        return max_followup_count

    def forward(
        self,
        call_transcript: str,
        prompt: str,
        token: str,
        document_id: str,
        available_slots: Optional[dict] = None,
        task_id: Optional[str] = None,
        model_config: Optional[dict] = None,
        assignee: Optional[str] = None,
    ) -> dspy.Prediction:
        logs = self._get_logs(token, document_id, task_id, assignee=assignee)
        max_calls = self._extract_max_calls(prompt)
        current_followup_count = self._get_current_followup_count(logs)
        # followup_count tracks retries. max_calls is total attempts (initial + retries).
        allowed_followups = max(0, max_calls - 1)

        if current_followup_count >= allowed_followups:
            return dspy.Prediction(
                followup_time=None,
                followup_required=False,
                max_calls=max_calls,
                reason=(
                    f"Follow-up suppressed: followup_count={current_followup_count} "
                    f"already reached retry_limit={allowed_followups} derived from max_calls={max_calls}."
                ),
            )

        combined_prompt = f"{FOLLOWUP_BASE_PROMPT}\n{prompt}"
        now = get_now(model_config)

        with dspy.context(lm=self.lm):
            res = self.analyzer(
                transcript=call_transcript,
                prompt=combined_prompt,
                logs=logs,
                current_date=now,
                available_slots=available_slots or {},
            )

        followup_required = self._coerce_followup_required(res.requires_followup)

        if followup_required and (current_followup_count + 1) > allowed_followups:
            return dspy.Prediction(
                followup_time=None,
                followup_required=False,
                max_calls=max_calls,
                reason=(
                    f"Follow-up suppressed after model output: next attempt would exceed "
                    f"retry_limit={allowed_followups} derived from max_calls={max_calls} "
                    f"with current followup_count={current_followup_count}."
                ),
            )

        return dspy.Prediction(
            followup_time=res.followup_time,
            followup_required=followup_required,
            max_calls=max_calls,
            reason=res.reason,
        )


if __name__ == "__main__":
    analyzer = FollowUpAnalyzer()
    from super_services.voice.models.config import ModelConfig

    task = TaskModel.get(task_id="Teca7456b08b511f1b50116b5cd486909")

    config = ModelConfig().get_config(task.assignee)

    res = analyzer.forward(
        call_transcript=task.output.get("transcript"),
        prompt="""
        If I do not answer the first call:
        Retry calling after 3 minutes.
        If the second call is not answered, retry again after another 3 minutes.
        If the third call is not answered, make one final attempt after another 3 minutes.
        In total, the agent should attempt to call me up to 4 times (initial call + 3 retries), with 3-minute gaps between each attempt.
        Stop further attempts once the call is answered.
        """,
        token="F1O3QJM1Y7Q1AVVUYNV4VPRB",
        document_id=task.ref_id,
    )

    print(res)
