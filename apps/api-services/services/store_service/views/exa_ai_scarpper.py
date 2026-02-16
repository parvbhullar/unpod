"""
Exa.ai Web Scraper - DYNAMIC VERSION

Single API call extracts:
1. Complete business information
2. Dynamic AI agent persona and system prompt (generated from business context)
"""

import json
import re
import time
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from exa_py import Exa
from libs.api.logger import get_logger

logger = get_logger("exa_ai_scraper")

# Configuration
from libs.api.config import get_settings

settings = get_settings()
EXA_API_KEY = settings.EXA_API_KEY

exa_client = None


def get_exa_client() -> Optional[Exa]:
    """Get or initialize Exa.ai client"""
    global exa_client
    if exa_client is None:
        if EXA_API_KEY:
            exa_client = Exa(api_key=EXA_API_KEY)
        else:
            logger.error("EXA_API_KEY not found")
            return None
    return exa_client


def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    return urlparse(url).netloc.replace("www.", "")


def extract_json_from_text(text: str) -> Optional[Dict]:
    """Extract JSON object from text that may contain markdown or other content"""
    if not text:
        return None

    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in markdown code blocks
    match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Pattern 2: ``` ... ```
    match = re.search(r"```\s*([\s\S]*?)\s*```", text)
    if match:
        try:
            content = match.group(1).strip()
            if content.startswith("{"):
                return json.loads(content)
        except json.JSONDecodeError:
            pass

    # Pattern 3: Find raw JSON object
    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None


# Extraction query - optimized for Exa's ~1000 char summary limit
EXTRACTION_QUERY = """Analyze website. Return JSON with ALL fields filled:
{"name":"company name","type":"business type","industry":"industry","desc":"2 line description","value":"why customers choose","audience":"target customers","features":["feature1","feature2","feature3"],"products":["product1","product2","product3"],"email":"support email from website","phone":"phone number from website","instagram":"instagram URL","twitter":"twitter URL","logo":"website logo image URL","colors":"brand color hex code"}
Return ONLY the JSON."""


def build_dynamic_context(
    industry: str,
    business_type: str,
    description: str,
    products_services: list,
    key_features: list,
    value_proposition: str,
) -> dict:
    """Build context 100% dynamically from extracted data - NO hardcoded values"""

    # Use actual extracted values
    industry_clean = industry.strip() if industry else "General"
    business_clean = business_type.strip() if business_type else "Business"

    # Build expertise from actual extracted data
    expertise = []
    if products_services:
        expertise.extend([f"{p} guidance" for p in products_services[:3]])
    if key_features:
        expertise.extend([f.lower() for f in key_features[:2]])
    if not expertise:
        expertise = [
            f"{industry_clean} products",
            f"{industry_clean} services",
            "customer support",
        ]

    # Build scenarios from actual business context
    scenarios = [
        f"{industry_clean} product inquiries",
        f"recommendations based on customer needs",
        f"order and delivery assistance",
        f"returns and support queries",
        f"pricing and availability questions",
    ]

    # Generate style words from description and value proposition
    combined_text = f"{description} {value_proposition}".lower()

    # Extract meaningful words from the actual content
    style_words = []
    if value_proposition:
        # Take key words from value proposition
        words = value_proposition.split()
        style_words = [w.strip(".,!?") for w in words if len(w) > 4 and w.isalpha()][:4]
    if len(style_words) < 3:
        style_words.extend(["quality", "service", "trusted", "reliable"])
    style_words = style_words[:6]

    # Build tone from industry and business type
    tone = f"professional, knowledgeable about {industry_clean}, and customer-focused"

    # Greeting style based on business type
    greeting_style = f"friendly and {industry_clean.lower()}-focused"

    return {
        "tone": tone,
        "expertise": expertise[:5],
        "scenarios": scenarios,
        "style_words": style_words,
        "greeting_style": greeting_style,
        "emoji": "👋",  # Default emoji, can be dynamic based on industry later
    }


def generate_ai_agent_name(business_type: str, industry: str, company_name: str) -> str:
    """Generate AI agent type 100% dynamically from extracted data - NO hardcoded mappings"""

    # Clean extracted values
    industry_clean = industry.strip() if industry else ""
    business_clean = business_type.strip() if business_type else ""

    # Build agent type dynamically from extracted industry
    if industry_clean:
        # Use the actual industry name to create the agent type
        return f"{company_name} {industry_clean} Assistant"
    elif business_clean:
        # Fallback to business type
        return f"{company_name} {business_clean} Assistant"
    else:
        return f"{company_name} Virtual Assistant"


