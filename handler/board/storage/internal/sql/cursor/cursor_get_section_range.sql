SELECT x, y, data
FROM cursor_section
WHERE (x BETWEEN ? AND ?) and (y BETWEEN ? AND ?)
ORDER BY y ASC, x ASC;
