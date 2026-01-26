import pandas as pd
import logging

logger = logging.getLogger(__name__)

def build_annual_metrics(annual_wages_df, annual_permits) -> pd.DataFrame:
    """Build derived annual metrics, and Zoning pressure calculation, 
    adjusting for inflation."""

    final_df = pd.merge(
        annual_wages_df,
        annual_permits,
        on=["Area", "Code", "Year"],
        suffixes=('_wage', '_permit')
    )

    final_df['Wage_Index'] = 1 + (final_df['Change_Real_Wage'] / 100) # adjusted for inflation
    final_df['Permit_Index'] = 1 + (final_df['Change_Permit'] / 100)
    final_df['Zoning_Pressure'] = final_df['Wage_Index'] / final_df['Permit_Index']
    return final_df


def build_cumulative_metrics(annual_wages_df: pd.DataFrame,
                             annual_permits: pd.DataFrame,
                             base_year: int) -> pd.DataFrame:
    """Build derived cumulative metrics, adjusting for inflation.
    Note: use base year as start year + 1 for cumulative indices."""
    # 1) merge raw totals
    cumulative_df = (
        annual_wages_df[["Area", "Code", "Year", "Real_Total_Wages"]]
        .merge(
            annual_permits[["Code", "Year", "Total_Permits"]],
            on=["Code", "Year"],
            how="inner",
        )
    )
    logger.debug(f"Cumulative DF head:\n{cumulative_df.head()}")
    base_year_check = (
        cumulative_df[cumulative_df["Year"] == base_year]
        .groupby("Code").size()
    )

    logger.debug(f"Base year check: {base_year_check} ")

    # keep types sane (Year as int is cleaner than string comparisons)
    cumulative_df["Year"] = cumulative_df["Year"].astype(int)

    # 2) filter years
    cumulative_df = cumulative_df[cumulative_df["Year"] >= base_year].copy()

    # 3) attach base-year totals per Code
    base = (
        cumulative_df[cumulative_df["Year"] == base_year][["Code", "Real_Total_Wages", "Total_Permits"]]
        .rename(columns={"Real_Total_Wages": "Base_Wage", "Total_Permits": "Base_Permits"})
    )

    dupes = base["Code"].duplicated().sum()
    assert dupes == 0, f"Base year has duplicate codes: {dupes}"
    cumulative_df = cumulative_df.merge(base, on="Code", how="left")

    # 4) compute indices
    cumulative_df["Cumul_Wage_Index"] = cumulative_df["Real_Total_Wages"] / cumulative_df["Base_Wage"]
    cumulative_df["Cumul_Permit_Index"] = cumulative_df["Total_Permits"] / cumulative_df["Base_Permits"]

    # 5) structural gap (guard divide-by-zero / missing base)
    cumulative_df["Structural_Gap"] = cumulative_df["Cumul_Wage_Index"] / cumulative_df["Cumul_Permit_Index"]

    return cumulative_df