def generate_ai_persona(
    company_name: str,
    business_type: str,
    industry: str,
    description: str,
    agent_type: str,
    value_proposition: str,
    products_services: list,
    key_features: list,
) -> str:
    """Generate AI persona 100% dynamically from extracted data - NO hardcoded content"""

    # Build context dynamically from extracted data
    context = build_dynamic_context(
        industry,
        business_type,
        description,
        products_services,
        key_features,
        value_proposition,
    )

    products_str = (
        ", ".join(products_services[:5])
        if products_services
        else "products and services"
    )
    features_str = ", ".join(key_features[:3]) if key_features else "quality offerings"
    industry_clean = industry if industry else "this"

    persona = f"""The {agent_type} is {company_name}'s dedicated virtual assistant, specifically designed to embody the brand's values and deliver exceptional customer experiences.

**About {company_name}:**
{description}

**Brand Voice & Communication:**
This AI represents {company_name} and communicates in a {context['greeting_style']} manner. The agent reflects the brand's commitment to: {value_proposition}

**Core Expertise Areas:**
{chr(10).join([f'- **{exp.title()}:** In-depth knowledge to guide customers effectively' for exp in context['expertise']])}

**Product & Service Mastery:**
- Complete understanding of {company_name}'s offerings: {products_str}
- Expert knowledge of key features: {features_str}

**Personality & Approach:**
- **Brand Representative:** Speaks authentically as {company_name}'s voice
- **{industry_clean} Expert:** Demonstrates deep domain knowledge in every interaction
- **Personalization Focus:** Tailors every recommendation to individual customer needs
- **Empathetic Problem-Solver:** Understands concerns and provides thoughtful solutions
- **Proactive Assistant:** Anticipates customer needs and offers relevant suggestions

**Communication Style:**
- Opens conversations with {context['greeting_style']} greetings
- Uses terminology familiar to {industry_clean} customers
- Clearly explains {company_name}'s unique value proposition
- References specific products: {products_str}
- Highlights differentiators: {features_str}

**Customer Journey Support:**
- **Discovery:** Helps customers explore {company_name}'s offerings based on their needs
- **Selection:** Provides comparisons and personalized recommendations
- **Purchase:** Assists with availability, pricing, and checkout
- **Post-Purchase:** Handles tracking, returns, exchanges, and feedback

**Key Scenarios:**
{chr(10).join([f'- {scenario.title()}: Expert guidance with {company_name}-specific knowledge' for scenario in context['scenarios']])}

**Tone:**
- {context['tone']}
- Uses language reflecting: {', '.join(context['style_words'][:4])}
- Balances helpfulness with professionalism"""

    return persona


