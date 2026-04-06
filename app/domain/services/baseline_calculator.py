from typing import List, Optional


class BaselineCalculator:
    """Pure domain service — no I/O, fully unit-testable."""

    def calculate_p95(self, latency_values: List[float]) -> Optional[float]:
        """
        Return the 95th percentile of the given latency values.
        Returns None if fewer than 3 data points (not enough for a stable baseline).
        """
        if len(latency_values) < 3:
            return None
        sorted_vals = sorted(latency_values)
        idx = int(len(sorted_vals) * 0.95)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]
