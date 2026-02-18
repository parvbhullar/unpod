import dspy
from dspy import ChainOfThought
from dotenv import load_dotenv
import re

load_dotenv()
from datetime import datetime
import os
from super.core.voice.prompts.evalution_prompts.followup_eval import (
    BASE_PROMPT as FOLLOWUP_BASE_PROMPT,
)
from super_services.db.services.models.task import TaskModel

turbo = dspy.LM("openai/gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))


class CallFollowUpSignatures(dspy.Signature):
    prompt = dspy.InputField(
        desc="system prompt based on which agen will decide weather to have follow up or not"
    )
    transcript = dspy.InputField(desc="transcript of current call")
    logs = dspy.InputField(
        desc="past calls with the user along with datetime, status of the call and transcript of precious calls"
    )
    current_date = dspy.InputField(desc="current date and time", default=datetime.now())
    requires_followup = dspy.OutputField(
        desc="whether the follow up call is required  or not this has be either true or false",
        type=bool,
    )
    followup_time = dspy.OutputField(
        desc="at what to schedule the follow up call if its required return in ",
        type=datetime,
    )
    reason = dspy.OutputField(
        desc="why we comes to the decision and  we made follow up in detail also folowup count logic too"
    )
    avaible_slots = dspy.InputField(
        desc="avaible days and time absed on which we have to schedule calls if none avaible schedule calls on weekdays froom 8am and 8pm"
    )


class FollowUpAnalyzer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.analyzer = ChainOfThought(CallFollowUpSignatures)

    def _get_logs(self, token, document_id):
        try:
            from bson import ObjectId
            from pymongo import MongoClient
            from super_services.libs.config import settings

            client = MongoClient(settings.MONGO_DSN)

            db = client[settings.MONGO_DB]

            query = {"ref_id": document_id}

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
                .limit(10)
            )

            if not logs:
                collection = db[f"collection_data_{token}"]

                result = collection.find_one(
                    {"_id": ObjectId(document_id)}, {"contact_number": 1, "_id": 0}
                )

                contact_number = [result.get("contact_number")]

                if not result.get("contact_number", "").startswith(
                    "91"
                ) and not result.get("contact_number", "").startswith("0"):
                    contact_number.append("91" + result.get("contact_number", ""))
                elif result.get("contact_number", "").startswith("91"):
                    contact_number.append(result.get("contact_number", "")[2:])

                query = {
                    "$or": [
                        {"input.contact_number": {"$in": contact_number}},
                        {"output.contact_number": {"$in": contact_number}},
                        {"input.number": {"$in": contact_number}},
                        {"output.customer": {"$in": contact_number}},
                    ]
                }

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
                    .limit(10)
                )

            client.close()

            return logs

        except Exception as e:
            print(f"could get recent conversations {str(e)}")
            return []

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
        available_slots: dict = {},
    ) -> dspy.Prediction:
        logs = self._get_logs(token, document_id)
        max_calls = self._extract_max_calls(prompt)
        current_followup_count = self._get_current_followup_count(logs)

        if current_followup_count >= max_calls:
            return dspy.Prediction(
                followup_time=None,
                followup_required=False,
                reason=(
                    f"Follow-up suppressed: followup_count={current_followup_count} "
                    f"already reached max_calls={max_calls} defined by prompt/default rules."
                ),
            )

        combined_prompt = f"{FOLLOWUP_BASE_PROMPT}\n{prompt}"
        with dspy.context(lm=turbo):
            res = self.analyzer(
                transcript=call_transcript,
                prompt=combined_prompt,
                logs=logs,
                current_date=datetime.now(),
                avaible_slots=available_slots,
            )

        if res.requires_followup and (current_followup_count + 1) > max_calls:
            return dspy.Prediction(
                followup_time=None,
                followup_required=False,
                reason=(
                    f"Follow-up suppressed after model output: next attempt would exceed "
                    f"max_calls={max_calls} with current followup_count={current_followup_count}."
                ),
            )

        return dspy.Prediction(
            followup_time=res.followup_time,
            followup_required=res.requires_followup,
            reason=res.reason,
        )


if __name__ == "__main__":
    analyxer = FollowUpAnalyzer()
    from super_services.db.services.models.task import TaskModel
    from super_services.voice.models.config import ModelConfig

    task = TaskModel.get(task_id="Teca7456b08b511f1b50116b5cd486909")

    config = ModelConfig().get_config(task.assignee)

    res = analyxer.forward(
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
