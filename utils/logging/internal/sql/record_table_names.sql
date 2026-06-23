-- Purpose: List logging/stat tables that are currently present in the SQLite database.
-- Structure: Loaded by utils.logging.internal.repository.get_record_table_names() for repository visibility checks.
SELECT name
FROM sqlite_master
WHERE type = 'table' AND name IN ('app_log', 'stat_event')
ORDER BY name;
