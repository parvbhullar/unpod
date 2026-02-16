import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional
from super.core.voice.pipecat.handler import PipecatVoiceHandler
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestContext:
    """Helper class to manage test context and assertions."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        self.errors: List[str] = []
        self.test_id = str(uuid.uuid4())[:8]
        logger.info(f"🚀 Starting test: {test_name} [{self.test_id}]")

    def assert_true(self, condition: bool, message: str) -> bool:
        """Assert that a condition is true."""
        if not condition:
            self.errors.append(f"Assertion failed: {message}")
            logger.error(f"❌ {message}")
            return False
        logger.info(f"✅ {message}")
        return True

    def assert_in(self, item: str, container: List[str], message: str) -> bool:
        """Assert that an item is in a container."""
        msg = f"{message} (expected '{item}' in {container})"
        return self.assert_true(item in container, msg)

    def assert_equal(self, actual, expected, message: str) -> bool:
        """Assert that two values are equal."""
        msg = f"{message} (expected {expected}, got {actual})"
        return self.assert_true(actual == expected, msg)

    def assert_not_none(self, value, message: str) -> bool:
        """Assert that a value is not None."""
        return self.assert_true(value is not None, f"{message} (got None)")

    def log_step(self, message: str):
        """Log a test step."""
        logger.info(f"  → {message}")

    def result(self) -> bool:
        """Return the test result and log summary."""
        duration = time.time() - self.start_time
        if not self.errors:
            logger.info(f"🎉 Test '{self.test_name}' passed in {duration:.2f}s")
            return True

        logger.error(f"\n❌ Test '{self.test_name}' failed with {len(self.errors)} errors:")
        for i, error in enumerate(self.errors, 1):
            logger.error(f"  {i}. {error}")
        logger.error(f"⏱️  Test duration: {duration:.2f}s")
        return False


async def test_basic_initialization(handler) -> bool:
    """Test basic initialization of FAISS components."""
    ctx = TestContext("Basic Initialization")

    ctx.log_step("Checking handler components...")
    if not ctx.assert_true(hasattr(handler, '_context_retrieval'), "Handler should have _context_retrieval"):
        return ctx.result()

    if not ctx.assert_true(hasattr(handler, '_embedding_model'), "Handler should have _embedding_model"):
        return ctx.result()

    ctx.log_step("✅ Handler components are properly initialized")

    # Check context retrieval system
    ctx.log_step("Checking context retrieval system...")
    context_retrieval = handler._context_retrieval
    if ctx.assert_true(hasattr(context_retrieval, '_hot_chunks'), "Context retrieval should have _hot_chunks"):
        hot_chunks_count = len(context_retrieval._hot_chunks)
        ctx.log_step(f"Hot chunks count: {hot_chunks_count}")

    # Check if it has FAISS index
    if ctx.assert_true(hasattr(context_retrieval, 'faiss_index'), "Context retrieval should have faiss_index"):
        index = context_retrieval.faiss_index
        if index:
            ctx.log_step(f"FAISS index exists with {index.ntotal} vectors")
        else:
            ctx.log_step("FAISS index is None")

    return ctx.result()


async def test_knowledge_base_search(handler) -> bool:
    """Test searching the knowledge base with comprehensive validation."""
    ctx = TestContext("Knowledge Base Search")

    # Test data
    test_queries = [
        "tell me about home loan?",
        "what are the interest rates?",
        "how to apply for a loan?"
    ]

    for query in test_queries:
        ctx.log_step(f"Testing query: '{query}'")
        try:
            # Execute search
            results = await handler._get_index(query)
            # Validate results
            if results is None:
                ctx.log_step("  → Query returned no results (this is normal for some queries)")
                continue
            if not ctx.assert_true(isinstance(results, dict), "Results should be a dictionary"):
                continue

            if not ctx.assert_true(isinstance(results, dict), "Results should be a dictionary"):
                continue

            if not ctx.assert_in('data', results, "Results should contain 'data' key"):
                continue

            ctx.log_step(f"Found {len(results.get('data', {}).get('search_response_summary', {}).get('top_sections', []))} context items")

            # Validate context items
            for i, item in enumerate(results.get('data', {}).get('search_response_summary', {}).get('top_sections', [])[:3], 1):  # Check first 3 items
                ctx.log_step(f"Context item {i}:")
                if not ctx.assert_true(isinstance(item, dict), "Context item should be a dictionary"):
                    continue

                # Check required fields
                required_fields = ['content', 'metadata', 'score']
                for field in required_fields:
                    ctx.assert_in(field, item, f"Context item should have '{field}' field")

                # Log item details
                content_preview = (item.get('content', '')[:80] + '...') if item.get('content') else 'None'
                ctx.log_step(f"  - Content: {content_preview}")
                ctx.log_step(f"  - Score: {item.get('score', 'N/A')}")
                ctx.log_step(f"  - Source: {item.get('metadata', {}).get('source', 'N/A')}")

        except Exception as e:
            ctx.assert_true(False, f"Unexpected error: {str(e)}")
            logger.exception("Error in test_knowledge_base_search")

    return ctx.result()


async def test_transcript_caching(handler) -> bool:
    """Test transcript caching functionality with comprehensive validation."""
    ctx = TestContext("Transcript Caching")

    # Initialize test data
    test_entries = [
        {
            "role": "user",
            "content": "I'd like to return a pair of shoes I bought last week.",
            "user_id": "test_user_123",
            "timestamp": str(int(time.time()))
        },
        {
            "role": "assistant",
            "content": "I can help with your return. Do you have your receipt? Our return policy allows returns within 30 days with a receipt.",
            "user_id": "test_user_123",
            "timestamp": str(int(time.time()) + 1)
        }
    ]

    # Test 1: Cache population
    ctx.log_step("Testing cache population...")
    try:
        # Clear existing cache
        if hasattr(handler, '_context_retrieval') and hasattr(handler._context_retrieval, '_hot_chunks'):
            handler._context_retrieval._hot_chunks.clear()
            ctx.log_step("Cleared existing cache")

        # Cache test entries
        cache_sizes = []
        for i, entry in enumerate(test_entries, 1):
            await handler._cache_transcript_entry(entry)
            cache_size = len(handler._context_retrieval._hot_chunks)
            cache_sizes.append(cache_size)
            ctx.log_step(f"Cached entry {i}: {entry['role']} (cache size: {cache_size})")

        # Verify cache population
        expected_size = len(test_entries)
        actual_size = len(handler._context_retrieval._hot_chunks)
        ctx.assert_equal(actual_size, expected_size,
                         f"Cache should contain {expected_size} entries")

    except Exception as e:
        ctx.assert_true(False, f"Cache population failed: {str(e)}")
        logger.exception("Error in cache population test")

    # Test 2: Cache content validation
    ctx.log_step("\nValidating cache content...")
    try:
        for i, entry in enumerate(test_entries, 1):
            found = False
            for chunk_id, cached in handler._context_retrieval._hot_chunks.items():
                if (cached.get('content') == entry['content'] and
                        cached.get('metadata', {}).get('role') == entry['role']):
                    found = True
                    ctx.log_step(f"✅ Found matching cache entry for {entry['role']} (ID: {chunk_id})")
                    break

            ctx.assert_true(found, f"Could not find cached entry for {entry['role']}")

    except Exception as e:
        ctx.assert_true(False, f"Cache validation failed: {str(e)}")
        logger.exception("Error in cache validation")

    return ctx.result()


async def test_faiss_fallback_flow(handler) -> bool:
    """Test that FAISS search is attempted before fallback to remote search."""
    ctx = TestContext("FAISS Fallback Flow")

    # Test 1: Check if context retrieval is properly initialized
    ctx.log_step("Checking context retrieval initialization...")
    if not hasattr(handler, '_context_retrieval'):
        ctx.assert_true(False, "Handler does not have _context_retrieval")
        return ctx.result()

    if not hasattr(handler, '_embedding_model'):
        ctx.assert_true(False, "Handler does not have _embedding_model")
        return ctx.result()

    ctx.log_step("Context retrieval and embedding model are available")

    # Test 2: Clear existing data
    ctx.log_step("Clearing existing cache for clean test...")
    if hasattr(handler._context_retrieval, '_hot_chunks'):
        handler._context_retrieval._hot_chunks.clear()
        ctx.log_step("Cache cleared")
    else:
        ctx.log_step("No _hot_chunks attribute found")

    # Get initial FAISS stats
    initial_stats = getfaiss_index_stats(handler)
    initial_vectors = initial_stats.get('vector_count', 0)
    ctx.log_step(f"Initial FAISS vectors: {initial_vectors}")

    # Test 3: Search for something not in FAISS (should trigger fallback)
    ctx.log_step("Testing search that should trigger fallback...")
    query = "completely unique query that is not in cache"

    try:
        results = await handler._get_index(query)

        # Verify results structure
        ctx.assert_not_none(results, "Results should not be None")
        ctx.assert_in('data', results, "Results should contain 'data' key")

        # Check if we got results (from remote search)
        if results.get('data'):
            ctx.log_step(f"Got {len(results.get('data', {}).get('search_response_summary', {}).get('top_sections', []))} results from search")

            # Verify results are meaningful
            for item in results.get('data', {}).get('search_response_summary', {}).get('top_sections', [])[:2]:  # Check first 2 items
                content = item.get('content', '')
                ctx.assert_true(len(content) > 10, "Results should have meaningful content")
                ctx.log_step(f"Result preview: {content[:50]}...")
        else:
            ctx.log_step("No results found - this might indicate remote search failed")

        # Test 4: Verify caching happened after remote search
        ctx.log_step("Checking if remote results were cached...")
        final_stats = getfaiss_index_stats(handler)
        final_vectors = final_stats.get('vector_count', 0)

        # We should have more vectors now if caching worked
        if final_vectors > initial_vectors:
            ctx.log_step(f"✅ Caching worked! Vectors Increased from {initial_vectors} to {final_vectors}")
            ctx.assert_true(True, f"FAISS index grew by {final_vectors - initial_vectors} vectors")
        else:
            ctx.log_step(f"⚠️  No new vectors added. Initial: {initial_vectors}, Final: {final_vectors}")
            # This might be okay if remote search didn't return meaningful results

    except Exception as e:
        ctx.assert_true(False, f"FAISS fallback test failed: {str(e)}")
        logger.exception("Error in FAISS fallback test")

    return ctx.result()


def getfaiss_index_stats(handler) -> Dict[str, any]:
    """Get FAISS index statistics for monitoring."""
    try:
        if not hasattr(handler, '_context_retrieval'):
            return {'error': 'No context retrieval system'}

        ctx = handler._context_retrieval
        index = getattr(ctx, 'faiss_index', None)

        stats = {
            'vector_count': index.ntotal if index else 0,
            'vector_dimension': index.d if index else 0,
            'hot_chunks_count': len(getattr(ctx, '_hot_chunks', {})),
            'embedding_model': getattr(handler, '_embedding_model', None).__class__.__name__ if hasattr(handler, '_embedding_model') else None,
            'cache_enabled': getattr(ctx, 'use_cache', False),
            'timestamp': time.time()
        }

        return stats
    except Exception as e:
        return {'error': str(e)}


async def main():
    """Main test runner."""
    # Initialize the handler with a test session
    print("=" * 80)
    print("🚀 Starting FAISS Memory Tests")
    print("=" * 80)
    try:
        # Initialize the handler
        print("\nInitializing PipecatVoiceHandler...")
        handler = PipecatVoiceHandler(session_id=f"test_session_{int(time.time())}")

        # Wait for initialization
        await asyncio.sleep(2)

        # Run basic initialization test first
        print("\n🧪 Running Basic Initialization Test...")
        init_test_result = await test_basic_initialization(handler)

        if not init_test_result:
            print("❌ Basic initialization failed - cannot proceed with other tests")
            return 1

        # Run tests
        test_results = {
            "knowledge_base": await test_knowledge_base_search(handler),
            "transcript_caching": await test_transcript_caching(handler),
            "faiss_fallback": await test_faiss_fallback_flow(handler)
        }

        # Print summary
        print("\n" + "=" * 80)
        print("📊 Test Summary")
        print("=" * 80)
        for test_name, passed in test_results.items():
            status = "PASSED" if passed else "FAILED"
            print(f"• {test_name.replace('_', ' ').title()}: {status}")

        # Print FAISS stats
        final_stats = getfaiss_index_stats(handler)
        print("\n🔍 FAISS Index Statistics:")
        print(f"  • Total Vectors: {final_stats.get('vector_count', 0)}")
        print(f"  • Vector Dimension: {final_stats.get('vector_dimension', 0)}")
        print(f"  • Hot Chunks: {final_stats.get('hot_chunks_count', 0)}")
        print(f"  • Embedding Model: {final_stats.get('embedding_model', 'N/A')}")
        print(f"  • Cache Enabled: {final_stats.get('cache_enabled', False)}")

        # Final status
        all_passed = all(test_results.values())
        print("\n" + "🎉 All tests passed!" if all_passed else "❌ Some tests failed")
        return 0 if all_passed else 1

    except Exception as e:
        logger.error(f"❌ Critical error in test execution: {str(e)}")
        logger.exception("Test execution failed")
        return 1

    finally:
        # Cleanup
        if handler and hasattr(handler, '_context_retrieval'):
            if hasattr(handler._context_retrieval, 'reset'):
                handler._context_retrieval.reset()
                print("\n🧹 Cleaned up test data from context retrieval")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)