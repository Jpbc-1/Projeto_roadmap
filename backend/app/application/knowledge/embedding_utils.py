from typing import List, Optional

SIMILARITY_THRESHOLD = 0.85


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def find_duplicate_node(embedding: List[float], existing_nodes: List) -> Optional[object]:
    """Entre os nós existentes, acha o mais parecido semanticamente -- se
    estiver acima do limiar, é considerado o mesmo conceito."""
    best_match = None
    best_score = 0.0
    for node in existing_nodes:
        score = cosine_similarity(embedding, node.embedding)
        if score > best_score:
            best_score = score
            best_match = node
    return best_match if best_score >= SIMILARITY_THRESHOLD else None