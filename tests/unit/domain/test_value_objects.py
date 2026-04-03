import pytest
from app.domain.value_objects.severity import Severity
from app.domain.value_objects.connection_config import ConnectionConfig
from app.domain.value_objects.database_metrics import DatabaseMetrics


class TestSeverity:
    def test_values_are_lowercase_strings(self):
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"

    def test_is_string_enum(self):
        assert isinstance(Severity.HIGH, str)


class TestConnectionConfig:
    def test_is_immutable(self):
        config = ConnectionConfig(host="localhost", port=5432, database="db", user="u", password="p")
        with pytest.raises(Exception):
            config.host = "other"  # type: ignore

    def test_equality_by_value(self):
        a = ConnectionConfig(host="localhost", port=5432, database="db", user="u", password="p")
        b = ConnectionConfig(host="localhost", port=5432, database="db", user="u", password="p")
        assert a == b

    def test_inequality_on_different_values(self):
        a = ConnectionConfig(host="localhost", port=5432, database="db1", user="u", password="p")
        b = ConnectionConfig(host="localhost", port=5432, database="db2", user="u", password="p")
        assert a != b


class TestDatabaseMetrics:
    def test_is_immutable(self):
        m = DatabaseMetrics(active_connections=5, qps=10.0, avg_query_time_ms=20.0, total_queries=100)
        with pytest.raises(Exception):
            m.active_connections = 999  # type: ignore

    def test_fields_are_accessible(self):
        m = DatabaseMetrics(active_connections=5, qps=10.0, avg_query_time_ms=20.0, total_queries=100)
        assert m.active_connections == 5
        assert m.qps == 10.0
        assert m.avg_query_time_ms == 20.0
        assert m.total_queries == 100
