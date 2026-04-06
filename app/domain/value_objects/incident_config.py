from dataclasses import dataclass


@dataclass(frozen=True)
class IncidentConfig:
    min_calls_per_minute: int = 20
    min_spike_duration_seconds: int = 30
    incident_trigger_minutes: int = 2
    cooldown_minutes: int = 5
    auto_resolve_minutes: int = 5
    baseline_window_minutes: int = 10
    detection_interval_seconds: int = 10
    # High-frequency threshold for CRITICAL severity
    critical_calls_per_minute: float = 1000.0
