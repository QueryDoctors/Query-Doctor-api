from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def sort_key(self) -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1}[self.value]
