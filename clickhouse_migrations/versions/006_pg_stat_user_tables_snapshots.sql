CREATE TABLE IF NOT EXISTS `{{DB}}`.pg_stat_user_tables_snapshots (
    db_id         String,
    schema_name   String,
    table_name    String,
    seq_scan      Int64,
    seq_tup_read  Int64,
    idx_scan      Int64,
    idx_tup_fetch Int64,
    n_tup_ins     Int64,
    n_tup_upd     Int64,
    n_tup_del     Int64,
    n_live_tup    Int64,
    n_dead_tup    Int64,
    captured_at   DateTime
) ENGINE = MergeTree()
ORDER BY (db_id, schema_name, table_name, captured_at)
TTL captured_at + INTERVAL 7 DAY
SETTINGS index_granularity = 8192
