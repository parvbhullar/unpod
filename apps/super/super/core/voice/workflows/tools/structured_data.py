import json
from datetime import datetime
import dspy
from dotenv import load_dotenv
from datetime import datetime
from ..dspy_config import get_dspy_lm
from ...prompts.evalution_prompts.structured_data_eval import BASE_PROMPT
from super.core.voice.prompts.evalution_prompts.structured_data_eval import BASE_PROMPT
load_dotenv(override=True)



class StructuredDataSignature(dspy.Signature):
    call_transcript = dspy.InputField(desc="full call transcript")
    schema_fields = dspy.InputField(
        desc="fields to extract from call transcript and their type and full description detail"
    )
    current_time = dspy.InputField(
        desc="current date and time based on which we should predict future events"
    )
    success_eval_result = dspy.InputField(
        desc="success evaluation result based on which you can satisfy some conditions in structured data"
    )
    prompt = dspy.InputField(
        desc="prompt that's used to extract structured data from the call. based on schema field and type of schema key "
    )
    extracted_data = dspy.OutputField(
        desc="JSON object mapping field names to extracted values based on the keys in schema field and their type eg: number or text",
        type=dict,
    )


class StructuredDataExtractor(dspy.Module):
    def __init__(self, lm=None):
        super().__init__()
        self.lm = lm or get_dspy_lm()
        self.extract = dspy.ChainOfThought(StructuredDataSignature)

    def forward(self, call_transcript, schema_fields, prompt, success_eval):
        with dspy.context(lm=self.lm):
            print(schema_fields)
            combined_prompt = f"{BASE_PROMPT}\n{prompt}"
            result = self.extract(
                call_transcript=call_transcript,
                schema_fields=schema_fields,
                prompt=combined_prompt,
                current_time=datetime.now(),
                success_eval_result=success_eval
            )

            res = result.extracted_data

            try:
                if isinstance(result.extracted_data, str):
                    res = json.loads(result.extracted_data)
            except Exception as e:
                res = result.extracted_data

            return res


