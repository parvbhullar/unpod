"""
Example Usage: Context Cache with Testing

Demonstrates how to:
1. Set up the context cache system
2. Add vectors and perform searches
3. Monitor performance metrics
4. Validate against targets
"""

import asyncio
import logging
import numpy as np
from typing import Dict

from .context_cache import (
    HighPerformanceContextRetrieval,
    CacheConfig,
    create_context_retrieval
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def mock_database_fetch(chunk_id: int) -> Dict:
    """Simulate database fetch"""
    await asyncio.sleep(0.001)  # 1ms latency
    return {
        "chunk_id": chunk_id,
        "content": f"This is the content for chunk {chunk_id}",
        "metadata": {
            "source": "documentation.pdf",
            "page": chunk_id // 10,
            "relevance_score": 0.95
        }
    }


async def example_basic_usage():
    """Example 1: Basic setup and search"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Context Retrieval")
    print("="*80 + "\n")

    # Create retrieval system using factory function
    retrieval = create_context_retrieval(
        vector_count=10_000,  # Expected scale
        embedding_dim=768,     # OpenAI ada-002 or similar
        use_redis=False        # Single-worker mode
    )

    # Generate sample embeddings (in production, use your embedding model)
    np.random.seed(42)
    num_docs = 100
    embeddings = np.random.randn(num_docs, 768).astype(np.float32)
    chunk_ids = list(range(num_docs))

    # Add vectors to index
    retrieval.add_vectors(embeddings, chunk_ids)
    logger.info(f"✓ Added {num_docs} document chunks to index")

    # Perform a search
    query_embedding = embeddings[5]  # Simulate user query
    chunk_ids, metrics = await retrieval.search_context(query_embedding, k=5)

    logger.info(f"\nSearch Results:")
    logger.info(f"  Found {len(chunk_ids)} relevant chunks")
    logger.info(f"  Chunk IDs: {chunk_ids}")
    logger.info(f"  Search latency: {metrics.total_latency_ms:.2f}ms")
    logger.info(f"  FAISS search: {metrics.faiss_search_ms:.2f}ms")

    # Cleanup
    await retrieval.cleanup()


async def example_full_pipeline():
    """Example 2: Full retrieval pipeline with chunk fetching"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Full Pipeline with Content Retrieval")
    print("="*80 + "\n")

    config = CacheConfig(
        vector_count=50_000,
        embedding_dim=384,     # sentence-transformers
        use_redis=False,
        hot_cache_size=256,
        query_cache_size=1024
    )

    retrieval = HighPerformanceContextRetrieval(config)

    # Add documents
    num_docs = 200
    embeddings = np.random.randn(num_docs, config.embedding_dim).astype(np.float32)
    retrieval.add_vectors(embeddings, list(range(num_docs)))

    # Full pipeline: search + fetch
    query = embeddings[42]
    chunks, stats = await retrieval.retrieve_context(
        query,
        k=5,
        db_fetch_callback=mock_database_fetch
    )

    logger.info(f"\nFull Pipeline Results:")
    logger.info(f"  Retrieved {len(chunks)} chunks")
    logger.info(f"  Total latency: {stats['total_latency_ms']:.2f}ms")
    logger.info(f"  Search latency: {stats['search_latency_ms']:.2f}ms")
    logger.info(f"  Fetch latency: {stats['fetch_latency_ms']:.2f}ms")
    logger.info(f"  Target met: {'✓' if stats['target_met'] else '✗'}")

    # Display chunks
    logger.info(f"\nRetrieved Chunks:")
    for i, chunk in enumerate(chunks):
        logger.info(f"  {i+1}. Chunk {chunk['chunk_id']}: {chunk['content'][:50]}...")

    await retrieval.cleanup()


