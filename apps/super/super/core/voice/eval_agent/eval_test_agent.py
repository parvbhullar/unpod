from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Any, Dict
import pytest

from livekit.agents import ChatContext, inference, llm
from super.core.voice.schema import UserState

from super.core.voice.livekit.livekit_lite_agent import LiveKitLiteAgent
from super.core.voice.schema import UserState
from super.core.voice.services.livekit_services import LiveKitServiceFactory
from super.core.voice.livekit.lite_handler import LiveKitLiteHandler
# Embedding model for semantic similarity (cross-language support)
_EMBEDDING_MODEL: Optional[Any] = None
_EMBEDDING_AVAILABLE: bool = False


def _get_embedding_model():
    """Lazy-load OpenAI embedding model for semantic similarity."""
    global _EMBEDDING_MODEL, _EMBEDDING_AVAILABLE
    if _EMBEDDING_MODEL is not None:
        return _EMBEDDING_MODEL
    try:
        from openai import OpenAI

        client = OpenAI()
        _EMBEDDING_MODEL = client
        _EMBEDDING_AVAILABLE = True
        return _EMBEDDING_MODEL
    except Exception:
        _EMBEDDING_AVAILABLE = False
        return None


@dataclass
class TestCaseResult:
    """Result of a single test case evaluation."""

    test_case_index: int
    question: str
    expected_answer: str
    intent: str
    passed: bool
    actual_response: Optional[str] = None
    error_message: Optional[str] = None
    tool_called: Optional[str] = None
    expected_tool: Optional[str] = None
    answer_similarity_score: Optional[float] = None
    answer_match_details: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvalResults:
    """Aggregated evaluation results."""

    agent_id: str
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    test_results: List[TestCaseResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return (self.passed_cases / self.total_cases) * 100

    @property
    def avg_similarity_score(self) -> float:
        """Calculate average answer similarity score across all test cases."""
        scores = [
            r.answer_similarity_score
            for r in self.test_results
            if r.answer_similarity_score is not None
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def add_result(self, result: TestCaseResult) -> None:
        self.test_results.append(result)
        self.total_cases += 1
        if result.passed:
            self.passed_cases += 1
        else:
            self.failed_cases += 1

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "pass_rate": f"{self.pass_rate:.1f}%",
            "avg_similarity_score": f"{self.avg_similarity_score:.1f}%",
            "test_results": [r.to_dict() for r in self.test_results],
        }

    def summary(self) -> str:
        return (
            f"\n{'= ' *60}\n"
            f"EVAL RESULTS SUMMARY - Agent: {self.agent_id}\n"
            f"{'= ' *60}\n"
            f"Total Cases: {self.total_cases}\n"
            f"Passed: {self.passed_cases}\n"
            f"Failed: {self.failed_cases}\n"
            f"Pass Rate: {self.pass_rate:.1f}%\n"
            f"Avg Answer Similarity: {self.avg_similarity_score:.1f}%\n"
            f"{'= ' *60}\n"
        )


class EvalTestAgent:
    def __init__(self, model_config):
        self.config = model_config
        self.service_factory = None

    async def evaluate_call_records(
        self,
        eval_records: Dict[str, Any],
        qa_pairs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate live call records (user/tool/assistant traces) against QA ground truth.
        """
        qa_pairs = self._normalize_qa_pairs(qa_pairs or [])
        if not isinstance(eval_records, dict):
            eval_records = {}

        user_messages = eval_records.get("user_messages", []) or []
        agent_responses = eval_records.get("agent_responses", []) or []
        tool_calls = eval_records.get("tool_calls", []) or []

        threshold = float(self.config.get("eval_answer_threshold", 35.0))
        question_match_threshold = float(
            self.config.get("eval_question_match_threshold", 35.0)
        )
        results: List[Dict[str, Any]] = []
        passed_cases = 0
        skipped_records = 0
        skipped_details: List[Dict[str, Any]] = []

        # Sort for deterministic matching by runtime sequence.
        user_messages = sorted(user_messages, key=lambda x: x.get("sequence_id", 0))
        agent_responses = sorted(agent_responses, key=lambda x: x.get("sequence_id", 0))
        tool_calls = sorted(tool_calls, key=lambda x: x.get("sequence_id", 0))

        async with self._judge_llm() as judge_llm_model:
            for user_record in user_messages:
                user_seq = user_record.get("sequence_id", -1)
                next_user_seq = self._next_user_seq(user_seq, user_messages)
                matched_response = self._find_response_for_window(
                    user_seq=user_seq,
                    next_user_seq=next_user_seq,
                    responses=agent_responses,
                )
                matched_tool = self._find_tool_for_window(
                    user_seq=user_seq,
                    next_user_seq=next_user_seq,
                    tools=tool_calls,
                )

                actual_response = (matched_response or {}).get("content", "")
                actual_tool = (matched_tool or {}).get("tool_name", "")
                llm_latency = (matched_response or {}).get("llm_latency")
                user_text = str(user_record.get("content", "") or "")

                if not user_text.strip():
                    skipped_records += 1
                    skipped_details.append(
                        {
                            "eval_record_sequence_id": user_seq,
                            "user_message": user_text,
                            "reason": "empty_user_message",
                        }
                    )
                    continue

                qa_match = self._best_qa_for_record(
                    user_text=user_text,
                    qa_pairs=qa_pairs,
                    actual_tool=actual_tool,
                    question_match_threshold=question_match_threshold,
                )
                if qa_match is None:
                    skipped_records += 1
                    best_guess = self._best_qa_similarity_only(
                        user_text=user_text,
                        qa_pairs=qa_pairs,
                    )
                    skipped_details.append(
                        {
                            "eval_record_sequence_id": user_seq,
                            "user_message": user_text,
                            "reason": "no_qa_match_above_threshold",
                            "best_question_match_score": round(
                                float(best_guess.get("score", 0.0)), 2
                            ),
                            "threshold": question_match_threshold,
                            "best_qa_question": best_guess.get("question"),
                        }
                    )
                    continue

                qa_idx, qa, question_score = qa_match
                question = str(qa.get("question", "") or "")
                expected_answer = str(
                    qa.get("answer", qa.get("expected_answer", "")) or ""
                )
                expected_intent = str(qa.get("intent", "") or "").strip()
                expected_tool = str(
                    qa.get("tool_name", qa.get("expected_tool", "")) or ""
                ).strip()

                llm_judgement = await self._judge_case_with_llm(
                    judge_llm_model=judge_llm_model,
                    question=question,
                    expected_answer=expected_answer,
                    expected_intent=expected_intent,
                    expected_tool=expected_tool,
                    actual_response=actual_response,
                    actual_tool=actual_tool,
                    answer_threshold=threshold,
                )

                if llm_judgement.get("parse_error"):
                    answer_score = (
                        self._calculate_text_similarity(
                            actual_response, expected_answer
                        )
                        if actual_response and expected_answer
                        else 0.0
                    )
                    answer_pass = not expected_answer or answer_score >= threshold
                    tool_pass = (
                        True
                        if not expected_tool
                        else expected_tool.lower() == str(actual_tool).lower()
                    )
                    intent_pass = (
                        True
                        if not expected_intent
                        else self._intent_match_heuristic(
                            expected_intent, actual_response, question
                        )
                    )
                    passed = bool(answer_pass and tool_pass and intent_pass)
                    judge_reason = (
                        llm_judgement.get("reason")
                        or "LLM parse failed; heuristic fallback used"
                    )
                else:
                    answer_score = float(llm_judgement.get("answer_score", 0.0) or 0.0)
                    answer_pass = bool(llm_judgement.get("answer_pass", False))
                    tool_pass = bool(llm_judgement.get("tool_pass", False))
                    intent_pass = bool(llm_judgement.get("intent_pass", False))
                    passed = bool(llm_judgement.get("passed", False))
                    judge_reason = llm_judgement.get("reason", "")

                if passed:
                    passed_cases += 1

                results.append(
                    {
                        "qa_index": qa_idx,
                        "index": len(results),
                        "eval_record_sequence_id": user_seq,
                        "question": question,
                        "matched_user_message": user_text,
                        "question_match_score": round(float(question_score or 0.0), 2),
                        "expected_answer": expected_answer,
                        "expected_tool": expected_tool or None,
                        "expected_intent": expected_intent or None,
                        "actual_response": actual_response or None,
                        "llm_latency": (
                            round(float(llm_latency), 4)
                            if isinstance(llm_latency, (int, float))
                            else None
                        ),
                        "actual_tool": actual_tool or None,
                        "answer_similarity_score": round(answer_score, 2),
                        "answer_pass": answer_pass,
                        "tool_pass": tool_pass,
                        "intent_pass": intent_pass,
                        "passed": passed,
                        "judge_reason": judge_reason,
                    }
                )

        total = len(qa_pairs)
        evaluated_total = len(results)
        failed = evaluated_total - passed_cases
        pass_rate = (passed_cases / evaluated_total * 100.0) if evaluated_total else 0.0
        return {
            "total_cases": evaluated_total,
            "total_qa_pairs": total,
            "total_eval_records": len(user_messages),
            "skipped_eval_records": skipped_records,
            "skipped_details": skipped_details,
            "passed_cases": passed_cases,
            "failed_cases": failed,
            "pass_rate": round(pass_rate, 2),
            "threshold": threshold,
            "question_match_threshold": question_match_threshold,
            "records_count": {
                "user_messages": len(user_messages),
                "agent_responses": len(agent_responses),
                "tool_calls": len(tool_calls),
            },
            "test_results": results,
        }

    def _best_qa_for_record(
        self,
        user_text: str,
        qa_pairs: List[Dict[str, Any]],
        actual_tool: str = "",
        question_match_threshold: float = 35.0,
    ) -> Optional[tuple[int, Dict[str, Any], float]]:
        """
        Pick best QA reference for one user record; returns None if below threshold.

        Uses semantic embeddings for cross-language matching when available,
        falls back to text similarity otherwise.
        """
        if not user_text or not qa_pairs:
            return None

        actual_tool_l = str(actual_tool or "").lower()
        best_idx = -1
        best_qa: Optional[Dict[str, Any]] = None
        best_score = -1.0

        # Try semantic similarity first (supports cross-language matching)
        use_semantic = self.config.get("use_semantic_matching", True)
        if use_semantic and _EMBEDDING_AVAILABLE:
            try:
                questions = [str(qa.get("question", "") or "") for qa in qa_pairs]
                semantic_scores = self._calculate_semantic_similarity_batch(
                    user_text, questions
                )
                if semantic_scores:
                    for idx, (qa, sem_score) in enumerate(
                        zip(qa_pairs, semantic_scores)
                    ):
                        question = str(qa.get("question", "") or "")
                        if not question:
                            continue

                        # Semantic score is 0-1, convert to 0-100
                        score = sem_score * 100

                        # Tool match bonus
                        expected_tool = str(
                            qa.get("tool_name", qa.get("expected_tool", "")) or ""
                        ).lower()
                        if (
                            expected_tool
                            and actual_tool_l
                            and expected_tool == actual_tool_l
                        ):
                            score += 10.0

                        if score > best_score:
                            best_score = score
                            best_idx = idx
                            best_qa = qa

                    if best_qa is not None and best_score >= question_match_threshold:
                        return best_idx, best_qa, best_score
            except Exception as e:
                # Fall through to text similarity
                print(f"Semantic matching failed, using text similarity: {e}")

        # Fallback: text-based similarity
        for idx, qa in enumerate(qa_pairs):
            question = str(qa.get("question", "") or "")
            if not question:
                continue

            score = self._calculate_text_similarity(user_text, question)

            expected_tool = str(
                qa.get("tool_name", qa.get("expected_tool", "")) or ""
            ).lower()
            if expected_tool and actual_tool_l and expected_tool == actual_tool_l:
                score += 10.0

            if score > best_score:
                best_score = score
                best_idx = idx
                best_qa = qa

        if best_qa is None or best_score < question_match_threshold:
            return None

        return best_idx, best_qa, best_score

    def _calculate_semantic_similarity_batch(
        self, query: str, candidates: List[str]
    ) -> Optional[List[float]]:
        try:
            client = _get_embedding_model()
            if client is None:
                return None

            valid_indices = [i for i, c in enumerate(candidates) if c.strip()]
            if not valid_indices:
                return None

            valid_candidates = [candidates[i] for i in valid_indices]

            all_texts = [query] + valid_candidates
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=all_texts,
            )

            embeddings = [item.embedding for item in response.data]
            query_embedding = embeddings[0]
            candidate_embeddings = embeddings[1:]

            import math

            def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
                dot_product = sum(a * b for a, b in zip(vec1, vec2))
                norm1 = math.sqrt(sum(a * a for a in vec1))
                norm2 = math.sqrt(sum(b * b for b in vec2))
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                return dot_product / (norm1 * norm2)

            results = [0.0] * len(candidates)
            for i, valid_idx in enumerate(valid_indices):
                results[valid_idx] = cosine_similarity(
                    query_embedding, candidate_embeddings[i]
                )

            return results

        except Exception as e:
            print(f"Embedding calculation failed: {e}")
            return None

    def _best_qa_similarity_only(
        self,
        user_text: str,
        qa_pairs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Return the closest QA question match without applying threshold."""
        best_score = -1.0
        best_question = None
        for qa in qa_pairs:
            question = str(qa.get("question", "") or "")
            if not question:
                continue
            score = self._calculate_text_similarity(user_text, question)
            if score > best_score:
                best_score = score
                best_question = question
        return {
            "score": best_score if best_score > -1 else 0.0,
            "question": best_question,
        }

    def _match_eval_records_to_qa_pairs(
        self,
        user_messages: List[Dict[str, Any]],
        qa_pairs: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
        question_match_threshold: float = 35.0,
    ) -> List[Dict[str, Any]]:
        """
        Match only relevant QA pairs against observed eval records.

        Strategy:
        - One QA pair max per user message (greedy).
        - Similarity between user utterance and QA question drives matching.
        - Small bonus if expected tool appears anywhere in observed tool calls.
        - Keep only matches above threshold.
        """
        if not user_messages or not qa_pairs:
            return []

        observed_tools = {str(t.get("tool_name", "") or "").lower() for t in tool_calls}

        remaining = list(enumerate(qa_pairs))
        matched: List[Dict[str, Any]] = []

        for um in user_messages:
            user_text = str(um.get("content", "") or "")
            best = None
            best_score = -1.0

            for qa_idx, qa in remaining:
                question = str(qa.get("question", "") or "")
                if not question:
                    continue

                score = self._calculate_text_similarity(user_text, question)

                expected_tool = str(
                    qa.get("tool_name", qa.get("expected_tool", "")) or ""
                ).lower()
                if expected_tool and expected_tool in observed_tools:
                    score += 8.0

                if score > best_score:
                    best_score = score
                    best = (qa_idx, qa)

            if best is None:
                continue

            qa_idx, qa = best
            if best_score < question_match_threshold:
                continue

            matched.append(
                {
                    "qa_index": qa_idx,
                    "qa": qa,
                    "user_message": um,
                    "question_score": best_score,
                }
            )

            remaining = [(i, q) for i, q in remaining if i != qa_idx]

        return matched

    def _normalize_qa_pairs(self, qa_pairs: Any) -> List[Dict[str, Any]]:
        """
        Normalize QA input into a flat list of dicts.

        Handles accidental nested lists, JSON strings, and wrapper objects.
        """
        import json

        normalized: List[Dict[str, Any]] = []

        def _walk(item: Any) -> None:
            if item is None:
                return
            if isinstance(item, list):
                for sub in item:
                    _walk(sub)
                return
            if isinstance(item, str):
                try:
                    parsed = json.loads(item)
                except Exception:
                    return
                _walk(parsed)
                return
            if isinstance(item, dict):
                # Common wrapper payloads
                if isinstance(item.get("qa_pairs"), list):
                    _walk(item.get("qa_pairs"))
                    return
                if isinstance(item.get("cases"), list):
                    _walk(item.get("cases"))
                    return
                # Actual QA case
                if any(
                    k in item
                    for k in [
                        "question",
                        "answer",
                        "expected_answer",
                        "intent",
                        "tool_name",
                        "expected_tool",
                    ]
                ):
                    normalized.append(item)
                return

        _walk(qa_pairs)
        return normalized

    def _find_best_user_message(
        self, question: str, user_messages: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if not question or not user_messages:
            return user_messages[0] if user_messages else None

        best_msg = None
        best_score = -1.0
        for msg in user_messages:
            content = str(msg.get("content", "") or "")
            score = self._calculate_text_similarity(question, content)
            if score > best_score:
                best_score = score
                best_msg = msg
        return best_msg

    def _next_user_seq(
        self, current_seq: int, user_messages: List[Dict[str, Any]]
    ) -> Optional[int]:
        candidates = [
            int(m.get("sequence_id", 0))
            for m in user_messages
            if int(m.get("sequence_id", 0)) > int(current_seq)
        ]
        return min(candidates) if candidates else None

    def _find_response_for_window(
        self,
        user_seq: int,
        next_user_seq: Optional[int],
        responses: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not responses:
            return None
        for resp in responses:
            seq = int(resp.get("sequence_id", 0))
            if seq > int(user_seq) and (
                next_user_seq is None or seq < int(next_user_seq)
            ):
                return resp
        return responses[0]

    def _find_tool_for_window(
        self,
        user_seq: int,
        next_user_seq: Optional[int],
        tools: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not tools:
            return None
        for tool in tools:
            seq = int(tool.get("sequence_id", 0))
            if seq > int(user_seq) and (
                next_user_seq is None or seq < int(next_user_seq)
            ):
                return tool
        return None

    def _intent_match_heuristic(
        self, expected_intent: str, response: str, question: str
    ) -> bool:
        expected = expected_intent.lower().strip()
        if not expected:
            return True
        response_l = (response or "").lower()
        question_l = (question or "").lower()
        if expected in response_l:
            return True
        if expected in question_l:
            return True
        return self._calculate_text_similarity(expected, response_l) >= 35.0

    async def _judge_case_with_llm(
        self,
        judge_llm_model,
        question: str,
        expected_answer: str,
        expected_intent: str,
        expected_tool: str,
        actual_response: str,
        actual_tool: str,
        answer_threshold: float,
    ) -> Dict[str, Any]:
        """
        LLM judge for a single realtime eval case. The judge decides pass/fail.
        """
        import json
        import re

        prompt = f"""You are a strict evaluator for voice-agent QA cases.

            Ground truth:
            - Question: {question}
            - Expected answer: {expected_answer}
            - Expected intent: {expected_intent or "<none>"}
            - Expected tool: {expected_tool or "<none>"}

            Observed agent behavior:
            - Actual response: {actual_response or "<empty>"}
            - Actual tool called: {actual_tool or "<none>"}

            Task:
            1) Judge answer quality (0-100) against expected answer.
            2) Judge intent match (true/false) when expected intent is provided; otherwise true.
            3) Judge tool match (true/false) when expected tool is provided; otherwise true.
            4) Decide final pass/fail. Be strict.
            5) Use answer threshold = {answer_threshold}.

            Return ONLY valid JSON with this exact schema:
            {{
              "passed": true/false,
              "answer_score": 0-100,
              "answer_pass": true/false,
              "intent_pass": true/false,
              "tool_pass": true/false,
              "reason": "short reason"
            }}
            """
        try:
            chat_ctx = ChatContext()
            chat_ctx.add_message(role="user", content=prompt)
            # LiveKit inference returns an LLMStream directly (not awaitable).
            response = judge_llm_model.chat(chat_ctx=chat_ctx)

            response_text = ""
            async for chunk in response:
                if hasattr(chunk, "delta") and hasattr(chunk.delta, "content"):
                    response_text += chunk.delta.content or ""
                elif hasattr(chunk, "content"):
                    response_text += chunk.content or ""

            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if not json_match:
                return {
                    "parse_error": True,
                    "reason": f"No JSON from judge: {response_text[:180]}",
                }

            parsed = json.loads(json_match.group())
            return {
                "passed": bool(parsed.get("passed", False)),
                "answer_score": float(parsed.get("answer_score", 0.0) or 0.0),
                "answer_pass": bool(parsed.get("answer_pass", False)),
                "intent_pass": bool(parsed.get("intent_pass", False)),
                "tool_pass": bool(parsed.get("tool_pass", False)),
                "reason": str(parsed.get("reason", "")),
                "parse_error": False,
            }
        except Exception as e:
            return {"parse_error": True, "reason": f"Judge error: {str(e)}"}

    async def new_userdata(self):
        return UserState(
            knowledge_base=self.config.get("knowledge_base", []),
        )

    def _main_llm(self) -> llm.LLM | llm.RealtimeModel:
        if self.service_factory is None:
            from super.core.voice.services.livekit_services import LiveKitServiceFactory

            self.service_factory = LiveKitServiceFactory(self.config)

        llm_model = self.service_factory.create_llm()

        if not llm_model:
            llm_model = inference.LLM(
                "openai/gpt-5.1",
                extra_kwargs={"parallel_tool_calls": False, "temperature": 0.45},
            )

        return llm_model

    def _judge_llm(self) -> llm.LLM:
        """Create a judge LLM for intent evaluation and similarity scoring."""
        return inference.LLM("openai/gpt-4o-mini", extra_kwargs={"temperature": 0.2})

    @pytest.mark.asyncio
    async def test_llm_agent(self, test_cases) -> EvalResults:
        """
        Run evaluation tests on the agent and return structured results.

        Args:
            test_cases: List of test case dictionaries

        Returns:
            EvalResults with detailed per-case results
        """
        userdata = await self.new_userdata()
        agent_id = self.config.get("agent_id", "unknown")
        eval_results = EvalResults(agent_id=agent_id)

        from livekit.agents import AgentSession
        from super.core.voice.livekit.livekit_lite_agent import LiveKitLiteAgent
        from super.core.voice.livekit.lite_handler import LiveKitLiteHandler

        async with (
            self._main_llm() as main_llm_model,
            self._judge_llm() as judge_llm_model,
            AgentSession(llm=main_llm_model, userdata=userdata) as sess,
        ):
            await sess.start(
                LiveKitLiteAgent(
                    user_state=userdata,
                    handler=LiveKitLiteHandler(),
                    instructions=self.config.get("system_prompt", ""),
                    testing_mode=True,
                )
            )

            for idx, case in enumerate(test_cases):
                user_input = case.get("question")
                expected_output = case.get("answer")
                is_first_message = case.get("is_first_message", False)
                is_tool_call = case.get("is_tool_call", False)
                intent = case.get("intent", "")
                expected_tool = case.get("tool_name", None)

                if not user_input:
                    continue

                test_result = TestCaseResult(
                    test_case_index=idx,
                    question=user_input,
                    expected_answer=expected_output,
                    intent=intent,
                    passed=False,
                    expected_tool=expected_tool,
                )

                try:
                    result = await sess.run(user_input=user_input)
                    actual_response = None
                    tool_called = None

                    # Store all events for debugging and response extraction
                    all_events = self._get_all_events(result)

                    if is_first_message:
                        msg_assert = result.expect.next_event().is_message(
                            role="assistant"
                        )
                        actual_response = self._extract_message_content(msg_assert)

                        # Fallback: get response from all events
                        if actual_response is None:
                            actual_response = self._extract_response_from_events(
                                all_events
                            )

                        await msg_assert.judge(judge_llm_model, intent=intent)

                        # Final fallback: try to get from msg_assert after judge
                        if actual_response is None:
                            actual_response = self._extract_from_assert_after_judge(
                                msg_assert
                            )

                        # Last resort: get from result.expect events after processing
                        if actual_response is None:
                            actual_response = self._extract_from_expect(result.expect)

                        test_result.passed = True

                    else:
                        if is_tool_call:
                            try:
                                fn_assert = result.expect.next_event().is_function_call(
                                    name=expected_tool
                                )
                                tool_called = expected_tool
                                result.expect.next_event().is_function_call_output()

                            except AssertionError as tool_err:
                                test_result.error_message = f"Tool call failed: {self._extract_clean_error_message(str(tool_err))}"
                                test_result.tool_called = None

                        msg_assert = result.expect.next_event().is_message(
                            role="assistant"
                        )
                        actual_response = self._extract_message_content(msg_assert)

                        # Fallback: get response from all events
                        if actual_response is None:
                            actual_response = self._extract_response_from_events(
                                all_events
                            )

                        await msg_assert.judge(judge_llm_model, intent=intent)

                        # Final fallback: try to get from msg_assert after judge
                        if actual_response is None:
                            actual_response = self._extract_from_assert_after_judge(
                                msg_assert
                            )

                        # Last resort: get from result.expect events after processing
                        if actual_response is None:
                            actual_response = self._extract_from_expect(result.expect)

                        result.expect.no_more_events()
                        test_result.passed = True

                    # Try to get response from result object if still None
                    if actual_response is None:
                        try:
                            if (
                                hasattr(result, "_final_output")
                                and result._final_output
                            ):
                                actual_response = result._final_output
                        except Exception:
                            pass

                    # Extract from string representation of result as last resort
                    if actual_response is None:
                        actual_response = self._extract_response_from_error(str(result))

                    # Try extracting from msg_assert string representation
                    if actual_response is None and msg_assert is not None:
                        actual_response = self._extract_response_from_error(
                            str(msg_assert)
                        )

                    # Try to get from expect's internal state
                    if actual_response is None and hasattr(result, "expect"):
                        expect_str = str(result.expect)
                        actual_response = self._extract_response_from_error(expect_str)

                    test_result.actual_response = actual_response
                    test_result.tool_called = tool_called

                    # Calculate answer similarity score for passing tests
                    if actual_response and expected_output:
                        # Fallback to text similarity
                        test_result.answer_similarity_score = (
                            self._calculate_text_similarity(
                                actual_response, expected_output
                            )
                        )

                except AssertionError as e:
                    test_result.passed = False
                    test_result.error_message = self._extract_clean_error_message(
                        str(e)
                    )
                    # Try to extract actual response from error context
                    if test_result.actual_response is None:
                        test_result.actual_response = self._extract_response_from_error(
                            str(e)
                        )

                    # Calculate similarity even for failed tests
                    if test_result.actual_response and expected_output:
                        test_result.answer_similarity_score = (
                            self._calculate_text_similarity(
                                test_result.actual_response, expected_output
                            )
                        )

                except Exception as e:
                    test_result.passed = False
                    test_result.error_message = f"Unexpected error: {str(e)}"

                eval_results.add_result(test_result)

                # Log individual result
                status = "PASS" if test_result.passed else "FAIL"
                print(f"[{status}] Test {idx + 1}: {user_input[:50]}...")

        # Print summary
        print(eval_results.summary())

        # Print detailed results
        for r in eval_results.test_results:
            status = "PASS" if r.passed else "FAIL"
            print(f"\n[{status}] Case {r.test_case_index + 1}: {r.question}")
            if r.actual_response:
                print(f"  Response: {r.actual_response[:100]}...")
            if r.answer_similarity_score is not None:
                print(f"  Similarity Score: {r.answer_similarity_score:.1f}%")
                if r.answer_match_details:
                    print(f"  Match Details: {r.answer_match_details[:100]}")
            if r.error_message:
                print(f"  Error: {r.error_message[:200]}")

        return eval_results

    def _extract_message_content(self, msg_assert) -> Optional[str]:
        """Extract message content from assertion object if possible."""
        try:
            # ChatMessageAssert has _event attribute which is ChatMessageEvent
            # ChatMessageEvent has item attribute which is ChatMessage
            # ChatMessage has text_content property

            # Try getting _event first (ChatMessageAssert stores event here)
            event = getattr(msg_assert, "_event", None)
            if event is None:
                event = getattr(msg_assert, "event", None)
                if callable(event):
                    event = event()

            if event is None:
                return None

            # Get the item (ChatMessage) from the event
            item = getattr(event, "item", None)
            if item is None:
                return None

            # ChatMessage has text_content property
            if hasattr(item, "text_content"):
                text_content = item.text_content
                if text_content:
                    return text_content

            # Fallback: try content attribute directly
            content = getattr(item, "content", None)
            if content is not None:
                if isinstance(content, list) and content:
                    # Content is list of str | ImageContent | AudioContent
                    text_parts = [c for c in content if isinstance(c, str)]
                    if text_parts:
                        return " ".join(text_parts)
                elif isinstance(content, str):
                    return content

            return None

        except Exception as e:
            print(f"Debug: Failed to extract message content: {e}")
            return None

    def _extract_response_from_error(self, error_str: str) -> Optional[str]:
        """Try to extract the actual response from an error message."""
        import re

        try:
            # Try to find content in the error string
            patterns = [
                r"'content':\s*\[\"(.*?)\"\]",
                r"'content':\s*\['(.*?)'\]",
                r'"content":\s*\["(.*?)"\]',
                r"'content':\s*\[(.*?)\]",
            ]
            for pattern in patterns:
                match = re.search(pattern, error_str, re.DOTALL)
                if match:
                    return match.group(1).strip("'\"")
        except Exception:
            pass
        return None

    def _get_all_events(self, result) -> List[Any]:
        """Get all events from a run result."""
        events = []
        try:
            # Try to access events from result object
            if hasattr(result, "events"):
                events = list(result.events)
            elif hasattr(result, "_events"):
                events = list(result._events)
            elif hasattr(result, "expect") and hasattr(result.expect, "_events"):
                events = list(result.expect._events)
        except Exception as e:
            print(f"Debug: Could not get events: {e}")
        return events

    def _extract_response_from_events(self, events: List[Any]) -> Optional[str]:
        """Extract the assistant's response from a list of events."""
        try:
            for event in events:
                # Check if it's a ChatMessageEvent with assistant role
                event_type = type(event).__name__
                if "ChatMessageEvent" in event_type or "Message" in event_type:
                    item = getattr(event, "item", None)
                    if item is None:
                        continue

                    # Get role - can be attribute or dict key
                    role = getattr(item, "role", None)
                    if role is None and isinstance(item, dict):
                        role = item.get("role", "")

                    if role == "assistant":
                        # Try text_content property first (ChatMessage object)
                        if hasattr(item, "text_content"):
                            text_content = item.text_content
                            if text_content:
                                return text_content

                        # Try content attribute
                        content = getattr(item, "content", None)
                        if content is None and isinstance(item, dict):
                            content = item.get("content", [])

                        if content:
                            if isinstance(content, list):
                                # Content is list of str | ImageContent | AudioContent
                                text_parts = [c for c in content if isinstance(c, str)]
                                if text_parts:
                                    return " ".join(text_parts)
                            elif isinstance(content, str):
                                return content
        except Exception as e:
            print(f"Debug: Failed to extract from events: {e}")
        return None

    def _extract_from_assert_after_judge(self, msg_assert) -> Optional[str]:
        """
        Try to extract response by inspecting all attributes of the assertion object.
        This is a brute-force approach to find the content.
        """
        try:
            # First, try to get string representation and extract from it
            str_repr = str(msg_assert)
            if "'content':" in str_repr:
                extracted = self._extract_response_from_error(str_repr)
                if extracted:
                    return extracted

            # Get all attributes of the object
            for attr_name in dir(msg_assert):
                if attr_name.startswith("__"):
                    continue
                try:
                    attr_val = getattr(msg_assert, attr_name)
                    # Skip methods
                    if callable(attr_val):
                        continue

                    # Try to find content in the attribute
                    content = self._try_extract_content(attr_val)
                    if content:
                        return content
                except Exception:
                    continue
        except Exception as e:
            print(f"Debug: _extract_from_assert_after_judge failed: {e}")
        return None

    def _try_extract_content(self, obj) -> Optional[str]:
        """Recursively try to extract content from an object."""
        if obj is None:
            return None

        # If it's a string, check if it looks like content
        if isinstance(obj, str) and len(obj) > 10:
            return obj

        # If it's a dict, look for 'content' key
        if isinstance(obj, dict):
            if "content" in obj:
                content = obj["content"]
                if isinstance(content, list) and content:
                    return str(content[0])
                elif isinstance(content, str):
                    return content
            # Check nested 'item' dict
            if "item" in obj and isinstance(obj["item"], dict):
                return self._try_extract_content(obj["item"])

        # If it has an 'item' attribute
        if hasattr(obj, "item"):
            item = obj.item
            if isinstance(item, dict) and "content" in item:
                content = item["content"]
                if isinstance(content, list) and content:
                    return str(content[0])
                elif isinstance(content, str):
                    return content

        return None

    def _extract_from_expect(self, expect_obj) -> Optional[str]:
        """
        Extract response from the expect object by looking at processed events.
        """
        try:
            # Try to get the string representation of expect and extract
            str_repr = str(expect_obj)
            if "'content':" in str_repr:
                extracted = self._extract_response_from_error(str_repr)
                if extracted:
                    return extracted

            # Try common attributes on expect object
            for attr_name in [
                "_events",
                "events",
                "_processed_events",
                "processed_events",
                "_history",
                "history",
            ]:
                if hasattr(expect_obj, attr_name):
                    events = getattr(expect_obj, attr_name)
                    if events:
                        try:
                            events_list = (
                                list(events) if not isinstance(events, list) else events
                            )
                            response = self._extract_response_from_events(events_list)
                            if response:
                                return response

                            # Also try str representation of events
                            for event in events_list:
                                event_str = str(event)
                                if "'content':" in event_str:
                                    extracted = self._extract_response_from_error(
                                        event_str
                                    )
                                    if extracted:
                                        return extracted
                        except Exception:
                            continue

            # Try parent reference if exists
            if hasattr(expect_obj, "_parent"):
                parent = expect_obj._parent
                if parent:
                    return self._extract_from_expect(parent)

        except Exception as e:
            print(f"Debug: _extract_from_expect failed: {e}")
        return None

    def _extract_clean_error_message(self, error_str: str) -> str:
        """
        Extract only the meaningful error reason from an assertion error.

        Removes verbose context like ChatMessageEvent, FunctionCallEvent data
        and keeps only the failure reason.
        """
        import re

        # Check for "Context around failure:" marker and extract only the part before it
        context_marker = "Context around failure:"
        if context_marker in error_str:
            # Get only the part before the context
            clean_message = error_str.split(context_marker)[0].strip()
            # Remove trailing newlines
            clean_message = clean_message.rstrip("\n")
            if clean_message:
                return clean_message

        # Handle "Judgement failed:" pattern - extract the reason
        judgement_match = re.match(r"(Judgement failed:\s*[^\n]+)", error_str)
        if judgement_match:
            return judgement_match.group(1).strip()

        # Handle "Expected another event" pattern
        expected_event_match = re.match(r"(Expected another event[^\n]*)", error_str)
        if expected_event_match:
            return expected_event_match.group(1).strip()

        # Handle "Tool call failed:" pattern
        tool_call_match = re.match(r"(Tool call failed:\s*[^\n]+)", error_str)
        if tool_call_match:
            return tool_call_match.group(1).strip()

        # Remove any ChatMessageEvent, FunctionCallEvent, FunctionCallOutputEvent patterns
        # These are verbose event dumps we don't want in error messages
        patterns_to_remove = [
            r"\[?\d+\]\s*ChatMessageEvent\(item=\{.*?\}\)",
            r"\[?\d+\]\s*FunctionCallEvent\(item=\{.*?\}\)",
            r"\[?\d+\]\s*FunctionCallOutputEvent\(item=\{.*?\}\)",
            r">>> \[\d+\].*?(?=\n|$)",
        ]

        cleaned = error_str
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)

        # Clean up multiple newlines and whitespace
        cleaned = re.sub(r"\n\s*\n", "\n", cleaned)
        cleaned = cleaned.strip()

        # If we still have content, return it; otherwise return first line of original
        if cleaned:
            return cleaned

        # Fallback: return just the first line
        first_line = error_str.split("\n")[0].strip()
        return first_line if first_line else error_str[:200]

    async def _calculate_answer_similarity(
        self, actual_response: str, expected_answer: str, judge_llm_model
    ) -> tuple[float, str]:
        """
        Use LLM to judge how well the actual response matches the expected answer.

        Returns:
            Tuple of (similarity_score 0-100, details string)
        """
        if not actual_response or not expected_answer:
            return 0.0, "Missing actual response or expected answer"

        try:
            prompt = f"""You are an evaluator comparing an AI agent's response to an expected answer.

            Expected Answer:
            {expected_answer}

            Actual Response:
            {actual_response}

            Evaluate how well the actual response matches the expected answer in terms of:
            1. Key information coverage (are the main points present?)
            2. Factual accuracy (is the information correct?)
            3. Completeness (does it cover all important aspects?)

            Respond with ONLY a JSON object in this exact format:
            {{"score": <number 0-100>, "details": "<brief explanation>"}}

            Score guidelines:
            - 90-100: Excellent match, covers all key points accurately
            - 70-89: Good match, most key information present
            - 50-69: Partial match, some key information missing or different
            - 30-49: Poor match, significant information missing
            - 0-29: Very poor match, response doesn't address the expected content"""

            # Create ChatContext properly using add_message method
            chat_ctx = ChatContext()
            chat_ctx.add_message(role="user", content=prompt)

            response = await judge_llm_model.chat(chat_ctx=chat_ctx)

            response_text = ""
            async for chunk in response:
                if hasattr(chunk, "delta") and hasattr(chunk.delta, "content"):
                    response_text += chunk.delta.content or ""
                elif hasattr(chunk, "content"):
                    response_text += chunk.content or ""

            # Parse the JSON response
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r"\{[^}]+\}", response_text)
            if json_match:
                result = json.loads(json_match.group())
                score = float(result.get("score", 0))
                details = result.get("details", "No details provided")
                return min(max(score, 0), 100), details

            return 0.0, f"Could not parse LLM response: {response_text[:100]}"

        except Exception as e:
            return 0.0, f"Error calculating similarity: {str(e)}"

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        import difflib
        import re

        if not text1 or not text2:
            return 0.0

        text1_n = re.sub(r"\s+", " ", str(text1).strip().lower())
        text2_n = re.sub(r"\s+", " ", str(text2).strip().lower())
        if not text1_n or not text2_n:
            return 0.0

        # Keep compact stop words list focused on high-frequency function words.
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "and",
            "or",
            "but",
            "if",
            "then",
            "else",
            "when",
            "up",
            "out",
            "so",
            "than",
            "too",
            "very",
            "just",
            "also",
            "now",
            "here",
            "there",
            "where",
            "why",
            "how",
            "all",
            "each",
            "every",
            "both",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "not",
            "only",
            "own",
            "same",
            "that",
            "this",
            "these",
            "those",
            "it",
        }

        # Canonical mappings for frequent paraphrases in QA and conversational text.
        synonym_groups = [
            {"definition", "define", "meaning", "means", "explain", "description"},
            {"question", "query", "ask", "asking"},
            {"similar", "similarity", "same", "equivalent", "alike"},
            {"price", "cost", "fee", "charge"},
            {"buy", "purchase", "order"},
            {"create", "make", "build", "generate"},
            {"cancel", "stop", "terminate"},
            {"start", "begin", "initiate"},
            {"error", "issue", "problem", "bug"},
            {"update", "change", "modify", "edit"},
            {"tool", "function", "method"},
            {"user", "customer", "client"},
            {"agent", "assistant", "bot"},
        ]
        synonym_map: Dict[str, str] = {}
        for group in synonym_groups:
            canonical = sorted(group)[0]
            for word in group:
                synonym_map[word] = canonical

        def _light_stem(token: str) -> str:
            # Very light stemming to keep behavior predictable and dependency-free.
            for suffix in ("ingly", "edly", "ing", "ed", "ies", "s"):
                if token.endswith(suffix) and len(token) > len(suffix) + 2:
                    if suffix == "ies":
                        return token[:-3] + "y"
                    return token[: -len(suffix)]
            return token

        def _tokenize(text: str) -> List[str]:
            raw = re.findall(r"[a-z0-9]+", text)
            cooked: List[str] = []
            for token in raw:
                if token in stop_words:
                    continue
                token = _light_stem(token)
                token = synonym_map.get(token, token)
                if token and token not in stop_words:
                    cooked.append(token)
            return cooked

        def _char_trigrams(text: str) -> set[str]:
            compact = re.sub(r"\s+", " ", text).strip()
            if len(compact) < 3:
                return {compact} if compact else set()
            return {compact[i : i + 3] for i in range(len(compact) - 2)}

        tokens1 = _tokenize(text1_n)
        tokens2 = _tokenize(text2_n)
        set1 = set(tokens1)
        set2 = set(tokens2)

        # 1) Token Jaccard.
        jaccard = 0.0
        if set1 or set2:
            union = set1.union(set2)
            jaccard = (
                (len(set1.intersection(set2)) / len(union)) * 100 if union else 0.0
            )

        # 2) Token F1 to reward partial containment (short question vs longer wording).
        token_f1 = 0.0
        if set1 and set2:
            inter = len(set1.intersection(set2))
            precision = inter / len(set1)
            recall = inter / len(set2)
            if precision + recall > 0:
                token_f1 = (2 * precision * recall / (precision + recall)) * 100

        # 3) Character trigram Dice score for flexible rewording/typos.
        tri1 = _char_trigrams(text1_n)
        tri2 = _char_trigrams(text2_n)
        trigram_score = 0.0
        if tri1 and tri2:
            trigram_score = (
                2 * len(tri1.intersection(tri2)) / (len(tri1) + len(tri2))
            ) * 100

        # 4) Fuzzy sequence ratio (order-aware).
        sequence_score = difflib.SequenceMatcher(None, text1_n, text2_n).ratio() * 100

        # Blend scores. Weights favor semantic token overlap over exact wording.
        score = (
            0.40 * token_f1
            + 0.25 * jaccard
            + 0.20 * trigram_score
            + 0.15 * sequence_score
        )

        # Strong containment hint for short/long paraphrases.
        shorter, longer = (
            (text1_n, text2_n) if len(text1_n) <= len(text2_n) else (text2_n, text1_n)
        )
        if len(shorter) >= 12 and shorter in longer:
            score = max(score, 78.0)

        # Light numeric consistency: reward same numbers, penalize conflicting numbers.
        nums1 = set(re.findall(r"\d+(?:\.\d+)?", text1_n))
        nums2 = set(re.findall(r"\d+(?:\.\d+)?", text2_n))
        if nums1 and nums2:
            if nums1 == nums2:
                score += 4.0
            elif nums1.isdisjoint(nums2):
                score -= 8.0

        return max(0.0, min(100.0, score))
