import dspy
from dotenv import load_dotenv
from dspy import ChainOfThought
from ..dspy_config import get_dspy_lm
from super.core.voice.prompts.evalution_prompts.success_eval import BASE_PROMPT

load_dotenv(override=True)


class EvaluationScale:
    def __init__(self, name, definition):
        self.name = name
        self.definition = definition

    def __repr__(self):
        return f"EvaluationScale(name='{self.name}', definition='{self.definition}')"


evaluation_scales = [
    EvaluationScale(name="NumericScale", definition="A scale of 1 to 10."),
    EvaluationScale(
        name="DescriptiveScale", definition="A scale of Excellent, Good, Fair, Poor."
    ),
    EvaluationScale(
        name="Checklist", definition="A checklist of criteria and their status."
    ),
    EvaluationScale(
        name="Matrix",
        definition="A grid that evaluates multiple criteria across different performance levels.",
    ),
    EvaluationScale(name="PercentageScale", definition="A scale of 0% to 100%."),
    EvaluationScale(
        name="LikertScale",
        definition="A scale of Strongly Agree, Agree, Neutral, Disagree, Strongly Disagree.",
    ),
    EvaluationScale(
        name="FCR(First-Call-Resolution)",
        definition="A scale of FCR,NotFCR.System shall mark call as FCR only if:  1.Query resolved by bot  2.No agent escalation  3.No call drop or abandonment ",
    ),
]


class SuccessEvaluatorSignature(dspy.Signature):
    call_transcript = dspy.InputField(desc="transcription of the entire call")
    prompt = dspy.InputField(
        desc="prompt that defines how to figure out if the call was successful or not "
    )
    metric = dspy.InputField(desc="which metric should the call success be defined in")
    reason = dspy.OutputField(desc="small summary of why we chose this success score")
    success = dspy.OutputField(
        desc="success score weather the call was successful or not based on the given prompt in given metric type"
    )


class SuccessEvaluator(dspy.Module):
    def __init__(self, lm=None):
        super().__init__()
        self.lm = lm or get_dspy_lm()
        self.generate_summary = ChainOfThought(SuccessEvaluatorSignature)

    async def forward(self, call_transcript, success_prompt, metric_name):
        with dspy.context(lm=self.lm):
            metric = next(
                (s for s in evaluation_scales if s.name == metric_name),
                evaluation_scales[0],
            )

            combined_prompt = f"{BASE_PROMPT}\n{success_prompt}"

            result = self.generate_summary(
                call_transcript=call_transcript,
                prompt=combined_prompt,
                metric={"name": metric.name, "definition": metric.definition},
            )

            print(
                f"\n\n success evaluation : \n\n {success_prompt}  \n\n {result.success} :  {result.reason}\n\n"
            )

            return dspy.Prediction(
                evaluate=result.success,
            )
