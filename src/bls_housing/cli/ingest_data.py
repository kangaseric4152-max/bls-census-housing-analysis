# src/bls_housing/cli/ingest_data.py

from __future__ import annotations

import argparse
import pandas as pd

from bls_housing.pipeline.ensure_lake import ensure_qcew_lake, ensure_permits_lake

def _parse_int_range(s: str) -> list[int]:
    # "2019-2023" -> [2019..2023], "2020" -> [2020]
    if "-" in s:
        a, b = s.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(s)]

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", choices=["qcew", "permits"], required=True)

    p.add_argument("--years", required=True, help="e.g. 2019-2023 or 2022")
    p.add_argument("--quarters", default="1-4", help="qcew only: e.g. 1-4 or 1,3")
    p.add_argument("--months", default="1-12", help="permits only: e.g. 1-12 or 1,2,3")

    p.add_argument("--cbsa", default="", help="qcew only: comma-separated CBSA codes like 17460,18140")
    p.add_argument("--force-download", action="store_true")
    p.add_argument("--force-parquet", action="store_true")

    args = p.parse_args()

    years = _parse_int_range(args.years)

    if args.dataset == "qcew":
        if not args.cbsa.strip():
            raise SystemExit("--cbsa is required for dataset=qcew (e.g. --cbsa 17460,18140)")
        cbsa_codes = [int(x.strip()) for x in args.cbsa.split(",") if x.strip()]

        # quarters: allow "1-4" or "1,3"
        if "-" in args.quarters:
            qa, qb = args.quarters.split("-", 1)
            quarters = list(range(int(qa), int(qb) + 1))
        else:
            quarters = [int(x.strip()) for x in args.quarters.split(",") if x.strip()]

        metros = pd.DataFrame({"Code": cbsa_codes})
        st = ensure_qcew_lake(
            metros,
            years,
            quarters,
            force_download=args.force_download,
            force_parquet=args.force_parquet,
        )

    else:
        # months: allow "1-12" or "1,2,3"
        if "-" in args.months:
            ma, mb = args.months.split("-", 1)
            months = list(range(int(ma), int(mb) + 1))
        else:
            months = [int(x.strip()) for x in args.months.split(",") if x.strip()]

        st = ensure_permits_lake(
            years,
            months,
            force_download=args.force_download,
            force_parquet=args.force_parquet,
        )

    print(
        f"[ingest-data] requested={st.requested} missing={st.missing} "
        f"fetched={st.fetched} parquet_written={st.parquet_written} skipped={st.parquet_skipped}"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())