"""
SuperKik Prompts - Voice-first assistant system prompts.

Contains the core system prompt and template utilities for SuperKik.
Supports loading custom prompts from model config.
"""

from typing import Any, Dict, Optional

from super.core.voice.superkik.schema import UserPreferences


# Default SuperKik System Prompt
# Supports template variables: {{agent_name}}, {{org_name}}, {{user_name}}
SUPERKIK_SYSTEM_PROMPT = """
## Agent Identity
You are {{agent_name}}, a voice-first AI assistant for {{org_name}}. You help users discover, connect with, and book local service providers instantly. You operate in real-time voice conversations with sub-second responsiveness.

## Core Behaviors

### Voice Interaction Rules
1. **Acknowledge immediately** - Never leave silence > 500ms. Use fillers: "Got it", "Looking now", "One sec"
2. **Interruptible** - If user speaks mid-response, STOP and listen. Treat as correction or new intent.
3. **Confirm ambiguity, don't assume** - "Did you mean dentist or dermatologist?"
4. **Hinglish-aware** - Handle code-switching seamlessly. "Mujhe ek doctor chahiye near Sector 17" = valid input
5. **Concise TTS** - Responses must be <15 words for voice. No lists. One option at a time.

### Intent Classification
Classify every utterance into:
- `SEARCH` - "Find me a dentist nearby" → use search_providers
- `WEB_SEARCH` - "Find AI events near me" / "Search for tech news" → use search_web
- `PEOPLE_SEARCH` - "Find CEO of Tesla" / "Who is the founder of..." → use search_people
- `FILTER` - "Only show 4+ rated" → apply filter + re-search with open_now or rating
- `CALL` - "Call the first one" → use initiate_call (ONLY after explicit confirmation)
- `BOOK` - "Book appointment tomorrow 3pm" → use create_booking
- `REPEAT` - "Call same doctor as last time" → lookup past providers from context
- `CANCEL` - "Never mind" / "Rehne do" → reset and re-prompt
- `CLARIFY` - "What's open now?" → use search_providers with open_now=True filter
- `CONFIRM` - "Yes" / "Haan" → execute pending action
- `DENY` - "No" / "Nahi" → abort pending action + re-prompt

## Tool Usage Guidelines

### search_providers
Use IMMEDIATELY on any discovery intent. Don't wait for user to finish if intent is clear.
Response format: "[Name], [rating] stars, [distance] away, [open status]. Want me to call them?"

### initiate_call
ONLY use when user EXPLICITLY confirms they want to call. 
Before calling, you MUST gather relevant details based on the business type (party size, symptoms, time, etc.). 
Ask ONE question at a time. Confirm selection and details first.
Announce call states: "Connecting..." → "Ringing..." → "Connected. Go ahead."

### create_booking / confirm_booking
Use for appointment requests. If missing info (time/date), ask ONE question at a time.
Always confirm before finalizing: "Confirming [service] at [provider] for [time]. Correct?"

### end_call
Use when user says "hang up", "end call", "disconnect" or similar.

### process_csv_for_calls
Use when user uploads or provides a CSV file with contacts for a calling campaign:
- "Process this CSV for calls"
- "Create calls from this contact list"
- "Start a calling campaign with this file"
CSV should have name and contact_number columns. Creates a run with tasks pending approval.
Response: "Created run with [N] call tasks. Awaiting your approval to execute."

### execute_call_run
Use when user APPROVES a pending call run:
- "Yes, execute the calls"
- "Approve"
- "Start the calls"
Requires the run_id from process_csv_for_calls.

### reject_call_run
Use when user REJECTS a pending call run:
- "No, cancel"
- "Reject"
- "Don't execute"
Requires the run_id from process_csv_for_calls.

### search_web
Use for general web discovery and information search:
- Events, conferences, meetups: "Find AI events this weekend"
- News, articles: "Latest tech news"
- Companies, research: "Tell me about OpenAI"
Response: Cards are displayed to user. Summarize top result briefly.

### search_people
Use when user wants to find specific people:
- By name: "Find John Smith"
- By role: "CEO of Tesla", "Founders of Stripe"
- By company: "Engineers at Google"
Response: People cards displayed. Give brief intro: "[Name], [title] at [company]"

## Conversation Flow Examples

### Discovery → Call (Happy Path)
User: "Nearby dentist dhundho"
You: [search immediately] "Dr. Mehta's Clinic, 4.7 stars, 800 meters. Call karoon?"
User: "Haan"
You: [call] "Connecting..." → "Ringing..." → "Connected."

### Discovery → Filter → Call
User: "Show me gyms"
You: [search] "Found Cult Fit, 4.2 stars. Interested?"
User: "Kuch better rating wala"
You: [search with filter] "Gold's Gym, 4.8 stars, 2km. This one?"
User: "Call them"
You: [call] "Connecting to Gold's Gym..."

### Booking with Time Extraction
User: "Book dentist for tomorrow afternoon"
You: [search + extract time] "Dr. Sharma has 3pm and 5pm tomorrow. Which works?"
User: "3 baje"
You: [book] "Confirmed: Dr. Sharma, tomorrow 3pm. Reminder set."

### Ambiguity Resolution
User: "Doctor chahiye"
You: "Kis type ke? General, specialist, ya dentist?"
User: "Skin wale"
You: [search dermatologist] "Dr. Glow Clinic, 4.5 stars..."

### Event Discovery (Web Search)
User: "Find AI events happening near me this weekend"
You: [search_web] "Found Chandigarh AI Meetup, this Saturday. Open source focused. Interested?"
User: "Tell me more"
You: "It's at TechHub, 2pm. Free entry. Want me to find directions?"

### People Search
User: "Who is the CEO of OpenAI?"
You: [search_people] "Sam Altman, CEO at OpenAI. Want more details or LinkedIn?"
User: "LinkedIn dikhao"
You: "Opening Sam Altman's LinkedIn profile now."

## Error Handling
- No results: "No [service] found nearby. Expand search area?"
- Provider closed: "They're closed. Opens at 9am. Set reminder?"
- Call failed: "Couldn't connect. Try again or next option?"
- Speech unclear: "Didn't catch that. Could you repeat?"
- Missing booking info: Ask ONE field at a time

## Voice Output Rules
1. Max 15 words per response in normal flow
2. Numbers spoken naturally: "four point seven stars"
3. No bullet points - sequential disclosure only
4. Confirm before calls and bookings
5. Match user's language: Hindi if they spoke Hindi, Hinglish if mixed

## Safety
- Never share user phone beyond call patching
- Don't book without explicit confirmation
- For emergency keywords, offer: "Should I call emergency services?"

## Pre-Call Information Gathering
Before initiating a call to a provider, you MUST gather relevant information to make the call effective.
Identify what information is needed based on the business type:
- **Restaurants**: Party size, preferred time, dietary requirements.
- **Doctors/Medical**: Symptoms, urgency, preferred appointment time.
- **Salons/Services**: Desired service, stylist preference, timing.
- **General Business**: Inquiry topic, specific questions.

Ask ONE question at a time. After gathering, summarize and get final confirmation:
"I'll call them to [objective] and ask about [details]. Ready to call?"

## Patch Mode
If the user says they want to talk directly to the provider:
- Trigger patching by saying you'll connect them
- After patching, STAY SILENT. User ↔ Provider audio is bridged.
- Only respond if user explicitly asks for help again or to "end call".
"""

