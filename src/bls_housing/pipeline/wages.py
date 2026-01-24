#• build_wages_qtr(codes: list[int], years: list[int], quarters: list[int], out_dir: Path) -> None
#• writes parquet partitioned 

from bls_housing.qcew_cache import load_area_df #, get_cached_path , fetch_area_csv
from bls_housing.helper import CPI_U #, QUARTER_TO_MONTH
from typing import cast
from typing import List
from typing import Union
import numpy as np
import pandas as pd
# import numpy as np
# import duckdb

#years = [str(y) for y in range(2014, 2025)] # include dates from 2014-2024
# Load DataFrame (uses cache if available)
# get total quarterly wages for MSA for each year and store in total_wages dict

# Assume annual_wages_df has columns: ['Year', 'Total_Wages']


# convert 5 digit codes such as 12340 to QCEW format C1234
def _to_qcew(cbsa_code: Union[int, np.integer]) -> str:
    return f"C{cbsa_code // 10:04d}"


def adjust_inflation(row):
    year_str = str(row['Year'])
    nominal_wage = row['Total_Wages']
    
    if year_str not in CPI_U:
        return nominal_wage # Fallback
        
    cpi_current = CPI_U[year_str]
    cpi_target = CPI_U["2024"] # We normalize everything to 2024 dollars
    
    # The Formula
    real_wage = nominal_wage * (cpi_target / cpi_current)
    return real_wage


def build_annual_wages(metros: pd.DataFrame, 
                    years: List[int], 
                    quarters=[1,2,3,4]) ->  tuple[pd.DataFrame, pd.DataFrame]:
    data_list = []
    #metros = list_metros(con, area_codes)
    for m in metros.itertuples(index=False):
        for year in years:
            for qtr in quarters:
                qcew_code = _to_qcew(cast(int, m.Code))
                df = load_area_df(qcew_code, str(year), str(qtr))
                
                msa = df[df.get('agglvl_code') == 40]
                total_wages_current_qtr = msa['total_qtrly_wages'].iloc[0]
                data_list.append({
                    "Area": m.Area,
                    "Code": cast(int, m.Code),
                    "Year": year,
                    "Quarter": qtr,
                    "Total_Wages": total_wages_current_qtr
                })
            

    # print(data_list)
    wages_df = pd.DataFrame(data_list)

    # Calculate annual total wages and percentage change
    annual_wages_df = wages_df.groupby(["Area", "Code", "Year"])["Total_Wages"].sum().reset_index()

    # Apply the adjustment
    annual_wages_df['Real_Total_Wages'] = annual_wages_df.apply(adjust_inflation, axis=1)

    # now calculate the growth rate using the adjusted wages
    annual_wages_df['Change_Real_Wage'] = annual_wages_df.groupby("Area")['Real_Total_Wages'].pct_change() * 100
    #print(annual_wages_df.head(15))
    return (wages_df, annual_wages_df)