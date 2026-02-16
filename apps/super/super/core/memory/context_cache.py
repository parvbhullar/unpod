"""
High-Performance Context Cache Layer for Real-time Retrieval
Multi-layer caching: LRU Cache -> Redis -> FAISS Vector Search

Performance Targets:
- <100K vectors: 1-5ms (IndexFlatL2 + lru_cache)
- 100K-1M vectors: 2-10ms (IndexIVFFlat + lru_cache + cachetools)
- 1M-10M vectors: 5-20ms (IndexIVFPQ + lru_cache + Redis)
- 10M+ vectors: 2-10ms (GPU IndexIVFPQ + lru_cache + Redis)
"""

import hashlib
import logging
import pickle
import time
from functools import lru_cache
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)


class IndexType(Enum):
    """FAISS index types based on scale"""
    FLAT_L2 = "IndexFlatL2"  # <100K vectors
    IVF_FLAT = "IndexIVFFlat"  # 100K-1M vectors
    IVF_PQ = "IndexIVFPQ"  # 1M-10M vectors
    GPU_IVF_PQ = "GpuIndexIVFPQ"  # 10M+ vectors


@dataclass
class CacheConfig:
    """Configuration for cache layers"""
    # Vector scale determines index type
    vector_count: int = 0
    embedding_dim: int = 768

    # Cache settings
    hot_cache_size: int = 256  # Process-local hot cache
    query_cache_size: int = 1024  # Query result cache
    chunk_cache_ttl: int = 3600  # Redis chunk TTL (1 hour)
    query_cache_ttl: int = 300  # Redis query TTL (5 minutes)

    # Redis settings
    redis_url: str = "redis://localhost:6379"
    use_redis: bool = True  # Set False for single-worker

    # FAISS settings
    index_path: Optional[str] = None
    nlist: int = 100  # For IVF indices
    m: int = 8  # For PQ indices
    nprobe: int = 10  # Search probes
    use_gpu: bool = False

    def get_index_type(self) -> IndexType:
        """Determine appropriate index type based on vector count"""
        if self.vector_count >= 10_000_000:
            return IndexType.GPU_IVF_PQ if self.use_gpu else IndexType.IVF_PQ
        elif self.vector_count >= 1_000_000:
            return IndexType.IVF_PQ
        elif self.vector_count >= 100_000:
            return IndexType.IVF_FLAT
        else:
            return IndexType.FLAT_L2


@dataclass
class SearchMetrics:
    """Performance metrics for search operations"""
    query_hash: str
    total_latency_ms: float
    hot_cache_hit: bool = False
    redis_cache_hit: bool = False
    faiss_search_ms: float = 0.0
    redis_fetch_ms: float = 0.0
    db_fetch_ms: float = 0.0
    chunks_fetched: int = 0
    timestamp: float = time.time()