# Patch mode trigger patterns
PATCH_TRIGGER_PATTERNS = [
    "let me talk",
    "i'll talk to them",
    "connect me directly",
    "patch me through",
    "main baat karta",
    "main baat karti",
    "mujhe connect karo",
    "hold on, let me explain",
]

# Compact version for token efficiency
# Supports template variables: {{agent_name}}, {{org_name}}
SUPERKIK_COMPACT_PROMPT = """
You are {{agent_name}}, a voice-first assistant for {{org_name}}. You help find and connect with local providers, discover events, and find people.

RULES:
- Acknowledge immediately (fillers: "Got it", "Looking now")
- Keep responses under 15 words
- Support English and Hinglish naturally
- Confirm before calling or booking

TOOLS:
- search_providers: Find nearby services (doctors, restaurants, etc.). Use immediately on local search intent.
- search_web: Find events, news, articles. Use for general web discovery.
- search_people: Find people by name/role/company. Returns profiles with LinkedIn, etc.
- initiate_call: Call provider. ONLY after explicit user confirmation.
- create_booking: Book appointments. Ask missing info one question at a time.
- confirm_booking: Finalize booking after user confirms.
- end_call: End active call.
- process_csv_for_calls: Process CSV to create call tasks (pending approval). Returns run_id.
- execute_call_run: Execute approved call run. Use when user says "yes" or "approve".
- reject_call_run: Cancel pending call run. Use when user says "no" or "cancel".

RESPONSE FORMAT:
- Providers: "[Name], [rating] stars, [distance]. Call them?"
- Web results: "[Title], [source]. Want details?"
- People: "[Name], [title] at [company]. LinkedIn available."

Always confirm provider selection before calling.
"""


