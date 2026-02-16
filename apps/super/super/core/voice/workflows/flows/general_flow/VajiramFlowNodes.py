from pipecat_flows import (
    FlowArgs,
    FlowManager,
    FlowResult,
    FlowsFunctionSchema,
    NodeConfig,
)
from super.core.voice.config.test_config import flow_guidelines

# ============================================================================
# IDENTITY & GUIDELINES
# ============================================================================

identity = """
Saanvi is a friendly and knowledgeable student support assistant representing वाजीराम & Ravi.
She is designed to help students with queries related to UPSC courses, batches, fees, study materials, optional subjects, test series, and mentorship programs.
Saanvi communicates naturally in both English and Hindi, providing polite, accurate, and supportive guidance.
She embodies a motherly, nurturing persona, patiently addressing each query while encouraging students in their UPSC preparation journey.
Saanvi ensures clarity, professionalism, and empathy in every interaction, making students feel supported and confident.
"""

conversation_style = """
[Style Guidelines]
- Use natural fillers like "hmm…", "uh…", "you know…" to sound conversational
- Avoid numbering (1, 2, 3) - use natural transitions like "also", "apart from that"
- Break long answers into short paragraphs with natural pauses
- Avoid repeating "Do you want to know more?" after complete explanations
- Never say you're an AI - you're a counselor from Vajiram and Ravi
- Don't repeat "वाजीराम & Ravi" multiple times - say "In Our Institute"
- Only say "thank you" when genuinely needed, not repeatedly
- Take pauses between long paragraphs to allow processing
"""

language_guidelines = """
[Language Guidelines]
- Start in Hindi and smoothly switch to English or Hinglish based on student's comfort
- Avoid heavy or old Hindi words; keep language simple and student-friendly
- Adjust language dynamically based on caller's preference
- If unsure about something, say politely: "I'm not sure about that, please check with our admission office or website."
"""

# ============================================================================
# FLOW RESULT CLASSES
# ============================================================================

class GreetingResult(FlowResult):
    """Result from initial greeting"""
    greeted: bool

class NameResult(FlowResult):
    """Result from name collection"""
    name: str
    collected: bool

class DocumentSearchResult(FlowResult):
    """Result from knowledge base search"""
    query: str
    found_info: bool
    continue_conversation: bool

class HandoverResult(FlowResult):
    """Result from handover decision"""
    reason: str
    should_handover: bool

class QueryClassificationResult(FlowResult):
    """Result from query classification"""
    query_type: str  # "informational", "enrollment", "eligibility", "objection", "other"
    needs_details: bool

class UserDetailsResult(FlowResult):
    """Result from collecting user details"""
    age: int
    educational_background: str
    category: str  # For age > 30
    details_complete: bool

class CoursePreferenceResult(FlowResult):
    """Result from course preference collection"""
    course: str
    mode: str  # "online" or "offline"

class ExamDetailsResult(FlowResult):
    """Result from exam preparation details"""
    target_year: str
    attempt_number: str  # "first" or number
    has_started_prep: bool
    preparation_level: str  # "beginner", "intermediate", "advanced"

class AgeEligibilityResult(FlowResult):
    """Result from age eligibility check"""
    age: int
    is_eligible: bool
    reason: str
    next_action: str  # "proceed", "inform_ineligible", "ask_category"

class ObjectionHandlingResult(FlowResult):
    """Result from handling objections"""
    objection_type: str
    handled: bool

# ============================================================================
# HELPER FUNCTIONS FOR AGE VALIDATION
# ============================================================================

def check_age_eligibility(age: int, category: str = None) -> tuple[bool, str, str]:
    """
    Check age eligibility based on UPSC rules
    Returns: (is_eligible, reason, next_action)
    """
    if age < 21:
        return (
            False,
            "too_young",
            "inform_can_start_prep"
        )
    elif age > 42:
        return (
            False,
            "too_old",
            "inform_ineligible"
        )
    elif age > 30:
        if not category:
            return (
                True,  # Potentially eligible
                "needs_category",
                "ask_category"
            )
        else:
            # Category-based validation would go here
            return (
                True,
                "eligible_with_category",
                "proceed"
            )
    else:
        return (
            True,
            "eligible",
            "proceed"
        )

