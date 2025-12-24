import sys
from notebook_proj.data_utils import load_records, compute_average

def main() -> None:
    """Run the template."""
    file_path = "data/sample.json"
    try:
        records = load_records(file_path)
        avg = compute_average(records)
        print(f"✅ Loaded {len(records)} records from {file_path}")
        print(f"📊 Average value: {avg:.2f}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()


