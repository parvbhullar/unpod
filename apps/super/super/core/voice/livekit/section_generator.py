import dspy
import json
import re
from typing import Dict, List, Any, Tuple


# Identity section detection patterns (bilingual)
IDENTITY_SECTION_PATTERNS = [
    r"\[identity\]",
    r"\[name.?collection\]",
    r"may i know (your name|who)",
    r"whom am i speaking",
    r"aapka naam",
    r"what is your name",
    r"can i get your name",
]

# Slot extraction patterns for structured content
SLOT_PATTERNS = [
    r"[-•]\s*(.+?):\s*(.+)",           # "- Classroom mode: ₹2,45,000"
    r"(\w+(?:\s+\w+)?)\s*[-–:]\s*(.+)",  # "Online fees - ₹1,85,000"
    r"\d+\.\s*(.+?):\s*(.+)",           # "1. Classroom: ₹2,45,000"
]


class ExtractBlocks(dspy.Signature):
    """
    Convert agent prompt into structured blocks.
    Output MUST be a JSON array of blocks.
    """
    prompt = dspy.InputField(description="Agent prompt for which blocks need to be generated for")
    system_prompt = dspy.InputField(desc="prompt or instructions for model to create blocks")
    blocks = dspy.OutputField(desc="JSON list of structured blocks")


class BlockExtractor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict(ExtractBlocks)

    def forward(self, prompt: str):
        raw = self.predict(prompt=prompt,system_prompt=SYSTEM_INSTRUCTIONS).blocks

        try:
            # Extract JSON array from the LLM output
            json_text = re.search(r"\[.*\]", raw, re.DOTALL).group()
            return json.loads(json_text)
        except Exception:
            print("Invalid LLM output:", raw)
            return []


SYSTEM_INSTRUCTIONS = """
You are a prompt-segmentation engine for a voice AI agent.

Given ANY long prompt, you will extract *clean functional blocks* needed for the agent.

For each block, output a dict with EXACTLY these fields:

{
  "id": "unique_slug_id",
  "title": "Readable Title",
  "content": "English version of the block",
  "content_hi": "Hinglish version of the same block",
  "delivery_order": 0,
  "trigger_condition": "sequential",
  "is_cta_point": false
}

Rules:
- id must be a slug: lowercase, hyphens only.
- If hinglish is not present, copy English into content_hi.
- Detect CTA blocks automatically (closing, visit, offer, submission, booking, request).
- delivery_order MUST follow the order of appearance in the prompt.
- Return ONLY JSON array of blocks. No commentary.
"""


def generate_sections(prompt: str) -> List[Dict[str, Any]]:
    """
    Pass in any raw system prompt.
    Returns: JSON list of extracted blocks.
    """
    dspy.configure(
        lm=dspy.LM(
            model="gpt-4o-mini",
        )
    )

    extractor = BlockExtractor()
    blocks = extractor(prompt)

    return blocks


def detect_identity_section(prompt: str) -> Tuple[bool, str]:
    """
    Detect if prompt contains identity collection section.

    Args:
        prompt: The agent system prompt

    Returns:
        Tuple of (has_identity_section, matched_pattern)
    """
    prompt_lower = prompt.lower()

    for pattern in IDENTITY_SECTION_PATTERNS:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            return True, pattern

    return False, ""


def extract_slots_from_content(content: str, slot_id: str) -> List[Dict[str, Any]]:
    """
    Extract sub-items from content block as nested content blocks.

    Recognizes list patterns like:
    - Classroom mode: ₹2,45,000
    - Online mode: ₹1,85,000

    Args:
        content: The content text to parse
        slot_id: Parent slot ID for generating sub-IDs

    Returns:
        List of content block dicts
    """
    content_blocks: List[Dict[str, Any]] = []

    for pattern in SLOT_PATTERNS:
        matches = re.findall(pattern, content, re.MULTILINE)
        if matches:
            for i, match in enumerate(matches):
                label, value = match[0].strip(), match[1].strip()
                block_id = f"{slot_id}_{slugify(label)}"

                content_blocks.append({
                    "id": block_id,
                    "content": f"{label}: {value}",
                    "content_hi": "",
                    "delivery_order": i,
                    "delivered": False,
                })

            # Only use first matching pattern
            break

    return content_blocks


def slugify(text: str) -> str:
    """Convert text to slug ID."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def generate_slots_from_blocks(
    blocks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Convert flat blocks into hierarchical slots with nested content blocks.

    Each block becomes a slot. If the block content contains list items
    (like fees breakdown), those become nested content_blocks.

    Args:
        blocks: Flat list of blocks from generate_sections()

    Returns:
        List of slot dicts with nested content_blocks
    """
    slots: List[Dict[str, Any]] = []

    for block in blocks:
        block_id = block.get("id", "")
        content = block.get("content", "")

        # Extract nested content blocks from list items
        nested_blocks = extract_slots_from_content(content, block_id)

        # Create slot with optional nested blocks
        slot = {
            "id": block_id,
            "description": block.get("title", block_id),
            "required": True,
            "filled": False,
            "value": "",
            "variants": _generate_variants(block_id, block.get("title", "")),
            "content_blocks": nested_blocks if nested_blocks else [{
                "id": block_id,
                "content": content,
                "content_hi": block.get("content_hi", ""),
                "delivery_order": 0,
                "delivered": False,
            }],
        }

        slots.append(slot)

    return slots


def _generate_variants(slot_id: str, title: str) -> List[str]:
    """
    Generate query matching variants for a slot.

    Args:
        slot_id: The slot identifier
        title: The slot title

    Returns:
        List of variant strings for query matching
    """
    variants: List[str] = []

    # Add words from ID (split by underscore/hyphen)
    id_words = re.split(r"[_-]", slot_id.lower())
    variants.extend([w for w in id_words if len(w) > 2])

    # Add words from title
    title_words = re.split(r"\s+", title.lower())
    variants.extend([w for w in title_words if len(w) > 2])

    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique_variants: List[str] = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            unique_variants.append(v)

    return unique_variants
