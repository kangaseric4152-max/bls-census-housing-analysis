SELECT
  code AS cbsa_code,
  y.year,
  q.quarter
FROM dim_metro_full
CROSS JOIN range(2019, 2024) AS y(year)
CROSS JOIN (VALUES (1),(2),(3),(4)) AS q(quarter)
WHERE title = 'OH';