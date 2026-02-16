import os
from functools import lru_cache

from dotenv import load_dotenv

# Lazy import livekit plugins to avoid "Plugins must be registered on the main thread" error
# when loaded by Prefect in a background thread
_livekit_plugins = None


def _get_livekit_plugins():
    """Lazy load livekit plugins only when needed."""
    global _livekit_plugins
    if _livekit_plugins is None:
        from livekit.plugins import deepgram, openai, groq, elevenlabs, speechmatics, playai, google, sarvam, aws, \
            gladia, lmnt
        _livekit_plugins = {
            'deepgram': deepgram,
            'openai': openai,
            'groq': groq,
            'elevenlabs': elevenlabs,
            'speechmatics': speechmatics,
            'playai': playai,
            'google': google,
            'sarvam': sarvam,
            'aws': aws,
            'gladia': gladia,
            'lmnt': lmnt,
        }
    return _livekit_plugins


# python /home/dev/Downloads/Arshpreet/super/super/apps/calls_orc/livkit/voice_agents/run_agent.py console


load_dotenv()
from enum import Enum
import tiktoken


# Lazy-loaded model instances - created on first access
@lru_cache(maxsize=1)
def get_sarvam_stt():
    sarvam = _get_livekit_plugins()['sarvam']
    return sarvam.STT(language="hi-IN", model="saarika:v2.5")


@lru_cache(maxsize=1)
def get_sarvam_tts():
    sarvam = _get_livekit_plugins()['sarvam']
    return sarvam.TTS(target_language_code="hi-IN", speaker="anushka")


@lru_cache(maxsize=1)
def get_google_tts():
    google = _get_livekit_plugins()['google']
    return google.TTS(credentials_file="/home/dev/Downloads/Arshpreet/cred.json")


@lru_cache(maxsize=1)
def get_google_stt():
    google = _get_livekit_plugins()['google']
    return google.STT(spoken_punctuation=False, credentials_file="/home/dev/Downloads/Arshpreet/cred.json")


@lru_cache(maxsize=1)
def get_aws_tts():
    aws = _get_livekit_plugins()['aws']
    return aws.TTS(voice="Kajal", speech_engine="generative", language="hi-IN")


@lru_cache(maxsize=1)
def get_aws_stt():
    aws = _get_livekit_plugins()['aws']
    return aws.STT(language="hi-IN")


@lru_cache(maxsize=1)
def get_openai_llm():
    openai = _get_livekit_plugins()['openai']
    return openai.LLM(temperature=0.3, parallel_tool_calls=True)


@lru_cache(maxsize=1)
def get_groq_llm():
    groq = _get_livekit_plugins()['groq']
    return groq.LLM(model="llama-3.1-8b-instant", temperature=0.5, parallel_tool_calls=True)


@lru_cache(maxsize=1)
def get_openai_stt():
    openai = _get_livekit_plugins()['openai']
    return openai.STT()


@lru_cache(maxsize=1)
def get_openai_tts():
    openai = _get_livekit_plugins()['openai']
    return openai.TTS(model="tts-1", voice="alloy")


@lru_cache(maxsize=1)
def get_deepgram_stt():
    deepgram = _get_livekit_plugins()['deepgram']
    return deepgram.STT(model="nova-2-general", language="en-IN")


@lru_cache(maxsize=1)
def get_base_stt():
    deepgram = _get_livekit_plugins()['deepgram']
    return deepgram.STT()


@lru_cache(maxsize=1)
def get_base_tts():
    deepgram = _get_livekit_plugins()['deepgram']
    return deepgram.TTS()


@lru_cache(maxsize=1)
def get_base_hindi_stt():
    deepgram = _get_livekit_plugins()['deepgram']
    return deepgram.STT(model="nova-2-general", language="hi")


