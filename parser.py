import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import time
from pathlib import Path


XML_FILE = "usa_00008.xml"
DAT_FILE = "usa_00008.dat"
OUTPUT_FILE = "usa_00008_decoded.csv"

# Increase if you have plenty of RAM.
# 250k is reasonable for ~16 GB RAM.
CHUNK_SIZE = 250_000


# =========================================================
# 1. Parse IPUMS DDI XML
# =========================================================

print("Reading XML metadata...")

tree = ET.parse(XML_FILE)
root = tree.getroot()

ns = {"ddi": "ddi:codebook:2_5"}

variables = []

for var in root.findall(".//ddi:dataDscr/ddi:var", ns):

    name = var.get("name")

    loc = var.find("ddi:location", ns)

    start = int(loc.get("StartPos")) - 1
    end = int(loc.get("EndPos"))

    decimals = int(var.get("dcml", "0"))

    labels = {}

    for cat in var.findall("ddi:catgry", ns):

        value_node = cat.find("ddi:catValu", ns)
        label_node = cat.find("ddi:labl", ns)

        if value_node is None or value_node.text is None:
            continue

        value = value_node.text.strip()

        label = (
            label_node.text.strip()
            if label_node is not None and label_node.text
            else ""
        )

        labels[value] = label

    variables.append({
        "name": name,
        "start": start,
        "end": end,
        "width": end - start,
        "decimals": decimals,
        "labels": labels
    })


print(f"Found {len(variables)} IPUMS variables.")


# =========================================================
# 2. Decode one chunk
# =========================================================

def decode_chunk(lines):

    data = {}

    for var in variables:

        name = var["name"]
        start = var["start"]
        end = var["end"]

        values = [
            line[start:end].strip()
            for line in lines
        ]

        # Preserve raw codes initially
        data[name] = values

        # Add readable labels
        if var["labels"]:

            mapping = var["labels"]

            data[name + "_LABEL"] = [
                mapping.get(v, "")
                for v in values
            ]

    df = pd.DataFrame(data)

    # -----------------------------------------------------
    # Numeric conversion
    # -----------------------------------------------------

    for var in variables:

        name = var["name"]

        # Categorical codes remain as strings.
        # Important because codes such as 01 must retain
        # their leading zeros.
        if var["labels"]:
            continue

        df[name] = pd.to_numeric(
            df[name],
            errors="coerce"
        )

        # IPUMS implied decimals
        if var["decimals"] > 0:
            df[name] /= 10 ** var["decimals"]

    return df


# =========================================================
# 3. Convert DAT -> CSV incrementally
# =========================================================

start_time = time.time()

rows_processed = 0
first_chunk = True

output_path = Path(OUTPUT_FILE)

if output_path.exists():
    output_path.unlink()


with open(
    DAT_FILE,
    "r",
    encoding="ISO-8859-1",
    buffering=1024 * 1024 * 16
) as f:

    batch = []

    for line in f:

        batch.append(line.rstrip("\r\n"))

        if len(batch) == CHUNK_SIZE:

            df = decode_chunk(batch)

            df.to_csv(
                OUTPUT_FILE,
                mode="w" if first_chunk else "a",
                header=first_chunk,
                index=False
            )

            rows_processed += len(batch)

            elapsed = time.time() - start_time

            speed = (
                rows_processed / elapsed
                if elapsed > 0
                else 0
            )

            print(
                f"{rows_processed:,} rows processed | "
                f"{speed:,.0f} rows/sec | "
                f"{elapsed / 60:.1f} min elapsed"
            )

            first_chunk = False

            del df
            batch.clear()


# =========================================================
# 4. Final partial chunk
# =========================================================

if batch:

    df = decode_chunk(batch)

    df.to_csv(
        OUTPUT_FILE,
        mode="w" if first_chunk else "a",
        header=first_chunk,
        index=False
    )

    rows_processed += len(batch)

    del df


# =========================================================
# 5. Summary
# =========================================================

elapsed = time.time() - start_time

size_gb = output_path.stat().st_size / (1024 ** 3)

print()
print("========================================")
print("Conversion complete")
print("========================================")
print(f"Rows:        {rows_processed:,}")
print(f"Variables:   {len(variables)}")
print(f"Output:      {OUTPUT_FILE}")
print(f"CSV size:    {size_gb:.2f} GB")
print(f"Runtime:     {elapsed / 60:.2f} minutes")
print(
    f"Average:     "
    f"{rows_processed / elapsed:,.0f} rows/sec"
)