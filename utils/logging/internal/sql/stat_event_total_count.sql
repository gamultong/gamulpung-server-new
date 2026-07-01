-- Purpose: Count all persisted stat events regardless of dashboard filter.
-- Structure: Loaded by utils.logging.internal.repository.get_total_stat_event_count() for dashboard stored summary.
SELECT COUNT(*) AS count
FROM stat_event;
