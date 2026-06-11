INSERT INTO app_log (
    level,
    module,
    function_name,
    line,
    message,
    context_json
) VALUES (?, ?, ?, ?, ?, ?);
