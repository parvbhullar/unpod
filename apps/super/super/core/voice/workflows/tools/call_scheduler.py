import dspy
from dspy import ChainOfThought
from dotenv import load_dotenv

load_dotenv()
from datetime import datetime
import os
from super.core.voice.prompts.evalution_prompts.followup_eval import (
    BASE_PROMPT as FOLLOWUP_BASE_PROMPT,
)

turbo = dspy.LM("openai/gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))


class CallFollowUpSignatures(dspy.Signature):
    prompt = dspy.InputField(
        desc="system prompt based on which agen will decide weather to have follow up or not"
    )
    transcript = dspy.InputField(desc="transcript of current call")
    logs = dspy.InputField(desc="past calls with the user ")
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
        desc="why we comes to the decision we made abou follow up"
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

            collection = db[f"collection_data_{token}"]

            result = collection.find_one(
                {"_id": ObjectId(document_id)}, {"overview": 1, "_id": 0}
            )
            client.close()

            if result and result.get("overview", {}).get("recent_conversations"):
                return result.get("overview", {}).get("recent_conversations")

            return []

        except Exception as e:
            print(f"could get recent conversations {str(e)}")
            return []

    def forward(
        self,
        call_transcript: str,
        prompt: str,
        token: str,
        document_id: str,
        available_slots: dict = {},
    ) -> dspy.Prediction:
        logs = self._get_logs(token, document_id)

        combined_prompt = f"{FOLLOWUP_BASE_PROMPT}\n{''}"
        with dspy.context(lm=turbo):
            res = self.analyzer(
                transcript=call_transcript,
                prompt=combined_prompt,
                logs=logs,
                current_date=datetime.now(),
                availble_slots=available_slots,
            )

        return dspy.Prediction(
            followup_time=res.followup_time,
            followup_required=res.requires_followup,
            reason=res.reason,
        )


if __name__ == "__main__":
    analyxer = FollowUpAnalyzer()
    from super_services.db.services.models.task import TaskModel

    task = TaskModel.get(task_id="T54c25cffea3811f0878d43cd8a99e069")
    res = analyxer.forward(
        call_transcript=task.output.get("transcript"),
        prompt="if user is interested follow up call",
        token="F1O3QJM1Y7Q1AVVUYNV4VPRB",
        document_id=task.ref_id,
    )
    print(bool(res.followup_required))

    print(res)
