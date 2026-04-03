from app.domain.entities.query_stat import QueryStat
from app.domain.entities.recommendation import Recommendation
from app.domain.value_objects.severity import Severity


class TestQueryStat:
    def test_rows_defaults_to_none(self):
        q = QueryStat(query="SELECT 1", mean_time_ms=1.0, calls=10, total_time_ms=10.0)
        assert q.rows is None

    def test_all_fields_set(self):
        q = QueryStat(query="SELECT *", mean_time_ms=200.0, calls=50, total_time_ms=10_000.0, rows=5000)
        assert q.query == "SELECT *"
        assert q.mean_time_ms == 200.0
        assert q.calls == 50
        assert q.total_time_ms == 10_000.0
        assert q.rows == 5000


class TestRecommendation:
    def test_all_fields_set(self):
        r = Recommendation(
            problem="Slow query",
            impact="High latency",
            suggestion="Add index",
            severity=Severity.HIGH,
        )
        assert r.problem == "Slow query"
        assert r.severity == Severity.HIGH

    def test_severity_is_enum(self):
        r = Recommendation(problem="x", impact="y", suggestion="z", severity=Severity.MEDIUM)
        assert isinstance(r.severity, Severity)
