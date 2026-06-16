SELECT name
FROM sqlite_master
WHERE type = 'table' AND name IN ('app_log', 'stat_event')
ORDER BY name;
