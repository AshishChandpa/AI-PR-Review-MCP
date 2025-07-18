from dataclasses import dataclass

@dataclass
class ReviewResult:
    content: str
    provider: str
    model_used: str
    review_type: str
