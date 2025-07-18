from dataclasses import dataclass
from typing import Optional

@dataclass
class PRData:
    title: str
    description: Optional[str]
    diff: str
    files_changed: int
    additions: int
    deletions: int
    number: int
    owner: str
    repo: str
    provider: str = "github"  # Add provider field
