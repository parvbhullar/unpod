

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Any
import pytest

from livekit.agents import AgentSession, ChatContext, inference, llm

from .livekit_lite_agent import LiveKitLiteAgent
from super.core.voice.schema import UserState
from super.core.voice.services.livekit_services import LiveKitServiceFactory
from super.core.voice.livekit.lite_handler import LiveKitLiteHandler


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
            "test_results": [r.to_dict() for r in self.test_results]
        }

    def summary(self) -> str:
        return (
            f"\n{'='*60}\n"
            f"EVAL RESULTS SUMMARY - Agent: {self.agent_id}\n"
            f"{'='*60}\n"
            f"Total Cases: {self.total_cases}\n"
            f"Passed: {self.passed_cases}\n"
            f"Failed: {self.failed_cases}\n"
            f"Pass Rate: {self.pass_rate:.1f}%\n"
            f"Avg Answer Similarity: {self.avg_similarity_score:.1f}%\n"
            f"{'='*60}\n"
        )


class EvalTestAgent:
    def __init__(self,model_config):
        self.config = model_config
        self.service_factory=LiveKitServiceFactory(model_config)


    async def new_userdata(self):
        return UserState(
            knowledge_base=self.config.get('knowledge_base', []),
        )

    def _main_llm(self) -> llm.LLM | llm.RealtimeModel:

        llm_model = self.service_factory.create_llm()

        if not llm_model:
            llm_model = inference.LLM(
            "openai/gpt-5.1", extra_kwargs={"parallel_tool_calls": False, "temperature": 0.45}
        )

        return llm_model

    def _judge_llm(self) -> llm.LLM:
        """Create a judge LLM for intent evaluation and similarity scoring."""
        return inference.LLM(
            "openai/gpt-4o-mini", extra_kwargs={"temperature": 0.2}
        )

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

        async with (
            self._main_llm() as main_llm_model,
            self._judge_llm() as judge_llm_model,
            AgentSession(llm=main_llm_model, userdata=userdata) as sess,
        ):
            await sess.start(LiveKitLiteAgent(
                user_state=userdata,
                handler=LiveKitLiteHandler(),
                instructions=self.config.get("system_prompt", ''),
                testing_mode=True
            ))

            for idx, case in enumerate(test_cases):
                user_input = case.get("question")
                expected_output = case.get("answer")
                is_first_message = case.get("is_first_message", False)
                is_tool_call = case.get("is_tool_call", False)
                intent = case.get('intent', '')
                expected_tool = case.get("tool_name", None)

                if not user_input:
                    continue

                test_result = TestCaseResult(
                    test_case_index=idx,
                    question=user_input,
                    expected_answer=expected_output,
                    intent=intent,
                    passed=False,
                    expected_tool=expected_tool
                )

                try:
                    result = await sess.run(user_input=user_input)
                    actual_response = None
                    tool_called = None

                    # Store all events for debugging and response extraction
                    all_events = self._get_all_events(result)

                    if is_first_message:
                        msg_assert = result.expect.next_event().is_message(role="assistant")
                        actual_response = self._extract_message_content(msg_assert)

                        # Fallback: get response from all events
                        if actual_response is None:
                            actual_response = self._extract_response_from_events(all_events)

                        await msg_assert.judge(judge_llm_model, intent=intent)

                        # Final fallback: try to get from msg_assert after judge
                        if actual_response is None:
                            actual_response = self._extract_from_assert_after_judge(msg_assert)

                        # Last resort: get from result.expect events after processing
                        if actual_response is None:
                            actual_response = self._extract_from_expect(result.expect)

                        test_result.passed = True

                    else:

                        if is_tool_call:

                            try:
                                fn_assert = result.expect.next_event().is_function_call(name=expected_tool)
                                tool_called = expected_tool
                                result.expect.next_event().is_function_call_output()

                            except AssertionError as tool_err:
                                test_result.error_message = f"Tool call failed: {self._extract_clean_error_message(str(tool_err))}"
                                test_result.tool_called = None

                        msg_assert = result.expect.next_event().is_message(role="assistant")
                        actual_response = self._extract_message_content(msg_assert)

                        # Fallback: get response from all events
                        if actual_response is None:
                            actual_response = self._extract_response_from_events(all_events)

                        await msg_assert.judge(judge_llm_model, intent=intent)

                        # Final fallback: try to get from msg_assert after judge
                        if actual_response is None:
                            actual_response = self._extract_from_assert_after_judge(msg_assert)

                        # Last resort: get from result.expect events after processing
                        if actual_response is None:
                            actual_response = self._extract_from_expect(result.expect)

                        result.expect.no_more_events()
                        test_result.passed = True

                    # Try to get response from result object if still None
                    if actual_response is None:
                        try:
                            if hasattr(result, '_final_output') and result._final_output:
                                actual_response = result._final_output
                        except Exception:
                            pass

                    # Extract from string representation of result as last resort
                    if actual_response is None:
                        actual_response = self._extract_response_from_error(str(result))

                    # Try extracting from msg_assert string representation
                    if actual_response is None and msg_assert is not None:
                        actual_response = self._extract_response_from_error(str(msg_assert))

                    # Try to get from expect's internal state
                    if actual_response is None and hasattr(result, 'expect'):
                        expect_str = str(result.expect)
                        actual_response = self._extract_response_from_error(expect_str)

                    test_result.actual_response = actual_response
                    test_result.tool_called = tool_called

                    # Calculate answer similarity score for passing tests
                    if actual_response and expected_output:
                        # Fallback to text similarity
                        test_result.answer_similarity_score = self._calculate_text_similarity(
                            actual_response, expected_output
                        )

                except AssertionError as e:
                    test_result.passed = False
                    test_result.error_message = self._extract_clean_error_message(str(e))
                    # Try to extract actual response from error context
                    if test_result.actual_response is None:
                        test_result.actual_response = self._extract_response_from_error(str(e))

                    # Calculate similarity even for failed tests
                    if test_result.actual_response and expected_output:
                        test_result.answer_similarity_score = self._calculate_text_similarity(
                            test_result.actual_response, expected_output
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
            event = getattr(msg_assert, '_event', None)
            if event is None:
                event = getattr(msg_assert, 'event', None)
                if callable(event):
                    event = event()

            if event is None:
                return None

            # Get the item (ChatMessage) from the event
            item = getattr(event, 'item', None)
            if item is None:
                return None

            # ChatMessage has text_content property
            if hasattr(item, 'text_content'):
                text_content = item.text_content
                if text_content:
                    return text_content

            # Fallback: try content attribute directly
            content = getattr(item, 'content', None)
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
            if hasattr(result, 'events'):
                events = list(result.events)
            elif hasattr(result, '_events'):
                events = list(result._events)
            elif hasattr(result, 'expect') and hasattr(result.expect, '_events'):
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
                if 'ChatMessageEvent' in event_type or 'Message' in event_type:
                    item = getattr(event, 'item', None)
                    if item is None:
                        continue

                    # Get role - can be attribute or dict key
                    role = getattr(item, 'role', None)
                    if role is None and isinstance(item, dict):
                        role = item.get('role', '')

                    if role == 'assistant':
                        # Try text_content property first (ChatMessage object)
                        if hasattr(item, 'text_content'):
                            text_content = item.text_content
                            if text_content:
                                return text_content

                        # Try content attribute
                        content = getattr(item, 'content', None)
                        if content is None and isinstance(item, dict):
                            content = item.get('content', [])

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
                if attr_name.startswith('__'):
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
            if 'content' in obj:
                content = obj['content']
                if isinstance(content, list) and content:
                    return str(content[0])
                elif isinstance(content, str):
                    return content
            # Check nested 'item' dict
            if 'item' in obj and isinstance(obj['item'], dict):
                return self._try_extract_content(obj['item'])

        # If it has an 'item' attribute
        if hasattr(obj, 'item'):
            item = obj.item
            if isinstance(item, dict) and 'content' in item:
                content = item['content']
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
            for attr_name in ['_events', 'events', '_processed_events', 'processed_events', '_history', 'history']:
                if hasattr(expect_obj, attr_name):
                    events = getattr(expect_obj, attr_name)
                    if events:
                        try:
                            events_list = list(events) if not isinstance(events, list) else events
                            response = self._extract_response_from_events(events_list)
                            if response:
                                return response

                            # Also try str representation of events
                            for event in events_list:
                                event_str = str(event)
                                if "'content':" in event_str:
                                    extracted = self._extract_response_from_error(event_str)
                                    if extracted:
                                        return extracted
                        except Exception:
                            continue

            # Try parent reference if exists
            if hasattr(expect_obj, '_parent'):
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
            clean_message = clean_message.rstrip('\n')
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
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = cleaned.strip()

        # If we still have content, return it; otherwise return first line of original
        if cleaned:
            return cleaned

        # Fallback: return just the first line
        first_line = error_str.split('\n')[0].strip()
        return first_line if first_line else error_str[:200]

    async def _calculate_answer_similarity(
        self,
        actual_response: str,
        expected_answer: str,
        judge_llm_model
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
                if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                    response_text += chunk.delta.content or ""
                elif hasattr(chunk, 'content'):
                    response_text += chunk.content or ""

            # Parse the JSON response
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                score = float(result.get("score", 0))
                details = result.get("details", "No details provided")
                return min(max(score, 0), 100), details

            return 0.0, f"Could not parse LLM response: {response_text[:100]}"

        except Exception as e:
            return 0.0, f"Error calculating similarity: {str(e)}"

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity as a fallback.
        Uses word overlap (Jaccard similarity).
        """
        if not text1 or not text2:
            return 0.0

        # Normalize texts
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'can', 'to',
                      'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
                      'and', 'or', 'but', 'if', 'then', 'else', 'when', 'up', 'out',
                      'so', 'than', 'too', 'very', 'just', 'also', 'now', 'here',
                      'there', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
                      'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not',
                      'only', 'own', 'same', 'that', 'this', 'these', 'those', 'it'}

        words1 = words1 - stop_words
        words2 = words2 - stop_words

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return (len(intersection) / len(union)) * 100










