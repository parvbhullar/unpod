"""
Eval Generation Service
Generates QA pairs from agent configuration and knowledge base documents using OpenAI.
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional
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
    keywords: List[str]


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

    AGENT_QA_COUNT = 20  # Number of QA pairs to generate for agent config

    # OpenAI model to use for QA generation
    OPENAI_MODEL = "gpt-4o"

    def __init__(self, gen_type: str, agent_id: str, kn_token: str, logger):
        self.gen_type = gen_type
        self.agent_id = agent_id
        self.kn_token = kn_token.split(",") if kn_token else None
        self.batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        self.openai_client = openai.AsyncClient(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger = logger

    def _agent_qa_pairs_exist(self, eval_token) -> int:
        """Check if QA pairs already exist for this agent_id."""
        try:
            count = AgentQAPairModel(eval_token).count(status="active")
            return count
        except Exception as e:
            self.logger.info(f"Error checking agent QA pairs: {e}")
            return 0

    def _kb_qa_pairs_exist(self, eval_token: str) -> int:
        """Check if QA pairs already exist for this kb_token."""
        try:
            count = KBQAPairModel(eval_token).count(status="active")
            return count
        except Exception as e:
            self.logger.info(f"Error checking KB QA pairs: {e}")
            return 0

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
        Skips generation if QA pairs already exist (unless force_regenerate=True).

        Args:
            force_regenerate: If True, regenerate even if QA pairs already exist

        Returns:
            Dict with generation statistics
        """
        self.logger.info(f"Starting eval generation for agent: {self.agent_id}")

        # Fetch agent config
        results = {
            "batch_id": self.batch_id,
            "agent_qa_count": 0,
            "kb_qa_count": 0,
            "total_qa_count": 0,
            "skipped": [],
            "errors": [],
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

            # Check if agent QA pairs already exist
            existing_agent_qa = self._agent_qa_pairs_exist(eval_token)
            if existing_agent_qa > 0 and not force_regenerate:
                skip_msg = f"Agent QA pairs already exist ({existing_agent_qa} pairs) - skipping generation"
                self.logger.info(skip_msg)
                results["skipped"].append(skip_msg)
                results["agent_qa_count"] = existing_agent_qa
                self._update_eval_status(
                    eval_id, "completed", extra_metadata={"already_generated": True}
                )
            else:
                # Generate QA pairs from agent config and save to agent_qa_pairs collection
                try:
                    agent_qa_pairs = await self._generate_agent_qa_pairs(agent_config)
                    saved_count = await self._save_agent_qa_pairs(
                        eval_token, agent_qa_pairs
                    )
                    results["agent_qa_count"] = saved_count
                    self._update_eval_status(
                        eval_id, "completed", results["batch_id"], saved_count
                    )
                    self.logger.info(f"Generated {saved_count} agent QA pairs")
                except Exception as e:
                    error_msg = f"Failed to generate agent QA pairs: {str(e)}"
                    self.logger.info(f"Error --> {error_msg}")
                    results["errors"].append(error_msg)

        # Generate QA pairs from knowledge base documents and save to kb_qa_pairs collection
        if gen_eval_kb:
            print("Generating evals for knowledgebase")
            if not self.kn_token and self.gen_type == "knowledgebase":
                raise ValueError(
                    "Knowledge base token(s) required for knowledgebase eval type"
                )
            kb_list = self.kn_token
            for kb_token in kb_list:
                eval_config = _fetch_eval_info("knowledgebase", kb_token)
                if not eval_config:
                    raise ValueError(
                        f"Eval config not found for knowledgebase: {kb_token}"
                    )

                eval_token = eval_config.get("eval_data", {}).get("space_token")
                eval_id = eval_config.get("id")
                if not eval_token:
                    raise ValueError(
                        f"Eval token not found for knowledgebase: {kb_token}"
                    )
                kb_name = eval_config.get("eval_name")
                kb_name = kb_name.replace("Evals", "").strip()
                existing_kb_qa = self._kb_qa_pairs_exist(eval_token)
                if existing_kb_qa > 0 and not force_regenerate:
                    skip_msg = f"KB '{kb_token}' QA pairs already exist ({existing_kb_qa} pairs) - skipping"
                    self.logger.info(skip_msg)
                    results["skipped"].append(skip_msg)
                    results["kb_qa_count"] += existing_kb_qa
                    self._update_eval_status(
                        eval_id, "completed", extra_metadata={"already_generated": True}
                    )
                    continue

                try:
                    documents = await self._fetch_kb_documents(kb_token)
                    if documents:
                        kb_qa_pairs = await self._generate_kb_qa_pairs(
                            documents, kb_name
                        )
                        saved_count = await self._save_kb_qa_pairs(
                            eval_token, kb_qa_pairs
                        )
                        results["kb_qa_count"] += saved_count
                        self._update_eval_status(
                            eval_id, "completed", results["batch_id"], saved_count
                        )
                        self.logger.info(
                            f"Generated {saved_count} KB QA pairs for {kb_name}"
                        )
                    else:
                        self._update_eval_status(
                            eval_id,
                            "completed",
                            extra_metadata={
                                "message": "No documents found in knowledge base"
                            },
                        )
                except Exception as e:
                    error_msg = (
                        f"Failed to generate KB QA pairs for {kb_name}: {str(e)}"
                    )
                    self.logger.info(f"Error --> {error_msg}")
                    results["errors"].append(error_msg)

        results["total_qa_count"] = results["agent_qa_count"] + results["kb_qa_count"]
        self.logger.info(
            f"Eval generation complete. Total: {results['total_qa_count']} QA pairs"
        )

        return results

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
        self, agent_config: Dict[str, Any]
    ) -> List[QAPair]:
        """
        Generate QA pairs from agent configuration.
        Uses system_prompt, persona, and greeting message.
        """
        system_prompt = agent_config.get("system_prompt", "")
        persona = agent_config.get("persona", "")
        first_message = agent_config.get("first_message", "")

        prompt = f"""You are an expert at generating Q&A evaluation pairs for voice agents.

Given the following agent configuration:

**System Prompt:**
{system_prompt}

**Persona:**
{persona}

**Greeting Message:**
{first_message}

Generate exactly {self.AGENT_QA_COUNT} diverse question-answer pairs that test the agent's capabilities. Include:
1. Questions about the agent's core functionality
2. Edge cases and boundary scenarios
3. Common user queries the agent should handle
4. Questions that test the agent's knowledge boundaries

For each pair, also generate 3-5 relevant keywords that would help identify when a user is asking this question.

Output ONLY a valid JSON array with this exact format (no markdown, no code blocks):
[
    {{"question": "What is...", "answer": "The answer is...", "keywords": ["keyword1", "keyword2", "keyword3"]}},
    ...
]"""

        return await self._call_openai_for_qa_pairs(
            prompt, max_pairs=self.AGENT_QA_COUNT
        )

    async def _generate_kb_qa_pairs(
        self, documents: List[Dict[str, Any]], kb_name: str
    ) -> List[QAPair]:
        """
        Generate QA pairs from knowledge base documents.
        Processes each document and generates all possible questions.
        """
        all_qa_pairs: List[QAPair] = []

        for doc in documents:
            content = doc.get("content", "")
            if not content or len(content.strip()) < 50:
                continue

            # Truncate very long documents
            if len(content) > 8000:
                content = content[:8000] + "..."

            prompt = f"""You are an expert at extracting Q&A pairs from documents for evaluation purposes.

Given the following document from knowledge base "{kb_name}":

---
{content}
---

Generate ALL possible question-answer pairs that cover the information in this document. Include:
1. Every fact, statistic, or data point mentioned
2. Procedures, processes, or how-to information
3. Definitions and explanations
4. Relationships between concepts
5. Any policies, rules, or guidelines mentioned

For each pair, generate 3-5 relevant keywords.

Output ONLY a valid JSON array with this exact format (no markdown, no code blocks):
[
    {{"question": "What is...", "answer": "The answer is...", "keywords": ["keyword1", "keyword2", "keyword3"]}},
    ...
]"""

            try:
                qa_pairs = await self._call_openai_for_qa_pairs(prompt, max_pairs=50)
                all_qa_pairs.extend(qa_pairs)
            except Exception as e:
                self.logger.warning(f"Failed to generate QA for document: {e}")
                continue

        return all_qa_pairs

    async def _call_openai_for_qa_pairs(
        self, prompt: str, max_pairs: int = 50
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

            # Parse JSON
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
                            keywords=item.get("keywords", []),
                        )
                    )

            return qa_pairs

        except json.JSONDecodeError as e:
            self.logger.info(f"Failed to parse OpenAI response as JSON: {e}")
            return []
        except Exception as e:
            self.logger.info(f"OpenAI API error: {e}")
            raise

    async def _save_agent_qa_pairs(self, eval_token, qa_pairs: List[QAPair]) -> int:
        """
        Save Agent QA pairs to agent_qa_pairs collection.

        Returns:
            Number of QA pairs saved
        """
        final_data = []
        for qa in qa_pairs:
            data = {
                "question": qa.question,
                "answer": qa.answer,
                "keywords": [kw.lower() for kw in qa.keywords],
                "status": "active",
                "batch_id": self.batch_id,
            }
            final_data.append(data)
        saved_results = AgentQAPairModel(eval_token).save_many_to_db(final_data)
        return len(saved_results)

    async def _save_kb_qa_pairs(self, eval_token, qa_pairs: List[QAPair]) -> int:
        """
        Save KB QA pairs to kb_qa_pairs collection.

        Returns:
            Number of QA pairs saved
        """
        final_data = []
        for qa in qa_pairs:
            data = {
                "question": qa.question,
                "answer": qa.answer,
                "keywords": [kw.lower() for kw in qa.keywords],
                "status": "active",
                "batch_id": self.batch_id,
            }
            final_data.append(data)
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
                "source": "agent",
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
                        "source": "knowledge_base",
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
