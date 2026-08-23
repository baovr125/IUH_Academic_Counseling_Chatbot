import pytest
from typing import List, Dict, Any


def compute_rrf_score(
    vector_rankings: List[str],
    keyword_rankings: List[str],
    k: int = 60
) -> Dict[str, float]:
    """
    Python reference implementation of Reciprocal Rank Fusion (RRF):
    RRF(d) = sum(1 / (k + rank_m(d))) for each ranking list m in M.
    """
    scores: Dict[str, float] = {}

    # Process vector rankings (1-indexed)
    for rank, doc_id in enumerate(vector_rankings, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # Process keyword rankings (1-indexed)
    for rank, doc_id in enumerate(keyword_rankings, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    return dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))


class TestReciprocalRankFusion:
    def test_rrf_formula_single_item_rank_1(self):
        # Rank 1 in one list: 1 / (60 + 1) = 1/61 ~= 0.0163934
        scores = compute_rrf_score(vector_rankings=["doc1"], keyword_rankings=[], k=60)
        assert pytest.approx(scores["doc1"], rel=1e-5) == 1.0 / 61.0

    def test_rrf_boost_item_appearing_in_both_lists_rank_1(self):
        # Rank 1 in both lists: (1/61) + (1/61) = 2/61 ~= 0.0327868
        scores = compute_rrf_score(
            vector_rankings=["doc_both"],
            keyword_rankings=["doc_both"],
            k=60
        )
        assert pytest.approx(scores["doc_both"], rel=1e-5) == 2.0 / 61.0

    def test_rrf_ordering_prefers_consensus_over_isolated_high_rank(self):
        # docA is rank 2 in both lists: 1/62 + 1/62 = 2/62 = 0.032258
        # docB is rank 1 in vector only: 1/61 + 0 = 0.016393
        vector = ["docB", "docA"]
        keyword = ["docC", "docA"]
        
        scores = compute_rrf_score(vector_rankings=vector, keyword_rankings=keyword, k=60)
        ordered_docs = list(scores.keys())
        
        # docA (present in both) must rank higher than docB (only in vector)
        assert ordered_docs[0] == "docA"
        assert scores["docA"] > scores["docB"]
        assert scores["docA"] > scores["docC"]

    def test_rrf_empty_rankings_returns_empty_dict(self):
        scores = compute_rrf_score(vector_rankings=[], keyword_rankings=[], k=60)
        assert scores == {}

    def test_rrf_different_k_parameter(self):
        scores_k60 = compute_rrf_score(["doc1"], ["doc1"], k=60)
        scores_k10 = compute_rrf_score(["doc1"], ["doc1"], k=10)
        
        # Lower k gives higher weight to top ranks
        assert scores_k10["doc1"] > scores_k60["doc1"]
        assert pytest.approx(scores_k10["doc1"], rel=1e-5) == 2.0 / 11.0

    def test_rrf_disjoint_lists_ranks_top_items_equally(self):
        vector = ["vec_1", "vec_2"]
        keyword = ["key_1", "key_2"]
        scores = compute_rrf_score(vector_rankings=vector, keyword_rankings=keyword, k=60)
        
        assert pytest.approx(scores["vec_1"], rel=1e-5) == scores["key_1"]
        assert pytest.approx(scores["vec_2"], rel=1e-5) == scores["key_2"]
        assert scores["vec_1"] > scores["vec_2"]
