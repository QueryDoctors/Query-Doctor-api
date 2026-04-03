from dataclasses import dataclass
from app.domain.value_objects.severity import Severity


@dataclass
class Recommendation:
    problem: str
    impact: str
    suggestion: str
    severity: Severity
