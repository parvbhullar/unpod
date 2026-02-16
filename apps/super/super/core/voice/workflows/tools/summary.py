import os
import dspy
from dotenv import load_dotenv
from dspy import ChainOfThought
from super.core.voice.prompts.evalution_prompts.summary_eval import BASE_PROMPT

load_dotenv(override=True)

turbo = dspy.LM('openai/gpt-4o-mini', api_key=os.getenv("OPENAI_API_KEY"))

class CallSummarySignature(dspy.Signature):
    call_transcript = dspy.InputField(desc="transcription of the entire call")
    guidelines = dspy.InputField(desc="guidelines for generating the summary")
    summary = dspy.OutputField(desc="Concise summary of the call transcript following the provided guidelines")

class CallSummarizer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_summary = ChainOfThought(CallSummarySignature)

    def forward(self, call_transcript, additional_guidelines=""):
        combined_guidelines = f"{BASE_PROMPT}\n{additional_guidelines}"
        result = self.generate_summary(
            call_transcript=call_transcript,
            guidelines=combined_guidelines
        )
        return dspy.Prediction(
            summary=result.summary
        )

if __name__ == "__main__":
    summary = CallSummarizer()
    transcript=[
        {
            'role': 'assistant',
            'content': 'Hello! How can I assist you today?',
            'user_id': None,
            'timestamp': '2025-10-16T05:32:13.345+00:00'
        },
        {
            'role': 'user',
            'content': 'Hello?',
            'user_id': 'PA_g5ZUtapAaPxq',
            'timestamp': '2025-10-16T05:32:24.952+00:00'
        },
        {
            'role': 'user',
            'content': 'Hello?',
            'user_id': 'PA_g5ZUtapAaPxq',
            'timestamp': '2025-10-16T05:32:25.130+00:00'
        },
        {
            'role': 'assistant',
            'content': 'क्या आप अभी भी यहाँ हैं?',
            'user_id': None,
            'timestamp': '2025-10-16T05:32:34.868+00:00'
        },
        {
            'role': 'user',
            'content': "Yes. Yes. I'm here.",
            'user_id': 'PA_g5ZUtapAaPxq',
            'timestamp': '2025-10-16T05:32:40.215+00:00'
        },
        {
            'role': 'user',
            'content': 'Hello?',
            'user_id': 'PA_g5ZUtapAaPxq     ',
            'timestamp': '2025-10-16T05:32:42.337+00:00'
        },
        {
            'role': 'user',
            'content': 'Hello?',
            'user_id': 'PA_g5ZUtapAaPxq',
            'timestamp': '2025-10-16T05:32:50.287+00:00'
        },
        {
            'role': 'user',
            'content': 'Hello?',
            'user_id': 'PA_g5ZUtapAaP     xq',
            'timestamp': '2025-10-16T05:32:53.661+00:00'
        },
        {
            'role': 'user',
            'content': 'Hello?',
            'user_id': 'PA_g5ZUtapAaPxq',
            'timestamp': '2025-10-16T05:33:04.588+00:00'
        },
        {
            'role': 'user',
            'content': 'Hello?',
            'user_id': 'PA_g5ZUtapA     aPxq',
            'timestamp': '2025-10-16T05:33:14.419+00:00'
        }
    ]
    import asyncio
    res = asyncio.run(summary.generate_summary(transcript=transcript, call_datetime="2025-10-16T05:32:13.345+00:00"))
    print(res)