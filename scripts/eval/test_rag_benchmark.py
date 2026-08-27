import pytest
from typing import List, Dict, Any, Set


def compute_hit_rate_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """
    Computes Hit Rate@K: 1.0 if at least one ground truth ID is in retrieved_ids[:k], else 0.0.
    """
    top_k = set(retrieved_ids[:k])
    return 1.0 if (top_k & ground_truth_ids) else 0.0


def compute_mrr_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """
    Computes Mean Reciprocal Rank (MRR@K): 1 / rank of first relevant item in retrieved_ids[:k].
    """
    for rank, doc_id in enumerate(retrieved_ids[:k], start=1):
        if doc_id in ground_truth_ids:
            return 1.0 / rank
    return 0.0


def compute_precision_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """
    Computes Precision@K: fraction of retrieved items in top-K that are relevant.
    """
    if k <= 0 or not retrieved_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in ground_truth_ids)
    return hits / len(top_k)


def evaluate_retrieval_benchmark(dataset: List[Dict[str, Any]], k_values: List[int] = [1, 3, 5]) -> Dict[str, float]:
    """
    Evaluates a benchmark dataset containing queries, retrieved_docs, and ground_truth_docs.
    """
    if not dataset:
        return {f"HitRate@{k}": 0.0 for k in k_values} | {f"MRR@{k}": 0.0 for k in k_values}

    total_queries = len(dataset)
    results = {}

    for k in k_values:
        total_hit_rate = 0.0
        total_mrr = 0.0
        total_precision = 0.0

        for item in dataset:
            retrieved = item["retrieved"]
            ground_truth = set(item["ground_truth"])

            total_hit_rate += compute_hit_rate_at_k(retrieved, ground_truth, k)
            total_mrr += compute_mrr_at_k(retrieved, ground_truth, k)
            total_precision += compute_precision_at_k(retrieved, ground_truth, k)

        results[f"HitRate@{k}"] = round(total_hit_rate / total_queries, 4)
        results[f"MRR@{k}"] = round(total_mrr / total_queries, 4)
        results[f"Precision@{k}"] = round(total_precision / total_queries, 4)

    return results


class TestRagRetrievalEvaluationBenchmark:
    @pytest.fixture
    def benchmark_sample_dataset(self):
        return [
            {
                "query": "Quy chế đăng ký học phần IUH",
                "retrieved": ["doc_dkhp_1", "doc_dkhp_2", "doc_hp_3", "doc_other"],
                "ground_truth": ["doc_dkhp_1", "doc_dkhp_2"]
            },
            {
                "query": "Điều kiện xét học bổng khuyến khích",
                "retrieved": ["doc_other", "doc_hocbong_1", "doc_hocbong_2"],
                "ground_truth": ["doc_hocbong_1"]
            },
            {
                "query": "Thời hạn đóng học phí kỳ 1",
                "retrieved": ["doc_random_1", "doc_random_2", "doc_hocphi_1"],
                "ground_truth": ["doc_hocphi_1"]
            },
            {
                "query": "Thủ tục xin cấp bảng điểm",
                "retrieved": ["doc_bangdiem_1", "doc_bangdiem_2"],
                "ground_truth": ["doc_bangdiem_1"]
            }
        ]

    def test_hit_rate_at_1_calculation(self, benchmark_sample_dataset):
        # Query 1: doc_dkhp_1 is rank 1 -> Hit
        # Query 2: doc_other is rank 1 -> Miss
        # Query 3: doc_random_1 is rank 1 -> Miss
        # Query 4: doc_bangdiem_1 is rank 1 -> Hit
        # Total: 2/4 = 0.50
        metrics = evaluate_retrieval_benchmark(benchmark_sample_dataset, k_values=[1, 3, 5])
        assert metrics["HitRate@1"] == 0.50

    def test_hit_rate_at_3_calculation(self, benchmark_sample_dataset):
        # Query 1: hit at rank 1 -> Hit
        # Query 2: hit at rank 2 -> Hit
        # Query 3: hit at rank 3 -> Hit
        # Query 4: hit at rank 1 -> Hit
        # Total: 4/4 = 1.00
        metrics = evaluate_retrieval_benchmark(benchmark_sample_dataset, k_values=[1, 3, 5])
        assert metrics["HitRate@3"] == 1.00

    def test_mrr_at_5_calculation(self, benchmark_sample_dataset):
        # Query 1: rank 1 -> 1/1 = 1.0
        # Query 2: rank 2 -> 1/2 = 0.5
        # Query 3: rank 3 -> 1/3 = 0.3333
        # Query 4: rank 1 -> 1/1 = 1.0
        # Mean MRR: (1.0 + 0.5 + 0.33333 + 1.0) / 4 = 2.83333 / 4 ~= 0.7083
        metrics = evaluate_retrieval_benchmark(benchmark_sample_dataset, k_values=[5])
        assert pytest.approx(metrics["MRR@5"], rel=1e-3) == 0.7083

    def test_empty_dataset_returns_zeros(self):
        metrics = evaluate_retrieval_benchmark([])
        assert metrics["HitRate@1"] == 0.0
        assert metrics["MRR@1"] == 0.0
