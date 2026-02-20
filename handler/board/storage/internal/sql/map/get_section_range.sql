SELECT x, y, data, flag
FROM section
WHERE (x BETWEEN ? AND ?) and (y BETWEEN ? AND ?)
ORDER BY y ASC, x ASC;