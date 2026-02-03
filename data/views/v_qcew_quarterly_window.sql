CREATE OR REPLACE VIEW v_qcew_quarterly_window AS
SELECT *
FROM v_qcew_quarterly_filtered
WHERE year BETWEEN 2014 AND 2023;