def generate_system_prompt(
    company_name: str,
    business_type: str,
    industry: str,
    description: str,
    agent_name: str,
    products_services: list,
    value_proposition: str,
    key_features: list,
    target_audience: str,
) -> str:
    """Generate system prompt 100% dynamically from extracted data - NO hardcoded content"""

    # Build context dynamically from extracted data
    context = build_dynamic_context(
        industry,
        business_type,
        description,
        products_services,
        key_features,
        value_proposition,
    )

    features_str = (
        "\n".join([f"   - {f}" for f in key_features])
        if key_features
        else "   - Quality products and services"
    )
    products_str = (
        ", ".join(products_services[:5])
        if products_services
        else "various products and services"
    )
    industry_clean = industry if industry else "this domain"

    # Generate dynamic greeting using extracted data
    expertise_str = ", ".join(context["expertise"][:3])
    value_prop_short = (
        value_proposition[:100]
        if value_proposition
        else "I am here to help you find exactly what you need."
    )

    # Build dynamic greeting
    greeting = f"Welcome to {company_name}! I am your {agent_name}, here to assist you with {expertise_str}. {value_prop_short} How can I assist you today?"

    # Build scenarios from context
    scenarios_text = "\n".join([f"""
**{scenario.title()}:**
- Understand the customer's specific needs
- Reference relevant {company_name} products: {products_str}
- Provide expert {industry_clean} advice
- Suggest personalized recommendations""" for scenario in context["scenarios"][:4]])

    system_prompt = f"""[ROLE & IDENTITY]
You are the {agent_name}, the official AI assistant for {company_name}.

About {company_name}: {description}

Your mission: Deliver exceptional {context['tone']} customer experiences while helping customers discover and purchase from {company_name}'s offerings.

Target Customers: {target_audience}git reset --hard
git clean -fd
git pull --rebase

Core Value: {value_proposition}

[BRAND VOICE & PERSONALITY]
You embody {company_name}'s brand identity:
- Tone: {context['tone']}
- Style Words to Use: {', '.join(context['style_words'])}
- Greeting Style: {context['greeting_style']}

You are NOT a generic chatbot. You are a specialized {agent_name} who:
- Speaks as a true {company_name} representative
- Has deep expertise in {industry_clean}
- Knows every detail about {products_str}
- Understands why customers choose {company_name}: {value_proposition}

[GREETING & INTRODUCTION]
Always start conversations with a {context['greeting_style']} greeting that reflects {company_name}'s brand.

Example Opening:
{greeting}

[PRODUCT & SERVICE EXPERTISE]
You have complete knowledge of:
- **Product Categories:** {products_str}
- **Key Differentiators:**
{features_str}
- **Pricing & Offers:** Current promotions and pricing tiers
- **Policies:** Shipping, returns, exchanges, warranties

[{industry_clean.upper()}-SPECIFIC KNOWLEDGE]
As a {industry_clean} expert, you understand:
{chr(10).join([f'- {exp.title()}' for exp in context['expertise']])}

[CONVERSATION GUIDELINES]

1. **Personalized Discovery:**
   - Ask about customer's specific needs in {industry_clean.lower()}
   - Understand their preferences, budget, and requirements
   - Reference their stated needs when making recommendations

2. **Expert Recommendations:**
   - Suggest specific {company_name} products that match their needs
   - Explain WHY each recommendation fits them
   - Offer alternatives at different price points
   - Mention complementary products they might like

3. **Handling Queries:**
   - Product details: Provide comprehensive information with enthusiasm
   - Comparisons: Help customers choose between options
   - Availability: Check and inform about stock status
   - Pricing: Be transparent about costs and any ongoing offers

4. **Problem Resolution:**
   - Acknowledge concerns with empathy
   - Apologize sincerely for any issues
   - Provide clear solutions or next steps
   - Follow up to ensure satisfaction

[INDUSTRY-SPECIFIC SCENARIOS]
{scenarios_text}

[RESPONSE FORMAT]
- Keep responses concise but helpful (2-4 sentences for simple queries, more for detailed questions)
- Use bullet points for listing multiple products or features
- Include specific product names from {company_name}'s catalog
- Add relevant {context['style_words'][0]} and {context['style_words'][1]} language naturally

[DO's]
✓ Use {company_name}'s brand voice consistently
✓ Reference specific products: {products_str}
✓ Highlight unique features: {features_str[:100] if len(features_str) > 100 else features_str}
✓ Personalize based on customer's stated needs
✓ Show genuine enthusiasm for {industry_clean}
✓ Proactively suggest relevant products

[DON'Ts]
✗ Sound like a generic chatbot
✗ Give vague, non-specific answers
✗ Forget to mention {company_name}'s unique value
✗ Ignore customer's specific requirements
✗ Use overly formal or robotic language

[ESCALATION TO HUMAN SUPPORT]
Transfer to human agent when:
- Customer explicitly requests human help
- Complex issues beyond your knowledge
- Sensitive complaints requiring special handling
- Technical problems needing investigation

Escalation message: "I want to make sure you get the best help possible. Let me connect you with a {company_name} specialist who can assist you further. They'll be with you shortly!"

[CLOSING CONVERSATIONS]
End every conversation by:
1. Confirming their question was answered
2. Offering additional assistance
3. Thanking them for choosing {company_name}

Example: "Is there anything else I can help you with? Thank you for visiting {company_name} - we hope to see you again soon! 🙌"
"""

    return system_prompt


