import dspy
from dspy import ChainOfThought


class CallAnalysisSignature(dspy.Signature):
    """Extract structured information from a call transcript and classify the call outcome."""

    call_transcript = dspy.InputField(
        desc="Complete transcription of the call conversation"
    )

    # Primary Status Field
    status = dspy.OutputField(
        desc="""Call outcome status. Must be exactly one of:
        - 'Interested': Candidate agrees to register child and provides name and grade
        - 'Call Back': Person requests a callback at a specific time
        - 'Not Interested': Person explicitly states they are not interested
        - 'Send Details': Person asks to receive details via WhatsApp or email
        - 'Not Connected': Call not answered or not connected for any reason
        - 'No Outcome': Call completed but no clear outcome or decision
        - 'Wrong Number': Person says it's wrong number or doesn't identify themselves"""
    )

    # Call Summary
    summary = dspy.OutputField(
        desc="Brief summary of the call conversation and key points discussed"
    )

    # Conditional Fields - For Registered Status
    child_name = dspy.OutputField(
        desc="Full name of the child (required if status='Registered', otherwise return 'N/A')"
    )

    child_grade = dspy.OutputField(
        desc="Grade/Class of the child, e.g., '5th Grade', 'Grade 8' (required if status='Registered', otherwise return 'N/A')"
    )

    # Conditional Fields - For Call Back Status
    callback_date = dspy.OutputField(
        desc="Date for callback in format 'YYYY-MM-DD' (required if status='Call Back', otherwise return 'N/A')"
    )

    callback_time = dspy.OutputField(
        desc="Time for callback in format 'HH:MM AM/PM' (required if status='Call Back', otherwise return 'N/A')"
    )


class CallAnalyzer(dspy.Module):
    """
    Analyzes call transcripts and extracts structured information including:
    - Call status/outcome
    - Child registration details (if applicable)
    - Callback scheduling (if applicable)
    - Call summary
    """

    def __init__(self):
        super().__init__()
        self.analyze_call = ChainOfThought(CallAnalysisSignature)

    def forward(self, call_transcript):
        """
        Process a call transcript and extract structured information.

        Args:
            call_transcript (str): The complete call transcription

        Returns:
            dspy.Prediction: Object containing all extracted fields
        """
        result = self.analyze_call(call_transcript=call_transcript)

        return dspy.Prediction(
            status=result.status,
            summary=result.summary,
            child_name=result.child_name,
            child_grade=result.child_grade,
            callback_date=result.callback_date,
            callback_time=result.callback_time
        )

    def get_structured_output(self, call_transcript):
        """
        Returns a dictionary with structured output for easier integration.

        Args:
            call_transcript (str): The complete call transcription

        Returns:
            dict: Structured dictionary with all extracted information
        """
        result = self.forward(call_transcript)

        output = {
            "status": result.status,
            "summary": result.summary,
            "registration_details": {
                "child_name": result.child_name if result.status == "Registered" else None,
                "child_grade": result.child_grade if result.status == "Registered" else None
            },
            "callback_details": {
                "date": result.callback_date if result.status == "Call Back" else None,
                "time": result.callback_time if result.status == "Call Back" else None
            }
        }

        return output