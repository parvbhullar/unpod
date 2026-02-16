from enum import Enum


class OPENAI_MODEL(str, Enum):
    GPT_4o = "gpt-4o"
    GPT_4o_MINI = "gpt-4o-mini"
    GPT_4o_REALTIME_PREVIEW = "gpt-4o-realtime-preview-2024-10-01"
    GPT_4o_LATEST = "chatgpt-4o-latest"
    GPT_4_TURBO = "gpt-4-turbo"


class OPENAI_TRANSCRIBER(str, Enum):
    GPT_4o = "gpt-4o-transcribe"
    GPT_4o_MINI = "gpt-4o-mini-transcribe"


class OPENAI_TTS(str, Enum):
    OPENAI = "openai"


class OPENAI_VOICE_ID(str, Enum):
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


class OPENAI_TTS_MODELS(str, Enum):
    TTS_1 = "tts-1"
    TTS_1_HD = "tts-1-hd"
    GPT_4o_MINI = "gpt-4o-mini-tts"


class GOOGLE_TRANSCRIBERS(str, Enum):
    GEMINI_PRO = "gemini-2.5-pro-preview-05-06"
    GEMINI_FLASH = "gemini-2.0-flash-exp"
    GEMINI_1 = "gemini-1.0-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"


class GOOGLE_MODELS(str, Enum):
    GEMINI_REALTIME = "gemini-2.0-flash-realtime-exp"
    GOOGLE_FLASH = "gemini-2.0-flash"


class DEEPGRAM_TRANSCRIBERS(str, Enum):
    NOVA_2 = "nova-2"
    NOVA_3 = "nova-3"
    NOVA_2_GENERAL = "nova-2-general"
    NOVA_3_GENERAL = "nova-3-general"
    BASE = "base"


class DEEPGRAM_VOICE_MODELS(str, Enum):
    AURA = "aura"
    AURA_2 = "aura-2"


class DEEPGRAM_VOICE_ID(str, Enum):
    ASTERIA = "asteria"
    LUNA = "luna"
    STELLA = "stella"
    ATHENA = "athena"
    HERA = "hera"
    ORION = "orion"
    ARACAS = "arcas"
    PERSEUS = "perseus"
    ANGUS = "angus"
    ORPHEUS = "orpheus"
    HELIOS = "helios"
    ZEUS = "zeus"
    THALIA = "thalia"
    ANDROMEDA = "andromeda"
    HELENA = "helena"
    APOLLO = "apollo"
    ARIES = "aries"
    ARCANIS = "arcanis"
    SELENE = "selene"
    AMALTHEA = "amalthea"
    HARMONICA = "harmonica"
    HERMES = "hermes"
    HYPERION = "hyperion"
    IRIS = "iris"
    JANUS = "janus"
    JUNO = "juno"
    JUPITER = "jupiter"
    MARS = "mars"
    ATLAS = "atlas"
    MINERVA = "minerva"
    NEPTUNE = "neptune"
    AURORA = "aurora"
    ODYSSEUS = "odysseus"
    OPHELIA = "ophelia"
    CALISTA = "calista"
    CARA = "cara"
    CORDELIA = "cordelia"
    PANDORA = "pandora"
    DELIA = "delia"
    PHOEBE = "phoebe"
    PLUTO = "pluto"
    DRACO = "draco"
    SATURN = "saturn"
    ELECTRA = "electra"
    VESTA = "vesta"


class GROQ_MODELS(str, Enum):
    LLAMA_VERSATILE = "llama-3.3-70b-versatile"
    LLAMA_REASONING = "llama-3.1-405b-reasoning"
    LLAMA_INSTANT = "llama-3.1-8b-instant"
    COMPOUND = "compound-beta-mini"


class ELVENLABS_MODELS(str, Enum):
    ELEVENLABS = "11labs"


class EVEVENLABS_TTS(str, Enum):
    ELEVEN_MULTILINGUAL_V2 = "eleven_multilingual_v2"
    ELEVEN_TURVO_V2 = "eleven_turbo_v2"
    ELEVEN_FLASH = "eleven_flash_v2_5"
    ELEVEN_MONOLINGUAL = "eleven_monolingual_v1"


class ELEVENLABS_TTS_VOICE(str, Enum):
    BURT = "burt"
    MARISSA = "marissa"
    SARAH = "sarah"
    ANDREA = "andrea"
    PHILLIP = "phillip"
    STEVE = "steve"
    JOSEPH = "joseph"
    MYRA = "myra"
    PAULA = "paula"
    RYAN = "ryan"
    DREW = "drew"
    PAUL = "paul"
    MRB = "mrb"
    MATILDA = "matilda"
    MARK = "mark"


class LLM_PROVIDER(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    GROQ = "groq"
    ANTHROPIC = "anthropic"


class STT_PROVIDER(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    ELEVENLABS = "11labs"
    DEEPGRAM = "deepgram"
    SPEECHMATIC = "speechmatics"


class TTS_PROVIDER(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    ELEVENLABS = "11labs"
    DEEPGRAM = "deepgram"


LLM_MODEL_MAP = {
    "gemini-2.0-flash-exp": GOOGLE_MODELS.GOOGLE_FLASH,
}

REALTIME_LLM_CONFIG = {
    "openai-realtime": {
        "provider": "openai",
        "model": OPENAI_MODEL.GPT_4o_REALTIME_PREVIEW,
    },
    "google-realtime": {
        "provider": "google",
        "model": GOOGLE_MODELS.GEMINI_REALTIME,
    },
}

DEFAULT_TTS_VOICES = {
    "openai": OPENAI_VOICE_ID.ALLOY,
    "deepgram": DEEPGRAM_VOICE_ID.LUNA,
}

TRANSCRIBER_MODEL_MAP = {
    "openai": OPENAI_TRANSCRIBER.GPT_4o,
    "google": GOOGLE_TRANSCRIBERS.GEMINI_FLASH,
}


class UNPOD_VOICE(str, Enum):
    Neha = "95d51f79-c397-46f9-b49a-23763d3eaa2d"
    Harry = "3dcaa773-fb1a-47f7-82a4-1bf756c4e1fb"
    Spencer = "3bf35adc-bcc4-464b-b834-c90c88cf6492"


UNPOD_VOICE_MAP = {
    "Neha": UNPOD_VOICE.Neha,
    "Harry": UNPOD_VOICE.Harry,
    "Spencer": UNPOD_VOICE.Spencer,
}
