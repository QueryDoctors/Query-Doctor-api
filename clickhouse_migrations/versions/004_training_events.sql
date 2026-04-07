CREATE TABLE IF NOT EXISTS `{{DB}}`.training_events (
    incident_id          String,
    event_type           String,   -- incident_created | acknowledged | resolved | auto_resolved | muted | whitelisted
    db_id                String,
    query_hash           String,
    query_text           String,

    -- Features (populated only for event_type = 'incident_created')
    mean_latency_ms      Float64,
    baseline_latency_ms  Float64,
    latency_ratio        Float64,
    calls_per_minute     Float64,
    spike_duration_s     Int32,
    active_connections   Int32,
    p95_baseline_ms      Float64,
    prior_incident_count UInt16,
    severity_fired       String,

    -- Outcome metadata (populated for resolved / auto_resolved)
    resolution_time_s    Int32,    -- 0 = not applicable

    captured_at          DateTime
) ENGINE = MergeTree()
ORDER BY (db_id, incident_id, captured_at)
TTL captured_at + INTERVAL 90 DAY
SETTINGS index_granularity = 8192