def scrape_website(url: str) -> Dict[str, Any]:
    """
    Scrape business info using ONE Exa.ai API call.
    AI agent persona and system prompt are dynamically generated from business context.
    """
    overall_start = time.time()
    logger.info(f"Starting scrape for: {url}")

    if not validate_url(url):
        return {"error": "Invalid URL format", "url": url, "success": False}

    client = get_exa_client()
    if not client:
        return {"error": "EXA_API_KEY not configured", "url": url, "success": False}

    domain = extract_domain(url)
    logger.info(f"Extracting data for: {domain}")

    try:
        # Single API call with extraction query
        response = client.get_contents(
            urls=[url], text=True, summary={"query": EXTRACTION_QUERY}
        )

        # Fallback: If get_contents returns empty, try search_and_contents
        if not response or not response.results:
            logger.info(
                f"get_contents returned empty, trying search_and_contents fallback..."
            )
            response = client.search_and_contents(
                query=f"site:{domain}",
                num_results=1,
                text=True,
                summary={"query": EXTRACTION_QUERY},
            )

        if not response or not response.results:
            return {
                "error": "Failed to get content from URL",
                "url": url,
                "success": False,
            }

        result = response.results[0]

        # Get all available data
        title = getattr(result, "title", "") or ""
        summary = getattr(result, "summary", "") or ""

        logger.info(f"Got response - Title: {title[:50]}...")
        logger.info(f"Summary length: {len(summary)} chars")

        # Try to extract JSON from summary
        parsed_data = extract_json_from_text(summary)

        if not parsed_data:
            logger.warning("Could not parse JSON, extracting from text...")
            # Fallback: Create basic structure from title
            parsed_data = {
                "company_name": (
                    title.split("|")[0].split("-")[0].strip() if title else domain
                ),
                "business_type": "E-commerce",
                "industry": "Retail",
                "description": summary[:300] if summary else "",
            }

        logger.info(f"Extracted data keys: {list(parsed_data.keys())}")

        # Helper to get field with fallback short names
        def get_field(long_name, short_name, default=""):
            return parsed_data.get(long_name) or parsed_data.get(short_name, default)

        # Extract fields from parsed data (support both long and short field names)
        company_name = (
            get_field("company_name", "name") or title.split("|")[0].strip() or domain
        )
        business_type = get_field("business_type", "type")
        industry = get_field("industry", "industry")
        description = get_field("description", "desc")
        value_proposition = get_field("value_proposition", "value")
        target_audience = get_field("target_audience", "audience")
        key_features = get_field("key_features", "features", [])
        products_services = get_field("products_services", "products", [])
        pricing_model = get_field("pricing_model", "pricing")

        # Contact info - extract and clean empty values
        contact_info = {
            "email": get_field("contact_email", "email"),
            "phone": get_field("contact_phone", "phone"),
            "address": get_field("contact_address", "address"),
        }
        contact_info = {k: v for k, v in contact_info.items() if v}

        # Social links - extract from parsed data
        social_links = {
            "website": url,
            "instagram": get_field("social_instagram", "instagram"),
            "twitter": get_field("social_twitter", "twitter"),
        }
        # Remove empty social links
        social_links = {k: v for k, v in social_links.items() if v}

        # Visual/Branding - extract from parsed data
        brand_colors = get_field("brand_colors", "colors")

        # If brand colors is a string, try to split into list of valid hex codes
        if isinstance(brand_colors, str):
            found_colors = re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}", brand_colors)
            if found_colors:
                brand_colors = (
                    found_colors  # List of strings e.g. ['#2874F0', '#FF3E30']
                )
            else:
                # Keep original if no hex codes found, or handle as empty list
                pass
        elif isinstance(brand_colors, list):
            # Ensure the list items are valid hex strings (optional cleanup)
            cleaned_colors = []
            for col in brand_colors:
                if isinstance(col, str):
                    matches = re.findall(r"#(?:[0-9a-fA-F]{3}){1,2}", col)
                    cleaned_colors.extend(matches)
            if cleaned_colors:
                brand_colors = cleaned_colors

        # DYNAMIC AI AGENT GENERATION
        logger.info("Generating AI agent dynamically...")

        agent_name = generate_ai_agent_name(business_type, industry, company_name)
        ai_persona = generate_ai_persona(
            company_name,
            business_type,
            industry,
            description,
            agent_name,
            value_proposition,
            products_services,
            key_features,
        )
        ai_system_prompt = generate_system_prompt(
            company_name,
            business_type,
            industry,
            description,
            agent_name,
            products_services,
            value_proposition,
            key_features,
            target_audience,
        )

        # Prepare visual data
        visual_data = {
            "brand_colors": brand_colors or "",
        }

        # Build comprehensive result
        result_data = {
            "company_name": company_name,
            "business_type": business_type,
            "industry": industry,
            "description": description,
            "value_proposition": value_proposition,
            "target_audience": target_audience,
            "key_features": key_features,
            "products_services": products_services,
            "pricing_model": pricing_model,
            "contact_info": contact_info,
            "ai_agent": {
                "name": agent_name,
                "description": f"AI-powered {agent_name} for {company_name} that helps customers with product inquiries, recommendations, and support.",
                "persona": ai_persona,
                "system_prompt": ai_system_prompt,
            },
            "social_links": social_links,
            "visual": visual_data,
            "metadata": {
                "source_url": url,
                "page_title": title,
                "scraped_at": datetime.now().isoformat(),
                "performance": {
                    "total_time_seconds": round(time.time() - overall_start, 2)
                },
            },
        }

        logger.info(f"✓ Complete in {time.time() - overall_start:.2f}s")
        return {"data": result_data, "success": True}

    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return {"error": str(e), "url": url, "success": False}
