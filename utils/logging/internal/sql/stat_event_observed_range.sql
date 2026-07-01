-- Purpose: Read the first and last persisted stat event timestamps.
-- Structure: Loaded by utils.logging.internal.repository.get_stat_event_observed_range() for dashboard range metadata.
SELECT
    MIN(added_at) AS first_seen_at,
    MAX(added_at) AS last_seen_at
FROM stat_event;