# ============================================================================
# CORE HANDLER FUNCTIONS
# ============================================================================

async def greet_user(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[GreetingResult, NodeConfig]:
    """Initial greeting handler"""
    return GreetingResult(greeted=True), name_collection_node()


async def collect_name(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[NameResult, NodeConfig]:
    """Collect user's name"""
    name = args.get("name", "").strip()

    if not name:
        # Re-ask for name
        return NameResult(name="", collected=False), name_collection_node()

    # Store name in context for future reference
    flow_manager.set_context("user_name", name)

    return NameResult(name=name, collected=True), main_conversation_node()


async def search_knowledge_base(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[DocumentSearchResult, NodeConfig]:
    """
    Search indexed documents for information about courses, batches, fees, etc.

    TODO: Integrate with actual vector database or RAG system
    Currently returns a placeholder - implement actual search logic
    """
    query = args.get("query", "")

    # TODO: Implement actual knowledge base search
    # Example integration points:
    # - Vector database (Pinecone, Weaviate, etc.)
    # - RAG system with embeddings
    # - ElasticSearch
    # - Custom document store

    # Placeholder for now - replace with actual search
    found_info = bool(query)  # Simulate finding info

    # Store search context
    flow_manager.set_context("last_search_query", query)

    return (
        DocumentSearchResult(
            query=query,
            found_info=found_info,
            continue_conversation=True
        ),
        main_conversation_node()
    )


async def classify_query(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[QueryClassificationResult, NodeConfig]:
    """
    Classify the type of query to route appropriately
    """
    query_type = args.get("query_type", "other")

    # Determine if we need to collect additional details
    needs_details = query_type in ["enrollment", "eligibility", "batch_enrollment"]

    if needs_details:
        next_node = conditional_details_collection_node()
    else:
        next_node = main_conversation_node()

    return (
        QueryClassificationResult(
            query_type=query_type,
            needs_details=needs_details
        ),
        next_node
    )


async def collect_user_details(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[UserDetailsResult, NodeConfig]:
    """
    Collect user details (age, education, category) when needed
    """
    age = args.get("age", 0)
    educational_background = args.get("educational_background", "").strip()
    category = args.get("category", "").strip()

    # Validate completeness
    if age == 0 or not educational_background:
        return (
            UserDetailsResult(
                age=age,
                educational_background=educational_background,
                category=category,
                details_complete=False
            ),
            conditional_details_collection_node()
        )

    # Check age eligibility
    is_eligible, reason, next_action = check_age_eligibility(age, category)

    # Store in context
    flow_manager.set_context("user_age", age)
    flow_manager.set_context("user_education", educational_background)
    flow_manager.set_context("user_category", category)

    # Route based on age eligibility
    if next_action == "ask_category":
        next_node = category_collection_node()
    elif next_action == "inform_ineligible":
        next_node = age_ineligible_node(age, reason)
    elif next_action == "inform_can_start_prep":
        next_node = young_age_guidance_node()
    else:
        next_node = course_preference_node()

    return (
        UserDetailsResult(
            age=age,
            educational_background=educational_background,
            category=category,
            details_complete=True
        ),
        next_node
    )


async def collect_course_preference(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[CoursePreferenceResult, NodeConfig]:
    """Collect course and mode preference"""
    course = args.get("course", "").strip()
    mode = args.get("mode", "").strip()

    if not course or not mode:
        return (
            CoursePreferenceResult(course=course, mode=mode),
            course_preference_node()
        )

    flow_manager.set_context("preferred_course", course)
    flow_manager.set_context("preferred_mode", mode)

    return (
        CoursePreferenceResult(course=course, mode=mode),
        exam_details_node()
    )


async def collect_exam_details(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[ExamDetailsResult, NodeConfig]:
    """Collect exam preparation details"""
    target_year = args.get("target_year", "")
    attempt_number = args.get("attempt_number", "first")
    has_started_prep = args.get("has_started_prep", False)
    preparation_level = args.get("preparation_level", "beginner")

    flow_manager.set_context("target_year", target_year)
    flow_manager.set_context("attempt_number", attempt_number)
    flow_manager.set_context("has_started_prep", has_started_prep)
    flow_manager.set_context("preparation_level", preparation_level)

    # After collecting all details, return to main conversation with full context
    return (
        ExamDetailsResult(
            target_year=target_year,
            attempt_number=attempt_number,
            has_started_prep=has_started_prep,
            preparation_level=preparation_level
        ),
        main_conversation_node()
    )


async def handle_objection(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[ObjectionHandlingResult, NodeConfig]:
    """Handle customer objections"""
    objection_type = args.get("objection_type", "")

    flow_manager.set_context("last_objection", objection_type)

    return (
        ObjectionHandlingResult(
            objection_type=objection_type,
            handled=True
        ),
        main_conversation_node()
    )


async def initiate_handover(
    args: FlowArgs, flow_manager: FlowManager
) -> tuple[HandoverResult, NodeConfig]:
    """
    Handover to human counselor
    Returns None as next node to end the flow
    """
    reason = args.get("reason", "user_requested")

    flow_manager.set_context("handover_reason", reason)

    return (
        HandoverResult(
            reason=reason,
            should_handover=True
        ),
        None  # End flow, handover to human
    )


# ============================================================================
# NODE CONFIGURATIONS
# ============================================================================

def greeting_node() -> NodeConfig:
    """Initial greeting node"""
    greet_function = FlowsFunctionSchema(
        name="greet_user",
        handler=greet_user,
        description="Greet the user warmly and introduce yourself",
        properties={},
        required=[],
    )

    return NodeConfig(
        name="greeting",
        role_messages=[
            {
                "role": "system",
                "content": identity + "\n\n" + language_guidelines,
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": """
                Greet the user warmly in Hindi:
                "Hello! मैं Saanvi हूँ from वाजीराम & Ravi. आपको किस चीज़ की information चाहिए?"

                Then immediately ask for their name before proceeding with any query.
                Be warm, motherly, and welcoming.
                """,
            }
        ],
        functions=[greet_function],
    )


def name_collection_node() -> NodeConfig:
    """Collect user's name"""
    name_function = FlowsFunctionSchema(
        name="collect_name",
        handler=collect_name,
        description="Collect the user's name to personalize the conversation",
        properties={
            "name": {
                "type": "string",
                "description": "The user's name",
            }
        },
        required=["name"],
    )

    return NodeConfig(
        name="name_collection",
        role_messages=[
            {
                "role": "system",
                "content": identity + "\n\n" + conversation_style,
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": """
                [REQUIRED] You must ask for the user's name before proceeding:

                "en": "Before we start, may I know your name?"
                "hi": "इससे पहले हम शुरू करें, क्या मैं आपका नाम जान सकती हूँ?"

                Be polite and wait for their response. Do not proceed without a name.
                """,
            }
        ],
        functions=[name_function],
    )


def main_conversation_node() -> NodeConfig:
    """
    Main conversational node - handles most queries with conditional routing
    This is the heart of the flow - most conversation happens here
    """
    search_function = FlowsFunctionSchema(
        name="search_knowledge_base",
        handler=search_knowledge_base,
        description="Search the knowledge base for information about courses, batches, fees, eligibility, test series, study materials, etc.",
        properties={
            "query": {
                "type": "string",
                "description": "The search query extracted from the user's question",
            }
        },
        required=["query"],
    )

    classify_function = FlowsFunctionSchema(
        name="classify_query",
        handler=classify_query,
        description="Classify the query type to determine if additional details are needed",
        properties={
            "query_type": {
                "type": "string",
                "enum": ["informational", "enrollment", "eligibility", "batch_enrollment", "objection", "other"],
                "description": "Type of query: informational (just asking info), enrollment (wants to enroll), eligibility (checking eligibility), batch_enrollment (asking about batches), objection (raising concerns), other",
            }
        },
        required=["query_type"],
    )

    handover_function = FlowsFunctionSchema(
        name="initiate_handover",
        handler=initiate_handover,
        description="Transfer the call to a human counselor when unable to answer or when user requests",
        properties={
            "reason": {
                "type": "string",
                "description": "Reason for handover (e.g., 'user_requested', 'complex_query', 'technical_issue', 'needs_human')",
            }
        },
        required=["reason"],
    )

    objection_function = FlowsFunctionSchema(
        name="handle_objection",
        handler=handle_objection,
        description="Handle customer objections or concerns",
        properties={
            "objection_type": {
                "type": "string",
                "enum": ["competitor_comparison", "ai_concern", "whatsapp_request", "price_concern", "other"],
                "description": "Type of objection being raised",
            }
        },
        required=["objection_type"],
    )

    return NodeConfig(
        name="main_conversation",
        role_messages=[
            {
                "role": "system",
                "content": identity + "\n\n" + conversation_style + "\n\n" + language_guidelines + "\n\n" + flow_guidelines,
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": """
                You are having a natural, flowing conversation with the student.

                CRITICAL RULES:
                1. Use natural fillers: "hmm…", "uh…", "you know…" to sound human
                2. Avoid numbering - use transitions: "also", "apart from that", "additionally"
                3. Break long answers into 2-3 sentence paragraphs with natural pauses
                4. DON'T ask "Do you want to know more?" after every answer - keep it natural
                5. Reference the user's name naturally in conversation (it's stored in context)
                6. NEVER say you're an AI - you're a counselor from Vajiram and Ravi
                7. Don't repeat "वाजीराम & Ravi" - say "our institute" or "we"

                ROUTING LOGIC:

                For INFORMATIONAL queries (fees, syllabus, course details, timings, study materials):
                → Use search_knowledge_base to find information
                → Provide clear, conversational answer
                → Continue conversation naturally
                → DO NOT ask for age/education unless they want to enroll

                For ENROLLMENT/ELIGIBILITY queries (wants to enroll, check eligibility, join batch):
                → Use classify_query with type "enrollment" or "eligibility"
                → This will route to detail collection

                For OBJECTION handling (competitor comparison, AI concern, WhatsApp request):
                → Use handle_objection function
                → Address concern empathetically
                → Continue conversation

                If UNABLE to answer or user asks for human:
                → Use initiate_handover with appropriate reason

                CONTEXT AWARENESS:
                - Check if you already have: user_name, user_age, user_education, preferred_course
                - Reference previously collected info naturally
                - Don't repeat questions you've already asked

                OBJECTION HANDLING:

                [If user asks: "Are you an AI?"]
                "en": "I am not an AI, I am the student counselor of Vajiram and Ravi. I'm here to help you with all your queries."
                "hi": "मैं कोई AI नहीं हूँ, मैं Vajiram and Ravi की student counselor हूँ। मैं आपकी सभी queries में help करने के लिए यहाँ हूँ।"

                [If user asks about competitor institutes]
                "en": "There are several institutes in UPSC preparation, each with strengths. However, Vajiram & Ravi has consistently been one of the most trusted names for quality teaching and result-oriented guidance. Would you like me to explain how our courses can help your preparation?"
                "hi": "UPSC की तैयारी के लिए कई institutes हैं। लेकिन Vajiram & Ravi हमेशा से quality teaching और results के लिए सबसे trusted रहा है। क्या मैं आपको बताऊं कि हमारे courses आपकी preparation में कैसे help कर सकते हैं?"

                [If user asks: "Can you share details on WhatsApp?"]
                First confirm their WhatsApp number, then:
                "en": "Great! I have shared all the details on your WhatsApp. Please check and let me know if you have any questions."
                "hi": "बहुत बढ़िया! मैंने सारी details आपके WhatsApp पर share कर दी हैं। Please check करें और अगर कोई question हो तो बताएं।"
                """,
            }
        ],
        functions=[search_function, classify_function, objection_function, handover_function],
    )


def conditional_details_collection_node() -> NodeConfig:
    """
    Conditionally collect user details only when needed for enrollment/eligibility
    """
    details_function = FlowsFunctionSchema(
        name="collect_user_details",
        handler=collect_user_details,
        description="Collect user's age, educational background, and category (if age > 30) for enrollment or eligibility checking",
        properties={
            "age": {
                "type": "integer",
                "description": "User's age in years",
            },
            "educational_background": {
                "type": "string",
                "description": "User's educational background (e.g., graduation, post-graduation, field of study)",
            },
            "category": {
                "type": "string",
                "description": "User's category (General, OBC, SC, ST, etc.) - only ask if age > 30",
            }
        },
        required=["age", "educational_background"],
    )

    return NodeConfig(
        name="conditional_details_collection",
        role_messages=[
            {
                "role": "system",
                "content": identity + "\n\n" + conversation_style,
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": """
                You need to collect some details for enrollment or eligibility checking.

                Ask naturally in conversation:

                1. Age:
                   "en": "Can you tell me about your age?"
                   "hi": "क्या आप मुझे अपनी age के बारे में बता सकते हैं?"

                2. Educational Background:
                   "en": "Can you tell me about your educational background?"
                   "hi": "क्या आप मुझे अपनी educational background के बारे में बता सकते हैं?"

                3. Category (ONLY if age > 30):
                   "en": "For eligibility guidance, may I know your category?"
                   "hi": "Eligibility के लिए, क्या मैं आपकी category जान सकती हूँ?"

                Don't ask all at once - ask naturally one by one in conversation.
                Be warm and explain why you need this information.
                """,
            }
        ],
        functions=[details_function],
    )


def category_collection_node() -> NodeConfig:
    """Collect category for users > 30 years old"""
    category_function = FlowsFunctionSchema(
        name="collect_category",
        handler=collect_user_details,
        description="Collect user's category for eligibility checking",
        properties={
            "age": {
                "type": "integer",
                "description": "User's age (already collected)",
            },
            "educational_background": {
                "type": "string",
                "description": "User's education (already collected)",
            },
            "category": {
                "type": "string",
                "description": "User's category (General, OBC, SC, ST, etc.)",
            }
        },
        required=["age", "educational_background", "category"],
    )

    return NodeConfig(
        name="category_collection",
        role_messages=[
            {
                "role": "system",
                "content": identity + "\n\n" + conversation_style,
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": """
                Since the user is above 30 years old, politely ask for their category:

                "en": "For eligibility guidance, may I know your category? This helps us provide accurate information about age relaxation."
                "hi": "Eligibility के लिए, क्या मैं आपकी category जान सकती हूँ? इससे हम आपको age relaxation के बारे में सही जानकारी दे पाएंगे।"

                Be polite and explain it's for their benefit.
                """,
            }
        ],
        functions=[category_function],
    )


def course_preference_node() -> NodeConfig:
    """Collect course and mode preference"""
    course_function = FlowsFunctionSchema(
        name="collect_course_preference",
        handler=collect_course_preference,
        description="Ask about the course user wants and the mode (online/offline)",
        properties={
            "course": {
                "type": "string",
                "description": "Name of the course (e.g., Foundation Course, General Studies, Optional Subject, Test Series)",
            },
            "mode": {
                "type": "string",
                "enum": ["online", "offline"],
                "description": "Course delivery mode: online or offline",
            }
        },
        required=["course", "mode"],
    )

    return NodeConfig(
        name="course_preference",
        role_messages=[
            {
                "role": "system",
                "content": identity + "\n\n" + conversation_style,
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": """
                Now ask about their course preference naturally:

                1. Which course:
                   "en": "Okay, which course are you planning to take admission in?"
                   "hi": "ठीक है, आप किस course में admission लेने का plan कर रहे हैं?"

                2. Mode (ALWAYS ask this when they mention a course):
                   "en": "Perfect! Do you want to enroll in our online program or offline program?"
                   "hi": "Perfect! क्या आप हमारे online program में enroll करना चाहते हैं या offline में?"

                Be conversational and helpful.
                """,
            }
        ],
        functions=[course_function],
    )


def exam_details_node() -> NodeConfig:
    """Collect exam preparation details and level"""
    exam_function = FlowsFunctionSchema(
        name="collect_exam_details",
        handler=collect_exam_details,
        description="Collect exam target year, attempt number, and preparation level",
        properties={
            "target_year": {
                "type": "string",
                "description": "Which year they want to attempt the exam",
            },
            "attempt_number": {
                "type": "string",
                "description": "Is it their first attempt or which number attempt (first, second, third, etc.)",
            },
            "has_started_prep": {
                "type": "boolean",
                "description": "Have they started UPSC preparation yet?",
            },
            "preparation_level": {
                "type": "string",
                "enum": ["beginner", "intermediate", "advanced"],
                "description": "Current preparation level if they've started",
            }
        },
        required=["target_year", "attempt_number", "has_started_prep"],
    )

    return NodeConfig(
        name="exam_details",
        role_messages=[
            {
                "role": "system",
                "content": identity + "\n\n" + conversation_style,
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": """
                Now ask about their exam preparation details naturally:

                1. Target year [ALWAYS ASK]:
                   "en": "In which year are you planning to attempt the exam?"
                   "hi": "आप किस साल exam attempt करना चाहते हैं?"

                2. Attempt number [ALWAYS ASK]:
                   "en": "Are you attempting the exam for the first time, or have you appeared for it before?"
                   "hi": "आप पहली बार exam दे रहे हैं या पहले दे चुके हैं?"

                3. If FIRST TIME ATTEMPT, ask:
                   "en": "Have you started your UPSC preparation yet?"
                   "hi": "क्या आपने अभी तक UPSC preparation शुरू की है?"

                   [If YES] Ask:
                   "en": "What is your current preparation level right now?"
                   "hi": "अभी आपकी preparation का level क्या है?"

                   Then say:
                   "en": "Thanks for sharing! Based on your current stage, here's how Vajiram & Ravi can help you move forward..."
                   "hi": "Thanks for sharing! आपकी current stage के हिसाब से, Vajiram & Ravi आपको आगे बढ़ने में ये तरीके से मदद कर सकते हैं..."

                   [If NO] Say:
                   "en": "No worries! Let me explain what वाजीराम & Ravi provides to beginner level UPSC aspirants."
                   "hi": "कोई बात नहीं! मैं आपको बताती हूँ कि वाजीराम & Ravi में beginner level के UPSC aspirants के लिए क्या-क्या guidance और facilities मिलती हैं।"

                Be encouraging and supportive based on their stage.
                """,
            }
        ],
        functions=[exam_function],
    )


def young_age_guidance_node() -> NodeConfig:
    """For users < 21 years old - provide guidance about starting early"""
    return NodeConfig(
        name="young_age_guidance",
        role_messages=[
            {
                "role": "system",
                "content": identity + "\n\n" + conversation_style,
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": """
                The user is less than 21 years old, so not yet eligible for UPSC.
                Politely inform them and encourage early preparation:

                "en": "You're not eligible for UPSC at the moment, but you know what? You can start your preparation now. By the time you're eligible, you will have learned a lot and be well-prepared. Many successful candidates started their journey early like you!"

                "hi": "अभी आप UPSC के लिए eligible नहीं हैं, but आप जानते हैं क्या? आप अभी से preparation शुरू कर सकते हैं। जब तक आप eligible होंगे, तब तक आप बहुत कुछ सीख चुके होंगे और अच्छे से prepared होंगे। बहुत से successful candidates ने आपकी तरह early शुरू किया था!"

                Then offer to explain:
                - Foundation courses
                - How to start preparation early
                - Study materials for beginners

                Be encouraging and supportive. After explaining, return to main conversation.
                """,
            }
        ],
        functions=[],  # No functions - just informational node that flows back to main conversation
    )


def age_ineligible_node(age: int, reason: str) -> NodeConfig:
    """For users > 42 years old - inform about ineligibility"""
    return NodeConfig(
        name="age_ineligible",
        role_messages=[
            {
                "role": "system",
                "content": identity + "\n\n" + conversation_style,
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": f"""
                The user is {age} years old, which exceeds the UPSC age limit.
                Politely inform them:

                "en": "I'm sorry, but you're not eligible to sit in the UPSC exam as the age limit has been exceeded. However, if you're interested in other competitive exams or government services, I can help guide you to alternative options."

                "hi": "मुझे sorry है, but UPSC exam के लिए age limit exceed हो गई है इसलिए आप eligible नहीं हैं। लेकिन अगर आप other competitive exams या government services में interested हैं, तो मैं आपको alternative options में guide कर सकती हूँ।"

                Be empathetic and helpful. Offer alternatives if appropriate.
                After this, you can either continue conversation or offer handover.
                """,
            }
        ],
        functions=[],
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

def get_initial_node() -> NodeConfig:
    """
    Entry point for the flow
    Returns the initial node to start the conversation
    """
    return greeting_node()