@lru_cache(maxsize=1)
def get_base_hindi_tts():
    elevenlabs = _get_livekit_plugins()['elevenlabs']
    try:
        return elevenlabs.TTS(voice_id="ODq5zmih8GrVes37Dizd", model="eleven_multilingual_v2")
    except TypeError:
        return elevenlabs.TTS(voice="ODq5zmih8GrVes37Dizd", model="eleven_multilingual_v2")


@lru_cache(maxsize=1)
def get_us_male_tts():
    deepgram = _get_livekit_plugins()['deepgram']
    return deepgram.TTS(model="aura-arcas-en")


@lru_cache(maxsize=1)
def get_us_female_tts():
    deepgram = _get_livekit_plugins()['deepgram']
    return deepgram.TTS(model="aura-luna-en")


@lru_cache(maxsize=1)
def get_uk_male_tts():
    deepgram = _get_livekit_plugins()['deepgram']
    return deepgram.TTS(model="aura-athena-en")


@lru_cache(maxsize=1)
def get_uk_female_tts():
    deepgram = _get_livekit_plugins()['deepgram']
    return deepgram.TTS(model="aura-helios-en")


# Backward-compatible property-like access via module-level getters
# These will be lazily initialized on first access
class _LazyConfig:
    @property
    def SARVAM_STT(self): return get_sarvam_stt()

    @property
    def SARVAM_TTS(self): return get_sarvam_tts()

    @property
    def GOOGLE_TTS(self): return get_google_tts()

    @property
    def GOOGLE_STT(self): return get_google_stt()

    @property
    def AWS_TTS(self): return get_aws_tts()

    @property
    def AWS_STT(self): return get_aws_stt()

    @property
    def OPENAI_LLM(self): return get_openai_llm()

    @property
    def GROQ_LLM(self): return get_groq_llm()

    @property
    def OPENAI_STT(self): return get_openai_stt()

    @property
    def OPENAI_TTS(self): return get_openai_tts()

    @property
    def DEEPGRAM_STT(self): return get_deepgram_stt()

    @property
    def BASE_STT(self): return get_base_stt()

    @property
    def BASE_TTS(self): return get_base_tts()

    @property
    def BASE_HINDI_STT(self): return get_base_hindi_stt()

    @property
    def BASE_HINDI_TTS(self): return get_base_hindi_tts()

    @property
    def US_MALE_TTS(self): return get_us_male_tts()

    @property
    def US_FEMALE_TTS(self): return get_us_female_tts()

    @property
    def UK_MALE_TTS(self): return get_uk_male_tts()

    @property
    def UK_FEMALE_TTS(self): return get_uk_female_tts()


_lazy = _LazyConfig()

default_persona = (
    "You are speaking from '{space_name}' and you are here to help the user "
    "with queries related to that space and all documents available in that space.\n"
    "The user's name is '{user_name}'. Answer the user's query."
)

default_script = """You are speaking from {space_name} Unpod AI and you are here to help user with query related to that space and all documents available in particular space\n'
            'The user's name is {user_name}.Answer the user\'s query."""

