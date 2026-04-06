CREATE TABLE IF NOT EXISTS `{{DB}}`.query_latency_snapshots (
    db_id            String,
    query_hash       String,
    query_text       String,
    mean_latency_ms  Float64,
    calls            UInt64,
    calls_per_minute Float64,
    captured_at      DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (db_id, query_hash, captured_at)
TTL captured_at + INTERVAL 1 DAY
SETTINGS index_granularity = 8192