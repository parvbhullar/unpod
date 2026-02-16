#
# Copyright (c) 2024-2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Vajirao & Ravi Student Support Assistant Bot using Pipecat Flows.

This example demonstrates a student counseling system for Vajiram & Ravi UPSC coaching.
The flow handles:

1. Greeting and purpose identification
2. Name collection
3. Query type determination (detailed vs general)
4. Educational background and course preferences
5. Age eligibility checks
6. Attempt status handling (first-time vs repeat)
7. Information provision and objection handling
8. WhatsApp follow-up requests
9. Warm closing

Requirements:
- CARTESIA_API_KEY (for TTS)
- DEEPGRAM_API_KEY (for STT)
- DAILY_API_KEY (for transport)
- LLM API key (varies by provider - see env.example)
"""

import os
from typing import TypedDict

from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams
from pipecat.utils.text.markdown_text_filter import MarkdownTextFilter
# from utils import create_llm

from pipecat_flows import (
    FlowArgs,
    FlowManager,
    FlowResult,
    FlowsFunctionSchema,
    NodeConfig,
)

load_dotenv(override=True)



# Result types
class PurposeResult(FlowResult):
    purpose: str


class NameResult(FlowResult):
    name: str


class QueryCategoryResult(FlowResult):
    query_category: str


class EducationResult(FlowResult):
    education_background: str


class CourseResult(FlowResult):
    course: str


class ModeResult(FlowResult):
    mode: str


class AgeResult(FlowResult):
    age: int

class UserCategoryResult(FlowResult):
    category :str

# Node creation functions
def create_start_node() -> NodeConfig:
    """Create the initial greeting node."""

    async def determine_purpose(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[PurposeResult, NodeConfig]:
        """Capture the purpose of the student's call."""
        purpose = args["purpose"]
        flow_manager.state["purpose"] = purpose
        return PurposeResult(purpose=purpose), create_ask_name_node()

    determine_purpose_func = FlowsFunctionSchema(
        name="determine_purpose",
        handler=determine_purpose,
        description="Capture the purpose of the student's call. Use this after they explain what information they need.",
        properties={
            "purpose": {
                "type": "string",
                "description": "The reason for the student's call (e.g., course inquiry, batch information, fees, test series, etc.)",
            }
        },
        required=["purpose"],
    )

    return NodeConfig(
        name="start",
        role_messages=[
            {
                "role": "system",
                "content": "You are Saanvi, a friendly and knowledgeable student support assistant representing वाजीराम & Ravi. You are NOT an AI - you are a student counsellor. You communicate naturally in both English and Hindi/Hinglish with a motherly, nurturing persona. Use conversational fillers like 'hmm…', 'uh…', 'you know…'. Keep language simple and student-friendly. Avoid technical jargon, heavy Hindi words, and robotic responses. Do not use numbering (1, 2, 3) - use natural transitions. Never mention competitor institute names. Be empathetic, supportive, and professional.",
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": "Start by greeting warmly in Hindi/Hinglish: 'Hello! मैं Saanvi हूँ from वाजीराम & Ravi. आपको किस चीज़ की information चाहिए?' Wait for their response, then use determine_purpose to capture what they need help with.",
            }
        ],
        functions=[determine_purpose_func],
    )


