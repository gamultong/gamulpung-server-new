-- Purpose: Read the newest application logs for the stats dashboard recent log panel.
-- Structure: Loaded by utils.logging.internal.repository.get_recent_app_logs(), then mapped by utils.stats.internal.dashboard_repository.
SELECT id, added_at, level, module, function_name, line, message, context_json
FROM app_log
ORDER BY id DESC
LIMIT ?;
