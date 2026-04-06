CREATE TABLE IF NOT EXISTS `{{DB}}`.query_baseline_agg (
    db_id      String,
    query_hash String,
    p95_state  AggregateFunction(quantile(0.95), Float64),
    last_seen  SimpleAggregateFunction(max, DateTime)
) ENGINE = AggregatingMergeTree()
ORDER BY (db_id, query_hash);

CREATE MATERIALIZED VIEW IF NOT EXISTS `{{DB}}`.query_baseline_mv
TO `{{DB}}`.query_baseline_agg
AS SELECT
    db_id,
    query_hash,
    quantileState(0.95)(mean_latency_ms) AS p95_state,
    max(captured_at)                      AS last_seen
FROM `{{DB}}`.query_latency_snapshots
GROUP BY db_id, query_hash