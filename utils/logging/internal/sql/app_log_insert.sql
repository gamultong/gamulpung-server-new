-- Purpose: Persist one Loguru application log record into app_log.
-- Structure: Loaded by utils.logging.internal.repository.insert_app_log() and utils.logging.internal.db_sink.AppLogDbSink.
INSERT INTO app_log (
    level,
    module,
    function_name,
    line,
    message,
    context_json
) VALUES (?, ?, ?, ?, ?, ?);