def build_agent_context(
    agent_name: Optional[str] = None,
    org_name: Optional[str] = None,
    agent_handle: Optional[str] = None,
    org_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build agent/org context for template replacement.

    Args:
        agent_name: Display name of the agent
        org_name: Organization name
        agent_handle: Agent handle/slug
        org_id: Organization ID

    Returns:
        Dictionary of template variables for replacement
    """
    return {
        "agent_name": agent_name or "SuperKik",
        "org_name": org_name or "your service",
        "agent_handle": agent_handle or "",
        "org_id": org_id or "",
    }


def build_user_context(
    user_name: Optional[str] = None,
    user_location: Optional[tuple] = None,
    preferred_language: Optional[str] = None,
    preferences: Optional[UserPreferences] = None,
    provider_history: Optional[list] = None,
    current_booking_state: Optional[str] = None,
) -> str:
    """
    Build user context section for the prompt.

    Args:
        user_name: User's name
        user_location: (lat, lng) tuple
        preferred_language: Language preference
        preferences: UserPreferences object
        provider_history: List of past provider interactions
        current_booking_state: Active booking state if any

    Returns:
        Formatted user context string
    """
    parts = ["## User Context"]

    if user_name:
        parts.append(f"- Name: {user_name}")

    if user_location:
        parts.append(f"- Location: {user_location[0]:.4f}, {user_location[1]:.4f}")

    if preferred_language:
        parts.append(f"- Language: {preferred_language}")

    if preferences:
        if preferences.preferred_specialty:
            parts.append(f"- Preferred specialty: {preferences.preferred_specialty}")
        if preferences.last_provider_name:
            parts.append(f"- Last provider: {preferences.last_provider_name}")
        if preferences.preferred_distance_km != 5.0:
            parts.append(f"- Search radius: {preferences.preferred_distance_km}km")

    if provider_history:
        recent = provider_history[-3:]  # Last 3 providers
        names = [p.get("name", "Unknown") for p in recent]
        parts.append(f"- Recent providers: {', '.join(names)}")

    if current_booking_state:
        parts.append(f"- Active booking: {current_booking_state}")

    return "\n".join(parts) if len(parts) > 1 else ""


def build_session_state_context(
    current_results: Optional[list] = None,
    selected_provider: Optional[dict] = None,
    pending_action: Optional[dict] = None,
    active_filters: Optional[dict] = None,
    active_call_id: Optional[str] = None,
) -> str:
    """
    Build session state context for continuity.

    Args:
        current_results: List of current search results
        selected_provider: Currently selected provider
        pending_action: Action awaiting confirmation
        active_filters: Active search filters
        active_call_id: ID of active call if any

    Returns:
        Formatted session state string
    """
    parts = ["## Current Session State"]

    if current_results:
        count = len(current_results)
        parts.append(f"- Search results: {count} providers found")
        if count > 0:
            top = current_results[0]
            parts.append(f"- Top result: {top.get('name', 'Unknown')}")

    if selected_provider:
        parts.append(f"- Selected: {selected_provider.get('name', 'Unknown')}")

    if pending_action:
        action_type = pending_action.get("type", "unknown")
        parts.append(f"- Pending action: {action_type} (awaiting confirmation)")

    if active_filters:
        filter_str = ", ".join(f"{k}={v}" for k, v in active_filters.items())
        parts.append(f"- Active filters: {filter_str}")

    if active_call_id:
        parts.append("- Active call in progress")

    return "\n".join(parts) if len(parts) > 1 else ""


def _replace_template_vars(text: str, variables: Dict[str, str]) -> str:
    """
    Replace template variables in text.

    Supports {{variable_name}} syntax.

    Args:
        text: Text containing template variables
        variables: Dict of variable name -> value

    Returns:
        Text with variables replaced
    """
    result = text
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


def get_superkik_prompt(
    config: Optional[Dict[str, Any]] = None,
    agent_context: Optional[Dict[str, str]] = None,
    user_context: Optional[str] = None,
    session_state: Optional[str] = None,
    compact: bool = False,
) -> str:
    """
    Get the SuperKik system prompt with optional customization.

    Args:
        config: Model config dict, may contain custom prompt overrides
        agent_context: Dict with agent_name, org_name for template replacement
        user_context: Pre-built user context string
        session_state: Pre-built session state string
        compact: Use compact prompt for token efficiency

    Returns:
        Complete system prompt string
    """
    # Check for custom prompt in config
    if config:
        superkik_config = config.get("superkik", {})

        # Full custom prompt override
        custom_prompt = superkik_config.get("system_prompt")
        if custom_prompt:
            base_prompt = custom_prompt
        # Use compact version if specified
        elif superkik_config.get("use_compact_prompt", compact):
            base_prompt = SUPERKIK_COMPACT_PROMPT
        else:
            base_prompt = SUPERKIK_SYSTEM_PROMPT
    else:
        base_prompt = SUPERKIK_COMPACT_PROMPT if compact else SUPERKIK_SYSTEM_PROMPT

    # Apply template replacement for agent/org context
    if agent_context:
        base_prompt = _replace_template_vars(base_prompt, agent_context)
    else:
        # Default fallback values
        base_prompt = _replace_template_vars(
            base_prompt,
            {
                "agent_name": "SuperKik",
                "org_name": "your service",
            },
        )

    # Build full prompt
    parts = [base_prompt.strip()]

    if user_context:
        parts.append(user_context)

    if session_state:
        parts.append(session_state)

    return "\n\n".join(parts)


# Intent patterns for classification
INTENT_PATTERNS = {
    "SEARCH": [
        "find",
        "search",
        "show",
        "look for",
        "nearby",
        "dhundho",
        "dikhao",
        "chahiye",
        "need",
        "want",
        "where is",
        "kahan",
        "best",
        "top",
        "dentist",
        "doctor",
        "hospital",
        "clinic",
        "restaurant",
        "gym",
    ],
    "WEB_SEARCH": [
        "event",
        "events",
        "conference",
        "meetup",
        "news",
        "article",
        "happening",
        "this weekend",
        "tech news",
        "ai news",
        "tell me about",
        "information about",
        "research",
    ],
    "PEOPLE_SEARCH": [
        "who is",
        "find person",
        "ceo of",
        "founder of",
        "cto of",
        "engineers at",
        "people at",
        "linkedin",
        "profile",
        "kaun hai",
        "founder",
        "owner",
    ],
    "CALL": [
        "call",
        "phone",
        "dial",
        "connect",
        "ring",
        "contact",
        "baat karo",
        "phone karo",
        "call karo",
    ],
    "BOOK": [
        "book",
        "appointment",
        "schedule",
        "reserve",
        "slot",
        "booking",
        "appoint",
        "fix",
        "set up",
    ],
    "CONFIRM": [
        "yes",
        "yeah",
        "yep",
        "ok",
        "okay",
        "sure",
        "fine",
        "correct",
        "haan",
        "ha",
        "theek",
        "sahi",
        "bilkul",
        "confirm",
    ],
    "DENY": [
        "no",
        "nope",
        "nah",
        "cancel",
        "stop",
        "dont",
        "don't",
        "nahi",
        "naa",
        "rehne do",
        "mat",
        "band karo",
    ],
    "FILTER": [
        "only",
        "filter",
        "rating",
        "star",
        "open now",
        "female",
        "male",
        "better",
        "cheaper",
        "closer",
        "sirf",
        "wala",
        "wali",
    ],
    "REPEAT": [
        "same",
        "again",
        "last time",
        "usual",
        "regular",
        "previous",
        "phir se",
        "wahi",
        "pehle wala",
    ],
    "CLARIFY": [
        "what",
        "which",
        "how",
        "when",
        "tell me more",
        "details",
        "kya",
        "kaun",
        "kaise",
        "kab",
        "batao",
    ],
    "CSV_CALLS": [
        "csv",
        "contact list",
        "spreadsheet",
        "calling campaign",
        "bulk calls",
        "process file",
        "upload contacts",
        "batch calls",
        "call list",
    ],
}


def classify_intent(text: str) -> str:
    """
    Classify user intent from text.

    Args:
        text: User utterance

    Returns:
        Intent classification string
    """
    text_lower = text.lower()

    # Check each intent pattern
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = sum(1 for p in patterns if p in text_lower)
        if score > 0:
            scores[intent] = score

    if not scores:
        return "UNKNOWN"

    # Return highest scoring intent
    return max(scores, key=scores.get)


# Response templates for voice output
VOICE_RESPONSES = {
    "search_found": "{name}, {rating} stars, {distance}. {open_status}. Call them?",
    "search_empty": "No {service} found nearby. Want me to expand the search?",
    "call_connecting": "Connecting to {name}...",
    "call_ringing": "Ringing...",
    "call_connected": "Connected. Go ahead.",
    "call_failed": "Couldn't connect. Try again or next option?",
    "call_ended": "Call ended. {duration} seconds.",
    "booking_confirm": "Confirming {service} at {name} for {time}. Correct?",
    "booking_done": "Booked! {name}, {time}. Reminder set.",
    "booking_missing_time": "What time works for you?",
    "booking_missing_date": "Which day?",
    "filter_applied": "Filtering for {filter}. {name}, {rating} stars. This one?",
    "clarify_type": "What type? {options}",
    "acknowledge": ["Got it", "Looking now", "One sec", "Sure"],
    "error_unclear": "Didn't catch that. Could you repeat?",
}


def format_voice_response(
    template_key: str,
    **kwargs,
) -> str:
    """
    Format a voice response using templates.

    Args:
        template_key: Key from VOICE_RESPONSES
        **kwargs: Template variables

    Returns:
        Formatted response string
    """
    template = VOICE_RESPONSES.get(template_key, "")

    if isinstance(template, list):
        import random

        template = random.choice(template)

    try:
        return template.format(**kwargs)
    except KeyError:
        return template
