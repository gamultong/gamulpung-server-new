-- Purpose: Fetch one application log row by exact message text for repository tests and smoke checks.
-- Structure: Loaded by utils.logging.internal.repository.get_app_log_by_message() against the app_log table.
SELECT level, message, context_json
FROM app_log
WHERE message = ?;
