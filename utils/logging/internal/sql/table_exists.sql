-- Purpose: Check whether a repository-owned table exists before running optional reads.
-- Structure: Loaded by utils.logging.internal.repository.table_exists() and shared by app_log/stat_event read helpers.
SELECT name
FROM sqlite_master
WHERE type = 'table' AND name = ?;
