from fastapi import APIRouter, Request
from libs.core.jsondecoder import customResponse
from services.messaging_service.views.persona import generate_template_based_persona
from libs.api.logger import get_logger

app_logging = get_logger("messaging_service")

router = APIRouter()


@router.post("/generate-ai-persona/")
async def generate_ai_persona_endpoint(request: Request):
    data = await request.json()
    from libs.storage.postgres import executeQuery

    prompt_template = {}

    if data.get("template"):
        res = executeQuery(
            "SELECT system_prompt, description, knowledge_base_schema, greeting_message FROM core_components_pilottemplate WHERE slug = %s",
            (data.get("template"),),
        )
        if res is None:
            app_logging.warning("template not found")
            prompt_template["template"] = data.get("template")
        else:
            prompt_template["template"] = {
                "sample_system_prompt": res.get("system_prompt"),
                "description": res.get("description"),
                "greeting_message": res.get("greeting_message"),
            }
    else:
        app_logging.info("template not passed, creating prompt based on business info")

    prompt_template["identity"] = data

    res = await generate_template_based_persona(prompt_template)
    return customResponse(res)
