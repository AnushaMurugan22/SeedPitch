
import csv
import os

manifest = "data/manifest.csv"
readme = "README.md"

with open(manifest, encoding="utf-8") as file:
    rows = list(csv.DictReader(file))

print("Downloaded PDFs:", len(rows))

for row in rows:
    print(
        row["file"],
        row["pages"],
        "pages"
    )
