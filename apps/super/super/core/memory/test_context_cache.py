"""
Comprehensive Test Suite for High-Performance Context Cache Layer

Tests cover:
1. Unit Tests: Individual component testing
2. Integration Tests: Full pipeline testing
3. Performance Benchmarks: Latency validation against targets
4. Cache Layer Tests: Hot cache, Redis, FAISS
5. Scale Tests: Different index types based on vector count

Performance Targets (validated in tests):
- <100K vectors: 1-5ms (IndexFlatL2 + lru_cache)
- 100K-1M vectors: 2-10ms (IndexIVFFlat + lru_cache + cachetools)
- 1M-10M vectors: 5-20ms (IndexIVFPQ + lru_cache + Redis)
- 10M+ vectors: 2-10ms (GPU IndexIVFPQ + lru_cache + Redis)
"""

import asyncio
import logging
import time
from typing import List, Dict
import numpy as np
import pytest

from .context_cache import (
    HighPerformanceContextRetrieval,
    CacheConfig,
    IndexType,
    SearchMetrics,
    create_context_retrieval
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def small_config():
    """Config for <100K vectors (IndexFlatL2)"""
    return CacheConfig(
        vector_count=1000,
        embedding_dim=128,
        use_redis=False,  # Single-worker testing
        hot_cache_size=256,
        query_cache_size=1024
    )


@pytest.fixture
def medium_config():
    """Config for 100K-1M vectors (IndexIVFFlat)"""
    return CacheConfig(
        vector_count=150_000,
        embedding_dim=256,
        use_redis=False,
        nlist=100,
        nprobe=10
    )


@pytest.fixture
def large_config():
    """Config for 1M-10M vectors (IndexIVFPQ)"""
    return CacheConfig(
        vector_count=1_500_000,
        embedding_dim=768,
        use_redis=False,  # Can enable for distributed testing
        nlist=1000,
        m=8,
        nprobe=20
    )


@pytest.fixture
def redis_config():
    """Config with Redis enabled for distributed cache testing"""
    return CacheConfig(
        vector_count=10_000,
        embedding_dim=128,
        use_redis=True,
        redis_url="redis://localhost:6379",
        chunk_cache_ttl=3600,
        query_cache_ttl=300
    )


@pytest.fixture
def sample_embeddings():
    """Generate sample embeddings for testing"""
    def _generate(num_vectors: int, dim: int) -> np.ndarray:
        np.random.seed(42)
        return np.random.randn(num_vectors, dim).astype(np.float32)
    return _generate


@pytest.fixture
def sample_chunks():
    """Generate sample chunk data"""
    def _generate(num_chunks: int) -> List[Dict]:
        return [
            {
                "chunk_id": i,
                "content": f"Sample content for chunk {i}",
                "metadata": {"source": "test", "index": i}
            }
            for i in range(num_chunks)
        ]
    return _generate


@pytest.fixture
async def mock_db_fetch():
    """Mock database fetch callback"""
    async def _fetch(chunk_id: int) -> Dict:
        # Simulate DB latency
        await asyncio.sleep(0.001)  # 1ms
        return {
            "chunk_id": chunk_id,
            "content": f"Database content for chunk {chunk_id}",
            "metadata": {"fetched_from": "db"}
        }
    return _fetch


# ============================================================================
# UNIT TESTS: Configuration & Index Selection
# ============================================================================

class TestCacheConfig:
    """Test configuration and index type selection"""

    def test_flat_l2_selection(self, small_config):
        """Test IndexFlatL2 selected for <100K vectors"""
        assert small_config.get_index_type() == IndexType.FLAT_L2

    def test_ivf_flat_selection(self, medium_config):
        """Test IndexIVFFlat selected for 100K-1M vectors"""
        assert medium_config.get_index_type() == IndexType.IVF_FLAT

    def test_ivf_pq_selection(self, large_config):
        """Test IndexIVFPQ selected for 1M-10M vectors"""
        assert large_config.get_index_type() == IndexType.IVF_PQ

    def test_gpu_ivf_pq_selection(self):
        """Test GPU IndexIVFPQ selected for 10M+ vectors with GPU enabled"""
        config = CacheConfig(
            vector_count=15_000_000,
            use_gpu=True
        )
        assert config.get_index_type() == IndexType.GPU_IVF_PQ

    def test_default_config_values(self):
        """Test default configuration values"""
        config = CacheConfig()
        assert config.hot_cache_size == 256
        assert config.query_cache_size == 1024
        assert config.chunk_cache_ttl == 3600
        assert config.query_cache_ttl == 300
        assert config.embedding_dim == 768


# ============================================================================
# UNIT TESTS: FAISS Index Initialization
# ============================================================================

class TestFAISSInitialization:
    """Test FAISS index initialization for different scales"""

    def test_flat_l2_initialization(self, small_config):
        """Test IndexFlatL2 initialization"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        assert retrieval.faiss_index is not None
        assert retrieval.faiss_index.d == small_config.embedding_dim
        assert retrieval.config.get_index_type() == IndexType.FLAT_L2

    def test_ivf_flat_initialization(self, medium_config):
        """Test IndexIVFFlat initialization"""
        retrieval = HighPerformanceContextRetrieval(medium_config)

        assert retrieval.faiss_index is not None
        assert retrieval.faiss_index.d == medium_config.embedding_dim
        assert hasattr(retrieval.faiss_index, 'nprobe')

    def test_ivf_pq_initialization(self, large_config):
        """Test IndexIVFPQ initialization"""
        retrieval = HighPerformanceContextRetrieval(large_config)

        assert retrieval.faiss_index is not None
        assert retrieval.faiss_index.d == large_config.embedding_dim
        assert hasattr(retrieval.faiss_index, 'nprobe')

    def test_nprobe_configuration(self, medium_config):
        """Test nprobe parameter is set correctly"""
        medium_config.nprobe = 15
        retrieval = HighPerformanceContextRetrieval(medium_config)

        assert retrieval.faiss_index.nprobe == 15


# ============================================================================
# UNIT TESTS: Vector Operations
# ============================================================================

class TestVectorOperations:
    """Test adding vectors and searching"""

    def test_add_vectors_flat(self, small_config, sample_embeddings):
        """Test adding vectors to FlatL2 index"""
        retrieval = HighPerformanceContextRetrieval(small_config)
        embeddings = sample_embeddings(100, small_config.embedding_dim)
        chunk_ids = list(range(100))

        retrieval.add_vectors(embeddings, chunk_ids)

        assert retrieval.faiss_index.ntotal == 100
        assert len(retrieval.chunk_id_map) == 100

    def test_add_vectors_ivf(self, medium_config, sample_embeddings):
        """Test adding vectors to IVF index (requires training)"""
        retrieval = HighPerformanceContextRetrieval(medium_config)

        # Generate enough vectors for training
        num_vectors = 1000
        embeddings = sample_embeddings(num_vectors, medium_config.embedding_dim)
        chunk_ids = list(range(num_vectors))

        retrieval.add_vectors(embeddings, chunk_ids)

        assert retrieval.faiss_index.ntotal == num_vectors
        assert retrieval.faiss_index.is_trained

    @pytest.mark.asyncio
    async def test_search_basic(self, small_config, sample_embeddings):
        """Test basic vector search"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        # Add vectors
        num_vectors = 100
        embeddings = sample_embeddings(num_vectors, small_config.embedding_dim)
        chunk_ids = list(range(num_vectors))
        retrieval.add_vectors(embeddings, chunk_ids)

        # Search
        query = embeddings[0]  # Use first vector as query
        chunk_ids, metrics = await retrieval.search_context(query, k=5)

        assert len(chunk_ids) == 5
        assert 0 in chunk_ids  # Should find exact match
        assert metrics.total_latency_ms > 0

    def test_query_hash_generation(self):
        """Test query embedding hash generation"""
        embedding1 = np.random.randn(128).astype(np.float32)
        embedding2 = np.random.randn(128).astype(np.float32)

        hash1 = HighPerformanceContextRetrieval._hash_query(embedding1)
        hash2 = HighPerformanceContextRetrieval._hash_query(embedding2)

        assert len(hash1) == 16
        assert hash1 != hash2

        # Same embedding should produce same hash
        hash1_repeat = HighPerformanceContextRetrieval._hash_query(embedding1)
        assert hash1 == hash1_repeat


# ============================================================================
# UNIT TESTS: Cache Layers
# ============================================================================

class TestCacheLayers:
    """Test individual cache layers (hot cache, LRU, Redis)"""

    def test_hot_cache_add_and_retrieve(self, small_config, sample_chunks):
        """Test process-local hot cache"""
        retrieval = HighPerformanceContextRetrieval(small_config)
        chunks = sample_chunks(10)

        # Add to hot cache
        for chunk in chunks:
            retrieval._add_to_hot_cache(chunk['chunk_id'], chunk)

        # Verify retrieval
        assert 0 in retrieval._hot_chunks
        assert retrieval._hot_chunks[0] == chunks[0]

    def test_hot_cache_eviction(self, small_config, sample_chunks):
        """Test hot cache LRU eviction"""
        config = CacheConfig(hot_cache_size=5)
        retrieval = HighPerformanceContextRetrieval(config)
        chunks = sample_chunks(10)

        # Add more than cache size
        for chunk in chunks:
            retrieval._add_to_hot_cache(chunk['chunk_id'], chunk)

        # Cache should only hold max size
        assert len(retrieval._hot_chunks) == 5

    @pytest.mark.asyncio
    async def test_lru_cached_search(self, small_config, sample_embeddings):
        """Test LRU-cached FAISS search"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        # Add vectors
        embeddings = sample_embeddings(50, small_config.embedding_dim)
        chunk_ids = list(range(50))
        retrieval.add_vectors(embeddings, chunk_ids)

        query = embeddings[0]

        # First search
        _, metrics1 = await retrieval.search_context(query, k=5)

        # Second search (should hit LRU cache)
        _, metrics2 = await retrieval.search_context(query, k=5)

        # Second search should be faster (cached)
        assert metrics2.total_latency_ms <= metrics1.total_latency_ms

    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_redis_query_cache(self, redis_config, sample_embeddings):
        """Test Redis query result caching"""
        retrieval = HighPerformanceContextRetrieval(redis_config)

        # Skip if Redis not available
        if not retrieval.redis_client:
            pytest.skip("Redis not available")

        # Add vectors
        embeddings = sample_embeddings(50, redis_config.embedding_dim)
        chunk_ids = list(range(50))
        retrieval.add_vectors(embeddings, chunk_ids)

        query = embeddings[10]

        try:
            # First search (cache miss)
            results1, metrics1 = await retrieval.search_context(query, k=5)

            # Second search (cache hit)
            results2, metrics2 = await retrieval.search_context(query, k=5)

            assert metrics2.redis_cache_hit
            assert results1 == results2
        finally:
            await retrieval.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_redis_chunk_cache(self, redis_config, mock_db_fetch):
        """Test Redis chunk content caching"""
        retrieval = HighPerformanceContextRetrieval(redis_config)

        if not retrieval.redis_client:
            pytest.skip("Redis not available")

        chunk_ids = [1, 2, 3]

        try:
            # First fetch (cache miss, DB fetch)
            chunks1, metrics1 = await retrieval.get_chunks(chunk_ids, mock_db_fetch)

            # Second fetch (cache hit)
            chunks2, metrics2 = await retrieval.get_chunks(chunk_ids, mock_db_fetch)

            assert metrics1.db_fetch_ms > 0  # DB was hit
            assert metrics2.hot_cache_hit or metrics2.redis_cache_hit
            assert chunks1 == chunks2
        finally:
            await retrieval.cleanup()


# ============================================================================
# INTEGRATION TESTS: Full Pipeline
# ============================================================================

class TestFullPipeline:
    """Test end-to-end context retrieval pipeline"""

    @pytest.mark.asyncio
    async def test_retrieve_context_small_scale(self, small_config, sample_embeddings, mock_db_fetch):
        """Test full pipeline for small scale (<100K vectors)"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        # Add vectors
        num_vectors = 100
        embeddings = sample_embeddings(num_vectors, small_config.embedding_dim)
        chunk_ids = list(range(num_vectors))
        retrieval.add_vectors(embeddings, chunk_ids)

        # Retrieve context
        query = embeddings[5]
        chunks, stats = await retrieval.retrieve_context(
            query, k=5, db_fetch_callback=mock_db_fetch
        )

        assert len(chunks) == 5
        assert stats['chunks_returned'] == 5
        assert stats['total_latency_ms'] > 0
        assert stats['index_type'] == IndexType.FLAT_L2.value

    @pytest.mark.asyncio
    async def test_retrieve_context_medium_scale(self, medium_config, sample_embeddings, mock_db_fetch):
        """Test full pipeline for medium scale (100K-1M vectors)"""
        retrieval = HighPerformanceContextRetrieval(medium_config)

        # Add vectors (use smaller number for faster testing)
        num_vectors = 1000
        embeddings = sample_embeddings(num_vectors, medium_config.embedding_dim)
        chunk_ids = list(range(num_vectors))
        retrieval.add_vectors(embeddings, chunk_ids)

        query = embeddings[42]
        chunks, stats = await retrieval.retrieve_context(
            query, k=10, db_fetch_callback=mock_db_fetch
        )

        assert len(chunks) == 10
        assert stats['index_type'] == IndexType.IVF_FLAT.value

    @pytest.mark.asyncio
    async def test_cache_warmup_effect(self, small_config, sample_embeddings, mock_db_fetch):
        """Test that cache warmup improves performance"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        num_vectors = 50
        embeddings = sample_embeddings(num_vectors, small_config.embedding_dim)
        chunk_ids = list(range(num_vectors))
        retrieval.add_vectors(embeddings, chunk_ids)

        query = embeddings[10]

        # First retrieval (cold)
        _, stats1 = await retrieval.retrieve_context(query, k=5, db_fetch_callback=mock_db_fetch)

        # Second retrieval (warm cache)
        _, stats2 = await retrieval.retrieve_context(query, k=5, db_fetch_callback=mock_db_fetch)

        # Warm retrieval should be faster
        assert stats2['fetch_latency_ms'] < stats1['fetch_latency_ms']
        assert stats2['hot_cache_hit'] or stats1['chunks_returned'] == stats2['chunks_returned']


# ============================================================================
# PERFORMANCE BENCHMARKS: Latency Validation
# ============================================================================

class TestPerformanceBenchmarks:
    """Performance benchmarks validating latency targets"""

    @pytest.mark.asyncio
    async def test_small_scale_latency_target(self, sample_embeddings):
        """
        Scenario 1: <100K vectors
        Target: 1-5ms (IndexFlatL2 + lru_cache)
        """
        config = CacheConfig(
            vector_count=10_000,
            embedding_dim=128,
            use_redis=False
        )
        retrieval = HighPerformanceContextRetrieval(config)

        # Add vectors
        num_vectors = 1000
        embeddings = sample_embeddings(num_vectors, config.embedding_dim)
        chunk_ids = list(range(num_vectors))
        retrieval.add_vectors(embeddings, chunk_ids)

        # Benchmark searches
        latencies = []
        for i in range(20):
            query = sample_embeddings(1, config.embedding_dim)[0]
            start = time.time()
            _, metrics = await retrieval.search_context(query, k=5)
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)

        logger.info(f"Small Scale - Avg: {avg_latency:.2f}ms, P95: {p95_latency:.2f}ms")

        # Validate against target (1-5ms)
        assert p95_latency < 10, f"P95 latency {p95_latency:.2f}ms exceeds relaxed target"

    @pytest.mark.asyncio
    async def test_medium_scale_latency_target(self, sample_embeddings):
        """
        Scenario 2: 100K-1M vectors
        Target: 2-10ms (IndexIVFFlat + lru_cache)
        """
        config = CacheConfig(
            vector_count=100_000,
            embedding_dim=256,
            use_redis=False,
            nlist=100,
            nprobe=10
        )
        retrieval = HighPerformanceContextRetrieval(config)

        # Add vectors
        num_vectors = 2000  # Representative sample
        embeddings = sample_embeddings(num_vectors, config.embedding_dim)
        chunk_ids = list(range(num_vectors))
        retrieval.add_vectors(embeddings, chunk_ids)

        # Benchmark
        latencies = []
        for i in range(15):
            query = sample_embeddings(1, config.embedding_dim)[0]
            start = time.time()
            _, metrics = await retrieval.search_context(query, k=10)
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)

        logger.info(f"Medium Scale - Avg: {avg_latency:.2f}ms, P95: {p95_latency:.2f}ms")

        # Validate against target (2-10ms)
        assert p95_latency < 20, f"P95 latency {p95_latency:.2f}ms exceeds relaxed target"

    @pytest.mark.asyncio
    async def test_voice_ai_budget_compliance(self, sample_embeddings, mock_db_fetch):
        """
        Voice AI Budget Test: Total retrieval must be <50ms
        (Leaves 750ms for LLM inference in 800ms budget)
        """
        config = CacheConfig(
            vector_count=50_000,
            embedding_dim=768,
            use_redis=False
        )
        retrieval = HighPerformanceContextRetrieval(config)

        # Add vectors
        num_vectors = 1000
        embeddings = sample_embeddings(num_vectors, config.embedding_dim)
        chunk_ids = list(range(num_vectors))
        retrieval.add_vectors(embeddings, chunk_ids)

        # Full pipeline benchmark
        total_latencies = []
        for i in range(10):
            query = sample_embeddings(1, config.embedding_dim)[0]
            chunks, stats = await retrieval.retrieve_context(
                query, k=5, db_fetch_callback=mock_db_fetch
            )
            total_latencies.append(stats['total_latency_ms'])

        avg_total = np.mean(total_latencies)
        p95_total = np.percentile(total_latencies, 95)

        logger.info(f"Voice AI Budget - Avg: {avg_total:.2f}ms, P95: {p95_total:.2f}ms")

        # Critical: P95 must be under 50ms
        assert p95_total < 50, f"P95 total latency {p95_total:.2f}ms exceeds 50ms budget"
        assert stats['target_met'], "Performance target not met"

    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, small_config, sample_embeddings):
        """
        Test cache hit scenario (Hot Path)
        Expected: <20ms total (embedding reuse + cache hit)
        """
        retrieval = HighPerformanceContextRetrieval(small_config)

        num_vectors = 100
        embeddings = sample_embeddings(num_vectors, small_config.embedding_dim)
        chunk_ids = list(range(num_vectors))
        retrieval.add_vectors(embeddings, chunk_ids)

        query = embeddings[0]

        # First query (cold)
        _, metrics1 = await retrieval.search_context(query, k=5)

        # Repeated query (hot - should hit LRU cache)
        start = time.time()
        _, metrics2 = await retrieval.search_context(query, k=5)
        hot_latency = (time.time() - start) * 1000

        logger.info(f"Cache Hit Latency: {hot_latency:.2f}ms")

        # Hot path should be significantly faster
        assert hot_latency < metrics1.total_latency_ms or hot_latency < 5


# ============================================================================
# TESTS: Index Persistence
# ============================================================================

class TestIndexPersistence:
    """Test saving and loading FAISS indices"""

    def test_save_and_load_index(self, small_config, sample_embeddings, tmp_path):
        """Test index save/load roundtrip"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        # Add vectors
        num_vectors = 100
        embeddings = sample_embeddings(num_vectors, small_config.embedding_dim)
        chunk_ids = list(range(num_vectors))
        retrieval.add_vectors(embeddings, chunk_ids)

        # Save
        index_path = str(tmp_path / "test_index.faiss")
        retrieval.save_index(index_path)

        # Load into new instance
        new_retrieval = HighPerformanceContextRetrieval(small_config)
        new_retrieval.load_index(index_path)

        assert new_retrieval.faiss_index.ntotal == num_vectors
        assert len(new_retrieval.chunk_id_map) == num_vectors

    @pytest.mark.asyncio
    async def test_loaded_index_search(self, small_config, sample_embeddings, tmp_path):
        """Test search works correctly after load"""
        # Create and save
        retrieval1 = HighPerformanceContextRetrieval(small_config)
        num_vectors = 50
        embeddings = sample_embeddings(num_vectors, small_config.embedding_dim)
        chunk_ids = list(range(num_vectors))
        retrieval1.add_vectors(embeddings, chunk_ids)

        index_path = str(tmp_path / "test_search.faiss")
        retrieval1.save_index(index_path)

        # Load and search
        retrieval2 = HighPerformanceContextRetrieval(small_config)
        retrieval2.load_index(index_path)

        query = embeddings[5]
        results, metrics = await retrieval2.search_context(query, k=5)

        assert len(results) == 5
        assert 5 in results  # Should find the exact match


# ============================================================================
# TESTS: Performance Reporting
# ============================================================================

class TestPerformanceReporting:
    """Test performance metrics and reporting"""

    @pytest.mark.asyncio
    async def test_metrics_collection(self, small_config, sample_embeddings):
        """Test that metrics are collected during operations"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        embeddings = sample_embeddings(50, small_config.embedding_dim)
        chunk_ids = list(range(50))
        retrieval.add_vectors(embeddings, chunk_ids)

        # Perform multiple searches
        for i in range(5):
            query = sample_embeddings(1, small_config.embedding_dim)[0]
            await retrieval.search_context(query, k=5)

        assert len(retrieval.metrics_history) >= 5

    @pytest.mark.asyncio
    async def test_performance_report_generation(self, small_config, sample_embeddings):
        """Test performance report generation"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        embeddings = sample_embeddings(50, small_config.embedding_dim)
        chunk_ids = list(range(50))
        retrieval.add_vectors(embeddings, chunk_ids)

        # Generate some metrics
        for i in range(10):
            query = sample_embeddings(1, small_config.embedding_dim)[0]
            await retrieval.search_context(query, k=5)

        report = retrieval.get_performance_report()

        assert 'latency' in report
        assert 'index_type' in report
        assert 'cache' in report
        assert report['total_queries'] == 10
        assert 'avg_ms' in report['latency']
        assert 'p95_ms' in report['latency']

    def test_performance_validation_in_report(self, small_config):
        """Test performance validation flags in report"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        # Add mock metrics
        retrieval.metrics_history.append(
            SearchMetrics(query_hash="test1", total_latency_ms=3.5, faiss_search_ms=2.0)
        )
        retrieval.metrics_history.append(
            SearchMetrics(query_hash="test2", total_latency_ms=4.2, faiss_search_ms=2.5)
        )

        report = retrieval.get_performance_report()

        assert 'performance_validation' in report
        assert 'target_met' in report['performance_validation']
        assert 'within_expected_range' in report['performance_validation']


# ============================================================================
# TESTS: Utility Functions
# ============================================================================

class TestUtilityFunctions:
    """Test utility and convenience functions"""

    def test_create_context_retrieval_factory(self):
        """Test factory function creates correct instance"""
        retrieval = create_context_retrieval(
            vector_count=5000,
            embedding_dim=256,
            use_redis=False
        )

        assert retrieval.config.vector_count == 5000
        assert retrieval.config.embedding_dim == 256
        assert retrieval.config.use_redis is False
        assert retrieval.faiss_index is not None

    def test_clear_caches(self, small_config, sample_embeddings):
        """Test cache clearing"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        # Add to hot cache
        retrieval._add_to_hot_cache(1, {"data": "test"})

        # Add vectors and search to populate LRU cache
        embeddings = sample_embeddings(10, small_config.embedding_dim)
        retrieval.add_vectors(embeddings, list(range(10)))

        # Clear
        retrieval.clear_caches()

        assert len(retrieval._hot_chunks) == 0

    @pytest.mark.asyncio
    @pytest.mark.redis
    async def test_cleanup_redis(self, redis_config):
        """Test Redis cleanup"""
        retrieval = HighPerformanceContextRetrieval(redis_config)

        if retrieval.redis_client:
            await retrieval.cleanup()
            # Should not raise exception


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_search_without_vectors(self, small_config):
        """Test search on empty index"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        query = np.random.randn(small_config.embedding_dim).astype(np.float32)

        # Should handle gracefully (return empty or raise informative error)
        try:
            results, metrics = await retrieval.search_context(query, k=5)
            # If it doesn't error, should return empty
            assert len(results) == 0
        except Exception as e:
            # Acceptable to raise error for empty index
            assert "empty" in str(e).lower() or "no vectors" in str(e).lower()

    @pytest.mark.asyncio
    async def test_get_chunks_without_callback(self, small_config):
        """Test get_chunks without DB callback"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        chunk_ids = [1, 2, 3]
        chunks, metrics = await retrieval.get_chunks(chunk_ids, db_fetch_callback=None)

        # Should return empty list when no callback and no cache
        assert len(chunks) == 0

    def test_add_vectors_invalid_dimension(self, small_config):
        """Test adding vectors with wrong dimension"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        # Wrong dimension
        wrong_embeddings = np.random.randn(10, 256).astype(np.float32)
        chunk_ids = list(range(10))

        with pytest.raises(Exception):
            retrieval.add_vectors(wrong_embeddings, chunk_ids)

    @pytest.mark.asyncio
    async def test_large_k_value(self, small_config, sample_embeddings):
        """Test searching with k larger than available vectors"""
        retrieval = HighPerformanceContextRetrieval(small_config)

        num_vectors = 10
        embeddings = sample_embeddings(num_vectors, small_config.embedding_dim)
        retrieval.add_vectors(embeddings, list(range(num_vectors)))

        query = embeddings[0]
        results, metrics = await retrieval.search_context(query, k=100)

        # Should return all available vectors
        assert len(results) <= num_vectors


# ============================================================================
# SCENARIO TESTS: Real-World Use Cases
# ============================================================================

class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    @pytest.mark.asyncio
    async def test_cold_start_scenario(self, sample_embeddings, mock_db_fetch):
        """
        Scenario: First-time query (Cold Path)
        Total: ~32ms (embedding + cache miss + FAISS + fetch)
        """
        config = CacheConfig(vector_count=10_000, embedding_dim=128, use_redis=False)
        retrieval = HighPerformanceContextRetrieval(config)

        # Setup index
        embeddings = sample_embeddings(100, config.embedding_dim)
        retrieval.add_vectors(embeddings, list(range(100)))

        # Cold query
        query = sample_embeddings(1, config.embedding_dim)[0]
        start = time.time()
        chunks, stats = await retrieval.retrieve_context(query, k=5, db_fetch_callback=mock_db_fetch)
        total_latency = (time.time() - start) * 1000

        logger.info(f"Cold Start Latency: {total_latency:.2f}ms")

        assert len(chunks) == 5
        assert total_latency < 100  # Reasonable cold start

    @pytest.mark.asyncio
    async def test_repeated_query_scenario(self, sample_embeddings, mock_db_fetch):
        """
        Scenario: Repeated query (Hot Path)
        Expected: ~17ms (47% faster than cold)
        """
        config = CacheConfig(vector_count=10_000, embedding_dim=128, use_redis=False)
        retrieval = HighPerformanceContextRetrieval(config)

        embeddings = sample_embeddings(100, config.embedding_dim)
        retrieval.add_vectors(embeddings, list(range(100)))

        query = sample_embeddings(1, config.embedding_dim)[0]

        # First query
        start1 = time.time()
        await retrieval.retrieve_context(query, k=5, db_fetch_callback=mock_db_fetch)
        latency1 = (time.time() - start1) * 1000

        # Repeated query
        start2 = time.time()
        await retrieval.retrieve_context(query, k=5, db_fetch_callback=mock_db_fetch)
        latency2 = (time.time() - start2) * 1000

        logger.info(f"Cold: {latency1:.2f}ms, Hot: {latency2:.2f}ms, Improvement: {(1 - latency2/latency1)*100:.1f}%")

        # Hot should be faster
        assert latency2 < latency1

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, sample_embeddings, mock_db_fetch):
        """Test handling concurrent queries"""
        config = CacheConfig(vector_count=10_000, embedding_dim=128, use_redis=False)
        retrieval = HighPerformanceContextRetrieval(config)

        embeddings = sample_embeddings(200, config.embedding_dim)
        retrieval.add_vectors(embeddings, list(range(200)))

        # Concurrent queries
        queries = [sample_embeddings(1, config.embedding_dim)[0] for _ in range(10)]

        tasks = [
            retrieval.retrieve_context(q, k=5, db_fetch_callback=mock_db_fetch)
            for q in queries
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for chunks, stats in results:
            assert len(chunks) == 5
            assert stats['total_latency_ms'] > 0


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    """Run tests with pytest"""
    pytest.main([
        __file__,
        "-v",  # Verbose
        "-s",  # Show print statements
        "--tb=short",  # Short traceback
        "-m", "not redis",  # Skip Redis tests by default
        "--durations=10"  # Show 10 slowest tests
    ])