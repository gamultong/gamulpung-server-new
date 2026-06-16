CREATE TABLE IF NOT EXISTS app_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    added_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    level TEXT NOT NULL,
    module TEXT,
    function_name TEXT,
    line INTEGER,
    message TEXT NOT NULL,
    context_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_app_log_added ON app_log(added_at);
CREATE INDEX IF NOT EXISTS idx_app_log_level_added ON app_log(level, added_at);
