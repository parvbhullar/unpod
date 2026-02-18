"""
Lightweight hybrid reranker for knowledge base search results.

Combines dense (embedding) scores with lexical (term frequency) and intent
(phrase matching) signals to improve ranking without external dependencies.

Usage:
    from super.core.memory.search.reranker import hybrid_rerank
    reranked = hybrid_rerank(query, search_docs)
"""

import math
import re
from dataclasses import dataclass
from typing import List, Optional

from super.core.memory.search.schema import SearchDoc


# Common English + Hindi/Hinglish stop words to exclude from lexical matching
_STOP_WORDS = frozenset(
    {
        # English
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "can", "could", "i", "me", "my", "we",
        "our", "you", "your", "he", "she", "it", "they", "them", "this",
        "that", "these", "those", "am", "if", "or", "but", "not", "no",
        "so", "at", "by", "for", "with", "about", "to", "from", "in", "on",
        "of", "and", "how", "what", "which", "who", "whom", "when", "where",
        "why", "all", "each", "every", "both", "few", "more", "most", "some",
        "any", "into", "through", "during", "before", "after", "above",
        "below", "up", "down", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "just", "also", "very",
        "too", "only", "own", "same", "than", "tell", "know", "get",
        # Hindi / Hinglish (romanized)
        "ke", "ka", "ki", "hai", "hain", "aur", "se", "ko", "me", "mein",
        "par", "liye", "tha", "the", "thi", "ho", "hota", "hoti", "hote",
        "yeh", "woh", "kya", "nahi", "na", "ya", "bhi", "toh", "jo",
        "jab", "tak", "koi", "kuch", "sab", "bahut", "ek", "ye", "wo",
        "apna", "apni", "apne", "unka", "unki", "uske", "iske", "jaise",
    }
)


@dataclass
class RerankerWeights:
    """Weights for combining ranking signals."""

    dense: float = 0.5
    lexical: float = 0.35
    intent: float = 0.15
    generic_penalty: float = 0.4


_CONTACT_DOC_MARKERS = (
    "phone:",
    "email:",
    "contact",
    "old rajinder nagar",
    "new delhi",
    "@",
)

_INTENTFUL_QUERY_MARKERS = (
    "why",
    "join",
    "process",
    "services",
    "fees",
    "timings",
)


def _tokenize(text: str) -> list[str]:
    """Extract lowercase word tokens from text."""
    return re.findall(r"\w+", text.lower())


def _content_tokens(text: str) -> set[str]:
    """Extract unique lowercase tokens from text."""
    return set(re.findall(r"\w+", text.lower()))


def _query_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from query (stop words removed)."""
    tokens = _tokenize(text)
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _lexical_score(query_keywords: list[str], doc_text: str) -> float:
    """
    BM25-inspired term frequency score.

    For each query keyword, counts occurrences in the document (as substring),
    applies log dampening, and normalizes by matched keyword count (not total).
    This avoids penalizing docs that strongly match a subset of query terms.
    """
    if not query_keywords:
        return 0.0

    doc_lower = doc_text.lower()
    total_score = 0.0
    matched_count = 0

    for keyword in query_keywords:
        count = doc_lower.count(keyword)
        if count > 0:
            matched_count += 1
            # Log-dampened frequency: 1 occurrence = 1.0, 3 = 2.1, 6 = 2.8
            total_score += 1.0 + math.log(1 + count)

    if matched_count == 0:
        return 0.0

    return total_score / matched_count


def _intent_score(query: str, doc_content: str) -> float:
    """
    Compute intent-matching bonus based on bigram overlap and phrase matching.

    Rewards documents that contain multi-word phrases from the query.
    """
    query_lower = query.lower()
    doc_lower = doc_content.lower()

    query_words = _tokenize(query_lower)
    if len(query_words) < 2:
        return 1.0 if query_lower.strip() in doc_lower else 0.0

    # Check bigrams
    bigrams = [
        f"{query_words[i]} {query_words[i + 1]}"
        for i in range(len(query_words) - 1)
    ]
    matched_bigrams = sum(1 for bg in bigrams if bg in doc_lower)
    bigram_score = matched_bigrams / len(bigrams) if bigrams else 0.0

    # Check trigrams for stronger signal
    trigram_score = 0.0
    if len(query_words) >= 3:
        trigrams = [
            f"{query_words[i]} {query_words[i + 1]} {query_words[i + 2]}"
            for i in range(len(query_words) - 2)
        ]
        matched_trigrams = sum(1 for tg in trigrams if tg in doc_lower)
        trigram_score = matched_trigrams / len(trigrams) if trigrams else 0.0

    return 0.6 * bigram_score + 0.4 * trigram_score


def _generic_doc_penalty(query: str, doc_content: str) -> float:
    """
    Penalize generic contact/address documents for intentful questions.

    This prevents entity-only matches (e.g. contact info pages) from outranking
    answer-rich documents when the user asks for substantive information.
    """
    query_lower = query.lower()
    if not any(marker in query_lower for marker in _INTENTFUL_QUERY_MARKERS):
        return 0.0

    doc_lower = doc_content.lower()
    marker_hits = sum(1 for marker in _CONTACT_DOC_MARKERS if marker in doc_lower)

    # Require multiple contact indicators to avoid over-penalizing normal docs.
    return 1.0 if marker_hits >= 2 else 0.0


def hybrid_rerank(
    query: str,
    docs: List[SearchDoc],
    weights: Optional[RerankerWeights] = None,
) -> List[SearchDoc]:
    """
    Re-rank search results using a hybrid scoring approach.

    Combines three signals:
    - Dense score: Original embedding similarity from vector search
    - Lexical score: BM25-inspired term frequency matching
    - Intent score: N-gram phrase matching for intent alignment

    Args:
        query: The user's search query
        docs: Search results with dense scores from vector search
        weights: Optional custom weights

    Returns:
        Re-ranked list of SearchDoc objects with updated scores
    """
    if not docs or len(docs) <= 1:
        return docs

    weights = weights or RerankerWeights()
    keywords = _query_keywords(query)

    scored_docs: list[tuple[float, SearchDoc]] = []
    for doc in docs:
        dense = doc.score or 0.0
        lexical = _lexical_score(keywords, doc.content)
        intent = _intent_score(query, doc.content)
        generic_penalty = _generic_doc_penalty(query, doc.content)

        combined = (
            weights.dense * dense
            + weights.lexical * lexical
            + weights.intent * intent
            - weights.generic_penalty * generic_penalty
        )
        scored_docs.append((combined, doc))

    scored_docs.sort(key=lambda x: x[0], reverse=True)

    reranked: list[SearchDoc] = []
    for combined_score, doc in scored_docs:
        doc.score = combined_score
        reranked.append(doc)

    return reranked