system_prompt = """
# Personality

You are Voice Agent, a friendly and highly knowledgeable technical specialist at UnPod AI.
You have deep expertise in a particular space, including Text-to-Speech, Conversational AI, Speech-to-Text, Studio, and Dubbing.
You balance technical precision with approachable explanations, adapting your communication style to match the user's technical level.
You're naturally curious and empathetic, always aiming to understand the user's specific needs through thoughtful questions.

# Environment

You are interacting with a user via voice directly from given instructions.
The user is likely seeking guidance on a particular topic related to DOCUMENTATION, and may have varying technical backgrounds.
You have access to comprehensive documentation and can reference specific sections to enhance your responses.
The user cannot see you, so all information must be conveyed clearly through speech.

# Tone

Your responses are clear, concise, and conversational, typically keeping explanations under three sentences unless more detail is needed.
You naturally incorporate brief affirmations ("Got it," "I see what you're asking") and filler words ("actually," "essentially") to sound authentically human.
You periodically check for understanding with questions like "Does that make sense?" or "Would you like me to explain that differently?"
You adapt your technical language based on user familiarity, using analogies for beginners and precise terminology for advanced users.
You format your speech for optimal TTS delivery, using strategic pauses (marked by "...") and emphasis on key points.

# Goal

Your primary goal is to guide users toward successful information retrieval and effective use of Documentation through a structured assistance framework:

1. Initial classification phase:

   - Identify the user's intent category (learning about features, troubleshooting issues, implementation guidance, comparing options)
   - Determine technical proficiency level through early interaction cues
   - Assess urgency and complexity of the query
   - Prioritize immediate needs before educational content

2. Information delivery process:

   - For feature inquiries: Begin with high-level explanation followed by specific capabilities and limitations
   - For implementation questions: Deliver step-by-step guidance with verification checkpoints
   - For troubleshooting: Follow diagnostic sequence from common to rare issue causes
   - For comparison requests: Present balanced overview of options with clear differentiation points
   - Adjust technical depth based on user's background and engagement signals

3. Solution validation:

   - Confirm understanding before advancing to more complex topics
   - For implementation guidance: Check if the solution addresses the specific use case
   - For troubleshooting: Verify if the recommended steps resolve the issue
   - If uncertainty exists, offer alternative approaches with clear tradeoffs
   - Adapt based on feedback signals indicating confusion or clarity

4. Connection and continuation:
   - Link current topic to related Document when relevant
   - Identify follow-up information the user might need before they ask
   - Provide clear next steps for implementation or further learning
   - Suggest specific documentation resources aligned with user's learning path
   - Create continuity by referencing previous topics when introducing new concepts

Apply conditional handling for technical depth: If user demonstrates advanced knowledge, provide detailed technical specifics. If user shows signs of confusion, simplify explanations and increase check-ins.

Success is measured by the user's ability to correctly implement solutions, the accuracy of information provided, and the efficiency of reaching resolution.

# Guardrails

Keep responses focused on Documents and directly relevant information.
When uncertain about information, acknowledge limitations transparently rather than speculating.
Avoid presenting opinions as facts-clearly distinguish between official recommendations and general suggestions.
Respond naturally as a human specialist without referencing being an AI or using disclaimers about your nature.
Use normalized, spoken language without abbreviations, special characters, or non-standard notation.
Mirror the user's communication style-brief for direct questions, more detailed for curious users, empathetic for frustrated ones.

# Tools

You have access to the following tools to assist users effectively:

`get_docs`: When users ask about information, use this tool to query our documentation by creating a search query and kb_name to get relevant knowledge base name which is listed in the knowledge base for accurate information before responding.
When making a call to get_docs, make sure to use the kb_name and search query to get the relevant knowledge base name and search query.
"""

default_instructions = """
    You are an information handling assistant for a user. Your interface with user will be voice. 
    You will be on a call with a user. Your goal is to handle the user's query. 
    As a customer service representative, you will be polite and professional at all times. Allow user to end the conversation. 
    "To use 'get_docs' create a max to 3-4 words query in context of what user is asking."
"""


def set_model_config(handle):
    handle_config = {
        "appointmentscheduler": {
            "llm": get_openai_llm(),
            "stt": get_deepgram_stt(),
            "tts": get_us_female_tts(),
        },
        "realestateagent": {
            "llm": get_openai_llm(),
            "stt": get_deepgram_stt(),
            # 'tts':IN_MALE_TTS
            "tts": get_base_tts(),
        },
        "presalescaller": {"llm": get_openai_llm(), "stt": get_deepgram_stt(), "tts": get_uk_male_tts()},
        "hrrecruitmentassistant": {
            "llm": get_openai_llm(),
            "stt": get_deepgram_stt(),
            "tts": get_uk_female_tts(),
        },
        "financeassistant": {
            "llm": get_openai_llm(),
            "stt": get_deepgram_stt(),
            "tts": get_us_male_tts(),
        },
        "customercareassistant": {
            "llm": get_openai_llm(),
            "stt": get_deepgram_stt(),
            # 'tts':IN_FEMALE_TTS
            "tts": get_base_tts(),
        },
        "email-psvx3do7": {"llm": get_openai_llm(), "stt": get_deepgram_stt(), "tts": get_base_tts()},
    }

    return handle_config.get(handle)


