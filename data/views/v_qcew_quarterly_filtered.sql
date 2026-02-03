CREATE OR REPLACE VIEW v_qcew_quarterly_filtered AS
SELECT
  cbsa_code,
  year,
  quarter,
  area_fips,
  own_code,
  industry_code,
  agglvl_code,
  size_code,
  disclosure_code,
  qtrly_estabs,
  month1_emplvl,
  month2_emplvl,
  month3_emplvl,
  total_qtrly_wages,
  taxable_qtrly_wages,
  qtrly_contributions,
  avg_wkly_wage
FROM v_qcew_quarterly_lake
WHERE 1=1
  AND agglvl_code = 40
  AND industry_code = '10'
  AND own_code = 0
  AND size_code = 0;