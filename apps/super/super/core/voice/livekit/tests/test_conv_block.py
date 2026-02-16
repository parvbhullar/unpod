from super.core.voice.livekit.conversation_state import parse_prompt_sections
from super_services.voice.models.config import ModelConfig

config = ModelConfig().get_config('tata_capital_23dec-3wl7im70pqpu')

res=parse_prompt_sections(config.get("system_prompt"))

print(res)