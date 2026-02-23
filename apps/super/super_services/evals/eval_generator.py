"""
Eval Generation Service
Generates QA pairs from agent configuration and knowledge base documents using OpenAI.
"""

import os
import json
import uuid
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import openai
import requests

from super_services.voice.models.config import ModelConfig
from super_services.db.services.models.agent_eval import (
    AgentQAPairModel,
    KBQAPairModel,
)


@dataclass
class QAPair:
    """Represents a single QA evaluation pair."""

    question: str
    answer: str
    is_first_message: bool
    intent: str
    tool_name: Optional[str]
    is_tool_call: bool
    eval_type: str = "general"
    source: Optional[str] = None
    language: Optional[str] = None


def _fetch_eval_info(gen_type, linked_handle, multi_fetch=False):
    from super_services.libs.core.db import executeQuery

    query = "SELECT * FROM knowledge_base_knowledgebaseevals WHERE eval_type=%s AND linked_handle=%s"
    params = (
        gen_type,
        linked_handle,
    )
    if multi_fetch and isinstance(linked_handle, list):
        placeholders = ",".join(["%s"] * len(linked_handle))
        query = f"SELECT * FROM knowledge_base_knowledgebaseevals WHERE eval_type=%s AND linked_handle IN ({placeholders})"
        params = (gen_type, *linked_handle)
    eval_info = executeQuery(
        query,
        params=params,
        many=multi_fetch,
    )
    print(eval_info)
    return eval_info


