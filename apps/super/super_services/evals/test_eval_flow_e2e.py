"""
End-to-End Test Script for Eval System
Tests the complete flow:
1. Generate QA pairs from agent config + knowledge base
2. Save QA pairs to MongoDB (agent_qa_pairs & kb_qa_pairs collections)
3. Simulate call evaluation with transcript
4. Compare responses and calculate metrics
5. Save metrics to MongoDB

Usage:
    python -m super_services.evals.test_eval_flow_e2e --agent_id <your_agent_id>
"""

# =============================================================================
# CONFIGURE YOUR AGENT ID AND KB TOKEN HERE (or pass via command line)
# =============================================================================
DEFAULT_AGENT_ID = "developer-38qph836fhp9"
DEFAULT_KB_TOKEN = "C1TU09CM2ZWD3HNOXHY70KCT"
# =============================================================================

import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import Dict, List
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Initialize MongoDB connection
from super_services.libs.core.model import *
from super_services.db.services import *

# Import eval modules
from super_services.evals.eval_generator import (
    EvalGenerator,
    get_agent_qa_pairs,
    get_kb_qa_pairs,
    get_all_qa_pairs_for_agent,
)
from super_services.db.services.models.agent_eval import (
    AgentQAPairModel,
    KBQAPairModel,
)

# Import voice evaluation modules
from super.core.voice.voice_agent_evals.voice_evaluation import (
    VoiceCallEvaluator,
    evaluate_voice_call,
)
from super_services.db.services.models.voice_evaluation import (
    CallEvaluationResultModel,
    CallQualityMetricsModel,
    QuestionNotFoundModel,
)


