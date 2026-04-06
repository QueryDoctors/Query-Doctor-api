from typing import Optional

from app.domain.value_objects.severity import Severity
from app.domain.value_objects.incident_config import IncidentConfig


class IncidentEngine:
    """Pure domain service — no I/O, fully unit-testable."""

    # Absolute floor threshold (ms) — never classify as normal below this
    _ABSOLUTE_THRESHOLD_MS = 500.0

    def is_abnormal(self, latency_ms: float, baseline_ms: Optional[float]) -> bool:
        """
        Abnormal = latency > max(500ms, baseline_p95 × 2).
        If baseline is None/0 → use absolute threshold only.
        """
        if latency_ms <= 0:
            return False
        dynamic = (baseline_ms * 2.0) if baseline_ms else 0.0
        threshold = max(self._ABSOLUTE_THRESHOLD_MS, dynamic)
        return latency_ms > threshold

    def classify_severity(
        self,
        latency_ms: float,
        baseline_ms: float,
        calls_per_min: float,
        config: IncidentConfig,
    ) -> Severity:
        if baseline_ms <= 0:
            return Severity.LOW
        ratio = latency_ms / baseline_ms
        if ratio > 5.0 or calls_per_min >= config.critical_calls_per_minute:
            return Severity.CRITICAL
        if ratio > 3.0:
            return Severity.HIGH
        if ratio > 2.0:
            return Severity.MEDIUM
        return Severity.LOW

    def compute_ratio(self, latency_ms: float, baseline_ms: float) -> float:
        if baseline_ms <= 0:
            return 0.0
        return round(latency_ms / baseline_ms, 2)

    def should_filter(
        self,
        calls_per_min: float,
        spike_duration_seconds: float,
        is_muted: bool,
        is_whitelisted: bool,
        config: IncidentConfig,
    ) -> bool:
        """
        Returns True if the query should be filtered (i.e. no incident created).
        Whitelist bypasses the frequency filter but NOT the mute filter.
        """
        if is_muted:
            return True
        if not is_whitelisted and calls_per_min < config.min_calls_per_minute:
            return True
        if spike_duration_seconds < config.min_spike_duration_seconds:
            return True
        return False
