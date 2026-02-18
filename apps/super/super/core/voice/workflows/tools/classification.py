import os
from datetime import datetime

import dspy
from dotenv import load_dotenv
from dspy import ChainOfThought
import requests
from super.core.logging.logging import print_log
from super_services.libs.core.db import executeQuery
from ..dspy_config import get_dspy_lm

load_dotenv(override=True)
import json

STORE_SERVICE_URL = os.getenv("STORE_SERVICE_URL")


class CallSummarySignature(dspy.Signature):
    """Extract structured information from a call transcript."""

    call_transcript = dspy.InputField(desc="Transcription of the entire call")
    call_datetime = dspy.InputField(
        desc="Datetime of call executed in format 'YYYY-MM-DD HH:MM'"
    )
    prompt = dspy.InputField(
        desc="system prompt based on which we must identify the call status"
    )
    # Primary output fields
    status = dspy.OutputField(
        desc="Call status if person shows any kind of interest in the product or service, then mark Interested. Must be one of: 'Interested', 'Call Back', 'Not Interested', 'Send Details', 'Not Connected', 'Abandoned', 'Dropped'",
    )
    summary = dspy.OutputField(
        desc="Detailed summary of what was discussed in the call. Include: 1) What the agent offered/proposed 2) User's response and concerns 3) Key points discussed 4) Any decisions made or next steps agreed. Write 2-4 sentences covering the main conversation flow."
    )

    # Conditional fields (for Interested status)
    name = dspy.OutputField(
        desc="Name of the person (only if status is 'Interested' or 'Call Back' or 'Send Details', otherwise return 'N/A')"
    )
    contact = dspy.OutputField(
        desc="Contact of the person (only if status is 'Interested' or 'Call Back' or 'Send Details', otherwise return 'N/A')"
    )

    # Conditional fields (for Call Back status)
    callback_datetime = dspy.OutputField(
        desc="Date and time for callback in format 'YYYY-MM-DD HH:MM' (only if status is 'Call Back', otherwise return 'N/A')"
    )
    hours_from_now = dspy.OutputField(
        desc="Number of hours from now for the callback (only if status is 'Call Back', otherwise return 'N/A')"
    )


class CallSummarizer(dspy.Module):
    def __init__(self, lm=None):
        super().__init__()
        self.lm = lm or get_dspy_lm()
        self.generate_summary = ChainOfThought(CallSummarySignature)

    def forward(self, call_transcript, call_datetime):
        from super.core.voice.prompts.evalution_prompts.status_label import BASE_PROMPT

        with dspy.context(lm=self.lm):
            result = self.generate_summary(
                call_transcript=call_transcript,
                call_datetime=call_datetime,
                prompt=BASE_PROMPT,
            )
            return dspy.Prediction(
                status=result.status,
                summary=result.summary,
                name=result.name,
                contact=result.contact,
                callback_datetime=result.callback_datetime,
                hours_from_now=result.hours_from_now,
            )


class ClassificationSignature(dspy.Signature):
    """Classify call transcript based on provided tags."""

    call_transcript = dspy.InputField(desc="transcription of the entire call")
    tags = dspy.InputField(desc="tags with descriptions to identify the based upon")
    # prompt = dspy.InputField(desc="Prompt to identify the call")
    output_tags = dspy.OutputField(
        desc="comma-separated list of tag names that have been identified from call transcript based on tags provided. Return only tag names like ['Interested', 'Urgent'] or empty string if no tags match."
    )


class CallClassifier(dspy.Module):
    def __init__(self, tag_descriptions: dict, lm=None):
        super().__init__()
        self.lm = lm or get_dspy_lm()
        self.tag_descriptions = tag_descriptions
        self.classification = dspy.ChainOfThought(ClassificationSignature)

    def forward(self, call_transcript):
        with dspy.context(lm=self.lm):
            result = self.classification(
                call_transcript=call_transcript,
                tags=self.tag_descriptions,
            )

            return dspy.Prediction(
                output_tags=result.output_tags,
            )