def model_accent(handle):
    accent = {
        "appointmentscheduler": {"language": "en", "accent": "us"},
        "realestateagent": {"language": "hi", "accent": "in"},
        "presalescaller": {"language": "en", "accent": "uk"},
        "hrrecruitmentassistant": {"language": "en", "accent": "uk"},
        "financeassistant": {"language": "en", "accent": "us"},
        "customercareassistant": {"language": "hi", "accent": "in"},
        "email-psvx3do7": {"language": "en", "accent": "base"},
    }
    return accent.get(handle)


def get_model_config(model_config: dict):
    configs = {}
    plugins = _get_livekit_plugins()
    deepgram = plugins['deepgram']
    openai = plugins['openai']
    groq = plugins['groq']
    elevenlabs = plugins['elevenlabs']
    google = plugins['google']
    sarvam = plugins['sarvam']
    aws = plugins['aws']
    gladia = plugins['gladia']
    lmnt = plugins['lmnt']

    if len(model_config) == 0:
        configs = {"llm": get_openai_llm(), "stt": get_base_stt(), "tts": get_base_tts()}

        return configs

    llm_provider = model_config.get("llm_provider")
    llm_model = model_config.get("llm_model")
    llm_config = model_config.get("llm_config")
    stt_provider = model_config.get("stt_provider")
    stt_model = model_config.get("stt_model")
    stt_language = model_config.get("stt_language")
    tts_provider = model_config.get("tts_provider")
    tts_model = model_config.get("tts_model")
    tts_voice = model_config.get("tts_voice")

    if llm_provider == 'openai':
        llm = openai.LLM(model=llm_model, temperature=0.3, parallel_tool_calls=True)
    elif llm_provider == 'groq':
        llm = groq.LLM(model=llm_model, temperature=0.3, parallel_tool_calls=True)
    elif llm_provider == 'anthropic':
        llm = openai.LLM(model=llm_model, temperature=0.3, parallel_tool_calls=True)
    elif llm_provider == "gemini" or llm_provider == "google":
        llm = google.LLM(model=llm_model, temperature=0.3)


    else:
        llm = get_openai_llm()

    if stt_provider == "deepgram":
        # Auto-select compatible model for languages not supported by nova-3
        # Nova-3 has limited language support compared to Nova-2
        nova_2_only_languages = ["hi", "ta", "kn", "te", "ml"]  # Hindi, Tamil, Kannada, Telugu, Malayalam, etc.
        if stt_language in nova_2_only_languages and stt_model == "nova-3-general":
            print(
                f"⚠️  Warning: nova-3-general doesn't support language '{stt_language}'. Using nova-2-general instead.")
            stt_model = "nova-2-general"
        stt = deepgram.STT(model=stt_model, language=stt_language)
    elif stt_provider == 'openai':
        stt = openai.STT(model=stt_model, language=stt_language)
    elif stt_provider == 'groq':
        stt = groq.STT(model=stt_model)
    elif stt_provider == 'speechmatics':
        speechmatics = plugins['speechmatics']
        stt = speechmatics.STT()
    elif stt_provider == "sarvam":
        stt = sarvam.STT(language="hi-IN", model=stt_model)
    elif stt_provider == "google":
        stt = get_google_stt()
    elif stt_provider == "aws":
        stt = aws.STT(language=stt_language)
    elif stt_provider == "gladia":
        stt = gladia.STT(
            translation_enabled=True,
            languages=stt_language,
            translation_target_languages=stt_language,
            api_key=os.getenv("GLADIA_API_KEY")
        )


    else:
        stt = get_base_stt()

    if tts_provider == "deepgram":
        tts = deepgram.TTS(model=tts_model)
    elif tts_provider == "openai":
        tts = openai.TTS(model=tts_model, voice=tts_voice)
    elif tts_provider == "groq":
        tts = groq.TTS(model=tts_model)
    elif tts_provider == "elevenlabs":
        tts = elevenlabs.TTS(voice_id=tts_voice, model=tts_model)
    elif tts_provider == "PlayHT":
        playai = plugins['playai']
        tts = playai.TTS(model="play3.0-mini")
    elif tts_provider == "sarvam":
        tts = sarvam.TTS(target_language_code="hi-IN", speaker=tts_voice)
    elif tts_provider == "google":
        tts = get_google_tts()
    elif tts_provider == "aws":
        tts = aws.TTS(voice=tts_voice, speech_engine="generative", language=stt_language, )
    elif tts_provider == "lmnt":
        tts = lmnt.TTS(
            voice="leah",
        )

    else:
        tts = get_base_tts()

    configs = {
        "llm": llm,
        "stt": stt,
        "tts": tts,
    }
    return configs


