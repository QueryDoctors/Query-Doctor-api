from typing import List
from app.domain.entities.query_stat import QueryStat
from app.domain.entities.recommendation import Recommendation
from app.domain.value_objects.database_metrics import DatabaseMetrics
from app.domain.value_objects.severity import Severity


class RecommendationEngine:
    """Pure domain service — no I/O, fully unit-testable."""

    def generate(
        self,
        metrics: DatabaseMetrics,
        slow_queries: List[QueryStat],
        frequent_queries: List[QueryStat],
        heaviest_queries: List[QueryStat],
    ) -> List[Recommendation]:
        results: List[Recommendation] = []

        self._check_slow_queries(slow_queries, results)
        self._check_high_total_time(heaviest_queries, results)
        self._check_full_table_scan(slow_queries + frequent_queries + heaviest_queries, results)
        self._check_too_many_connections(metrics, results)
        self._check_low_qps_high_latency(metrics, results)

        return results

    def _check_slow_queries(
        self, queries: List[QueryStat], results: List[Recommendation]
    ) -> None:
        for q in queries:
            if q.mean_time_ms > 200 and q.calls > 100:
                results.append(Recommendation(
                    problem="Slow query detected",
                    impact="Increases response time for end users",
                    suggestion="Consider adding an index or optimizing the WHERE clause",
                    severity=Severity.HIGH,
                ))
                return

    def _check_high_total_time(
        self, heaviest: List[QueryStat], results: List[Recommendation]
    ) -> None:
        if heaviest and heaviest[0].total_time_ms > 10_000:
            results.append(Recommendation(
                problem="Query with very high cumulative execution time",
                impact="Consumes disproportionate database resources",
                suggestion="Optimize the query or reduce its call frequency",
                severity=Severity.MEDIUM,
            ))

    def _check_full_table_scan(
        self, queries: List[QueryStat], results: List[Recommendation]
    ) -> None:
        seen = set()
        for q in queries:
            if q.query in seen:
                continue
            seen.add(q.query)
            if q.rows is not None and q.calls > 0 and (q.rows / q.calls) > 10_000:
                results.append(Recommendation(
                    problem="Possible full table scan detected",
                    impact="High I/O — slows down the entire database under load",
                    suggestion="Run EXPLAIN ANALYZE — a missing index may be causing sequential scans",
                    severity=Severity.HIGH,
                ))
                return

    def _check_too_many_connections(
        self, metrics: DatabaseMetrics, results: List[Recommendation]
    ) -> None:
        if metrics.active_connections > 80:
            results.append(Recommendation(
                problem="High number of active connections",
                impact="May exhaust the connection limit, causing new connections to fail",
                suggestion="Use a connection pooler like pgBouncer to reduce direct connections",
                severity=Severity.HIGH,
            ))

    def _check_low_qps_high_latency(
        self, metrics: DatabaseMetrics, results: List[Recommendation]
    ) -> None:
        if metrics.qps < 10 and metrics.avg_query_time_ms > 500:
            results.append(Recommendation(
                problem="Low query throughput with high average latency",
                impact="Suggests blocking or locking issues slowing down queries",
                suggestion="Check pg_locks and pg_stat_activity for blocked queries or long transactions",
                severity=Severity.MEDIUM,
            ))
