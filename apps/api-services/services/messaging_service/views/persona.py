import os
from openai import AsyncOpenAI

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_persona_from_template(data):
    """
    Generate persona using direct OpenAI API call (no LangChain dependency)
    """
    identity = data.get("identity", {})
    placeholder_mappings = []

    # Build placeholder mappings for template compilation
    for key, value in identity.items():
        if key not in ["template"]:
            placeholder_mappings.append(
                f"- {{{{{key}}}}} should be replaced with: {value}"
            )
            placeholder_mappings.append(
                f"- {{{{{key.lower()}}}}} should be replaced with: {value}"
            )
            placeholder_mappings.append(
                f"- {{{{{key.upper()}}}}} should be replaced with: {value}"
            )

    placeholder_section = (
        "\n".join(placeholder_mappings)
        if placeholder_mappings
        else "No specific placeholders provided"
    )

    # Build the prompt
    query = f"""
    SYSTEM ROLE: SYSTEM PROMPT ENGINE

    You operate in exactly ONE of the following modes.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    MODE SELECTION (AUTOMATIC)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    IF a TEMPLATE is provided and is non-empty:
    → Operate in TEMPLATE COMPILER MODE

    IF a TEMPLATE is missing or empty:
    → Operate in IDENTITY-BASED GENERATOR MODE

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    MODE 1: TEMPLATE COMPILER MODE
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    You are a deterministic SYSTEM PROMPT COMPILER.

    RULES:
    1. Use the TEMPLATE as the single source of truth
    2. Preserve all sections, wording, order, and intent
    3. Do NOT add, remove, or reorder content
    4. Replace ONLY explicitly mapped placeholders
    5. Placeholder matching is case-insensitive
    6. Leave all unmapped placeholders unchanged
    7. Do NOT wrap output in JSON, YAML, or objects
    8. Output ONLY the final SYSTEM PROMPT text

    [PLACEHOLDER MAPPINGS — REPLACE THESE ONLY]
    {placeholder_section}

    FAILURE MODE:
    If compliance would require guessing, restructuring, or inventing content,
    output the ORIGINAL TEMPLATE unchanged.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    MODE 2: IDENTITY-BASED GENERATOR MODE
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    You are a SYSTEM PROMPT GENERATOR.

    RULES:
    1. Generate a complete SYSTEM PROMPT using ONLY the BUSINESS IDENTITY
    2. Do NOT invent facts beyond the identity
    3. Maintain a professional, deployment-ready tone
    4. ALWAYS include the following sections:
       - [identity]
       - [persona]
       - [Response Guidelines]
       - [Conversation Flow]
    5. Align the prompt fully with the business purpose and domain
    6. Output ONLY the SYSTEM PROMPT text
    7. Do NOT include metadata, keys, or explanations

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    INPUTS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    [TEMPLATE]
    {data.get('template')}

    [BUSINESS IDENTITY]
    {data.get("identity")}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    FINAL DIRECTIVE
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Select the correct mode automatically and return ONLY the SYSTEM PROMPT text now.
    """

    # Direct OpenAI API call
    response = await client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "system", "content": query}], temperature=0
    )

    system_prompt = response.choices[0].message.content
    return system_prompt


async def generate_template_based_persona(data: dict):

    res = await generate_persona_from_template(data)
    data = {"system_prompt": res}
    return data