class HighPerformanceContextRetrieval:
    """
    Hybrid cache + vector search for <50ms context fetching

    Architecture:
    LAYER 1: Query Embedding (10-50ms)
    LAYER 2: Redis/Memcached Cache Lookup (0.5-3ms)
    LAYER 3: FAISS Vector Search (1-20ms config-dependent)
    LAYER 4: Redis/Memcached Content Cache (0.5-3ms per chunk)
    """

    def __init__(self, config: CacheConfig):
        self.config = config
        self.metrics_history: List[SearchMetrics] = []

        # Layer 1: Process-local hot cache for chunks
        self._hot_chunks: Dict[str, Any] = {}
        self._hot_cache_max_size = config.hot_cache_size

        # Layer 2: FAISS vector index
        self.faiss_index = None
        self.chunk_id_map = None  # Maps FAISS index -> chunk_id
        self._initialize_faiss()

        # Layer 3: Redis distributed cache (optional)
        self.redis_client = None
        if config.use_redis:
            self._initialize_redis()

    def _initialize_faiss(self):
        """Initialize FAISS index based on configuration"""
        try:
            import faiss

            if self.config.index_path:
                # Load existing index
                logger.info(f"Loading FAISS index from {self.config.index_path}")
                self.faiss_index = faiss.read_index(self.config.index_path)
            else:
                # Create new index based on scale
                index_type = self.config.get_index_type()
                logger.info(f"Creating {index_type.value} index for {self.config.vector_count} vectors")

                if index_type == IndexType.FLAT_L2:
                    self.faiss_index = faiss.IndexFlatL2(self.config.embedding_dim)

                elif index_type == IndexType.IVF_FLAT:
                    quantizer = faiss.IndexFlatL2(self.config.embedding_dim)
                    self.faiss_index = faiss.IndexIVFFlat(
                        quantizer, self.config.embedding_dim, self.config.nlist
                    )

                elif index_type == IndexType.IVF_PQ:
                    quantizer = faiss.IndexFlatL2(self.config.embedding_dim)
                    self.faiss_index = faiss.IndexIVFPQ(
                        quantizer, self.config.embedding_dim,
                        self.config.nlist, self.config.m, 8
                    )

                elif index_type == IndexType.GPU_IVF_PQ:
                    if not self.config.use_gpu:
                        raise ValueError("GPU not enabled in config")

                    res = faiss.StandardGpuResources()
                    quantizer = faiss.IndexFlatL2(self.config.embedding_dim)
                    cpu_index = faiss.IndexIVFPQ(
                        quantizer, self.config.embedding_dim,
                        self.config.nlist, self.config.m, 8
                    )
                    self.faiss_index = faiss.index_cpu_to_gpu(res, 0, cpu_index)

            # Set search parameters for IVF indices
            if hasattr(self.faiss_index, 'nprobe'):
                self.faiss_index.nprobe = self.config.nprobe

            logger.info(f"FAISS index initialized: {self.faiss_index.ntotal} vectors")

        except ImportError:
            logger.error("FAISS not installed. Install with: pip install faiss-cpu or faiss-gpu")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {e}")
            raise

    def _initialize_redis(self):
        """Initialize Redis client for distributed caching"""
        try:
            from redis.asyncio import Redis
            self.redis_client = Redis.from_url(self.config.redis_url)
            logger.info(f"Redis client initialized: {self.config.redis_url}")
        except ImportError:
            logger.warning("redis-py not installed. Install with: pip install redis")
            self.config.use_redis = False
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.config.use_redis = False

    @staticmethod
    def _hash_query(query_embedding: np.ndarray) -> str:
        """Generate hash for query embedding to use as cache key"""
        return hashlib.sha256(query_embedding.tobytes()).hexdigest()[:16]

    @lru_cache(maxsize=1024)
    def _cached_search(self, query_hash: str, query_bytes: bytes, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        LRU-cached FAISS search
        This provides process-local caching of query results
        """
        query_embedding = np.frombuffer(query_bytes, dtype=np.float32).reshape(1, -1)
        distances, indices = self.faiss_index.search(query_embedding, k)
        return distances, indices

    async def search_context(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        use_cache: bool = True
    ) -> Tuple[List[int], SearchMetrics]:
        """
        Search for similar contexts with aggressive caching

        Args:
            query_embedding: Query vector (1D numpy array)
            k: Number of results to return
            use_cache: Whether to use cache layers

        Returns:
            Tuple of (chunk_ids, metrics)
        """
        start_time = time.time()
        query_hash = self._hash_query(query_embedding)

        metrics = SearchMetrics(
            query_hash=query_hash,
            total_latency_ms=0.0
        )

        # LAYER 2: Redis cache lookup for query results
        if use_cache and self.redis_client:
            try:
                redis_start = time.time()
                cache_key = f"query:{query_hash}:k{k}"
                cached = await self.redis_client.get(cache_key)

                if cached:
                    indices = pickle.loads(cached)
                    metrics.redis_cache_hit = True
                    metrics.redis_fetch_ms = (time.time() - redis_start) * 1000
                    metrics.total_latency_ms = (time.time() - start_time) * 1000
                    logger.debug(f"Redis cache hit for query {query_hash}: {metrics.redis_fetch_ms:.2f}ms")
                    return indices.tolist(), metrics
            except Exception as e:
                logger.warning(f"Redis cache lookup failed: {e}")

        # LAYER 3: FAISS vector search
        faiss_start = time.time()

        # Use LRU-cached search
        query_bytes = query_embedding.astype(np.float32).tobytes()
        distances, indices = self._cached_search(query_hash, query_bytes, k)

        metrics.faiss_search_ms = (time.time() - faiss_start) * 1000

        # Map FAISS indices to chunk IDs
        if self.chunk_id_map:
            chunk_ids = [self.chunk_id_map[idx] for idx in indices[0]]
        else:
            chunk_ids = indices[0].tolist()

        # Cache results in Redis for future queries
        if use_cache and self.redis_client:
            try:
                cache_key = f"query:{query_hash}:k{k}"
                await self.redis_client.setex(
                    cache_key,
                    self.config.query_cache_ttl,
                    pickle.dumps(indices[0])
                )
            except Exception as e:
                logger.warning(f"Failed to cache query results in Redis: {e}")

        metrics.total_latency_ms = (time.time() - start_time) * 1000
        self.metrics_history.append(metrics)

        logger.debug(
            f"FAISS search for {query_hash}: {metrics.faiss_search_ms:.2f}ms, "
            f"total: {metrics.total_latency_ms:.2f}ms"
        )

        return chunk_ids, metrics

    async def get_chunks(
        self,
        chunk_ids: List[int],
        db_fetch_callback: Optional[callable] = None
    ) -> Tuple[List[Dict], SearchMetrics]:
        """
        Fetch actual chunk content with aggressive caching

        Architecture:
        1. Check process-local hot cache (0.1μs)
        2. Check Redis cache (0.5-3ms)
        3. Database fetch (50-100ms) with callback

        Args:
            chunk_ids: List of chunk IDs to fetch
            db_fetch_callback: Async function(chunk_id) -> chunk_data

        Returns:
            Tuple of (chunks, metrics)
        """
        start_time = time.time()
        chunks = []
        db_fetches = 0

        metrics = SearchMetrics(
            query_hash="fetch_chunks",
            total_latency_ms=0.0
        )

        for cid in chunk_ids:
            chunk = None

            # LAYER 1: Process-local hot cache (0.1μs)
            if cid in self._hot_chunks:
                chunk = self._hot_chunks[cid]
                metrics.hot_cache_hit = True
                logger.debug(f"Hot cache hit for chunk {cid}")

            # LAYER 2: Redis cache (0.5-3ms)
            elif self.redis_client:
                try:
                    redis_start = time.time()
                    cache_key = f"chunk:{cid}"
                    cached = await self.redis_client.get(cache_key)

                    if cached:
                        chunk = pickle.loads(cached)
                        metrics.redis_cache_hit = True
                        metrics.redis_fetch_ms += (time.time() - redis_start) * 1000

                        # Promote to hot cache
                        self._add_to_hot_cache(cid, chunk)
                        logger.debug(f"Redis cache hit for chunk {cid}")
                except Exception as e:
                    logger.warning(f"Redis cache fetch failed for chunk {cid}: {e}")

            # LAYER 3: Database fetch (50-100ms)
            if chunk is None:
                if db_fetch_callback:
                    try:
                        db_start = time.time()
                        chunk = await db_fetch_callback(cid)
                        metrics.db_fetch_ms += (time.time() - db_start) * 1000
                        db_fetches += 1

                        # Cache aggressively
                        self._add_to_hot_cache(cid, chunk)

                        if self.redis_client:
                            try:
                                cache_key = f"chunk:{cid}"
                                await self.redis_client.setex(
                                    cache_key,
                                    self.config.chunk_cache_ttl,
                                    pickle.dumps(chunk)
                                )
                            except Exception as e:
                                logger.warning(f"Failed to cache chunk {cid} in Redis: {e}")

                        logger.debug(f"DB fetch for chunk {cid}: {metrics.db_fetch_ms:.2f}ms")
                    except Exception as e:
                        logger.error(f"Failed to fetch chunk {cid} from database: {e}")
                        continue
                else:
                    logger.warning(f"No db_fetch_callback provided, skipping chunk {cid}")
                    continue

            if chunk:
                chunks.append(chunk)

        metrics.chunks_fetched = len(chunks)
        metrics.total_latency_ms = (time.time() - start_time) * 1000
        self.metrics_history.append(metrics)

        logger.info(
            f"Fetched {len(chunks)} chunks: "
            f"hot={metrics.hot_cache_hit}, "
            f"redis={metrics.redis_cache_hit}, "
            f"db={db_fetches}, "
            f"latency={metrics.total_latency_ms:.2f}ms"
        )

        return chunks, metrics

    def _add_to_hot_cache(self, chunk_id: int, chunk_data: Any):
        """Add chunk to hot cache with LRU eviction"""
        if len(self._hot_chunks) >= self._hot_cache_max_size:
            # Simple FIFO eviction (can be improved with LRU)
            first_key = next(iter(self._hot_chunks))
            del self._hot_chunks[first_key]

        self._hot_chunks[chunk_id] = chunk_data

    async def retrieve_context(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        db_fetch_callback: Optional[callable] = None,
        use_cache: bool = True
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        End-to-end context retrieval with full pipeline

        Args:
            query_embedding: Query vector
            k: Number of results
            db_fetch_callback: Async function to fetch chunks from DB
            use_cache: Whether to use caching layers

        Returns:
            Tuple of (chunks, performance_stats)
        """
        pipeline_start = time.time()

        # Step 1: Search for similar chunk IDs
        chunk_ids, search_metrics = await self.search_context(
            query_embedding, k=k, use_cache=use_cache
        )

        # Step 2: Fetch chunk content
        chunks, fetch_metrics = await self.get_chunks(
            chunk_ids, db_fetch_callback=db_fetch_callback
        )

        total_latency = (time.time() - pipeline_start) * 1000

        stats = {
            "total_latency_ms": total_latency,
            "search_latency_ms": search_metrics.total_latency_ms,
            "fetch_latency_ms": fetch_metrics.total_latency_ms,
            "faiss_search_ms": search_metrics.faiss_search_ms,
            "redis_cache_hit": search_metrics.redis_cache_hit or fetch_metrics.redis_cache_hit,
            "hot_cache_hit": fetch_metrics.hot_cache_hit,
            "chunks_returned": len(chunks),
            "target_met": total_latency < 50.0,  # <50ms target
            "index_type": self.config.get_index_type().value,
            "vector_count": self.config.vector_count
        }

        logger.info(
            f"Context retrieval completed: {total_latency:.2f}ms "
            f"(search={search_metrics.total_latency_ms:.2f}ms, "
            f"fetch={fetch_metrics.total_latency_ms:.2f}ms) "
            f"- Target {'MET' if stats['target_met'] else 'MISSED'}"
        )

        return chunks, stats

    def add_vectors(self, embeddings: np.ndarray, chunk_ids: List[int]):
        """
        Add vectors to FAISS index

        Args:
            embeddings: Numpy array of shape (n, embedding_dim)
            chunk_ids: List of chunk IDs corresponding to embeddings
        """
        if not self.faiss_index:
            raise RuntimeError("FAISS index not initialized")

        # Train index if needed (IVF indices)
        if hasattr(self.faiss_index, 'is_trained') and not self.faiss_index.is_trained:
            logger.info("Training FAISS index...")
            self.faiss_index.train(embeddings)

        # Add vectors
        self.faiss_index.add(embeddings.astype(np.float32))

        # Update chunk ID mapping
        if self.chunk_id_map is None:
            self.chunk_id_map = {}

        start_idx = len(self.chunk_id_map)
        for i, chunk_id in enumerate(chunk_ids):
            self.chunk_id_map[start_idx + i] = chunk_id

        self.config.vector_count = self.faiss_index.ntotal
        logger.info(f"Added {len(chunk_ids)} vectors. Total: {self.config.vector_count}")

    def save_index(self, path: str):
        """Save FAISS index to disk"""
        if not self.faiss_index:
            raise RuntimeError("FAISS index not initialized")

        import faiss
        faiss.write_index(self.faiss_index, path)
        logger.info(f"FAISS index saved to {path}")

        # Also save chunk ID mapping
        mapping_path = path + ".mapping.pkl"
        with open(mapping_path, 'wb') as f:
            pickle.dump(self.chunk_id_map, f)
        logger.info(f"Chunk ID mapping saved to {mapping_path}")

    def load_index(self, path: str):
        """Load FAISS index from disk"""
        import faiss
        self.faiss_index = faiss.read_index(path)
        self.config.vector_count = self.faiss_index.ntotal
        logger.info(f"FAISS index loaded from {path}: {self.config.vector_count} vectors")

        # Load chunk ID mapping
        mapping_path = path + ".mapping.pkl"
        try:
            with open(mapping_path, 'rb') as f:
                self.chunk_id_map = pickle.load(f)
            logger.info(f"Chunk ID mapping loaded from {mapping_path}")
        except FileNotFoundError:
            logger.warning(f"Chunk ID mapping not found at {mapping_path}")

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report from metrics history"""
        if not self.metrics_history:
            return {"message": "No metrics collected yet"}

        latencies = [m.total_latency_ms for m in self.metrics_history]
        faiss_times = [m.faiss_search_ms for m in self.metrics_history if m.faiss_search_ms > 0]
        redis_hits = sum(1 for m in self.metrics_history if m.redis_cache_hit)
        hot_hits = sum(1 for m in self.metrics_history if m.hot_cache_hit)

        index_type = self.config.get_index_type()
        expected_latency = self._get_expected_latency(index_type)

        report = {
            "index_type": index_type.value,
            "vector_count": self.config.vector_count,
            "total_queries": len(self.metrics_history),
            "latency": {
                "avg_ms": np.mean(latencies),
                "p50_ms": np.percentile(latencies, 50),
                "p95_ms": np.percentile(latencies, 95),
                "p99_ms": np.percentile(latencies, 99),
                "min_ms": np.min(latencies),
                "max_ms": np.max(latencies),
                "expected_range": expected_latency
            },
            "faiss": {
                "avg_search_ms": np.mean(faiss_times) if faiss_times else 0,
                "p95_search_ms": np.percentile(faiss_times, 95) if faiss_times else 0
            },
            "cache": {
                "redis_hit_rate": redis_hits / len(self.metrics_history),
                "hot_hit_rate": hot_hits / len(self.metrics_history),
                "total_hits": redis_hits + hot_hits
            },
            "performance_validation": {
                "target_met": np.percentile(latencies, 95) <= 50,
                "within_expected_range": (
                    expected_latency[0] <= np.mean(latencies) <= expected_latency[1]
                )
            }
        }

        return report

    @staticmethod
    def _get_expected_latency(index_type: IndexType) -> Tuple[float, float]:
        """Get expected latency range for index type"""
        ranges = {
            IndexType.FLAT_L2: (1, 5),
            IndexType.IVF_FLAT: (2, 10),
            IndexType.IVF_PQ: (5, 20),
            IndexType.GPU_IVF_PQ: (2, 10)
        }
        return ranges.get(index_type, (0, 100))

    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    def clear_caches(self):
        """Clear all cache layers"""
        self._hot_chunks.clear()
        self._cached_search.cache_clear()
        logger.info("Caches cleared")


# Convenience function for quick setup
def create_context_retrieval(
    vector_count: int,
    embedding_dim: int = 768,
    redis_url: str = "redis://localhost:6379",
    use_redis: bool = True,
    index_path: Optional[str] = None,
    use_gpu: bool = False
) -> HighPerformanceContextRetrieval:
    """
    Factory function to create HighPerformanceContextRetrieval with sensible defaults

    Args:
        vector_count: Number of vectors in the index
        embedding_dim: Dimension of embeddings
        redis_url: Redis connection URL
        use_redis: Whether to use Redis caching
        index_path: Path to existing FAISS index
        use_gpu: Whether to use GPU acceleration

    Returns:
        Configured HighPerformanceContextRetrieval instance
    """
    config = CacheConfig(
        vector_count=vector_count,
        embedding_dim=embedding_dim,
        redis_url=redis_url,
        use_redis=use_redis,
        index_path=index_path,
        use_gpu=use_gpu
    )

    return HighPerformanceContextRetrieval(config)