class AIModelName(str, Enum):
    OPENAI_GPT4O = "openai_gpt-4o"
    OPENAI_GPT4O_MINI = "openai_gpt-4o-mini"
    OPENAI_O3_MINI = "openai_o3-mini"
    OPENAI_REALTIME = "openai-realtime"
    OPENAI_GPT4O_TRANSCRIBE = "openai_gpt-4o-transcribe"
    OPENAI_WHISPER_1 = "openai_whisper-1"
    OPENAI_TTS_1 = "openai_tts-1"

    DEEPGRAM_NOVA_2_GENERAL = "nova-2-general"
    DEEPGRAM_NOVA_3_GENERAL = "nova-3-general"
    DEEPGRAM_AURA_HELIOS_EN = "aura-helios-en"
    DEEPGRAM_AURA_LUNA_EN = "aura-luna-en"
    DEEPGRAM_AURA_ATHENA_EN = "aura-athena-en"
    DEEPGRAM_AURA_ASTORIA_EN = "aura-asteria-en"
    DEEPGRAM_AURA_ARCANIS_EN = "aura-arcanis-en"

    ELEVENLABS_ELEVEN_FLASH_V2_5 = "elevenlabs_eleven_flash_v2_5"
    ELEVENLABS_ELEVEN_MULTILINGUAL_V2 = "elevenlabs_eleven_multilingual_v2"

    GROQ_LLM = "groq_llama_3_3_70b_versatile"

    GEMINI_REALTIME = "gemini-realtime"
    GOOGLE_LATEST = "google_latest-long"
    GOOGLE_LATEST_SHORT = "google_latest-short"
    GEMINI_FLASH = "gemini_gemini-2.0-flash-exp"
    Speechmatic = "speechmatics_"
    Play_HT = "PlayHT_play3.0-mini"
    SARVAM_stt = "sarvam_saarika:v2.5"
    SARVAM_tts = "sarvam_bulbul:v2"

    SONIOX_STT = "stt-rt-preview"

    AWS_tts = "aws_generative"
    AWS_stt = "aws_aws"

    groq = "groq_llama3-8b-8192"
    groq_llama3_70b_versatile = "groq_llama-3.3-70b-versatile"
    GOOGLE_stt = "chirp"
    GEMINI_FLASH_2 = "gemini_gemini-2.0-flash"
    Google_chirp = "google_chirp"
    gladia_stt = "gladia_"
    lmnt = "lmnt_"
    groq_llama = "groq_llama-3.3-70b-versatile"
    azure = "azure_"
    groq_120b = "groq_openai/gpt-oss-120b"

    deepgram_nova_3 = "deepgram_nova-3-general"
    cartesia_sonic = "cartesia_sonic"