class CallLabelClassifier:
    def __init__(
        self,
        transcript: dict,
        tag_descriptions: dict,
        lm=None,
    ):
        self.transcript = transcript
        if not tag_descriptions:
            print("tag_descriptions dict must be provided")
            tag_descriptions = {}
        self.tag_descriptions = tag_descriptions
        self.lm = lm or get_dspy_lm()
        self.call_classifier = CallClassifier(tag_descriptions, lm=self.lm)
        self.summarizer = CallSummarizer(lm=self.lm)

    def classify(self):
        text = self.transcript
        pred = self.call_classifier.forward(text)
        summary = self.summarizer(
            text, call_datetime=datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        print("prediction results", pred.output_tags)

        results = {"label": pred.output_tags, "summary": summary.summary}

        return {"status": "completed", "data": results}


class CallClassificationService:
    def __init__(self, transcript, token, document_id):
        self.transcript = transcript
        self.token = token
        self.document_id = document_id
        self.tags = self.get_tags()

    def get_tags(self):
        query = f"""
            SELECT
                "relevant_tag"."id",
                "relevant_tag"."name",
                "relevant_tag"."slug",
                "relevant_tag_link"."description",
                "relevant_tag"."is_default"
            FROM
                "relevant_tag"
            INNER JOIN
                "relevant_tag_link"
            ON
                "relevant_tag"."id" = "relevant_tag_link"."tag_id"
            WHERE
                "relevant_tag_link"."content_type_id" = (
                    SELECT "django_content_type"."id"
                    FROM "django_content_type"
                    WHERE "django_content_type"."model" = 'space'
                    LIMIT 1
                )
            AND
                "relevant_tag_link"."object_id" = (
                    SELECT "space_space"."id"
                    FROM "space_space"
                    WHERE "space_space"."token" = '{self.token}'
                );
            """

        result = executeQuery(query, many=True)
        print(result, "query result")
        tags = {}
        for tag in result:
            tags[tag["name"]] = tag["description"]
        print_log("Tags fetched for classification", tags)
        return tags

    def process_label(self, labels, tags):
        new_labels = []
        tags = {key.strip(): value for key, value in tags.items()}

        # Handle empty or None labels
        if not labels:
            print("No labels to process", labels, tags)
            return new_labels
        print_log(f"Processing labels: {labels}", "label_processing")

        # Convert labels to list format
        if isinstance(labels, str):
            # Handle empty string
            if not labels.strip():
                print("Empty labels string", labels, tags)
                return new_labels

            # Try to parse as JSON first (handles ['tag1', 'tag2'] format)
            try:
                labels = json.loads(labels)
            except json.JSONDecodeError:
                # If not JSON, treat as comma-separated string
                labels = [label.strip() for label in labels.split(",") if label.strip()]

        # Ensure labels is iterable (list or tuple)
        if not isinstance(labels, (list, tuple)):
            print_log(
                f"Labels is not iterable: {type(labels)}, labels={labels}",
                "classification_error",
            )
            return new_labels

        # Filter labels to only include those that exist in tags
        for label in labels:
            label_str = str(label).strip()
            if label_str in tags.keys():
                new_labels.append(label_str)

        print("New labels", new_labels, labels, tags)
        return new_labels

    async def process_doc(self, data):
        try:
            url = f"{STORE_SERVICE_URL}/api/v1/store/collection-doc-data/{self.token}/{self.document_id}"
            response = requests.get(url)

            if response.status_code == 200:
                doc_data = response.json().get("data")
                doc_data["labels"] = data.get("labels", [])
                payload = doc_data
                url_response = requests.post(url, json=payload)

                if url_response.status_code == 200:
                    print("upsert successful")
                    return {
                        "status": "completed",
                        "data": url_response.json()["data"],
                    }

                else:
                    return {}

        except Exception as e:
            print_log(f"unable to update labels {e}")

    async def classify_call(self):
        classifier = CallLabelClassifier(self.transcript, self.tags)
        data = classifier.classify()
        print(f"label after classifying data {data}")
        res = {
            "labels": self.process_label(
                data.get("data", {}).get("label", []), self.tags
            ),
            "summary": data.get("data").get("summary"),
        }

        await self.process_doc(res)
        return res


class ProfileSummarySignature(dspy.Signature):
    """Extract detailed profile summary from a call transcript to understand the user."""

    call_transcript = dspy.InputField(desc="Transcription of the entire call")

    # Sentiment & Tone
    sentiment = dspy.OutputField(
        desc="Overall sentiment of the user. Must be one of: 'Positive', 'Negative', 'Neutral'"
    )
    tone = dspy.OutputField(
        desc="User's tone/behavior during call. Must be one of: 'Friendly', 'Professional', 'Frustrated', 'Confused', 'Rude', 'Neutral'"
    )
    engagement = dspy.OutputField(
        desc="User's engagement level. Must be one of: 'High', 'Medium', 'Low'"
    )

    # Interest
    interest_level = dspy.OutputField(
        desc="Analyze user's ACTUAL responses in the conversation to determine interest level. Look for: 'Very Interested' = user asked questions, requested details/demo, showed excitement; 'Interested' = user engaged positively, didn't reject; 'Maybe' = user was hesitant, said 'will think about it', asked to call later; 'Not Interested' = user explicitly declined, said not interested, asked to stop calling. Must be one of: 'Very Interested', 'Interested', 'Maybe', 'Not Interested'"
    )

    # Behavior
    objections = dspy.OutputField(
        desc='List of objections or concerns raised by user. Return as JSON array like ["objection1", "objection2"] or [] if none'
    )
    questions_asked = dspy.OutputField(
        desc='List of questions asked by user. Return as JSON array like ["question1", "question2"] or [] if none'
    )
    pain_points = dspy.OutputField(
        desc='List of problems or pain points mentioned by user. Return as JSON array like ["pain1", "pain2"] or [] if none'
    )

    # Outcome
    outcome = dspy.OutputField(
        desc="Call outcome. Must be one of: 'Connected', 'Callback Requested', 'Not Interested', 'Follow-up Needed', 'Sale', 'Information Sent'"
    )
    next_action = dspy.OutputField(
        desc="Next action to take. Examples: 'Send details on email', 'Schedule demo', 'Call back Monday', 'No action needed'"
    )
    callback_requested = dspy.OutputField(
        desc="Whether user requested callback. Must be: 'true' or 'false'"
    )
    callback_time = dspy.OutputField(
        desc="When to callback if requested. Example: 'Monday 10 AM', 'Tomorrow', 'Next week'. Return 'N/A' if not requested"
    )

    # Summary
    summary_text = dspy.OutputField(
        desc="2-3 sentence summary about the user based on the call. Focus on user's personality, interest, and what they want."
    )


class ProfileSummaryExtractor(dspy.Module):
    def __init__(self, lm=None):
        super().__init__()
        self.lm = lm or get_dspy_lm()
        self.extract_profile = ChainOfThought(ProfileSummarySignature)

    def parse_json_field(self, value):
        """Parse JSON array fields safely"""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def forward(self, call_transcript):
        with dspy.context(lm=self.lm):
            result = self.extract_profile(call_transcript=call_transcript)

            return {
                "tone": result.tone,
                "engagement": result.engagement,
                "interest_level": result.interest_level,
                "objections": self.parse_json_field(result.objections),
                "questions_asked": self.parse_json_field(result.questions_asked),
                "pain_points": self.parse_json_field(result.pain_points),
                "outcome": result.outcome,
                "next_action": result.next_action,
                "callback_requested": (
                    result.callback_requested.lower() == "true"
                    if isinstance(result.callback_requested, str)
                    else bool(result.callback_requested)
                ),
                "callback_time": (
                    result.callback_time if result.callback_time != "N/A" else None
                ),
                "summary_text": result.summary_text,
            }


if __name__ == "__main__":
    import asyncio

    transcript = [
        {
            "role": "user",
            "content": "Hello?",
            "user_id": "PA_Z3qPpu7ZGhWh",
            "timestamp": "2025-10-16T05 :55:15.613+00:00",
        },
        {
            "role": "assistant",
            "content": "Hello! How can I assist you today?",
            "user_id": None,
            "timestamp": "2025-10-16T05:55:15.332+00:00",
        },
        {
            "role": "user",
            "content": "How can you assist me?",
            "user_id": "PA_Z3qP pu7ZGhWh",
            "timestamp": "2025-10-16T05:55:20.872+00:00",
        },
        {
            "role": "assistant",
            "content": "Hey there! मैं GIA from GameStop हूँ। मैं आपको शानदार games, consoles, या accessories खोजने में मदद कर सकती हूँ। क्या आपके पास बात करने  के लिए एक मिनट है, या मैं बाद में संपर्क करूँ?",
            "user_id": None,
            "timestamp": "2025-10-16T05:55:22.867+00:00",
        },
        {
            "role": "user",
            "content": "Sorry, I'm not interested.",
            "user_id": "PA_Z3qPpu7ZGhWh",
            "timestamp": "2025-10-16T05 :55:37.171+00:00",
        },
        {
            "role": "user",
            "content": "I'm not interested in your service.",
            "user_id": "PA_Z3qPpu7ZGhWh",
            "timestamp": "2025-10-16T05:55:39.113+00:00",
        },
        {
            "role": "user",
            "content": "Please.",
            "user_id": "PA_Z3qPpu7ZGh Wh",
            "timestamp": "2025-10-16T05:55:39.533+00:00",
        },
        {
            "role": "assistant",
            "content": "कोई बात नहीं, आपका समय देने के लिए धन्यवाद! आप GIA से GameStop से बात कर रहे थे। अगर कभी गेम्स की ज़रूरत पड़े, तो हम हमेशा यहाँ हैं। Take care !",
            "user_id": None,
            "timestamp": "2025-10-16T05:55:41.906+00:00",
        },
    ]
    call_classification_service = CallClassificationService(
        transcript, "F1O3QJM1Y7Q1AVVUYNV4VPRB", "689d8dc77ba71026cbd36ce8"
    )

    asyncio.run(call_classification_service.classify_call())
