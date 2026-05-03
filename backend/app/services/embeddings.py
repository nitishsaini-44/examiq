"""
ExamIQ Embedding & Clustering Service
Semantic embeddings with Sentence-Transformers + FAISS for clustering.
STEP 1 (cont.) + STEP 2 (clustering)
"""
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-loaded globals
_model = None
_index = None


def _get_model():
    """Lazy load the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.core.config import EMBEDDING_MODEL
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            _model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            _model = None
    return _model


def generate_embeddings(texts: list[str]) -> Optional[np.ndarray]:
    """
    Generate semantic embeddings for a list of texts.
    Returns numpy array of shape (n_texts, embedding_dim).
    """
    model = _get_model()
    if model is None:
        logger.warning("Embedding model not available, using fallback")
        return _fallback_embeddings(texts)

    try:
        embeddings = model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=32
        )
        return embeddings.astype('float32')
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return _fallback_embeddings(texts)


def _fallback_embeddings(texts: list[str]) -> np.ndarray:
    """
    Simple TF-IDF-like fallback when sentence-transformers is unavailable.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
    try:
        matrix = vectorizer.fit_transform(texts).toarray().astype('float32')
        # Normalize
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1
        matrix = matrix / norms
        return matrix
    except Exception as e:
        logger.error(f"Fallback embedding failed: {e}")
        return np.random.randn(len(texts), 384).astype('float32')


def cluster_questions(embeddings: np.ndarray, n_clusters: int = 10) -> np.ndarray:
    """
    Cluster question embeddings using FAISS K-Means.
    Returns cluster labels for each question.
    """
    n_samples = embeddings.shape[0]

    # Adjust clusters if too few samples
    actual_clusters = min(n_clusters, max(2, n_samples // 2))

    try:
        import faiss

        dimension = embeddings.shape[1]
        kmeans = faiss.Kmeans(
            d=dimension,
            k=actual_clusters,
            niter=20,
            verbose=False,
            gpu=False
        )
        kmeans.train(embeddings)
        _, labels = kmeans.index.search(embeddings, 1)
        return labels.flatten()

    except ImportError:
        logger.warning("FAISS not available, using sklearn K-Means")
        from sklearn.cluster import KMeans
        km = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
        return km.fit_predict(embeddings)


def find_similar_questions(
    embeddings: np.ndarray,
    query_idx: int,
    k: int = 5,
    threshold: float = 0.75
) -> list[tuple[int, float]]:
    """
    Find questions semantically similar to a given question.
    Returns list of (index, similarity_score) tuples.
    """
    try:
        import faiss

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product (cosine for normalized)
        index.add(embeddings)

        query = embeddings[query_idx:query_idx + 1]
        distances, indices = index.search(query, min(k + 1, len(embeddings)))

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != query_idx and dist >= threshold:
                results.append((int(idx), float(dist)))

        return results

    except ImportError:
        # Fallback: manual cosine similarity
        query = embeddings[query_idx]
        similarities = embeddings @ query
        top_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in top_indices[:k + 1]:
            if idx != query_idx and similarities[idx] >= threshold:
                results.append((int(idx), float(similarities[idx])))

        return results


def detect_concept_repetition(
    questions: list,
    embeddings: np.ndarray,
    threshold: float = 0.8
) -> list[dict]:
    """
    Detect concept-level repetition across years.
    Returns groups of similar questions from different years.
    """
    repetitions = []
    visited = set()

    for i in range(len(questions)):
        if i in visited:
            continue

        similar = find_similar_questions(embeddings, i, k=10, threshold=threshold)
        if not similar:
            continue

        group = [{"index": i, "year": questions[i].year, "text": questions[i].text[:100]}]
        visited.add(i)

        for idx, score in similar:
            if idx not in visited:
                group.append({
                    "index": idx,
                    "year": questions[idx].year,
                    "text": questions[idx].text[:100],
                    "similarity": round(score, 3)
                })
                visited.add(idx)

        # Only report cross-year repetitions
        years_in_group = set(item["year"] for item in group if item["year"] > 0)
        if len(years_in_group) > 1:
            repetitions.append({
                "concept": questions[i].text[:80],
                "occurrences": len(group),
                "years": sorted(years_in_group),
                "questions": group
            })

    return repetitions
