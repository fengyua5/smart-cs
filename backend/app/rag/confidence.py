import re
from typing import Tuple
from app.config import CONFIDENCE_RETRIEVAL_THRESHOLD, CONFIDENCE_LLM_THRESHOLD


def extract_confidence_from_answer(answer: str) -> int:
    match = re.search(r'\[自信度:\s*(\d+)\]', answer)
    if match:
        return int(match.group(1))
    match = re.search(r'[Cc]onfidence[:\s]*(\d+)', answer)
    if match:
        return int(match.group(1))
    return 5


def evaluate_confidence(
    retrieval_scores: list[float],
    llm_answer: str,
) -> Tuple[float, bool]:
    max_retrieval_score = max(retrieval_scores) if retrieval_scores else 0.0
    llm_confidence = extract_confidence_from_answer(llm_answer)

    retrieval_flag = max_retrieval_score < CONFIDENCE_RETRIEVAL_THRESHOLD
    llm_flag = llm_confidence < CONFIDENCE_LLM_THRESHOLD

    need_review = retrieval_flag or llm_flag
    combined = min(max_retrieval_score, llm_confidence / 10.0)

    return combined, need_review
