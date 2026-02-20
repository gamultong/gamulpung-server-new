SELECT x, y, data, flag
FROM cursor_section
WHERE (x BETWEEN ? AND ?) and (y BETWEEN ? AND ?)
ORDER BY y ASC, x ASC;