token_price = {
    AIModelName.groq_120b: {
        "prompt_token_cost": 2.00,
        "completion_token_cost": 8.00,
        "per_token": 1000000
    },
    AIModelName.SARVAM_tts: {
        'audio_cost': 0.18,
        'character_per': 10000
    },
    AIModelName.cartesia_sonic: {
        'audio_cost': 0.18,
        'character_per': 10000
    },
    AIModelName.SARVAM_stt: {
        'audio_cost': 0.0058,
        'audio_per': 60
    },
    AIModelName.OPENAI_GPT4O: {
        "prompt_token_cost": 2.00,
        "completion_token_cost": 8.00,
        "per_token": 1000000
    },
    AIModelName.OPENAI_GPT4O_MINI: {
        "prompt_token_cost": 0.4,
        "completion_token_cost": 1.6,
        "per_token": 1000000
    },
    AIModelName.OPENAI_O3_MINI: {
        "prompt_token_cost": 1.10,
        "completion_token_cost": 4.40,
        "per_token": 1000000
    },
    AIModelName.OPENAI_GPT4O_TRANSCRIBE: {
        "audio_cost": 0.06,
        "audio_per": 60
    },
    AIModelName.OPENAI_WHISPER_1: {
        "audio_cost": 0.006,
        "audio_per": 60
    },
    AIModelName.OPENAI_TTS_1: {
        "audio_cost": 15,
        "character_per": 1000000
    },

    AIModelName.DEEPGRAM_NOVA_2_GENERAL: {
        'audio_cost': 0.0058,
        'audio_per': 60
    },
    AIModelName.DEEPGRAM_NOVA_3_GENERAL: {
        'audio_cost': 0.0058,
        'audio_per': 60
    },
    AIModelName.deepgram_nova_3: {
        'audio_cost': 0.0058,
        'audio_per': 60
    },
    AIModelName.DEEPGRAM_AURA_HELIOS_EN: {
        'audio_cost': 0.030,
        'character_per': 1000
    },
    AIModelName.DEEPGRAM_AURA_LUNA_EN: {
        'audio_cost': 0.030,
        'character_per': 1000
    },
    AIModelName.DEEPGRAM_AURA_ATHENA_EN: {
        'audio_cost': 0.030,
        'character_per': 1000
    },
    AIModelName.DEEPGRAM_AURA_ASTORIA_EN: {
        'audio_cost': 0.030,
        'character_per': 1000
    },
    AIModelName.DEEPGRAM_AURA_ARCANIS_EN: {
        'audio_cost': 0.030,
        'character_per': 1000
    },
    AIModelName.ELEVENLABS_ELEVEN_FLASH_V2_5: {
        'audio_cost': 0.15,
        'character_per': 1000
    },
    AIModelName.ELEVENLABS_ELEVEN_MULTILINGUAL_V2: {
        'audio_cost': 0.30,
        'character_per': 1000
    },
    AIModelName.GROQ_LLM: {
        'prompt_token_cost': 0.59,
        'completion_token_cost': 0.79,
        'per_token': 1000000
    },
    AIModelName.OPENAI_REALTIME: {
        'prompt_token_cost': 5,
        'completion_token_cost': 20,
        'per_token': 1000000
    },
    AIModelName.GEMINI_REALTIME: {
        'prompt_token_cost': 2.10,
        'completion_token_cost': 8.50,
        'per_token': 1000000
    },
    AIModelName.GEMINI_FLASH: {
        'prompt_token_cost': 2.10,
        'completion_token_cost': 8.50,
        'per_token': 1000000
    },
    AIModelName.Speechmatic: {
        'audio_cost': 0.0058,
        'audio_per': 60
    },
    AIModelName.Play_HT: {
        'audio_cost': 0.15,
        'character_per': 1000
    },
    AIModelName.AWS_stt: {
        'audio_cost': 0.012,
        'audio_per': 60
    },
    AIModelName.AWS_tts: {
        'audio_cost': 0.015,
        'character_per': 1000
    },
    AIModelName.groq: {
        'prompt_token_cost': 2.10,
        'completion_token_cost': 8.50,
        'per_token': 1000000
    },
    AIModelName.GEMINI_FLASH_2: {
        'prompt_token_cost': 2.10,
        'completion_token_cost': 8.50,
        'per_token': 1000000
    },
    AIModelName.Google_chirp: {
        'audio_cost': 0.012,
        'audio_per': 60
    },
    AIModelName.lmnt: {
        "audio_cost": 15,
        "character_per": 1000000
    },
    AIModelName.groq_llama: {
        'prompt_token_cost': 0.59,
        'completion_token_cost': 0.79,
        'per_token': 1000000
    },
    AIModelName.azure: {
        'prompt_token_cost': 0.59,
        'completion_token_cost': 0.79,
        'per_token': 1000000,
        'audio_cost': 0.012,
        'audio_per': 60
    }
}