class EvalFlowE2ETester:
    """End-to-End tester for the evaluation system."""

    def __init__(self, agent_id: str, kb_token: str = None, force_regenerate: bool = False, verbose: bool = True):
        self.agent_id = agent_id
        self.kb_token = kb_token
        self.force_regenerate = force_regenerate
        self.verbose = verbose
        self.test_session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.results = {
            "generation": {},
            "kb_generation": {},
            "mongodb_verification": {},
            "evaluation": {},
            "metrics_verification": {},
        }

    def log(self, message: str, level: str = "INFO"):
        """Print log message with timestamp."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARN": "⚠️"}.get(level, "")
            print(f"[{timestamp}] {emoji} {message}")

    # =========================================================================
    # STEP 1: Test Eval Generation
    # =========================================================================
    async def test_eval_generation(self) -> bool:
        """Test QA pair generation from agent config and knowledge base."""
        self.log("=" * 60)
        self.log("STEP 1: Testing Eval Generation", "INFO")
        if self.force_regenerate:
            self.log("Force regenerate: ON (will regenerate even if exists)", "WARN")
        self.log("=" * 60)

        try:
            # Run the eval generator
            generator = EvalGenerator(self.agent_id)
            results = await generator.generate_all_evals(force_regenerate=self.force_regenerate)

            self.results["generation"] = {
                "batch_id": results["batch_id"],
                "agent_qa_count": results["agent_qa_count"],
                "kb_qa_count": results["kb_qa_count"],
                "total_qa_count": results["total_qa_count"],
                "skipped": results.get("skipped", []),
                "errors": results.get("errors", []),
            }

            # Show skipped messages
            if results.get("skipped"):
                for skip_msg in results["skipped"]:
                    self.log(f"SKIPPED: {skip_msg}", "WARN")

            self.log(f"Agent QA pairs: {results['agent_qa_count']}", "SUCCESS")
            self.log(f"KB QA pairs: {results['kb_qa_count']}", "SUCCESS")
            self.log(f"Total QA pairs: {results['total_qa_count']}", "SUCCESS")

            if results.get("errors"):
                for err in results["errors"]:
                    self.log(f"Error: {err}", "WARN")

            return results["total_qa_count"] > 0

        except Exception as e:
            self.log(f"Eval generation failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    # =========================================================================
    # STEP 1B: Test KB QA Generation (with direct kb_token)
    # =========================================================================
    async def test_kb_qa_generation(self) -> bool:
        """Test QA pair generation from knowledge base using kb_token."""
        if not self.kb_token:
            self.log("No KB token provided, skipping KB QA generation", "WARN")
            return True

        self.log("=" * 60)
        self.log("STEP 1B: Testing KB QA Generation", "INFO")
        self.log(f"KB Token: {self.kb_token}", "INFO")
        self.log("=" * 60)

        try:
            # Use EvalGenerator to generate KB QA pairs
            generator = EvalGenerator(self.agent_id)

            # Check if KB QA pairs already exist (unless force_regenerate is True)
            existing_kb_qa = generator._kb_qa_pairs_exist(self.kb_token)
            if existing_kb_qa > 0 and not self.force_regenerate:
                self.log(f"SKIPPED: KB QA pairs already exist ({existing_kb_qa} pairs)", "WARN")
                self.results["kb_generation"] = {
                    "kb_token": self.kb_token,
                    "skipped": True,
                    "existing_count": existing_kb_qa,
                }
                return True

            # Fetch KB documents
            self.log("Fetching KB documents...")
            documents = await generator._fetch_kb_documents(self.kb_token)

            if not documents:
                self.log("No documents found in KB", "ERROR")
                return False

            self.log(f"Found {len(documents)} documents in KB", "SUCCESS")

            # Generate QA pairs from KB documents
            self.log("Generating QA pairs from KB documents...")
            kb_qa_pairs = await generator._generate_kb_qa_pairs(documents, f"KB-{self.kb_token[:8]}")

            if not kb_qa_pairs:
                self.log("No QA pairs generated from KB", "ERROR")
                return False

            # Save KB QA pairs to kb_qa_pairs collection
            saved_count = await generator._save_kb_qa_pairs(kb_qa_pairs, self.kb_token)

            self.results["kb_generation"] = {
                "kb_token": self.kb_token,
                "documents_count": len(documents),
                "qa_pairs_generated": len(kb_qa_pairs),
                "qa_pairs_saved": saved_count,
            }

            self.log(f"KB documents processed: {len(documents)}", "SUCCESS")
            self.log(f"KB QA pairs generated: {len(kb_qa_pairs)}", "SUCCESS")
            self.log(f"KB QA pairs saved: {saved_count}", "SUCCESS")

            # Print sample KB QA pairs
            if kb_qa_pairs:
                self.log("\nSample KB QA Pairs:", "INFO")
                for i, qa in enumerate(kb_qa_pairs[:3]):
                    self.log(f"  Q{i+1}: {qa.question[:80]}...")
                    self.log(f"  A{i+1}: {qa.answer[:80]}...")
                    self.log(f"  Keywords: {qa.keywords[:5]}")
                    self.log("")

            return saved_count > 0

        except Exception as e:
            self.log(f"KB QA generation failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    # =========================================================================
    # STEP 2: Verify QA Pairs in MongoDB
    # =========================================================================
    def test_mongodb_qa_pairs(self) -> bool:
        """Verify QA pairs are saved correctly in MongoDB."""
        self.log("=" * 60)
        self.log("STEP 2: Verifying QA Pairs in MongoDB", "INFO")
        self.log("=" * 60)

        try:
            # Get agent QA pairs from agent_qa_pairs collection
            agent_pairs = get_agent_qa_pairs(self.agent_id)
            self.log(f"Found {len(agent_pairs)} agent QA pairs in agent_qa_pairs collection")

            # Get KB QA pairs from kb_qa_pairs collection
            kb_pairs = get_kb_qa_pairs(self.agent_id)
            self.log(f"Found {len(kb_pairs)} KB QA pairs in kb_qa_pairs collection")

            # Combine for total
            all_pairs = agent_pairs + kb_pairs
            self.log(f"Total QA pairs: {len(all_pairs)}")

            self.results["mongodb_verification"] = {
                "total_pairs": len(all_pairs),
                "agent_pairs": len(agent_pairs),
                "kb_pairs": len(kb_pairs),
            }

            self.log(f"Agent QA pairs (agent_qa_pairs): {len(agent_pairs)}", "SUCCESS")
            self.log(f"KB QA pairs (kb_qa_pairs): {len(kb_pairs)}", "INFO")

            # Print sample QA pairs
            if all_pairs:
                self.log("\nSample QA Pairs:", "INFO")
                for i, qa in enumerate(all_pairs[:3]):
                    self.log(f"  Q{i+1}: {qa['question'][:80]}...")
                    self.log(f"  A{i+1}: {qa['answer'][:80]}...")
                    self.log(f"  Source: {qa.get('source', 'unknown')}")
                    self.log(f"  Keywords: {qa.get('keywords', [])[:5]}")
                    self.log("")

            return len(all_pairs) > 0

        except Exception as e:
            self.log(f"MongoDB verification failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    # =========================================================================
    # STEP 3: Test Call Evaluation
    # =========================================================================
    async def test_call_evaluation(self, custom_transcript: List[Dict] = None) -> bool:
        """Test call evaluation with a sample or custom transcript."""
        self.log("=" * 60)
        self.log("STEP 3: Testing Call Evaluation", "INFO")
        self.log("=" * 60)

        try:
            # Get all QA pairs (agent + KB) to create a realistic transcript
            qa_pairs = get_all_qa_pairs_for_agent(self.agent_id)

            if not qa_pairs:
                self.log("No QA pairs found, cannot run evaluation test", "ERROR")
                return False

            # Create test transcript from actual QA pairs
            if custom_transcript:
                transcript = custom_transcript
            else:
                transcript = self._create_test_transcript(qa_pairs)

            self.log(f"Test transcript has {len(transcript)} turns")

            # Create sample turn metrics (simulating pipecat observer data)
            turn_metrics = self._create_sample_turn_metrics(len(transcript) // 2)

            # Run evaluation
            self.log("Running voice call evaluation...")
            result = await evaluate_voice_call(
                session_id=self.test_session_id,
                agent_id=self.agent_id,
                transcript=transcript,
                turn_metrics=turn_metrics,
            )

            self.results["evaluation"] = {
                "session_id": result.get("session_id"),
                "total_turns_evaluated": len(result.get("evaluation_results", [])),
                "quality_metrics": result.get("quality_metrics", {}),
            }

            # Print evaluation results
            quality = result.get("quality_metrics", {})
            self.log(f"Evaluation completed for session: {self.test_session_id}", "SUCCESS")
            self.log(f"Total turns evaluated: {quality.get('total_turns', 0)}")
            self.log(f"Questions matched: {quality.get('questions_matched', 0)}")
            self.log(f"Average similarity: {quality.get('avg_similarity', 0):.2f}")
            self.log(f"Average relevancy: {quality.get('avg_relevancy', 0):.2f}")
            self.log(f"Average completeness: {quality.get('avg_completeness', 0):.2f}")
            self.log(f"Average accuracy: {quality.get('avg_accuracy', 0):.2f}")
            self.log(f"Overall quality score: {quality.get('overall_quality_score', 0):.2f}", "SUCCESS")

            return True

        except Exception as e:
            self.log(f"Call evaluation failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    def _create_test_transcript(self, qa_pairs: List[Dict]) -> List[Dict]:
        """Create a test transcript from QA pairs."""
        transcript = []

        # Use first 3-5 QA pairs to create conversation
        for qa in qa_pairs[:5]:
            # User message
            transcript.append({
                "role": "user",
                "content": qa["question"]
            })
            # Agent response (slightly modified to test matching)
            transcript.append({
                "role": "assistant",
                "content": qa["answer"]
            })

        # Add one off-topic question to test "question not found"
        transcript.append({
            "role": "user",
            "content": "What is the weather like today?"
        })
        transcript.append({
            "role": "assistant",
            "content": "I'm sorry, I don't have access to weather information."
        })

        return transcript

    def _create_sample_turn_metrics(self, num_turns: int) -> Dict:
        """Create sample turn metrics simulating pipecat observer data."""
        metrics = {}
        for i in range(1, num_turns + 1):
            metrics[i] = {
                "llm_cost": 0.001 * i,
                "stt_cost": 0.0005 * i,
                "tts_cost": 0.0008 * i,
                "llm_latency": 150 + (i * 10),
                "stt_latency": 50 + (i * 5),
                "tts_latency": 100 + (i * 8),
                "llm_ttfb": 0.1 + (i * 0.01),
                "stt_ttfb": 0.05,
                "tts_ttfb": 0.08,
            }
        return metrics

    # =========================================================================
    # STEP 4: Verify Metrics in MongoDB
    # =========================================================================
    def test_mongodb_metrics(self) -> bool:
        """Verify evaluation metrics are saved correctly in MongoDB."""
        self.log("=" * 60)
        self.log("STEP 4: Verifying Metrics in MongoDB", "INFO")
        self.log("=" * 60)

        try:
            # Check evaluation results collection
            eval_results = list(CallEvaluationResultModel._get_collection().find({
                "session_id": self.test_session_id
            }))

            self.log(f"Found {len(eval_results)} evaluation results in MongoDB")

            # Check quality metrics collection
            quality_metrics = CallQualityMetricsModel._get_collection().find_one({
                "session_id": self.test_session_id
            })

            # Check questions not found collection
            not_found = list(QuestionNotFoundModel._get_collection().find({
                "session_id": self.test_session_id
            }))

            self.results["metrics_verification"] = {
                "eval_results_count": len(eval_results),
                "quality_metrics_saved": quality_metrics is not None,
                "questions_not_found": len(not_found),
            }

            if eval_results:
                self.log(f"Evaluation results saved: {len(eval_results)}", "SUCCESS")
                # Print sample result
                sample = eval_results[0]
                self.log(f"  Sample - Turn {sample.get('turn_number')}:")
                self.log(f"    Question found: {sample.get('question_found')}")
                self.log(f"    Similarity: {sample.get('similarity', 0):.2f}")
                self.log(f"    Relevancy: {sample.get('relevancy', 0):.2f}")
                self.log(f"    Overall quality: {sample.get('overall_quality', 0):.2f}")

            if quality_metrics:
                self.log("Quality metrics saved successfully", "SUCCESS")
                self.log(f"  Total turns: {quality_metrics.get('total_turns')}")
                self.log(f"  Overall quality score: {quality_metrics.get('overall_quality_score', 0):.2f}")

            if not_found:
                self.log(f"Questions not found recorded: {len(not_found)}", "WARN")
                for q in not_found:
                    self.log(f"  - {q.get('user_question', '')[:50]}...")

            return len(eval_results) > 0 and quality_metrics is not None

        except Exception as e:
            self.log(f"Metrics verification failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    # =========================================================================
    # Cleanup
    # =========================================================================
    def cleanup_test_data(self, cleanup: bool = False):
        """Clean up test data from MongoDB."""
        if not cleanup:
            return

        self.log("=" * 60)
        self.log("Cleaning up test data...", "INFO")
        self.log("=" * 60)

        try:
            # Delete test evaluation results
            result1 = CallEvaluationResultModel._get_collection().delete_many({
                "session_id": self.test_session_id
            })
            self.log(f"Deleted {result1.deleted_count} evaluation results")

            # Delete test quality metrics
            result2 = CallQualityMetricsModel._get_collection().delete_many({
                "session_id": self.test_session_id
            })
            self.log(f"Deleted {result2.deleted_count} quality metrics")

            # Delete test questions not found
            result3 = QuestionNotFoundModel._get_collection().delete_many({
                "session_id": self.test_session_id
            })
            self.log(f"Deleted {result3.deleted_count} questions not found records")

            self.log("Cleanup completed", "SUCCESS")

        except Exception as e:
            self.log(f"Cleanup failed: {e}", "ERROR")

    # =========================================================================
    # Run All Tests
    # =========================================================================
    async def run_all_tests(self, skip_generation: bool = False, cleanup: bool = False) -> Dict:
        """Run all end-to-end tests."""
        self.log("=" * 60)
        self.log("EVAL SYSTEM END-TO-END TEST", "INFO")
        self.log(f"Agent ID: {self.agent_id}", "INFO")
        self.log(f"Test Session ID: {self.test_session_id}", "INFO")
        self.log("=" * 60)

        test_results = {
            "agent_id": self.agent_id,
            "test_session_id": self.test_session_id,
            "tests": {},
        }

        # Step 1: Eval Generation
        if not skip_generation:
            test_results["tests"]["generation"] = await self.test_eval_generation()
        else:
            self.log("Skipping eval generation (using existing QA pairs)", "WARN")
            test_results["tests"]["generation"] = True

        # Step 1B: KB QA Generation (if kb_token provided)
        if self.kb_token:
            test_results["tests"]["kb_generation"] = await self.test_kb_qa_generation()

        # Step 2: MongoDB QA Pairs Verification
        test_results["tests"]["mongodb_qa_pairs"] = self.test_mongodb_qa_pairs()

        # Step 3: Call Evaluation
        if test_results["tests"]["mongodb_qa_pairs"]:
            test_results["tests"]["call_evaluation"] = await self.test_call_evaluation()
        else:
            self.log("Skipping call evaluation - no QA pairs available", "ERROR")
            test_results["tests"]["call_evaluation"] = False

        # Step 4: MongoDB Metrics Verification
        if test_results["tests"]["call_evaluation"]:
            test_results["tests"]["mongodb_metrics"] = self.test_mongodb_metrics()
        else:
            self.log("Skipping metrics verification - evaluation failed", "ERROR")
            test_results["tests"]["mongodb_metrics"] = False

        # Summary
        self.log("=" * 60)
        self.log("TEST SUMMARY", "INFO")
        self.log("=" * 60)

        all_passed = all(test_results["tests"].values())
        for test_name, passed in test_results["tests"].items():
            status = "PASS" if passed else "FAIL"
            level = "SUCCESS" if passed else "ERROR"
            self.log(f"{test_name}: {status}", level)

        self.log("")
        if all_passed:
            self.log("ALL TESTS PASSED!", "SUCCESS")
        else:
            self.log("SOME TESTS FAILED!", "ERROR")

        # Cleanup if requested
        self.cleanup_test_data(cleanup)

        return test_results


async def main():
    parser = argparse.ArgumentParser(description="End-to-End Test for Eval System")
    parser.add_argument("--agent_id", default=DEFAULT_AGENT_ID,
                       help="Agent handle/ID to test (or set DEFAULT_AGENT_ID in file)")
    parser.add_argument("--kb_token", default=DEFAULT_KB_TOKEN,
                       help="Knowledge base token for KB QA generation (optional)")
    parser.add_argument("--skip-generation", action="store_true",
                       help="Skip QA generation and use existing pairs")
    parser.add_argument("--force", action="store_true",
                       help="Force regenerate QA pairs even if they already exist")
    parser.add_argument("--cleanup", action="store_true",
                       help="Clean up test data after running")
    parser.add_argument("--quiet", action="store_true",
                       help="Reduce output verbosity")

    args = parser.parse_args()

    # Check if agent_id is provided
    if args.agent_id == "your-agent-id-here":
        print("ERROR: Please provide agent_id via --agent_id flag or set DEFAULT_AGENT_ID in file")
        print("Example: python -m super_services.evals.test_eval_flow_e2e --agent_id my-agent")
        sys.exit(1)

    tester = EvalFlowE2ETester(
        agent_id=args.agent_id,
        kb_token=args.kb_token if args.kb_token else None,
        force_regenerate=args.force,
        verbose=not args.quiet
    )

    results = await tester.run_all_tests(
        skip_generation=args.skip_generation,
        cleanup=args.cleanup
    )

    # Exit with appropriate code
    sys.exit(0 if all(results["tests"].values()) else 1)


if __name__ == "__main__":
    asyncio.run(main())
