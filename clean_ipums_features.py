import pandas as pd
import time
from pathlib import Path

INPUT_FILE = "usa_00008_decoded.csv"
OUTPUT_FILE = "usa_00008_cleaned.csv"
CHUNK_SIZE = 500_000

print(f"Loading: {INPUT_FILE}")
start = time.time()

all_columns = pd.read_csv(INPUT_FILE, nrows=0).columns.tolist()

drop_columns = [

    # -----------------------------------------
    # Technical fields not used as predictors
    # -----------------------------------------
    "YEAR_LABEL",
    "SAMPLE",
    "SAMPLE_LABEL",
    "SERIAL",
    "CBSERIAL",
    "HHWT",
    "CLUSTER",
    "STRATA",
    "GQ",
    "GQ_LABEL",
    "PERNUM",

    # -----------------------------------------
    # Keep LABEL for categorical variables
    # -----------------------------------------
    "HHTYPE",
    "REGION",
    "STATEFIP",
    "METRO",
    "OWNERSHP",
    "VEHICLES",
    "COUPLETYPE",

    "SEX",
    "MARST",
    "MARRNO",
    "DIVINYR",
    "RACE",
    "HISPAN",
    "EDUC",
    "EMPSTAT",
    "LABFORCE",
    "CLASSWKR",
    "WKSWORK2",
    "MIGRATE1",

    # -----------------------------------------
    # Drop detailed versions completely
    # -----------------------------------------
    "OWNERSHPD",
    "OWNERSHPD_LABEL",

    "RACED",
    "RACED_LABEL",

    "HISPAND",
    "HISPAND_LABEL",

    "EDUCD",
    "EDUCD_LABEL",

    "EMPSTATD",
    "EMPSTATD_LABEL",

    "CLASSWKRD",
    "CLASSWKRD_LABEL",

    "MIGRATE1D",
    "MIGRATE1D_LABEL",

    # -----------------------------------------
    # Numeric variables: keep number,
    # drop redundant text label
    # -----------------------------------------
    "AGE_LABEL",
    "FAMSIZE_LABEL",
    "NCHILD_LABEL",
    "UHRSWORK_LABEL",
    "POVERTY_LABEL",
    "RENT_LABEL",
    "VALUEH_LABEL",
    "YRMARR_LABEL",
]

# Keep YEAR: this extract pools the 2008, 2016 and 2024 ACS samples.
# Keep PERWT for survey weighting.
# Keep numeric:
# YEAR
# AGE
# FAMSIZE
# NCHILD
# UHRSWORK
# YRMARR
# RENT
# VALUEH
# HHINCOME
# INCTOT
# FTOTINC
# INCWAGE
# INCEARN
# POVERTY
# PERWT

existing_drop_columns = [
    col for col in drop_columns
    if col in all_columns
]
keep_columns = [
    col for col in all_columns
    if col not in existing_drop_columns
]

print(f"Dropping {len(existing_drop_columns)} columns...")

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
