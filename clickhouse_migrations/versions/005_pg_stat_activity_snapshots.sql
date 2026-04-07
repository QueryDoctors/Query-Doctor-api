CREATE TABLE IF NOT EXISTS `{{DB}}`.pg_stat_activity_snapshots (
    db_id            String,
    pid              Int32,
    username         String,
    app_name         String,
    client_addr      String,
    state            String,    -- active | idle | idle in transaction | ...
    wait_event_type  String,
    wait_event       String,
    query            String,
    query_duration_s Float64,   -- seconds since query_start (0 if null / idle)
    state_duration_s Float64,   -- seconds since last state change (0 if null)
    captured_at      DateTime
) ENGINE = MergeTree()
ORDER BY (db_id, captured_at, pid)
TTL captured_at + INTERVAL 1 DAY
SETTINGS index_granularity = 8192
