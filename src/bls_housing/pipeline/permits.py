#• build_permits_month(...)
#• build_permits_qtr(...) (reads stage parquet, writes stage parquet)


# Load cleaned CBSA CSV from cache instead of manual XLS parsing
from bls_housing.census_cache import load_cbsa_df
from bls_housing.helper import QUARTER_TO_MONTH
from typing import cast
from typing import List
import pandas as pd
from collections import defaultdict

def build_annual_permits(metros, 
                         years: List[int], 
                         quarters = [1, 2, 3, 4]) -> tuple[pd.DataFrame, pd.DataFrame]:
    total_permits = defaultdict(int)
    data_list = []

    for m in metros.itertuples(index=False):
        for year in years:
            total_permits[year] = 0
            for qtr in quarters:
                for mon in QUARTER_TO_MONTH[str(qtr)]:  # months in quarter
                    df = load_cbsa_df(str(year), str(mon))
                    df_current_area = df[df['CBSA'] == m.Code]  # filter for CBSA
                
                # get Total_Permits for CBSA
                    total_permits_current_month = df_current_area['Total'].iloc[0]

                    data_list.append({
                    "Area": m.Area,
                    "Code": cast(int, m.Code),
                    "Year": int(year),
                    "Quarter": qtr,
                    "Month": int(mon),
                    "Total_Permits": total_permits_current_month
                })
                
    permits_df = pd.DataFrame(data_list)
    
    # Calculate annual total permits and percentage change
    annual_permits = permits_df.groupby(["Area", "Code", "Year"])["Total_Permits"].sum().reset_index()
    annual_permits["Change_Permit"] = annual_permits.groupby("Code")["Total_Permits"].pct_change() * 100
    return (permits_df, annual_permits)
