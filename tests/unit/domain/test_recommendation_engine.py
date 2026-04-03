import pytest
from app.domain.services.recommendation_engine import RecommendationEngine
from app.domain.entities.query_stat import QueryStat
from app.domain.value_objects.database_metrics import DatabaseMetrics
from app.domain.value_objects.severity import Severity


@pytest.fixture
def engine() -> RecommendationEngine:
    return RecommendationEngine()


@pytest.fixture
def healthy_metrics() -> DatabaseMetrics:
    return DatabaseMetrics(active_connections=10, qps=100.0, avg_query_time_ms=20.0, total_queries=5000)


@pytest.fixture
def empty_queries():
    return []


# ─── Rule 1: Slow query ──────────────────────────────────────────────────────

class TestSlowQueryRule:
    def test_triggers_when_mean_time_above_200_and_calls_above_100(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=300.0, calls=150, total_time_ms=45_000.0)
        results = engine.generate(healthy_metrics, [query], [], [])
        assert any(r.problem == "Slow query detected" for r in results)

    def test_does_not_trigger_when_mean_time_below_200(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=199.0, calls=150, total_time_ms=29_850.0)
        results = engine.generate(healthy_metrics, [query], [], [])
        assert not any(r.problem == "Slow query detected" for r in results)

    def test_does_not_trigger_when_calls_below_100(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=500.0, calls=99, total_time_ms=49_500.0)
        results = engine.generate(healthy_metrics, [query], [], [])
        assert not any(r.problem == "Slow query detected" for r in results)

    def test_boundary_exactly_200ms_and_100_calls_does_not_trigger(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=200.0, calls=100, total_time_ms=20_000.0)
        results = engine.generate(healthy_metrics, [query], [], [])
        assert not any(r.problem == "Slow query detected" for r in results)

    def test_severity_is_high(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=500.0, calls=500, total_time_ms=250_000.0)
        results = engine.generate(healthy_metrics, [query], [], [])
        match = next(r for r in results if r.problem == "Slow query detected")
        assert match.severity == Severity.HIGH


# ─── Rule 2: High total time ─────────────────────────────────────────────────

class TestHighTotalTimeRule:
    def test_triggers_when_total_time_above_10000(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=10.0, calls=1001, total_time_ms=10_001.0)
        results = engine.generate(healthy_metrics, [], [], [query])
        assert any(r.problem == "Query with very high cumulative execution time" for r in results)

    def test_does_not_trigger_when_total_time_below_threshold(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=10.0, calls=100, total_time_ms=9_999.0)
        results = engine.generate(healthy_metrics, [], [], [query])
        assert not any(r.problem == "Query with very high cumulative execution time" for r in results)

    def test_severity_is_medium(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=10.0, calls=2000, total_time_ms=20_000.0)
        results = engine.generate(healthy_metrics, [], [], [query])
        match = next(r for r in results if r.problem == "Query with very high cumulative execution time")
        assert match.severity == Severity.MEDIUM


# ─── Rule 3: Full table scan ─────────────────────────────────────────────────

class TestFullTableScanRule:
    def test_triggers_when_rows_per_call_above_10000(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=5.0, calls=10, total_time_ms=50.0, rows=200_000)
        results = engine.generate(healthy_metrics, [query], [], [])
        assert any(r.problem == "Possible full table scan detected" for r in results)

    def test_does_not_trigger_when_rows_per_call_below_threshold(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=5.0, calls=10, total_time_ms=50.0, rows=9_999)
        results = engine.generate(healthy_metrics, [query], [], [])
        assert not any(r.problem == "Possible full table scan detected" for r in results)

    def test_does_not_trigger_when_rows_is_none(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=5.0, calls=10, total_time_ms=50.0, rows=None)
        results = engine.generate(healthy_metrics, [query], [], [])
        assert not any(r.problem == "Possible full table scan detected" for r in results)

    def test_severity_is_high(self, engine, healthy_metrics):
        query = QueryStat(query="SELECT *", mean_time_ms=5.0, calls=1, total_time_ms=5.0, rows=50_000)
        results = engine.generate(healthy_metrics, [query], [], [])
        match = next(r for r in results if r.problem == "Possible full table scan detected")
        assert match.severity == Severity.HIGH


# ─── Rule 4: Too many connections ────────────────────────────────────────────

class TestTooManyConnectionsRule:
    def test_triggers_when_connections_above_80(self, engine, empty_queries):
        metrics = DatabaseMetrics(active_connections=81, qps=100.0, avg_query_time_ms=20.0, total_queries=1000)
        results = engine.generate(metrics, empty_queries, empty_queries, empty_queries)
        assert any(r.problem == "High number of active connections" for r in results)

    def test_does_not_trigger_when_connections_at_or_below_80(self, engine, empty_queries):
        metrics = DatabaseMetrics(active_connections=80, qps=100.0, avg_query_time_ms=20.0, total_queries=1000)
        results = engine.generate(metrics, empty_queries, empty_queries, empty_queries)
        assert not any(r.problem == "High number of active connections" for r in results)

    def test_severity_is_high(self, engine, empty_queries):
        metrics = DatabaseMetrics(active_connections=95, qps=100.0, avg_query_time_ms=20.0, total_queries=1000)
        results = engine.generate(metrics, empty_queries, empty_queries, empty_queries)
        match = next(r for r in results if r.problem == "High number of active connections")
        assert match.severity == Severity.HIGH


# ─── Rule 5: Low QPS + high latency ─────────────────────────────────────────

class TestLowQpsHighLatencyRule:
    def test_triggers_when_qps_low_and_latency_high(self, engine, empty_queries):
        metrics = DatabaseMetrics(active_connections=5, qps=5.0, avg_query_time_ms=600.0, total_queries=100)
        results = engine.generate(metrics, empty_queries, empty_queries, empty_queries)
        assert any(r.problem == "Low query throughput with high average latency" for r in results)

    def test_does_not_trigger_when_qps_is_normal(self, engine, empty_queries):
        metrics = DatabaseMetrics(active_connections=5, qps=50.0, avg_query_time_ms=600.0, total_queries=1000)
        results = engine.generate(metrics, empty_queries, empty_queries, empty_queries)
        assert not any(r.problem == "Low query throughput with high average latency" for r in results)

    def test_does_not_trigger_when_latency_is_normal(self, engine, empty_queries):
        metrics = DatabaseMetrics(active_connections=5, qps=5.0, avg_query_time_ms=100.0, total_queries=100)
        results = engine.generate(metrics, empty_queries, empty_queries, empty_queries)
        assert not any(r.problem == "Low query throughput with high average latency" for r in results)

    def test_boundary_exactly_qps_10_and_500ms_does_not_trigger(self, engine, empty_queries):
        metrics = DatabaseMetrics(active_connections=5, qps=10.0, avg_query_time_ms=500.0, total_queries=500)
        results = engine.generate(metrics, empty_queries, empty_queries, empty_queries)
        assert not any(r.problem == "Low query throughput with high average latency" for r in results)

    def test_severity_is_medium(self, engine, empty_queries):
        metrics = DatabaseMetrics(active_connections=5, qps=1.0, avg_query_time_ms=1000.0, total_queries=10)
        results = engine.generate(metrics, empty_queries, empty_queries, empty_queries)
        match = next(r for r in results if r.problem == "Low query throughput with high average latency")
        assert match.severity == Severity.MEDIUM