class EvalGenerator:
    """
    Generates QA evaluation pairs from agent configuration and knowledge base documents.
    Uses OpenAI for intelligent QA pair generation.
    """

    # OpenAI model to use for QA generation
    OPENAI_MODEL = "gpt-4o"

    # Agent evaluation types — 7 types × 5 pairs = 35 total
    AGENT_EVAL_TYPES = [
        "system_prompt_eval",
        "call_handover",
        "followup",
        "summary",
        "structured_data",
        "prompt_generation",
        "analytics_fields",
    ]

    # KB document evaluation types — 3 types × 3 pairs × num_pages
    KB_EVAL_TYPES = [
        "Introduction",
        "Q&A",
        "ObjectionHandling",
    ]

    AGENT_PAIRS_PER_TYPE = 5        # 7 × 5 = 35 agent pairs total
    KB_PAIRS_PER_TYPE_PER_PAGE = 3  # 3 × 3 × pages KB pairs per token
    KB_DEFAULT_PAIRS_TOTAL = 65     # fallback when KB has no documents

    def __init__(
        self,
        gen_type: str,
        agent_id: str,
        kn_token: str,
        logger,
        language: Optional[str] = None,
    ):
        self.gen_type = gen_type
        self.agent_id = agent_id
        self.kn_token = kn_token.split(",") if kn_token else None
        self.batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        self.openai_client = openai.AsyncClient(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger = logger
        self.languages = self._normalize_languages(language)
        self.language = self.languages[0]
        self.language_count = len(self.languages)
        self.formality = "formal"

    def _normalize_languages(self, language: Optional[str]) -> List[str]:
        normalized = (language or "").strip().lower()
        allowed = {
            "english": "English",
            "sanskrit": "Sanskrit",
            "malayalam": "Malayalam",
            "odia": "Odia",
            "kannada": "Kannada",
            "marathi": "Marathi",
            "gujarati": "Gujarati",
            "urdu": "Urdu",
            "telugu": "Telugu",
            "bengali": "Bengali",
            "tamil": "Tamil",
            "punjabi": "Punjabi",
            "hindi": "Hindi",
        }
        selected = allowed.get(normalized, "English")
        if selected == "English":
            return ["English"]
        return ["English", selected]

    def _get_existing_type_counts(
        self, eval_token: str, model
    ) -> Dict[Tuple[str, str], int]:
        """Return {(eval_type, language): count} for all active QA pairs."""
        try:
            pairs = list(model(eval_token).find(status="active"))
            counts: Dict[Tuple[str, str], int] = {}
            for qa in pairs:
                t = getattr(qa, "eval_type", None) or "unknown"
                lang = getattr(qa, "language", None) or "English"
                key = (t, lang)
                counts[key] = counts.get(key, 0) + 1
            return counts
        except Exception as e:
            self.logger.info(f"Error fetching type counts: {e}")
            return {}

    def _update_eval_status(
        self,
        eval_id: str,
        status: str,
        batch_id: str = None,
        batch_saved_count: int = 0,
        extra_metadata: dict = {},
    ):
        from super_services.libs.core.db import executeQuery

        """Update status of all QA pairs for this eval_token."""
        metadata = {}
        if status == "completed":
            metadata = {
                "last_batch_id": batch_id,
                "batch_saved_count": batch_saved_count,
            }
        if extra_metadata:
            metadata = {**metadata, **extra_metadata}
        query = "UPDATE knowledge_base_knowledgebaseevals SET gen_status = %s, WHERE id = %s"
        params = (
            status,
            eval_id,
        )
        if metadata:
            query = """
                UPDATE knowledge_base_knowledgebaseevals
                SET gen_status = %s,
                    eval_data = eval_data || %s
                WHERE id = %s
            """
            params = (
                status,
                json.dumps(metadata),
                eval_id,
            )
        executeQuery(query, params=params, commit=True)

    async def generate_all_evals(
        self, force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate all QA pairs for the agent (from config + knowledge base).
        Skips per eval_type if already generated (unless force_regenerate=True).

        Agent evals: 7 types × 5 pairs = 35 total
        KB evals: 3 types × 3 pairs × num_pages (or 65 default if no pages)

        Returns:
            Dict with generation statistics and per-type status
        """
        self.logger.info(f"Starting eval generation for agent: {self.agent_id}")

        results: Dict[str, Any] = {
            "batch_id": self.batch_id,
            "agent_qa_count": 0,
            "kb_qa_count": 0,
            "total_qa_count": 0,
            "skipped": [],
            "errors": [],
            "type_status": {
                "agent": {},
                "kb": {},
            },
        }

        gen_eval_kb = False
        if self.gen_type == "knowledgebase":
            gen_eval_kb = True
        elif self.gen_type == "pilot":
            gen_eval_kb = True
            agent_config = self._get_agent_config()
            if not agent_config:
                raise ValueError(f"Agent config not found for: {self.agent_id}")

            eval_config = _fetch_eval_info("pilot", self.agent_id)
            if not eval_config:
                raise ValueError(f"Eval config not found for: {self.agent_id}")

            eval_token = eval_config.get("eval_data", {}).get("space_token")
            eval_id = eval_config.get("id")
            if not eval_token:
                raise ValueError(f"Eval token not found for: {self.agent_id}")

            existing_type_counts = self._get_existing_type_counts(eval_token, AgentQAPairModel)
            total_existing = sum(existing_type_counts.values())

            all_types_complete = all(
                existing_type_counts.get(t, 0) >= self.AGENT_PAIRS_PER_TYPE
                for t in self.AGENT_EVAL_TYPES
            )

            if all_types_complete and not force_regenerate:
                skip_msg = f"All agent eval types complete ({total_existing} pairs) - skipping"
                self.logger.info(skip_msg)
                results["skipped"].append(skip_msg)
                results["agent_qa_count"] = total_existing
                results["type_status"]["agent"] = {
                    t: {
                        "action": "skipped",
                        "existing": existing_type_counts.get(t, 0),
                        "expected": self.AGENT_PAIRS_PER_TYPE,
                    }
                    for t in self.AGENT_EVAL_TYPES
                }
                self._update_eval_status(
                    eval_id, "completed", extra_metadata={"already_generated": True}
                )
            else:
                try:
                    agent_type_status: Dict[str, Any] = {}
                    agent_saved_total = 0

                    agent_qa_pairs_en, type_status = await self._generate_agent_qa_pairs(
                        agent_config,
                        existing_type_counts,
                        force_regenerate,
                        language="English",
                    )
                    saved_count_en = await self._save_agent_qa_pairs(
                        eval_token, agent_qa_pairs_en
                    )
                    agent_saved_total += saved_count_en
                    for t, info in type_status.items():
                        aggregate = agent_type_status.get(t, {"count": 0, "action": "skipped"})
                        if info.get("action") == "generated":
                            aggregate["count"] += info.get("count", 0)
                            aggregate["action"] = "generated"
                        agent_type_status[t] = aggregate

                    for language in self.languages:
                        if language == "English":
                            continue
                        translated_pairs = await self._translate_qa_pairs(
                            agent_qa_pairs_en, language
                        )
                        if not translated_pairs:
                            continue
                        self._apply_rule_based_fields(translated_pairs, source="agent")
                        saved_count = await self._save_agent_qa_pairs(
                            eval_token, translated_pairs
                        )
                        agent_saved_total += saved_count
                        for t in self.AGENT_EVAL_TYPES:
                            aggregate = agent_type_status.get(t, {"count": 0, "action": "skipped"})
                            aggregate["count"] += self.AGENT_PAIRS_PER_TYPE
                            aggregate["action"] = "generated"
                            agent_type_status[t] = aggregate

                    existing_totals = {
                        t: sum(existing_type_counts.get((t, lang), 0) for lang in self.languages)
                        for t in self.AGENT_EVAL_TYPES
                    }
                    results["agent_qa_count"] = total_existing + agent_saved_total
                    results["type_status"]["agent"] = {
                        t: {
                            "action": agent_type_status.get(t, {}).get("action", "skipped"),
                            "existing": existing_totals.get(t, 0),
                            "expected": self.AGENT_PAIRS_PER_TYPE * self.language_count,
                            "count": agent_type_status.get(t, {}).get("count", 0),
                        }
                        for t in self.AGENT_EVAL_TYPES
                    }
                    self._update_eval_status(
                        eval_id, "completed", results["batch_id"], agent_saved_total
                    )
                    self.logger.info(f"Generated {agent_saved_total} agent QA pairs")
                except Exception as e:
                    error_msg = f"Failed to generate agent QA pairs: {str(e)}"
                    self.logger.info(f"Error --> {error_msg}")
                    results["errors"].append(error_msg)

        if gen_eval_kb:
            print("Generating evals for knowledgebase")
            if not self.kn_token and self.gen_type == "knowledgebase":
                raise ValueError(
                    "Knowledge base token(s) required for knowledgebase eval type"
                )

            kb_list = self.kn_token if self.kn_token else []
            if not kb_list:
                print(f"No KB tokens found - generating {self.KB_DEFAULT_PAIRS_TOTAL} default KB evals")
                self.language = "English"
                default_kb_qa_pairs_en = await self._generate_default_kb_evals()
                all_default_pairs: List[QAPair] = list(default_kb_qa_pairs_en)
                for language in self.languages:
                    if language == "English":
                        continue
                    translated_pairs = await self._translate_qa_pairs(
                        default_kb_qa_pairs_en, language
                    )
                    if translated_pairs:
                        self._apply_rule_based_fields(translated_pairs, source="kb")
                        all_default_pairs.extend(translated_pairs)
                results["kb_qa_count"] = len(all_default_pairs)
                results["total_qa_count"] = results["agent_qa_count"] + results["kb_qa_count"]
                print(f"Generated {results['kb_qa_count']} default KB QA pairs")
                return results
            else:
                for kb_token in kb_list:
                    eval_config = _fetch_eval_info("knowledgebase", kb_token)
                    if not eval_config:
                        print(f"KB eval config not found for: {kb_token} - skipping")
                        continue

                    eval_token = eval_config.get("eval_data", {}).get("space_token")
                    eval_id = eval_config.get("id")
                    if not eval_token:
                        print(f"KB eval token not found for: {kb_token} - skipping")
                        continue

                    kb_name = eval_config.get("eval_name", kb_token)
                    kb_name = kb_name.replace("Evals", "").strip()

                    try:
                        documents = await self._fetch_kb_documents(kb_token)
                        num_pages = len(documents)
                        existing_type_counts = self._get_existing_type_counts(
                            eval_token, KBQAPairModel
                        )

                        if num_pages > 0:
                            expected_per_type = (
                                self.KB_PAIRS_PER_TYPE_PER_PAGE
                                * num_pages
                                * self.language_count
                            )
                            all_types_complete = all(
                                sum(
                                    existing_type_counts.get((t, lang), 0)
                                    for lang in self.languages
                                )
                                >= expected_per_type
                                for t in self.KB_EVAL_TYPES
                            )

                            if all_types_complete and not force_regenerate:
                                total_existing = sum(existing_type_counts.values())
                                skip_msg = f"KB '{kb_token}' all types complete ({total_existing} pairs) - skipping"
                                print(skip_msg)
                                results["skipped"].append(skip_msg)
                                results["kb_qa_count"] += total_existing
                                results["type_status"]["kb"][kb_token] = {
                                    t: {
                                        "action": "skipped",
                                        "existing": sum(
                                            existing_type_counts.get((t, lang), 0)
                                            for lang in self.languages
                                        ),
                                        "expected": expected_per_type,
                                    }
                                    for t in self.KB_EVAL_TYPES
                                }
                                self._update_eval_status(
                                    eval_id, "completed", extra_metadata={"already_generated": True}
                                )
                                continue

                            print(f"Found {num_pages} pages for KB: {kb_name}")
                            kb_type_status: Dict[str, Any] = {}
                            kb_saved_total = 0

                            kb_qa_pairs_en, type_status = await self._generate_kb_qa_pairs(
                                documents,
                                kb_name,
                                existing_type_counts,
                                force_regenerate,
                                language="English",
                            )
                            saved_count_en = await self._save_kb_qa_pairs(
                                eval_token, kb_qa_pairs_en
                            )
                            kb_saved_total += saved_count_en
                            for t, info in type_status.items():
                                aggregate = kb_type_status.get(t, {"count": 0, "action": "skipped"})
                                if info.get("action") == "generated":
                                    aggregate["count"] += info.get("count", 0)
                                    aggregate["action"] = "generated"
                                kb_type_status[t] = aggregate

                            for language in self.languages:
                                if language == "English":
                                    continue
                                translated_pairs = await self._translate_qa_pairs(
                                    kb_qa_pairs_en, language
                                )
                                if not translated_pairs:
                                    continue
                                self._apply_rule_based_fields(translated_pairs, source="kb")
                                saved_count = await self._save_kb_qa_pairs(
                                    eval_token, translated_pairs
                                )
                                kb_saved_total += saved_count
                                for t in self.KB_EVAL_TYPES:
                                    aggregate = kb_type_status.get(t, {"count": 0, "action": "skipped"})
                                    aggregate["count"] += (
                                        self.KB_PAIRS_PER_TYPE_PER_PAGE * len(documents)
                                    )
                                    aggregate["action"] = "generated"
                                    kb_type_status[t] = aggregate
                            results["kb_qa_count"] += kb_saved_total
                            results["type_status"]["kb"][kb_token] = {
                                t: {
                                    "action": kb_type_status.get(t, {}).get("action", "skipped"),
                                    "count": kb_type_status.get(t, {}).get("count", 0),
                                    "expected": expected_per_type,
                                    "existing": sum(
                                        existing_type_counts.get((t, lang), 0)
                                        for lang in self.languages
                                    ),
                                }
                                for t in self.KB_EVAL_TYPES
                            }
                            self._update_eval_status(
                                eval_id, "completed", results["batch_id"], kb_saved_total
                            )
                            print(
                                f"Generated {kb_saved_total} KB QA pairs for {kb_name} ({num_pages} pages)"
                            )
                        else:
                            # No pages → generate KB_DEFAULT_PAIRS_TOTAL default pairs
                            print(
                                f"No documents found in KB: {kb_name} - "
                                f"generating {self.KB_DEFAULT_PAIRS_TOTAL} default pairs"
                            )
                            self.language = "English"
                            default_pairs_en = await self._generate_default_kb_evals()
                            all_default_pairs: List[QAPair] = list(default_pairs_en)
                            for language in self.languages:
                                if language == "English":
                                    continue
                                translated_pairs = await self._translate_qa_pairs(
                                    default_pairs_en, language
                                )
                                if translated_pairs:
                                    self._apply_rule_based_fields(translated_pairs, source="kb")
                                    all_default_pairs.extend(translated_pairs)
                            if all_default_pairs:
                                saved_count = await self._save_kb_qa_pairs(
                                    eval_token, all_default_pairs
                                )
                                results["kb_qa_count"] += saved_count
                                self._update_eval_status(
                                    eval_id,
                                    "completed",
                                    results["batch_id"],
                                    saved_count,
                                    extra_metadata={
                                        "message": f"Generated {saved_count} default pairs (no documents)"
                                    },
                                )
                                print(f"Generated {saved_count} default KB QA pairs for {kb_name}")
                            else:
                                self._update_eval_status(
                                    eval_id,
                                    "completed",
                                    extra_metadata={"message": "No documents found in knowledge base"},
                                )
                    except Exception as e:
                        error_msg = f"Failed to generate KB QA pairs for {kb_name}: {str(e)}"
                        print(f"Error --> {error_msg}")
                        results["errors"].append(error_msg)

        results["total_qa_count"] = results["agent_qa_count"] + results["kb_qa_count"]
        results["eval_generation_status"] = self._build_eval_generation_status(
            results["type_status"]
        )
        self.logger.info(
            f"Eval generation complete. Total: {results['total_qa_count']} QA pairs"
        )

        return results

    def _build_eval_generation_status(
        self, type_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build per-type eval generation status for UI/API display
        from the type_status collected during generate_all_evals.
        """
        agent_types = type_status.get("agent", {})
        kb_types_by_token = type_status.get("kb", {})

        agent_type_list = []
        for t in self.AGENT_EVAL_TYPES:
            info = agent_types.get(t, {})
            current = info.get("existing", info.get("count", 0))
            complete = info.get("action") == "skipped" or current >= self.AGENT_PAIRS_PER_TYPE
            agent_type_list.append(
                {
                    "type": t,
                    "current": current,
                    "expected": self.AGENT_PAIRS_PER_TYPE * self.language_count,
                    "complete": complete,
                    "action": info.get("action", "pending"),
                }
            )
        agent_complete = all(t["complete"] for t in agent_type_list)

        kb_type_list = []
        for token_types in kb_types_by_token.values():
            for t, info in token_types.items():
                expected = info.get("expected", 0)
                current = info.get("existing", info.get("count", 0))
                complete = info.get("action") == "skipped" or current >= expected
                kb_type_list.append(
                    {
                        "type": t,
                        "current": current,
                        "expected": expected,
                        "complete": complete,
                        "action": info.get("action", "pending"),
                    }
                )
        kb_complete = all(t["complete"] for t in kb_type_list) if kb_type_list else True

        return {
            "agent_evals": {
                "types": agent_type_list,
                "expected_total": len(self.AGENT_EVAL_TYPES)
                * self.AGENT_PAIRS_PER_TYPE
                * self.language_count,
                "status": "complete" if agent_complete else "incomplete",
            },
            "kb_evals": {
                "types": kb_type_list,
                "status": "complete" if kb_complete else "incomplete",
            },
            "overall_status": "complete" if (agent_complete and kb_complete) else "incomplete",
        }

    def _get_agent_config(self) -> Optional[Dict[str, Any]]:
        """Fetch agent configuration using ModelConfig."""
        try:
            config = ModelConfig().get_config(self.agent_id)
            return config if config else None
        except Exception as e:
            self.logger.info(f"Error --> fetching agent config: {e}")
            return None

    async def _fetch_kb_documents(self, kb_token: str) -> List[Dict[str, Any]]:
        """
        Fetch all documents from a knowledge base.
        Uses the search service API to get all documents.
        """
        search_service_url = os.getenv("SEARCH_SERVICE_URL", "").rstrip("/")
        if not search_service_url:
            self.logger.warning("SEARCH_SERVICE_URL not configured")
            return []

        url = f"{search_service_url}/api/v1/search/query/docs/"
        payload = {
            "query": "file",  # Generic query to fetch all documents
            "kn_token": [kb_token],
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                docs = (
                    result.get("data", {})
                    .get("search_response_summary", {})
                    .get("top_sections", [])
                )
                self.logger.info(f"Fetched {len(docs)} documents from KB {kb_token}")
                return docs
            else:
                self.logger.warning(
                    f"Failed to fetch KB documents: {response.status_code}"
                )
                return []
        except Exception as e:
            self.logger.info(f"Error --> fetching KB documents: {e}")
            return []

    async def _generate_agent_qa_pairs(
        self,
        agent_config: Dict[str, Any],
        existing_counts: Dict[Tuple[str, str], int],
        force_regenerate: bool = False,
        language: str = "English",
    ) -> Tuple[List[QAPair], Dict[str, Any]]:
        """
        Generate agent QA pairs only for eval_types that are missing or incomplete.
        Skips any type that already has >= AGENT_PAIRS_PER_TYPE pairs.
        """
        self.language = language
        system_prompt = agent_config.get("system_prompt", "")
        persona = agent_config.get("persona", "")
        first_message = agent_config.get("first_message", "")

        all_qa_pairs: List[QAPair] = []
        type_status: Dict[str, Any] = {}

        for eval_type in self.AGENT_EVAL_TYPES:
            existing = existing_counts.get((eval_type, language), 0)
            if existing >= self.AGENT_PAIRS_PER_TYPE and not force_regenerate:
                type_status[eval_type] = {
                    "action": "skipped",
                    "existing": existing,
                    "expected": self.AGENT_PAIRS_PER_TYPE,
                    "language": language,
                }
                continue

            prompt = self._generate_agent_eval_prompt(
                eval_type, system_prompt, persona, first_message
            )
            qa_pairs = await self._call_openai_for_qa_pairs(
                prompt, max_pairs=self.AGENT_PAIRS_PER_TYPE, eval_type=eval_type
            )
            self._apply_rule_based_fields(qa_pairs, source="agent")
            all_qa_pairs.extend(qa_pairs)
            type_status[eval_type] = {
                "action": "generated",
                "count": len(qa_pairs),
                "expected": self.AGENT_PAIRS_PER_TYPE,
                "language": language,
            }

        return all_qa_pairs, type_status

    def _generate_agent_eval_prompt(
        self, eval_type: str, system_prompt: str, persona: str, first_message: str
    ) -> str:
        """Generate specialized prompt for agent evaluation types."""

        language_line = f"Write the question and answer in {self.language}."

        prompts = {
            "system_prompt_eval": f"""You are an expert at generating system prompt evaluation questions for voice agents.

Given the agent configuration:
**System Prompt:** {system_prompt}
**Persona:** {persona}
**Greeting Message:** {first_message}

Generate exactly 5 question-answer pairs that test SYSTEM PROMPT EVALUATION. Include:
1. Questions about agent's behavior based on system prompt
2. Questions about agent's instructions and rules
3. Questions about agent's operational boundaries
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{{"question": "What are your instructions?", "answer": "Based on my system prompt...", "is_first_message": false, "intent": "understand system capabilities", "tool_name": null, "is_tool_call": false}}]""",

            "call_handover": f"""You are an expert at generating call handover evaluation questions for voice agents.

Given the agent configuration:
**System Prompt:** {system_prompt}
**Persona:** {persona}
**Greeting Message:** {first_message}

Generate exactly 5 question-answer pairs that test CALL HANDOVER scenarios. Include:
1. Requests to speak to human agent
2. Complex issues requiring escalation
3. Emergency situations
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{{"question": "Can I speak to a human?", "answer": "I can transfer you...", "is_first_message": false, "intent": "request human agent", "tool_name": null, "is_tool_call": false}}]""",

            "followup": f"""You are an expert at generating follow-up evaluation questions for voice agents.

Given the agent configuration:
**System Prompt:** {system_prompt}
**Persona:** {persona}
**Greeting Message:** {first_message}

Generate exactly 5 question-answer pairs that test FOLLOW-UP capabilities. Include:
1. Questions about scheduling follow-ups
2. Questions about callback requests
3. Questions about ongoing support
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{{"question": "Can you call me back?", "answer": "I can schedule...", "is_first_message": false, "intent": "request callback", "tool_name": null, "is_tool_call": false}}]""",

            "summary": f"""You are an expert at generating summary evaluation questions for voice agents.

Given the agent configuration:
**System Prompt:** {system_prompt}
**Persona:** {persona}
**Greeting Message:** {first_message}

Generate exactly 5 question-answer pairs that test SUMMARY capabilities. Include:
1. Questions about summarizing conversations
2. Questions about key points extraction
3. Questions about conversation overview
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{{"question": "Can you summarize our conversation?", "answer": "To summarize...", "is_first_message": false, "intent": "request summary", "tool_name": null, "is_tool_call": false}}]""",

            "structured_data": f"""You are an expert at generating structured data evaluation questions for voice agents.

Given the agent configuration:
**System Prompt:** {system_prompt}
**Persona:** {persona}
**Greeting Message:** {first_message}

Generate exactly 5 question-answer pairs that test STRUCTURED DATA extraction. Include:
1. Questions about form filling
2. Questions about information collection
3. Questions about data validation
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{{"question": "Can you help me fill this form?", "answer": "I can help you collect...", "is_first_message": false, "intent": "request form filling", "tool_name": null, "is_tool_call": false}}]""",

            "prompt_generation": f"""You are an expert at generating prompt generation evaluation questions for voice agents.

Given the agent configuration:
**System Prompt:** {system_prompt}
**Persona:** {persona}
**Greeting Message:** {first_message}

Generate exactly 5 question-answer pairs that test PROMPT GENERATION. Include:
1. Questions about creating prompts
2. Questions about template generation
3. Questions about content creation
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{{"question": "Can you help me write a message?", "answer": "I can help you create...", "is_first_message": false, "intent": "request content creation", "tool_name": null, "is_tool_call": false}}]""",

            "analytics_fields": f"""You are an expert at generating analytics evaluation questions for voice agents.

Given the agent configuration:
**System Prompt:** {system_prompt}
**Persona:** {persona}
**Greeting Message:** {first_message}

Generate exactly 5 question-answer pairs that test ANALYTICS capabilities. Include:
1. Questions about metrics and measurements
2. Questions about performance data
3. Questions about usage statistics
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{{"question": "What are my usage statistics?", "answer": "Based on my analytics...", "is_first_message": false, "intent": "request analytics data", "tool_name": null, "is_tool_call": false}}]""",
        }

        return prompts.get(eval_type, prompts["system_prompt_eval"])

    def _infer_intent(self, question: str, answer: str) -> str:
        text = f"{question} {answer}".lower()
        question_text = question.lower()

        greet_re = r"\b(hi|hello|hey|namaste|good morning|good afternoon|good evening)\b"
        end_re = r"\b(bye|goodbye|see you|take care|end the call|hang up|that's all|thank you,? bye)\b"
        handover_re = r"\b(human|agent|representative|supervisor|manager|escalate|transfer)\b"
        callback_re = r"\b(call back|callback|call me back|schedule|reschedule|follow up|follow-up|call later|later today|tomorrow)\b"
        record_info_re = (
            r"\b(my name is|i am|i'm|call me|reach me at|my email|my phone|my number|"
            r"my contact|my address|preferred time|available at)\b"
        )

        if re.search(greet_re, question_text):
            return "greet the user"
        if re.search(end_re, text):
            return "end the call"
        if re.search(handover_re, text):
            return "handover to human agent"
        if re.search(callback_re, text):
            return "schedule callback"
        if re.search(record_info_re, text):
            return "record user information"
        return "answer user query using knowledge base"

    def _infer_is_first_message(self, question: str, answer: str, intent: str) -> bool:
        if intent == "greet the user":
            return True
        greet_re = r"\b(hi|hello|hey|namaste|good morning|good afternoon|good evening)\b"
        if re.search(greet_re, question.lower()):
            return True
        if re.search(greet_re, answer.lower()):
            return True
        return False

    def _infer_tool_call(
        self, question: str, answer: str, intent: str
    ) -> Tuple[bool, Optional[str]]:
        text = f"{question} {answer}".lower()

        tool_rules = [
            ("voicemail_detector", r"\b(voicemail|answering machine|leave a message|beep)\b"),
            ("handover_tool", r"\b(human|agent|representative|supervisor|manager|escalate|transfer)\b"),
            ("get_past_calls", r"\b(previous call|past call|last call|earlier conversation|last time)\b"),
            ("create_followup_or_callback", r"\b(call back|callback|call me back|schedule|reschedule|follow up|follow-up|call later|later today|tomorrow)\b"),
            ("end_call", r"\b(bye|goodbye|see you|take care|end the call|hang up|that's all|thank you,? bye)\b"),
            ("record_user_info", r"\b(my name is|i am|i'm|call me|reach me at|my email|my phone|my number|my contact|my address|preferred time|available at)\b"),
            ("report_breakdown", r"\b(repeat|didn't understand|did not understand|misunderstood|confused|what did you say)\b"),
            ("mark_objective_achieved", r"\b(booked|confirmed|agreed|signed up|registered|payment done|done with it)\b"),
            ("mark_topic_covered", r"\b(covered|we discussed|we talked about|that answers|topic covered)\b"),
        ]

        for tool_name, pattern in tool_rules:
            if re.search(pattern, text):
                return True, tool_name

        if intent == "answer user query using knowledge base":
            return True, "get_docs"

        return False, None

    def _apply_rule_based_fields(self, qa_pairs: List[QAPair], source: str) -> None:
        for qa in qa_pairs:
            intent = self._infer_intent(qa.question, qa.answer)
            qa.intent = intent
            qa.is_first_message = self._infer_is_first_message(
                qa.question, qa.answer, intent
            )
            qa.is_tool_call, qa.tool_name = self._infer_tool_call(
                qa.question, qa.answer, intent
            )
            qa.source = source
            qa.language = self.language

    async def _generate_default_kb_evals(self) -> List[QAPair]:
        """
        Generate default KB evaluation pairs when no documents are available.
        Creates KB_DEFAULT_PAIRS_TOTAL pairs for comprehensive coverage.
        """
        all_qa_pairs: List[QAPair] = []

        for eval_type in self.KB_EVAL_TYPES:
            prompt = self._generate_default_kb_prompt(eval_type)

            try:
                qa_pairs = await self._call_openai_for_qa_pairs(
                    prompt, max_pairs=10, eval_type=eval_type
                )
                self._apply_rule_based_fields(qa_pairs, source="kb")
                all_qa_pairs.extend(qa_pairs)
                print(f"Generated {len(qa_pairs)} default {eval_type} QA pairs")

                # Add additional pairs for variety to reach KB_DEFAULT_PAIRS_TOTAL
                if len(all_qa_pairs) < self.KB_DEFAULT_PAIRS_TOTAL:
                    additional_pairs = await self._call_openai_for_qa_pairs(
                        prompt, max_pairs=5, eval_type=eval_type
                    )
                    self._apply_rule_based_fields(additional_pairs, source="kb")
                    all_qa_pairs.extend(additional_pairs)
                    print(f"Generated {len(additional_pairs)} additional {eval_type} QA pairs")
            except Exception as e:
                self.logger.warning(f"Failed to generate default {eval_type} QA pairs: {e}")
                continue

        return all_qa_pairs

    def _generate_default_kb_prompt(self, eval_type: str) -> str:
        """Generate default prompt for KB evaluation types when no documents exist."""

        language_line = f"Write the question and answer in {self.language}."

        prompts = {
            "Introduction": f"""You are an expert at generating introduction evaluation questions for voice agents.

Generate exactly 10 question-answer pairs that test INTRODUCTION capabilities. Include:
1. Questions about agent introduction and identity
2. Questions about agent purpose and role
3. Questions about greeting scenarios
4. Questions about initial interactions
5. Questions about agent background
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{"question": "Who are you?", "answer": "I am...", "is_first_message": true, "intent": "greet the user", "tool_name": null, "is_tool_call": false}]""",

            "Q&A": f"""You are an expert at generating Q&A evaluation pairs for voice agents.

Generate exactly 10 question-answer pairs that test Q&A SCENARIOS. Include:
1. Questions about common user queries
2. Questions about frequently asked topics
3. Questions about typical conversations
4. Questions about information requests
5. Questions about general inquiries
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{"question": "What can you help with?", "answer": "I can help you with...", "is_first_message": false, "intent": "ask about capabilities", "tool_name": null, "is_tool_call": false}]""",

            "ObjectionHandling": f"""You are an expert at generating objection handling evaluation questions for voice agents.

Generate exactly 10 question-answer pairs that test OBJECTION HANDLING. Include:
1. Questions about user concerns
2. Questions about handling objections
3. Questions about resolving issues
4. Questions about addressing complaints
5. Questions about managing resistance
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{"question": "What if I don't want to proceed?", "answer": "I understand your concern...", "is_first_message": false, "intent": "express hesitation", "tool_name": null, "is_tool_call": false}]""",
        }

        return prompts.get(eval_type, prompts["Introduction"])

    async def _generate_kb_qa_pairs(
        self,
        documents: List[Dict[str, Any]],
        kb_name: str,
        existing_counts: Dict[Tuple[str, str], int],
        force_regenerate: bool = False,
        language: str = "English",
    ) -> Tuple[List[QAPair], Dict[str, Any]]:
        """
        Generate KB QA pairs only for eval_types that are missing or incomplete.
        Expected per type = KB_PAIRS_PER_TYPE_PER_PAGE × num_pages.
        """
        self.language = language
        all_qa_pairs: List[QAPair] = []
        num_pages = len(documents)
        expected_per_type = self.KB_PAIRS_PER_TYPE_PER_PAGE * num_pages
        type_status: Dict[str, Any] = {}

        for eval_type in self.KB_EVAL_TYPES:
            existing = existing_counts.get((eval_type, language), 0)
            if existing >= expected_per_type and not force_regenerate:
                type_status[eval_type] = {
                    "action": "skipped",
                    "existing": existing,
                    "expected": expected_per_type,
                    "language": language,
                }
                continue

            type_pairs: List[QAPair] = []
            for doc in documents:
                content = doc.get("content", "")
                if not content or len(content.strip()) < 50:
                    continue

                if len(content) > 8000:
                    content = content[:8000] + "..."

                prompt = self._generate_kb_eval_prompt(eval_type, content, kb_name)
                try:
                    qa_pairs = await self._call_openai_for_qa_pairs(
                        prompt,
                        max_pairs=self.KB_PAIRS_PER_TYPE_PER_PAGE,
                        eval_type=eval_type,
                    )
                    self._apply_rule_based_fields(qa_pairs, source="kb")
                    type_pairs.extend(qa_pairs)
                except Exception as e:
                    self.logger.warning(f"Failed to generate QA for document: {e}")
                    continue

            all_qa_pairs.extend(type_pairs)
            type_status[eval_type] = {
                "action": "generated",
                "count": len(type_pairs),
                "expected": expected_per_type,
                "language": language,
            }

        return all_qa_pairs, type_status

    def _generate_kb_eval_prompt(
        self, eval_type: str, content: str, kb_name: str
    ) -> str:
        """Generate specialized prompt for KB document evaluation types."""

        language_line = f"Write the question and answer in {self.language}."

        prompts = {
            "Introduction": f"""You are an expert at extracting introduction evaluation questions from documents.

Given the following document from knowledge base "{kb_name}":
---
{content}
---

Generate exactly 3 question-answer pairs that test INTRODUCTION content. Include:
1. Questions about overview information
2. Questions about background context
3. Questions about purpose and scope
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{{"question": "What is this about?", "answer": "This document covers...", "is_first_message": false, "intent": "ask about document overview", "tool_name": null, "is_tool_call": false}}]""",

            "Q&A": f"""You are an expert at extracting Q&A evaluation pairs from documents.

Given the following document from knowledge base "{kb_name}":
---
{content}
---

Generate exactly 3 question-answer pairs that test Q&A SCENARIOS. Include:
1. Questions about common queries
2. Questions about frequently asked topics
3. Questions about typical user questions
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{{"question": "What are common questions?", "answer": "Based on document...", "is_first_message": false, "intent": "ask about common questions", "tool_name": null, "is_tool_call": false}}]""",

            "ObjectionHandling": f"""You are an expert at extracting objection handling scenarios from documents.

Given the following document from knowledge base "{kb_name}":
---
{content}
---

Generate exactly 3 question-answer pairs that test OBJECTION HANDLING. Include:
1. Questions about addressing concerns
2. Questions about handling objections
3. Questions about resolving issues
{language_line}

For each pair, also generate:
- is_first_message: boolean (true if this is the first message)
- intent: string (describing the user's intent)
- tool_name: string or null (name of tool if applicable)
- is_tool_call: boolean (true if this involves a tool call)

Output ONLY a valid JSON array:
[{{"question": "What if there's an issue?", "answer": "The document suggests...", "is_first_message": false, "intent": "express concern", "tool_name": null, "is_tool_call": false}}]""",
        }

        return prompts.get(eval_type, prompts["Introduction"])

    async def _call_openai_for_qa_pairs(
        self, prompt: str, max_pairs: int = 50, eval_type: str = "general"
    ) -> List[QAPair]:
        """
        Call OpenAI to generate QA pairs from a prompt.
        """
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates Q&A evaluation pairs. Always output valid JSON arrays only, with no additional text or formatting.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=4000,
            )

            content = response.choices[0].message.content
            if not content:
                return []

            # Clean up the response (remove markdown code blocks if present)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            qa_data = json.loads(content)

            if not isinstance(qa_data, list):
                self.logger.warning("OpenAI response is not a list")
                return []

            qa_pairs = []
            for item in qa_data[:max_pairs]:
                if isinstance(item, dict) and "question" in item and "answer" in item:
                    qa_pairs.append(
                        QAPair(
                            question=item["question"],
                            answer=item["answer"],
                            is_first_message=item.get("is_first_message", False),
                            intent=item.get("intent", ""),
                            tool_name=item.get("tool_name"),
                            is_tool_call=item.get("is_tool_call", False),
                            eval_type=eval_type,
                        )
                    )

            return qa_pairs

        except json.JSONDecodeError as e:
            self.logger.info(f"Failed to parse OpenAI response as JSON: {e}")
            return []
        except Exception as e:
            self.logger.info(f"OpenAI API error: {e}")
            raise

    async def _translate_qa_pairs(
        self, qa_pairs: List[QAPair], target_language: str
    ) -> List[QAPair]:
        if not qa_pairs:
            return []

        formality_note = "Use formal register (e.g., Hindi 'aap')."
        if target_language.lower() != "hindi":
            formality_note = "Use formal, respectful register."

        items = [
            {"question": qa.question, "answer": qa.answer}
            for qa in qa_pairs
        ]

        prompt = (
            f"Translate the following Q&A pairs from English to {target_language}. "
            "Preserve meaning exactly. Do not add or remove questions. "
            f"{formality_note} Output ONLY a valid JSON array with the same length "
            'and objects of shape {"question": "...", "answer": "..."}.\n\n'
            f"{json.dumps(items, ensure_ascii=False)}"
        )

        response = await self.openai_client.chat.completions.create(
            model=self.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise translator. "
                        "Output only valid JSON arrays, no extra text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=4000,
        )

        content = response.choices[0].message.content or ""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            translated = json.loads(content)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse translation JSON")
            return []

        if not isinstance(translated, list):
            return []

        translated_pairs: List[QAPair] = []
        for original, item in zip(qa_pairs, translated):
            if not isinstance(item, dict):
                continue
            q = item.get("question")
            a = item.get("answer")
            if not isinstance(q, str) or not isinstance(a, str):
                continue
            translated_pairs.append(
                QAPair(
                    question=q.strip(),
                    answer=a.strip(),
                    is_first_message=original.is_first_message,
                    intent=original.intent,
                    tool_name=original.tool_name,
                    is_tool_call=original.is_tool_call,
                    eval_type=original.eval_type,
                    source=original.source,
                    language=target_language,
                )
            )

        return translated_pairs

    async def _save_agent_qa_pairs(self, eval_token: str, qa_pairs: List[QAPair]) -> int:
        """
        Save Agent QA pairs to agent_qa_pairs collection.

        Returns:
            Number of QA pairs saved
        """
        final_data = [
            {
                "question": qa.question,
                "answer": qa.answer,
                "eval_type": qa.eval_type,
                "intent": qa.intent,
                "is_first_message": qa.is_first_message,
                "is_tool_call": qa.is_tool_call,
                "tool_name": qa.tool_name,
                "source": qa.source,
                "language": qa.language,
                "keywords": [],
                "status": "active",
                "batch_id": self.batch_id,
            }
            for qa in qa_pairs
        ]
        saved_results = AgentQAPairModel(eval_token).save_many_to_db(final_data)
        return len(saved_results)

    async def _save_kb_qa_pairs(self, eval_token: str, qa_pairs: List[QAPair]) -> int:
        """
        Save KB QA pairs to kb_qa_pairs collection.

        Returns:
            Number of QA pairs saved
        """
        final_data = [
            {
                "question": qa.question,
                "answer": qa.answer,
                "eval_type": qa.eval_type,
                "intent": qa.intent,
                "is_first_message": qa.is_first_message,
                "is_tool_call": qa.is_tool_call,
                "tool_name": qa.tool_name,
                "source": qa.source,
                "language": qa.language,
                "keywords": [],
                "status": "active",
                "batch_id": self.batch_id,
            }
            for qa in qa_pairs
        ]
        saved_results = KBQAPairModel(eval_token).save_many_to_db(final_data)
        return len(saved_results)


def get_agent_qa_pairs(agent_id: str) -> List[Dict[str, Any]]:
    """
    Get all active QA pairs from agent_qa_pairs collection.

    Returns:
        List of QA pair dictionaries with question, answer, keywords
    """
    try:
        eval_config = _fetch_eval_info("pilot", agent_id)
        if not eval_config:
            return []
        eval_token = eval_config.get("eval_data", {}).get("space_token")
        qa_pairs: List[AgentQAPairModel.Meta.model] = list(
            AgentQAPairModel(eval_token).find(status="active")
        )

        return [
            {
                "question": qa.question,
                "answer": qa.answer,
                "keywords": qa.keywords,
                "eval_type": qa.eval_type,
                "intent": qa.intent,
                "is_first_message": qa.is_first_message,
                "is_tool_call": getattr(qa, "is_tool_call", False),
                "tool_name": getattr(qa, "tool_name", None),
                "source": getattr(qa, "source", "agent") or "agent",
                "language": getattr(qa, "language", "English") or "English",
            }
            for qa in qa_pairs
        ]
    except Exception as e:
        print(f"Error fetching agent QA pairs: {e}")
        return []


def get_kb_qa_pairs(agent_id: str, kb_token: str = None) -> List[Dict[str, Any]]:
    """
    Get all active QA pairs from kb_qa_pairs collection.

    Args:
        agent_id: Agent handle
        kb_token: Optional KB token to filter by specific knowledge base

    Returns:
        List of QA pair dictionaries with question, answer, keywords
    """
    try:
        if not kb_token:
            agent_config = ModelConfig().get_config(agent_id)
            if not agent_config:
                return []
            knowledge_base = agent_config.get("knowledge_base")
            if not knowledge_base:
                return []
        else:
            knowledge_base = [{"token": kb_token}]
        kn_tokens = [kb["token"] for kb in knowledge_base]
        evals_config = _fetch_eval_info("knowledgebase", kn_tokens, multi_fetch=True)
        all_pairs = []
        for eval_config in evals_config:
            eval_token = eval_config.get("eval_data", {}).get("space_token")
            linked_handle = eval_config.get("linked_handle")
            qa_pairs: List[KBQAPairModel.Meta.model] = list(
                KBQAPairModel(eval_token).find(status="active")
            )
            for qa in qa_pairs:
                all_pairs.append(
                    {
                        "question": qa.question,
                        "answer": qa.answer,
                        "keywords": qa.keywords,
                        "eval_type": qa.eval_type,
                        "intent": qa.intent,
                        "is_first_message": qa.is_first_message,
                        "is_tool_call": getattr(qa, "is_tool_call", False),
                        "tool_name": getattr(qa, "tool_name", None),
                        "source": getattr(qa, "source", "kb") or "kb",
                        "language": getattr(qa, "language", "English") or "English",
                        "kn_token": linked_handle,
                    }
                )
        return all_pairs
    except Exception as e:
        print(f"Error fetching KB QA pairs: {e}")
        return []


def get_all_qa_pairs_for_agent(agent_id: str) -> List[Dict[str, Any]]:
    """
    Get all active QA pairs (both agent and KB) for an agent.

    Returns:
        Combined list of QA pairs from both collections
    """
    agent_pairs = get_agent_qa_pairs(agent_id)
    kb_pairs = get_kb_qa_pairs(agent_id)
    return agent_pairs + kb_pairs
