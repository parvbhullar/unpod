
import random
import json
from datetime import timedelta ,datetime
from super_services.voice.models.config import ModelConfig
import pytz
import os
from dotenv import load_dotenv
load_dotenv(override=True)
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WEEKDAY_MAP = {
    "Mon": 0,
    "Tue": 1,
    "Wed": 2,
    "Thu": 3,
    "Fri": 4,
    "Sat": 5,
    "Sun": 6,
}


def get_next_date(model_config:dict):
    try:

        time_range= json.loads(model_config.get("calling_time_ranges",[]))
        days_range= json.loads(model_config.get("calling_days",[]))

        if days_range and time_range:
            selected_day=days_range[random.randint(0,len(days_range)-1)]
            time_range=time_range[0]

            start_time =time_range.get("start")
            end_time =time_range.get("end")

            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

            total_seconds = int((end_dt - start_dt).total_seconds())
            if total_seconds < 0:
                total_seconds *= -1  # fix for reversed start/end times
            random_seconds = random.randint(0, total_seconds)
            chosen_time = (start_dt + timedelta(seconds=random_seconds)).time()

            # Find the next upcoming weekday that matches selected_day
            now = datetime.now(pytz.utc)
            target_weekday = WEEKDAY_MAP[selected_day]
            days_ahead = (target_weekday - now.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7  # schedule next week if same day passed
            scheduled_date = now + timedelta(days=days_ahead)

            # Combine date + chosen time
            final_datetime = scheduled_date.replace(
                hour=chosen_time.hour, minute=chosen_time.minute, second=0, microsecond=0
            )

            print(f"Scheduled for: {final_datetime.isoformat()}")
            return final_datetime
    except Exception as e:
        print("Invalid datetime format:", e)
        return None


def query_analyzer(query) -> bool:


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                Classify the user message as a question or not.
                If the message is asking for information, clarification, or explanation —
                even without a question mark — treat it as a question.
                Examples:
                - "What is Python?" → True
                - "Tell me about Python" → True
                - "Explain Python" → True
                - "I love Python" → False
                - "Okay" → False

                Return only BOOLEAN: true or false.
                """,
            },
            {"role": "user", "content": query},
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content.strip().lower()
    # print(response)
    # Normalize and return boolean
    if "true" in answer:
        return True
    else:
        return False


if __name__ == "__main__":
   # config=ModelConfig().get_config('pipecat-test-agent')
   # print(config)
   # get_next_date(config)

   print(query_analyzer(query="hello"))