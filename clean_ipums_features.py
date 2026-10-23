import pandas as pd
import time
from pathlib import Path

INPUT_FILE = "usa_00008_decoded.csv"
OUTPUT_FILE = "usa_00008_cleaned.csv"
CHUNK_SIZE = 500_000

print(f"Loading: {INPUT_FILE}")
start = time.time()

all_columns = pd.read_csv(INPUT_FILE, nrows=0).columns.tolist()

# Numeric variables that IPUMS also labels (e.g. top-codes, N/A).
# These are real numbers, not categories, so the number is kept.
numeric_variables = {
    "YEAR",
    "AGE",
    "FAMSIZE",
    "NCHILD",
    "UHRSWORK",
    "YRMARR",
    "RENT",
    "VALUEH",
    "POVERTY",
}

# For categorical features, drop the numeric code and keep the
# readable label, e.g. DIVINYR (dropped) / DIVINYR_LABEL (kept).
drop_columns = [
    col for col in all_columns
    if f"{col}_LABEL" in all_columns
    and col not in numeric_variables
]
keep_columns = [
    col for col in all_columns
    if col not in drop_columns
]

print(f"Dropping {len(drop_columns)} columns...")

# File is several GB, so read only the kept columns and write in chunks.
# dtype=str preserves the original formatting (e.g. leading zeros).
total_rows = 0
reader = pd.read_csv(
    INPUT_FILE,
    usecols=keep_columns,
    dtype=str,
    keep_default_na=False,
    chunksize=CHUNK_SIZE,
)

for i, chunk in enumerate(reader):
    chunk = chunk[keep_columns]
    chunk.to_csv(
        OUTPUT_FILE,
        index=False,
        mode="w" if i == 0 else "a",
        header=(i == 0),
    )
    total_rows += len(chunk)
    print(f"  processed {total_rows:,} rows...")

elapsed = time.time() - start
output_path = Path(OUTPUT_FILE)

print()
print("========================================")
print("Cleaning complete")
print("========================================")
print(f"Rows:              {total_rows:,}")
print(f"Columns remaining: {len(keep_columns):,}")
print(f"Runtime:           {elapsed:.1f} seconds")

if output_path.exists():
    size_mb = output_path.stat().st_size / (1024 ** 2)
    print(f"Output size:       {size_mb:.1f} MB")

print()
print("Remaining columns:")

for col in keep_columns:
    print(f"  - {col}")