async def example_performance_monitoring():
    """Example 3: Performance monitoring and reporting"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Performance Monitoring")
    print("="*80 + "\n")

    retrieval = create_context_retrieval(
        vector_count=100_000,
        embedding_dim=256,
        use_redis=False
    )

    # Add vectors
    num_vectors = 500
    embeddings = np.random.randn(num_vectors, 256).astype(np.float32)
    retrieval.add_vectors(embeddings, list(range(num_vectors)))

    # Perform multiple searches to collect metrics
    logger.info("Running 20 test queries...")
    for i in range(20):
        query = np.random.randn(256).astype(np.float32)
        await retrieval.search_context(query, k=10)

    # Generate performance report
    report = retrieval.get_performance_report()

    logger.info(f"\nPerformance Report:")
    logger.info(f"{'='*60}")
    logger.info(f"Index Type: {report['index_type']}")
    logger.info(f"Vector Count: {report['vector_count']:,}")
    logger.info(f"Total Queries: {report['total_queries']}")
    logger.info(f"\nLatency Metrics (ms):")
    logger.info(f"  Average:  {report['latency']['avg_ms']:>8.2f}")
    logger.info(f"  Median:   {report['latency']['p50_ms']:>8.2f}")
    logger.info(f"  P95:      {report['latency']['p95_ms']:>8.2f}")
    logger.info(f"  P99:      {report['latency']['p99_ms']:>8.2f}")
    logger.info(f"\nExpected Range: {report['latency']['expected_range'][0]}-{report['latency']['expected_range'][1]}ms")
    logger.info(f"Target Met: {'✓ YES' if report['performance_validation']['target_met'] else '✗ NO'}")

    await retrieval.cleanup()


async def example_cache_effectiveness():
    """Example 4: Cache effectiveness demonstration"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Cache Effectiveness (Hot vs Cold)")
    print("="*80 + "\n")

    retrieval = create_context_retrieval(
        vector_count=10_000,
        embedding_dim=128,
        use_redis=False
    )

    # Setup
    embeddings = np.random.randn(100, 128).astype(np.float32)
    retrieval.add_vectors(embeddings, list(range(100)))

    query = embeddings[10]

    # Cold query (first time)
    logger.info("Executing cold query (first time)...")
    _, metrics_cold = await retrieval.search_context(query, k=5)

    # Hot query (cached)
    logger.info("Executing hot query (cached)...")
    _, metrics_hot = await retrieval.search_context(query, k=5)

    logger.info(f"\nCache Performance:")
    logger.info(f"  Cold path: {metrics_cold.total_latency_ms:.2f}ms")
    logger.info(f"  Hot path:  {metrics_hot.total_latency_ms:.2f}ms")

    if metrics_hot.total_latency_ms < metrics_cold.total_latency_ms:
        speedup = metrics_cold.total_latency_ms / metrics_hot.total_latency_ms
        improvement = ((metrics_cold.total_latency_ms - metrics_hot.total_latency_ms) / metrics_cold.total_latency_ms) * 100
        logger.info(f"  Speedup:   {speedup:.2f}x")
        logger.info(f"  Improvement: {improvement:.1f}%")

    await retrieval.cleanup()


async def example_voice_ai_scenario():
    """Example 5: Voice AI real-time scenario"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Voice AI Real-Time Scenario")
    print("="*80 + "\n")
    print("Budget: 800ms total (50ms retrieval + 750ms LLM)")
    print("-"*80 + "\n")

    # Voice AI optimized configuration
    config = CacheConfig(
        vector_count=50_000,
        embedding_dim=768,
        use_redis=False,  # Process-local for minimal latency
        hot_cache_size=512,  # Larger hot cache for common queries
        nprobe=10  # Balance speed vs accuracy
    )

    retrieval = HighPerformanceContextRetrieval(config)

    # Simulate knowledge base
    num_kb_chunks = 1_000
    kb_embeddings = np.random.randn(num_kb_chunks, 768).astype(np.float32)
    retrieval.add_vectors(kb_embeddings, list(range(num_kb_chunks)))

    # Simulate voice query
    logger.info("User: 'What's your return policy?'")
    logger.info("System: Embedding query...")

    voice_query = kb_embeddings[42]  # Simulated query embedding

    # Retrieve context (must be <50ms)
    chunks, stats = await retrieval.retrieve_context(
        voice_query,
        k=5,
        db_fetch_callback=mock_database_fetch
    )

    logger.info(f"\nRetrieval Stats:")
    logger.info(f"  Total latency: {stats['total_latency_ms']:.2f}ms")
    logger.info(f"  Search: {stats['search_latency_ms']:.2f}ms")
    logger.info(f"  Fetch: {stats['fetch_latency_ms']:.2f}ms")
    logger.info(f"  Budget compliance: {'✓ PASS' if stats['total_latency_ms'] < 50 else '✗ FAIL'}")

    if stats['total_latency_ms'] < 50:
        remaining_budget = 800 - stats['total_latency_ms']
        logger.info(f"  Remaining for LLM: {remaining_budget:.2f}ms")
        logger.info(f"\n✓ Ready for real-time voice interaction!")
    else:
        logger.warning(f"\n✗ Exceeds budget - optimization needed")

    await retrieval.cleanup()


async def example_index_persistence():
    """Example 6: Saving and loading indices"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Index Persistence")
    print("="*80 + "\n")

    # Create and populate index
    retrieval1 = create_context_retrieval(
        vector_count=10_000,
        embedding_dim=256,
        use_redis=False
    )

    embeddings = np.random.randn(200, 256).astype(np.float32)
    retrieval1.add_vectors(embeddings, list(range(200)))
    logger.info("✓ Created and populated index with 200 vectors")

    # Save to disk
    index_path = "/tmp/context_cache_index.faiss"
    retrieval1.save_index(index_path)
    logger.info(f"✓ Saved index to {index_path}")

    await retrieval1.cleanup()

    # Load into new instance
    retrieval2 = create_context_retrieval(
        vector_count=10_000,
        embedding_dim=256,
        use_redis=False
    )
    retrieval2.load_index(index_path)
    logger.info(f"✓ Loaded index ({retrieval2.faiss_index.ntotal} vectors)")

    # Verify it works
    query = embeddings[5]
    results, metrics = await retrieval2.search_context(query, k=5)
    logger.info(f"✓ Search successful: found {len(results)} results in {metrics.total_latency_ms:.2f}ms")

    await retrieval2.cleanup()


async def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("CONTEXT CACHE - EXAMPLE USAGE")
    print("="*80)

    await example_basic_usage()
    await example_full_pipeline()
    await example_performance_monitoring()
    await example_cache_effectiveness()
    await example_voice_ai_scenario()
    await example_index_persistence()

    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())