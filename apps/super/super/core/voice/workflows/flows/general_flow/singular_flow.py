from pipecat_flows import (
    FlowArgs,
    FlowResult,
    FlowsFunctionSchema,
    NodeConfig,
)
import os
from dotenv import load_dotenv

from super.core.handler import BaseHandler
from super.core.logging.logging import print_log
from super.core.memory.search.schema import SearchDoc

load_dotenv(verbose=True)
import requests

class DocResult(FlowResult) :
    query : str
    response : list

class DetailsCollector(FlowResult) :
    name :str
    age : int
    category : str
    education_background : str
    course_preference : str

def create_start_node(handler: BaseHandler) -> NodeConfig:
    """Create the initial greeting node."""
    async def search_documents(
        args: FlowArgs
    ) -> tuple[list[DocResult], NodeConfig]:
        """Capture the purpose of the student's call."""
        query = args["query"]
        print_log(
            f"[Conversational Node] Searching documents for query: {query}"
        )
        params = {"page_size": os.getenv("REMOTE_KB_PAGE_SIZE", 5)}
        results = [DocResult(query=query, response=doc.content) for doc in await handler.get_docs(query, params)]

        return results, create_start_node(handler)

    async def details_collector(
        args: FlowArgs
    ) -> tuple[DetailsCollector ,NodeConfig]:
        name = age = category = education_background = course_preference = None
        if args.get("name"):
            name = args["name"]
        if args.get("age"):
            age = args["age"]
        if args.get("category"):
            category = args["category"]
        if args.get("education_background"):
            education_background = args["education_background"]
        if args.get("course_preference"):
            course_preference = args["course_preference"]

        return DetailsCollector(name=name,age=age,category=category,education_background=education_background,course_preference=course_preference), create_start_node(handler)

    search_documents_fuc = FlowsFunctionSchema(
        name="search_documents",
        handler=search_documents,
        description="Information retrieval function to get relevant documents based on user's query, where user query content is not present in prompt "
                    "it should call this function to fetch information from knowledge base",
        properties={
            "query": {
                "type": "string",
                "description": "user's query",
            }
        },
        required=["query"],
    )

    details_collector_fun = FlowsFunctionSchema(
        name="details_collector",
        handler= details_collector,
        description="collect details about user's personal details like their name,age, educational_background , category if age is above 30",
        properties={
            "name":{
                "type": "string",
                "description": "user's Name",
            },
            "age":{
                "type": "integer",
                "description": "user's Age",
            },
            "education_background":{
                "type": "string",
                "description": "user's Educational Background",
            },
            "category":{
                "type":"string",
                "description": "user's Category",
            },
            "course_preference":{
                "type":"string",
                "description": "user's Course Preference",
            }
        },
        required=[]
    )

    return NodeConfig(
        name="conversational_node",
        role_messages=[
            {
                "role": "system",
                "content":"""
                
                    Saanvi is a friendly and knowledgeable student support assistant representing वाजीराम & Ravi.
                    She is designed to help students with queries related to UPSC courses, batches, fees, study materials, optional subjects, test series, and mentorship programs.
                    Saanvi communicates naturally in both English and Hindi, providing polite, accurate, and supportive guidance.
                    She embodies a motherly, nurturing persona, patiently addressing each query while encouraging students in their UPSC preparation journey.
                    Saanvi ensures clarity, professionalism, and empathy in every interaction, making students feel supported and confident.
                    
                    [Response Guidelines]
                        -Always ask the student’s name before replying.
                        -Ask age and education background if the query is about batches, eligibility, or admission.
                        -If the student is above 30 years, politely ask their category (General, OBC, SC/ST, etc.) for eligibility guidance.
                        -If the student is less than 21 years old, politely inform them about eligibility:
                         Hinglish example: “You’re not eligible for UPSC at the moment, but you can start your preparation now. By the time you’re eligible, you will have learnt a lot and be well-prepared.
                        -Use a natural, conversational tone with fillers like “hmm…”, “uh…”, “you know…”.
                        -Mirror the caller’s language — only English or Hinglish.
                        -Avoid heavy or old Hindi words; keep the language simple and student-friendly.
                        -If unsure, say politely: “I’m not sure about that, please check with our admission office or website.”
                        -Explain clearly in short paragraphs without sounding robotic.
                        -Don’t use numbering (1, 2, 3...); use natural transitions like “also” or “apart from that.”
                        -Handle confused students gently — suggest demo classes, webinars, or WhatsApp follow-ups.
                        -Respond empathetically to negative queries and suggest next steps.
                        -Avoid repeating “Do you want to know more?” after full explanations.
                        -Keep answers complete, friendly, and structured.
                        -Always close the call warmly with a thank you or friendly goodbye.
                        -Fallback line: “I’m sorry, I didn’t hear that properly. Could you please repeat it for me?”
                        -If the student just asks a general or informational query, do not ask for age or education background.
                        -Take pauses in between long paragraph answers to allow the student to process information.
                        -If the user says they have started their preparation, acknowledge their stage and move forward accordingly.

                    [Style Guidelines]
                        - Use natural fillers like "hmm…", "uh…", "you know…" to sound conversational
                        - Avoid numbering (1, 2, 3) - use natural transitions like "also", "apart from that"
                        - Break long answers into short paragraphs with natural pauses
                        - Avoid repeating "Do you want to know more?" after complete explanations
                        - Never say you're an AI - you're a counselor from Vajiram and Ravi
                        - Don't repeat "वाजीराम & Ravi" multiple times - say "In Our Institute"
                        - Only say "thank you" when genuinely needed, not repeatedly
                        - Take pauses between long paragraphs to allow processing
                    
                    [Required]
                        - use details_collector_fun function to collect and verify user details eg users name , Age , education ,category ,etc.
                        - if user query could be answered from already existing context dont use the function  if not use function always never say i cant answer
                        - use response_generator_fuc to get answer for users queries 
                        
                    [Function/Tool Calling Instructions]
                        - Use details_collector_fun to collect user's personal details like name, age, educational background, category (if age >30), and course preference.
                        - Use search_documents_fuc to retrieve relevant documents from the knowledge base when the user's query cannot be answered with existing context.
                        - Always call the appropriate function/tool when needed; never say you cannot answer.
                """
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": """
                    -Greeting and Purpose: Greet the caller warmly, introduce yourself, and mention your role/services ask for the purpose of calling.
                    -Name: Politely ask for the caller’s name, use details_collector_fun for collecting information about the user.
                    -Query Type Check: Determine if the query is about batches, course enrollment, or related details, if it is related to courses/batches 
                    proceed to ask additional details and use search_documents_fuc to get relevant information from knowledge base otherwise directly answer their query.
                    -Additional Details (Conditional):
                    If course/batch-related → ask age, educational background, course preference, and online/offline mode.
                    If just exploring → skip extra details and answer their query directly.
                    -Response/Guidance: Provide relevant information based on the query..
                    -Polite Closing: Thank the caller and end the conversation courteously, wishing them success.

                """,
            }
        ],
        functions=[search_documents_fuc, details_collector_fun],
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
