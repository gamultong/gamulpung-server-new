SELECT id, added_at, level, module, function_name, line, message, context_json
FROM app_log
ORDER BY id DESC
LIMIT ?;
