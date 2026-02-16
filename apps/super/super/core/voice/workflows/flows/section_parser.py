"""
Section Parser for Section-Based Flow Generation

Parses a list of sections into typed structures for flow creation.
Each section becomes a typed node with specific behavior.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ParsedSection:
    """Represents a parsed section with type and metadata."""
    id: str
    section_name: str
    type: str  # identity, greeting, question, condition, objection, guideline, pitch
    content: str
    required: List[str] = field(default_factory=list)
    field_types: Dict[str, str] = field(default_factory=dict)
    field_descriptions: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    next_section_id: Optional[str] = None

    # For conditional sections
    condition_type: Optional[str] = None  # yes, no, custom
    yes_target: Optional[str] = None
    no_target: Optional[str] = None
    parent_section_id: Optional[str] = None

    # For objection sections
    trigger_keywords: List[str] = field(default_factory=list)
    return_to: str = "previous"

    # Raw section for reference
    raw_section: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedFlowConfig:
    """Complete parsed flow configuration."""
    instructions: Optional[ParsedSection] = None
    identity: Optional[ParsedSection] = None
    greeting: Optional[ParsedSection] = None
    questions: List[ParsedSection] = field(default_factory=list)
    conditions: List[ParsedSection] = field(default_factory=list)
    objections: List[ParsedSection] = field(default_factory=list)
    guidelines: List[ParsedSection] = field(default_factory=list)
    pitches: List[ParsedSection] = field(default_factory=list)
    faqs: List[ParsedSection] = field(default_factory=list)
    flow_order: List[str] = field(default_factory=list)
    sections_by_id: Dict[str, ParsedSection] = field(default_factory=dict)
    conditions_by_parent: Dict[str, List[str]] = field(default_factory=dict)
    condition_parent_map: Dict[str, str] = field(default_factory=dict)
    post_condition_by_parent: Dict[str, Optional[str]] = field(default_factory=dict)
    post_condition_by_condition: Dict[str, Optional[str]] = field(default_factory=dict)


class SectionParser:
    """
    Parses section list or raw prompt into typed flow configuration.

    Section Types:
    - identity: Agent personality and role (goes into role_messages)
    - greeting: Initial interaction
    - question: Data collection step
    - condition: If YES/NO branching
    - objection: Customer objection handler
    - guideline: Response rules
    - pitch: Value proposition presentation
    - instructions: System-level guidelines and rules
    - faq: Q&A knowledge base pairs
    """

    def __init__(self):
        # Patterns to identify section types (order matters!)
        self.identity_patterns = ['identity', 'introduction', 'who you are', 'agent identity']
        self.greeting_patterns = ['greeting', 'welcome', 'hello', 'opening']
        self.guideline_patterns = ['guideline', 'rule', 'restriction', 'never']  # Removed 'always' to avoid collision with 'always ask'
        self.instruction_patterns = ['instructions', 'guidelines', 'response guidelines', 'style']

        # Conditions and objections need to be checked BEFORE questions to avoid false positives
        self.condition_patterns = ['if yes', 'if no', 'if customer', 'usecase', 'when']
        self.objection_patterns = [
            'if customer says', 'if student says', 'if caller says', 'if user says',  # Conversational objections
            'if they say', 'if he says', 'if she says',
            'if customer asks', 'if student asks', 'if caller asks', 'if user asks',  # Question-like objections
            'objection', 'if refuses', 'concern'
        ]

        self.pitch_patterns = ['pitch', 'offer', 'proposal']  # Removed 'main' and 'goal' to avoid collision
        self.faq_patterns = ['faq', 'knowledge base', 'q&a', 'questions']
        self.question_patterns = [
            'always ask',  # Moved to first for highest priority
            'ask', 'collect', 'details', 'information',
            'check', 'question', 'inquiry', 'verify',
            'status', 'background', 'employment', 'income'
        ]

    def parse_prompt(self, system_prompt: str) -> ParsedFlowConfig:
        """
        Parse raw system prompt string into typed flow configuration.

        This is the main entry point - extracts sections from raw text first,
        then parses them into structured config.

        Args:
            system_prompt: Raw prompt text with [Section] markers

        Returns:
            ParsedFlowConfig with typed sections and flow order
        """
        # Step 0: Normalize text (handle literal escaped newlines from agent configs)
        normalized = self._normalize_text(system_prompt)

        # Step 1: Extract sections from raw prompt
        sections = self._extract_sections_from_prompt(normalized)

        # Step 2: Parse extracted sections
        return self.parse_sections(sections)

    def _normalize_text(self, text: str) -> str:
        """
        Normalize whitespace and line breaks.

        CRITICAL: Agent configs often have literal escaped newlines (\\r\\n as 4-char string)
        instead of actual newline characters. This fixes that.
        """
        # Handle both literal escaped newlines (\r\n as string) and actual CR+LF
        text = text.replace('\\r\\n', '\n')  # Convert literal \r\n to actual newline
        text = text.replace('\\n', '\n')    # Convert literal \n to actual newline
        text = re.sub(r'\r\n', '\n', text)  # Convert actual CR+LF to LF
        text = re.sub(r'\n{3,}', '\n\n', text)  # Collapse multiple newlines
        return text.strip()

    def _extract_sections_from_prompt(self, text: str) -> List[Dict[str, str]]:
        """
        Extract sections from raw prompt text.

        Supports formats:
        - [Section Name]
        - # Section Name
        - ## Section Name
        - === Section Name ===

        Returns list of dicts with 'section' and 'content' keys.
        """
        # Pattern: [Header] or # Header or === Header ===
        pattern = r'(?:^|\n)(?:\[([^\]]+)\]|#+\s*([^\n]+)|==+\s*([^\n]+)\s*==+)'

        matches = list(re.finditer(pattern, text, re.MULTILINE))

        if not matches:
            # No sections found - treat entire text as one section
            return [{
                "section": "Main Content",
                "content": text.strip()
            }]

        sections = []
        for i, match in enumerate(matches):
            # Extract header from any of the three groups
            header = match.group(1) or match.group(2) or match.group(3)
            header = header.strip()

            # Extract content between this header and next header
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            content = text[start:end].strip()

            if content:  # Skip empty sections
                sections.append({
                    "section": header,
                    "content": content
                })

        return sections

    def parse_sections(self, sections: List[Dict[str, str]]) -> ParsedFlowConfig:
        """
        Parse sections into typed flow configuration.

        Args:
            sections: List of dicts with 'section' and 'content' keys

        Returns:
            ParsedFlowConfig with typed sections and flow order
        """
        config = ParsedFlowConfig()

        flow_sequence: List[str] = []
        last_primary_id: Optional[str] = None

        for idx, section in enumerate(sections):
            section_name = section.get('section', f'section_{idx}')
            content = section.get('content', '')

            # Skip empty sections
            if not content or not content.strip():
                continue

            section_type = self._identify_section_type(section_name, content)
            section_id = self._generate_section_id(section_name, idx)

            parsed = ParsedSection(
                id=section_id,
                section_name=section_name,
                type=section_type,
                content=content,
                raw_section=section
            )

            # Parse based on type
            if section_type == 'instructions':
                parsed = self._parse_instructions_section(parsed)
                config.instructions = parsed

            elif section_type == 'identity':
                parsed = self._parse_identity_section(parsed)
                config.identity = parsed

            elif section_type == 'greeting':
                parsed = self._parse_greeting_section(parsed)
                config.greeting = parsed
                last_primary_id = section_id
                flow_sequence.append(section_id)

            elif section_type == 'question' or section_type == 'pitch':
                parsed = self._parse_question_section(parsed)
                if section_type == 'pitch':
                    config.pitches.append(parsed)
                else:
                    config.questions.append(parsed)
                last_primary_id = section_id
                flow_sequence.append(section_id)

            elif section_type == 'condition':
                parsed = self._parse_condition_section(parsed, last_primary_id)
                config.conditions.append(parsed)
                flow_sequence.append(section_id)

                if parsed.parent_section_id:
                    config.conditions_by_parent.setdefault(parsed.parent_section_id, []).append(section_id)
                    config.condition_parent_map[section_id] = parsed.parent_section_id

            elif section_type == 'objection':
                parsed = self._parse_objection_section(parsed)
                config.objections.append(parsed)

            elif section_type == 'faq':
                parsed = self._parse_faq_section(parsed)
                config.faqs.append(parsed)

            elif section_type == 'guideline':
                parsed = self._parse_guideline_section(parsed)
                config.guidelines.append(parsed)

            # Store by ID for lookup
            config.sections_by_id[section_id] = parsed

        # Build flow order
        config.flow_order = self._build_flow_order(config, flow_sequence)

        # Link next_section_id
        self._link_sections(config)

        return config

    def _identify_section_type(self, section_name: str, content: str) -> str:
        """Identify section type from name and content."""
        name_lower = section_name.lower()

        # Check patterns in order of specificity
        if any(pattern in name_lower for pattern in self.instruction_patterns):
            return 'instructions'

        if any(pattern in name_lower for pattern in self.identity_patterns):
            return 'identity'

        if any(pattern in name_lower for pattern in self.greeting_patterns):
            return 'greeting'

        if any(pattern in name_lower for pattern in self.faq_patterns):
            return 'faq'

        if any(pattern in name_lower for pattern in self.objection_patterns):
            return 'objection'

        if any(pattern in name_lower for pattern in self.condition_patterns):
            return 'condition'

        # CRITICAL FIX: Check question patterns BEFORE guideline patterns
        # This ensures "Always ask this" is classified as 'question' not 'guideline'
        if (any(pattern in name_lower for pattern in self.question_patterns) or
            self._contains_template_variables(content)):
            return 'question'

        if any(pattern in name_lower for pattern in self.guideline_patterns):
            return 'guideline'

        if any(pattern in name_lower for pattern in self.pitch_patterns):
            return 'pitch'

        # Check content for Q&A format
        if self._is_qa_content(content):
            return 'faq'

        # Fallback to question if uncertain (was 'guideline' before)
        return 'question'

    def _generate_section_id(self, section_name: str, index: int) -> str:
        """Generate unique ID from section name."""
        # Convert to snake_case
        id_base = re.sub(r'[^\w\s]', '', section_name.lower())
        id_base = re.sub(r'\s+', '_', id_base)
        return f"{id_base}_{index}"

    def _parse_identity_section(self, section: ParsedSection) -> ParsedSection:
        """Parse identity/introduction section."""
        section.description = "Agent identity and personality"
        return section

    def _parse_greeting_section(self, section: ParsedSection) -> ParsedSection:
        """Parse greeting section."""
        section.description = "Initial greeting and conversation start"
        template_fields = self._extract_template_variables(section.content)
        prompts = self._extract_question_prompts(section.content)

        if template_fields:
            section.required = template_fields
            section.field_types = {field: 'string' for field in section.required}
            section.field_descriptions = self._map_descriptions_to_fields(
                section.required,
                prompts,
                default_description=section.section_name
            )
        else:
            derived = self._derive_fields_from_content(section, prompts)
            section.required = [item["field"] for item in derived]
            section.field_types = {item["field"]: item["type"] for item in derived}
            section.field_descriptions = {item["field"]: item["description"] for item in derived}

        if prompts:
            section.description = prompts[0]

        if not section.required:
            fallback_field = self._generate_fallback_field(section.section_name)
            section.required = [fallback_field]
            section.field_types = {fallback_field: 'string'}
            section.field_descriptions = {fallback_field: section.section_name}

        return section

    def _parse_question_section(self, section: ParsedSection) -> ParsedSection:
        """Parse question/data collection section."""
        template_fields = self._extract_template_variables(section.content)

        prompts = self._extract_question_prompts(section.content)

        if template_fields:
            section.required = template_fields
            section.field_types = self._infer_field_types(section.content, section.required)
            section.field_descriptions = self._map_descriptions_to_fields(
                section.required,
                prompts,
                default_description=section.section_name
            )
        else:
            derived = self._derive_fields_from_content(section, prompts)
            section.required = [item["field"] for item in derived]
            section.field_types = {item["field"]: item["type"] for item in derived}
            section.field_descriptions = {item["field"]: item["description"] for item in derived}

        if not section.required:
            fallback_field = self._generate_fallback_field(section.section_name)
            section.required = [fallback_field]
            section.field_types = {fallback_field: 'string'}
            section.field_descriptions = {fallback_field: section.section_name}

        # Generate description
        section.description = prompts[0] if prompts else section.section_name

        return section

    def _parse_condition_section(self, section: ParsedSection, last_question_id: Optional[str]) -> ParsedSection:
        """Parse conditional (If YES/NO) section."""
        name_lower = section.section_name.lower()

        if 'if yes' in name_lower:
            section.condition_type = 'yes'
        elif 'if no' in name_lower:
            section.condition_type = 'no'
        else:
            section.condition_type = 'custom'

        section.parent_section_id = last_question_id

        section.description = f"Conditional: {section.section_name}"

        template_fields = self._extract_template_variables(section.content)
        prompts = self._extract_question_prompts(section.content)

        if template_fields:
            section.required = template_fields
            section.field_types = self._infer_field_types(section.content, section.required)
            section.field_descriptions = self._map_descriptions_to_fields(
                section.required,
                prompts,
                default_description=section.section_name
            )
        else:
            derived = self._derive_fields_from_content(section, prompts, allow_empty=True)
            section.required = [item["field"] for item in derived]
            section.field_types = {item["field"]: item["type"] for item in derived}
            section.field_descriptions = {item["field"]: item["description"] for item in derived}

        if prompts:
            section.description = prompts[0]

        return section

    def _parse_objection_section(self, section: ParsedSection) -> ParsedSection:
        """Parse objection handler section."""
        # Extract trigger keywords from section name
        # "Customer Objection: Interest Rate Too High" → ["interest rate too high"]
        if ':' in section.section_name:
            trigger = section.section_name.split(':', 1)[1].strip().lower()
            section.trigger_keywords = [trigger]
        else:
            section.trigger_keywords = []

        section.description = f"Handle objection: {section.section_name}"
        section.return_to = "previous"  # Return to last active section

        return section

    def _parse_guideline_section(self, section: ParsedSection) -> ParsedSection:
        """Parse guideline/rule section."""
        section.description = "Response guidelines and rules"
        return section

    def _parse_instructions_section(self, section: ParsedSection) -> ParsedSection:
        """Parse instructions/system guidelines section."""
        section.description = "System instructions and guidelines"
        return section

    def _parse_faq_section(self, section: ParsedSection) -> ParsedSection:
        """Parse FAQ/knowledge base section."""
        section.description = "Frequently asked questions"
        return section

    def _is_qa_content(self, content: str) -> bool:
        """Check if content is in Q&A format."""
        # Check for Q: ... A: ... pattern
        pattern = r'Q:\s*.+?\s*A:\s*.+?'
        return bool(re.search(pattern, content, re.IGNORECASE | re.DOTALL))

    def _extract_template_variables(self, content: str) -> List[str]:
        """Extract {{variable}} from content."""
        matches = re.findall(r'\{\{(\w+)\}\}', content)
        return list(set(matches))  # Deduplicate

    def _contains_template_variables(self, content: str) -> bool:
        """Check if content contains template variables."""
        return bool(re.search(r'\{\{\w+\}\}', content))

    def _infer_field_types(self, content: str, fields: List[str]) -> Dict[str, str]:
        """Infer field types from content context."""
        field_types = {}

        content_lower = content.lower()

        for field in fields:
            field_lower = field.lower()

            # Field-name based heuristics
            if any(keyword in field_lower for keyword in ['yes', 'no', 'interested', 'boolean']):
                field_types[field] = 'boolean'
                continue
            if any(keyword in field_lower for keyword in ['count', 'number', 'amount', 'year', 'pincode', 'age']):
                field_types[field] = 'number'
                continue

            # Check for enum indicators (options, choices)
            if re.search(r'\(.*\bor\b.*\)', content_lower):
                field_types[field] = 'enum'
            # Check for yes/no questions
            elif any(word in content_lower for word in ['yes', 'no', 'interested', 'agree']):
                field_types[field] = 'boolean'
            # Check for numeric indicators
            elif any(word in content_lower for word in ['number', 'amount', 'rupees', 'lakh', 'income']):
                field_types[field] = 'number'
            else:
                field_types[field] = 'string'

        return field_types

    def _build_flow_order(self, config: ParsedFlowConfig, flow_sequence: List[str]) -> List[str]:
        """Build execution order for sections."""
        flow_order = []

        for section_id in flow_sequence:
            if section_id in config.sections_by_id:
                flow_order.append(section_id)

        return flow_order

    def _link_sections(self, config: ParsedFlowConfig):
        """
        Link sections with next_section_id pointers.

        CRITICAL FIX: Properly implement conditional branching where YES/NO go to different sections.

        Sequential Inference Logic:
        - [Question] followed by [If YES] and [If NO]
        - [If YES] followed by [Section A] → YES branch goes to Section A
        - [If NO] followed by [Section B] → NO branch goes to Section B
        - Both branches eventually converge at a later section (merge point)

        IMPORTANT: Uses ALL sections (including objections) for target finding,
        not just flow_order.
        """
        flow_order = config.flow_order
        order_index = {section_id: idx for idx, section_id in enumerate(flow_order)}

        # Create list of ALL section IDs in parse order (dict keys preserve insertion order in Python 3.7+)
        all_section_ids = list(config.sections_by_id.keys())
        all_sections_index = {section_id: idx for idx, section_id in enumerate(all_section_ids)}

        # Step 1: Link non-condition sections sequentially (within flow_order)
        for idx, section_id in enumerate(flow_order):
            section = config.sections_by_id[section_id]

            if section.type == 'condition':
                # Defer linking for conditions; handled in Step 2
                continue

            next_id = flow_order[idx + 1] if idx + 1 < len(flow_order) else None
            section.next_section_id = next_id

        # Step 2: Link condition branches using sequential inference in ALL sections
        for parent_id, condition_ids in config.conditions_by_parent.items():
            if not condition_ids:
                continue

            # For each condition, find its branch target (next non-condition section in ALL sections)
            for cid in condition_ids:
                condition_section = config.sections_by_id[cid]
                condition_idx_in_all = all_sections_index.get(cid, -1)

                if condition_idx_in_all == -1:
                    continue

                # Find next non-condition, non-identity, non-guideline section as the branch target
                # Search in ALL sections (including objections), not just flow_order
                branch_target_id = None
                for next_idx in range(condition_idx_in_all + 1, len(all_section_ids)):
                    next_section_id = all_section_ids[next_idx]
                    next_section = config.sections_by_id[next_section_id]

                    # Valid targets: questions, pitches, objections (not identity/guideline/other conditions)
                    if next_section.type in ('question', 'pitch', 'objection'):
                        branch_target_id = next_section_id
                        break

                # Set the target based on condition type
                if condition_section.condition_type == 'yes':
                    condition_section.yes_target = branch_target_id
                elif condition_section.condition_type == 'no':
                    condition_section.no_target = branch_target_id

                condition_section.next_section_id = branch_target_id

            # Step 3: Find the merge point (post-condition section)
            # This is the section AFTER all branches from this parent have their targets
            last_condition_idx = max(order_index.get(cid, -1) for cid in condition_ids if cid in order_index)

            # Find the last branch target
            max_branch_target_idx = -1
            for cid in condition_ids:
                condition_section = config.sections_by_id[cid]
                target_id = condition_section.yes_target or condition_section.no_target
                if target_id and target_id in order_index:
                    target_idx = order_index[target_id]
                    max_branch_target_idx = max(max_branch_target_idx, target_idx)

            # Post-condition is the section after the last branch target
            post_condition_id = None
            if max_branch_target_idx != -1 and max_branch_target_idx + 1 < len(flow_order):
                post_condition_id = flow_order[max_branch_target_idx + 1]

            config.post_condition_by_parent[parent_id] = post_condition_id

            for cid in condition_ids:
                config.post_condition_by_condition[cid] = post_condition_id

        # Step 4: Handle standalone conditions (without parent)
        for condition in config.conditions:
            if condition.parent_section_id is None:
                condition_idx_in_all = all_sections_index.get(condition.id, -1)

                if condition_idx_in_all != -1:
                    # Find next valid target section in ALL sections
                    for next_idx in range(condition_idx_in_all + 1, len(all_section_ids)):
                        next_section_id = all_section_ids[next_idx]
                        next_section = config.sections_by_id[next_section_id]

                        if next_section.type in ('question', 'pitch', 'objection'):
                            if condition.condition_type == 'yes':
                                condition.yes_target = next_section_id
                            elif condition.condition_type == 'no':
                                condition.no_target = next_section_id

                            condition.next_section_id = next_section_id
                            break

    # ---------------------------------------------------------------------
    # Field extraction helpers
    # ---------------------------------------------------------------------

    def _extract_question_prompts(self, content: str) -> List[str]:
        """
        Extract English-language prompts/questions from mixed-language content.
        """
        prompts: List[str] = []

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Remove list markers
            line = re.sub(r'^[\-\*\u2022]+\s*', '', line)

            english_text = self._extract_english_text(line)
            if not english_text:
                # Skip pure non-Latin lines to avoid duplicating Hindi prompts
                if any('\u0900' <= ch <= '\u097F' for ch in line):
                    continue
                english_text = line

            if english_text.strip().lower().startswith('options'):
                # Skip option metadata before normalization
                continue

            english_text = english_text.strip().strip('"').strip()
            if not english_text:
                continue

            cleaned = self._normalize_prompt_text(english_text)
            if not cleaned:
                continue

            if cleaned.lower().startswith(('option', 'options')):
                # Treat as metadata for enum extraction, not a prompt
                continue

            prompts.append(cleaned)

        return prompts

    def _extract_english_text(self, line: str) -> str:
        """
        Extract English portion from bilingual lines using common patterns.
        """
        patterns = [
            r'^\*\*en\*\*\s*[–\-:]\s*(.+)$',
            r'^"en"\s*:\s*"(.+)"',
            r'^en\s*:\s*\\"?(.+?)\\"?$',
            r'^\[?en\]?\s*[:\-]\s*(.+)$'
        ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""

    def _normalize_prompt_text(self, text: str) -> str:
        """
        Trim filler tokens and whitespace.
        """
        cleaned = text.replace("<wait for response>", "").replace("<wait>", "")
        cleaned = re.sub(r'\*\*\w+\*\*\s*[–\-:]\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^\w+\s*:\s*', '', cleaned)
        cleaned = cleaned.replace('**', '')
        cleaned = re.sub(r'^(en|hi)\s*[–\-:]\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace('“', '"').replace('”', '"')
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def _derive_fields_from_content(
        self,
        section: ParsedSection,
        prompts: List[str],
        allow_empty: bool = False
    ) -> List[Dict[str, str]]:
        """
        Derive field metadata (name/type/description) from prompts.
        """
        derived: List[Dict[str, str]] = []

        questions = prompts or []

        if not questions and not allow_empty:
            questions = [section.section_name]

        for idx, prompt in enumerate(questions):
            field_name = self._derive_field_name(prompt, section, idx)
            base_name = field_name
            duplicate_counter = 2
            while any(item["field"] == field_name for item in derived):
                field_name = f"{base_name}_{duplicate_counter}"
                duplicate_counter += 1

            field_type = self._infer_field_type_for_prompt(prompt)
            derived.append(
                {
                    "field": field_name,
                    "type": field_type,
                    "description": prompt
                }
            )

        return derived

    def _derive_field_name(self, prompt: str, section: ParsedSection, index: int) -> str:
        """
        Generate a field name from the prompt text using heuristics.
        """
        prompt_lower = prompt.lower()

        heuristics = {
            "your name": "name",
            "name?": "name",
            "educational background": "educational_background",
            "background": "background",
            "preparation level": "preparation_level",
            "attempt": "exam_attempt_status",
            "attempted": "exam_attempt_status",
            "year are you planning": "target_exam_year",
            "which year": "target_exam_year",
            "course": "course_interest",
            "program": "program_preference",
            "online program": "program_mode_preference",
            "offline program": "program_mode_preference",
            "whatsapp": "whatsapp_number",
            "contact number": "contact_number",
            "phone number": "contact_number",
            "city": "city",
            "pincode": "pincode",
            "employment status": "employment_status",
            "work experience": "work_experience",
            "why": "objection_reason",
            "interested": "interest_level",
            "interest": "interest_level",
        }

        for key, value in heuristics.items():
            if key in prompt_lower:
                return value

        candidate = re.sub(r'[^a-z0-9]+', '_', prompt_lower).strip('_')
        candidate = re.sub(r'_{2,}', '_', candidate)

        if not candidate or len(candidate) < 3:
            candidate = f"{section.id}_{index + 1}"

        if len(candidate) > 40:
            candidate = candidate[:40].rstrip('_')

        return candidate

    def _infer_field_type_for_prompt(self, prompt: str) -> str:
        """
        Infer field type based on prompt keywords.
        """
        prompt_lower = prompt.lower()

        boolean_keywords = ['yes', 'no', 'interested', 'would you like', 'do you want', 'are you']
        numeric_keywords = ['how many', 'year', 'age', 'pincode', 'amount', 'rupee', 'fee', 'fees']

        if any(re.search(r'\b' + re.escape(keyword) + r'\b', prompt_lower) for keyword in boolean_keywords):
            return 'boolean'
        if any(re.search(r'\b' + re.escape(keyword) + r'\b', prompt_lower) for keyword in numeric_keywords):
            return 'number'

        return 'string'

    def _map_descriptions_to_fields(
        self,
        fields: List[str],
        prompts: List[str],
        default_description: str
    ) -> Dict[str, str]:
        """
        Map prompts to fields for description metadata.
        """
        descriptions: Dict[str, str] = {}

        for idx, field in enumerate(fields):
            if prompts and idx < len(prompts):
                descriptions[field] = prompts[idx]
            else:
                descriptions[field] = default_description

        return descriptions

    def _generate_fallback_field(self, section_name: str) -> str:
        candidate = re.sub(r'[^a-z0-9]+', '_', section_name.lower()).strip('_')
        if not candidate:
            candidate = "field"
        return candidate