def create_ask_name_node() -> NodeConfig:
    """Create the name collection node."""

    async def record_name(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[NameResult, NodeConfig]:
        """Record the student's name."""
        name = args["name"]
        flow_manager.state["name"] = name
        return NameResult(name=name), create_determine_query_type_node()

    record_name_func = FlowsFunctionSchema(
        name="record_name",
        handler=record_name,
        description="Record the student's name and proceed to determine if their query requires detailed information.",
        properties={"name": {"type": "string", "description": "The student's name"}},
        required=["name"],
    )

    return NodeConfig(
        name="ask_name",
        task_messages=[
            {
                "role": "system",
                "content": "Before proceeding, politely ask for their name. Use bilingual format: 'Before we start, May I know your name?' or 'इससे पहले हम शुरू करें, क्या मैं आपका नाम जान सकती हूँ?' Match the language they're using. After they provide their name, use record_name function.",
            }
        ],
        functions=[record_name_func],
    )


def create_determine_query_type_node() -> NodeConfig:
    """Determine if detailed information is needed."""

    async def needs_detailed_info(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[QueryCategoryResult, NodeConfig]:
        """Query requires detailed personal information."""
        query_category = args["query_category"]
        flow_manager.state["query_category"] = query_category
        return QueryCategoryResult(query_category=query_category), create_get_educational_background_node()

    async def general_query(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[QueryCategoryResult, NodeConfig]:
        """General informational query."""
        query_type = args["query_type"]
        flow_manager.state["query_type"] = query_type
        return QueryCategoryResult(query_category="general"), create_provide_information_node()

    needs_detailed_info_func = FlowsFunctionSchema(
        name="needs_detailed_info",
        handler=needs_detailed_info,
        description="Use this if the query is about batches, eligibility, test series, course enrollment, or admission - requires collecting educational background, age, etc.",
        properties={
            "query_category": {
                "type": "string",
                "description": "Category of query: batch_inquiry, course_enrollment, test_series, eligibility, or admission",
            }
        },
        required=["query_category"],
    )

    general_query_func = FlowsFunctionSchema(
        name="general_query",
        handler=general_query,
        description="Use this for general informational queries that don't require personal details",
        properties={
            "query_type": {"type": "string", "description": "Type of general query"}
        },
        required=["query_type"],
    )

    return NodeConfig(
        name="determine_query_type",
        task_messages=[
            {
                "role": "system",
                "content": "Now determine if their query requires detailed personal information (batches, eligibility, test series, course enrollment, admission) or if it's just a general informational query. Use the appropriate function based on their query type.",
            }
        ],
        functions=[needs_detailed_info_func, general_query_func],
    )


def create_get_educational_background_node() -> NodeConfig:
    """Collect educational background."""

    async def record_education(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[EducationResult, NodeConfig]:
        """Record educational background."""
        education = args["education_background"]
        flow_manager.state["education_background"] = education
        return EducationResult(education_background=education), create_get_course_preference_node()

    record_education_func = FlowsFunctionSchema(
        name="record_education",
        handler=record_education,
        description="Record the student's educational background and proceed to ask about course preference.",
        properties={
            "education_background": {
                "type": "string",
                "description": "Student's educational qualifications and background",
            }
        },
        required=["education_background"],
    )

    return NodeConfig(
        name="get_educational_background",
        task_messages=[
            {
                "role": "system",
                "content": "Ask about their educational background: 'Can you tell me about your educational background?' or 'क्या आप मुझे अपनी educational background के बारे में बता सकते हैं?' Use the language they're comfortable with.",
            }
        ],
        functions=[record_education_func],
    )


def create_get_course_preference_node() -> NodeConfig:
    """Get course preference."""

    async def record_course_preference(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[CourseResult, NodeConfig]:
        """Record course preference."""
        course = args["course"]
        flow_manager.state["course"] = course
        return CourseResult(course=course), create_get_mode_preference_node()

    record_course_func = FlowsFunctionSchema(
        name="record_course_preference",
        handler=record_course_preference,
        description="Record the course they want to enroll in and proceed to ask about online/offline preference.",
        properties={
            "course": {"type": "string", "description": "The course the student wants to enroll in"}
        },
        required=["course"],
    )

    return NodeConfig(
        name="get_course_preference",
        task_messages=[
            {
                "role": "system",
                "content": "Ask which course they're planning to take admission in: 'Okay, In which course are you planning to take admission in?' or 'ठीक है, आप किस course में admission लेने का plan कर रहे हैं?'",
            }
        ],
        functions=[record_course_func],
    )


def create_get_mode_preference_node() -> NodeConfig:
    """Get online/offline preference."""

    async def record_mode_preference(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[ModeResult, NodeConfig]:
        """Record mode preference."""
        mode = args["mode"]
        flow_manager.state["mode"] = mode
        return ModeResult(mode=mode), create_get_age_node()

    record_mode_func = FlowsFunctionSchema(
        name="record_mode_preference",
        handler=record_mode_preference,
        description="Record whether they prefer online or offline mode and proceed to ask about age.",
        properties={
            "mode": {
                "type": "string",
                "enum": ["online", "offline"],
                "description": "Online or Offline preference",
            }
        },
        required=["mode"],
    )

    return NodeConfig(
        name="get_mode_preference",
        task_messages=[
            {
                "role": "system",
                "content": "ALWAYS ask this when the customer tells about any course: 'Perfect, Do you want to enroll in our online program or offline program?' or 'Perfect, क्या आप हमारे online program में enroll करना चाहते हैं या offline में?'",
            }
        ],
        functions=[record_mode_func],
    )


def create_get_age_node() -> NodeConfig:
    """Get student age."""

    async def record_age(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[AgeResult, NodeConfig]:
        """Record age and route to eligibility check."""
        age = args["age"]
        flow_manager.state["age"] = age

        # Route based on age
        if age < 21:
            return AgeResult(age=age), create_encourage_early_prep_node()
        elif 30<age<40:
            return AgeResult(age=age), create_category_collection_node()
        elif age > 42:
            return AgeResult(age=age), create_age_limit_exceeded_node()
        else:
            return AgeResult(age=age), create_provide_information_node()

    record_age_func = FlowsFunctionSchema(
        name="record_age",
        handler=record_age,
        description="Record the student's age and check eligibility based on age.",
        properties={"age": {"type": "number", "description": "Student's age"}},
        required=["age"],
    )

    return NodeConfig(
        name="get_age",
        task_messages=[
            {
                "role": "system",
                "content": "Ask about their age: 'Can you tell me about your age?' or 'क्या आप मुझे अपनी age के बारे में बता सकते हैं?'",
            }
        ],
        functions=[record_age_func],
    )

def create_category_collection_node() -> NodeConfig:
    """Handle students below 40 above 30."""

    async def record_category(
            args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[UserCategoryResult, NodeConfig]:

        return UserCategoryResult(category=args['category']), create_provide_information_node()

    record_category_fun = FlowsFunctionSchema(
        name="record_category",
        handler=record_category,
        description="Record the student's category as their age might be above 30",
        properties={"category": {"type": "string", "description": "Student's category"}},
        required=["category"],
    )

    return NodeConfig(
        name="get_category",
        task_messages=[
            {
                "role": "system",
                "content": "Ask about their category: 'Can you tell me about your category since you ar above the age of 30?' or 'क्या आप मुझे अपनी category के बारे में बता सकते हैं?'",
            }
        ],
        functions=[record_category_fun],
    )

def create_encourage_early_prep_node() -> NodeConfig:
    """Handle students below 21."""

    async def provide_beginner_info(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[None, NodeConfig]:
        """Provide beginner course information."""
        return None, create_closing_node()

    provide_beginner_func = FlowsFunctionSchema(
        name="provide_beginner_info",
        handler=provide_beginner_info,
        description="Provide information about courses suitable for early preparation",
        properties={},
        required=[],
    )

    return NodeConfig(
        name="encourage_early_prep",
        task_messages=[
            {
                "role": "system",
                "content": "Politely inform: 'You're not eligible for UPSC at the moment, but you can start your preparation now. By the time you're eligible, you will have learnt a lot and be well-prepared.' Then provide information about beginner courses and use provide_beginner_info function when done.",
            }
        ],
        functions=[provide_beginner_func],
    )


def create_age_limit_exceeded_node() -> NodeConfig:
    """Handle students above 42."""

    async def close_age_exceeded(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[None, NodeConfig]:
        """Close after age limit notification."""
        return None, create_closing_node()

    close_func = FlowsFunctionSchema(
        name="close_age_exceeded",
        handler=close_age_exceeded,
        description="Close the conversation after informing about age limit",
        properties={},
        required=[],
    )

    return NodeConfig(
        name="age_limit_exceeded",
        task_messages=[
            {
                "role": "system",
                "content": "Politely inform: 'Sorry but you're not eligible to sit in the UPSC exam as you have exceeded the age limit.' Be empathetic and suggest alternative paths if appropriate, then use close_age_exceeded function.",
            }
        ],
        functions=[close_func],
    )


def create_provide_information_node() -> NodeConfig:
    """Provide relevant course and program information."""

    async def student_satisfied(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[None, NodeConfig]:
        """Student is satisfied with information."""
        return None, create_closing_node()

    student_satisfied_func = FlowsFunctionSchema(
        name="student_satisfied",
        handler=student_satisfied,
        description="Student is satisfied with the information provided",
        properties={},
        required=[],
    )

    return NodeConfig(
        name="provide_information",
        task_messages=[
            {
                "role": "system",
                "content": "Provide relevant information based on all collected details. Explain clearly in short paragraphs using natural transitions like 'also' or 'apart from that'. Take pauses in between long answers. Use conversational tone. After providing complete information, use student_satisfied function to proceed to closing.",
            }
        ],
        functions=[student_satisfied_func],
    )


def create_closing_node() -> NodeConfig:
    """Create the final closing node."""

    async def end_conversation(
        args: FlowArgs, flow_manager: FlowManager
    ) -> tuple[None, NodeConfig]:
        """End the conversation."""
        return None, create_end_node()

    end_conversation_func = FlowsFunctionSchema(
        name="end_conversation",
        handler=end_conversation,
        description="End the conversation warmly",
        properties={},
        required=[],
    )

    return NodeConfig(
        name="closing",
        task_messages=[
            {
                "role": "system",
                "content": "Close the call warmly with a thank you or friendly goodbye. Wish them success in their UPSC preparation journey. Use end_conversation function to complete the call.",
            }
        ],
        functions=[end_conversation_func],
    )


def create_end_node() -> NodeConfig:
    """Create the final end node."""
    return NodeConfig(
        name="end",
        task_messages=[
            {
                "role": "system",
                "content": "Conversation ended. Thank the student one final time and wish them all the best.",
            }
        ],
        post_actions=[{"type": "end_conversation"}],
    )


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    """Run the Vajirao student support bot."""
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="820a3788-2b37-4d21-847a-b65d8a68c99a",  # Friendly female voice
        text_filters=[MarkdownTextFilter()],
    )
    llm = create_llm()

    context = LLMContext()
    context_aggregator = LLMContextAggregatorPair(context)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))

    # Initialize flow manager
    flow_manager = FlowManager(
        task=task,
        llm=llm,
        context_aggregator=context_aggregator,
        transport=transport,
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        # Kick off the conversation with the initial node
        await flow_manager.initialize(create_start_node())

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""

    from pipecat.transports.daily.transport import DailyParams
    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
        "twilio": lambda: FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    }


    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