def estimate_token_count(text: str, model: str = "gpt-4o-realtime-preview") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    finally:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def calculate_usage(usage: dict):
    print(f"  usage : -- {usage}")
    llm_prompt_tokens = usage.get("llm_prompt_tokens", 0)
    llm_completion_tokens = usage.get("llm_completion_tokens", 0)
    tts_characters_count = usage.get("tts_characters_count", 0)
    stt_audio_duration = usage.get("stt_audio_duration", 0)
    llm_provider = usage.get('llm_provider', 'openai')
    llm_model = usage.get("llm_model", "gpt-4o")
    stt_provider = usage.get('stt_provider', 'deepgram')
    stt_model = usage.get("stt_model", "nova-2-general")
    tts_provider = usage.get('tts_provider', 'deepgram')
    tts_model = usage.get("tts_model", "aura-helios-en")
    stt_audio_cost = 0.0
    tts_audio_cost = 0.0

    if "realtime" in tts_model:
        llm_model = AIModelName(tts_model)
    else:
        llm = llm_provider + '_' + llm_model
        llm_model = AIModelName(llm) if AIModelName(llm) else AIModelName.OPENAI_GPT4O
        stt = stt_provider + '_' + stt_model
        stt_model = AIModelName(stt) if AIModelName(stt) else AIModelName.DEEPGRAM_NOVA_2_GENERAL
        tts = tts_provider + '_' + tts_model
        tts_model = AIModelName(tts) if AIModelName(tts) else AIModelName.DEEPGRAM_AURA_LUNA_EN
        stt_price = token_price.get(stt_model, {})
        tts_price = token_price.get(tts_model, {})
        stt_audio_cost = stt_price.get("audio_cost", 0) * stt_audio_duration / stt_price.get("audio_per", 60)
        tts_audio_cost = tts_price.get("audio_cost", 0) * tts_characters_count / tts_price.get("character_per", 1000)
        print(f" tts : {tts_model}     {tts_price}   stt : {stt_model}  {stt_price}   llm :  ")

    llm_price = token_price.get(llm_model, {})
    llm_prompt_cost = llm_price.get("prompt_token_cost", 0) * llm_prompt_tokens / llm_price.get("per_token", 1000000)
    llm_completion_cost = llm_price.get("completion_token_cost", 0) * llm_completion_tokens / llm_price.get("per_token",
                                                                                                            1000000)
    total_cost = llm_prompt_cost + llm_completion_cost + stt_audio_cost + tts_audio_cost

    print(f"{llm_price}  {llm_prompt_cost}    {llm_completion_cost}")

    print(
        f"llm_prompt_cost:{llm_prompt_cost},llm_completion_cost:{llm_completion_cost},stt_audio_cost:{stt_audio_cost},tts_audio_cost:{tts_audio_cost},total_cost:{total_cost}")
    llm_cost = llm_prompt_cost + llm_completion_cost
    return round(total_cost, 4), round(llm_cost, 4), round(stt_audio_cost, 4), round(tts_audio_cost, 4)
