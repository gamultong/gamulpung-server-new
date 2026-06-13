SELECT level, message, context_json
FROM app_log
WHERE message = ?;
