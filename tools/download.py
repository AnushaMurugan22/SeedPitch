
import csv
import hashlib
import os
import sys
import time

from datetime import date
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from pypdf import PdfReader


# ==============================
# SeedPitch Dataset Downloader
# ==============================

RAW = "data/raw"

MANIFEST = "data/manifest.csv"

README = "README.md"

USER_AGENT = "SeedPitchStudentProject/1.0"

HEADERS = {
    "User-Agent": USER_AGENT
}

DELAY = 2

robots_cache = {}

session = requests.Session()

session.headers.update(HEADERS)


# ==============================
# Check robots.txt
# ==============================

def allowed(url):

    parsed = urlparse(url)

    root = f"{parsed.scheme}://{parsed.netloc}"

    if root not in robots_cache:

        parser = RobotFileParser()

        parser.set_url(root + "/robots.txt")

        try:

            parser.read()

            robots_cache[root] = parser

        except Exception:

            print("Cannot check robots.txt:", root)

            return False

    return robots_cache[root].can_fetch(
        USER_AGENT,
        url
    )


# ==============================
# Generate filename
# ==============================


from urllib.parse import urlparse, unquote
import hashlib
import os

def name_for(url):

    parsed = urlparse(url)

    filename = os.path.basename(
        unquote(parsed.path)
    )

    if not filename:
        filename = "document.pdf"

    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    url_hash = hashlib.sha256(
        url.encode()
    ).hexdigest()[:10]

    name, extension = os.path.splitext(filename)

    return f"{name}_{url_hash}{extension}"


# ==============================
# Read existing manifest
# ==============================

def read_manifest():

    records = {}

    if not os.path.exists(MANIFEST):

        return records

    with open(
        MANIFEST,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            records[row["source_url"]] = row

    return records


# ==============================
# Download PDF
# ==============================

def download_pdf(url, records):

    print("\nChecking:", url)

    if not allowed(url):

        print("BLOCKED by robots.txt:", url)

        return

    try:

        response = session.get(
            url,
            timeout=60
        )

        response.raise_for_status()

    except requests.RequestException as error:

        print("Download failed:", error)

        return

    content_type = response.headers.get(
        "Content-Type",
        ""
    )

    # Accept PDF content only

    if "pdf" not in content_type.lower():

        print("Not a PDF document:", content_type)

        return

    content = response.content

    if not content:

        print("Empty document")

        return

    filename = name_for(url)

    filepath = os.path.join(
        RAW,
        filename
    )

    # Skip existing downloaded document

    if os.path.exists(filepath):

        print("Already downloaded:", filepath)

        return

    # Save PDF

    with open(filepath, "wb") as file:

        file.write(content)

    # Calculate page count

    try:

        reader = PdfReader(filepath)

        pages = len(reader.pages)

    except Exception as error:

        print("PDF reading error:", error)

        os.remove(filepath)

        return

    # Calculate checksum

    digest = hashlib.sha256(
        content
    ).hexdigest()

    # Save metadata

    records[url] = {

        "file": filepath,

        "source_url": url,

        "pages": pages,

        "license": "Verify official source terms",

        "downloaded_on": date.today().isoformat(),

        "bytes": len(content),

        "sha256": digest

    }

    print("\nSUCCESS")

    print("File:", filepath)

    print("Total pages:", pages)

    print("Size:", len(content), "bytes")

    time.sleep(DELAY)


# ==============================
# Save manifest CSV
# ==============================

def save_manifest(records):

    os.makedirs(
        os.path.dirname(MANIFEST),
        exist_ok=True
    )

    fields = [
        "file",
        "source_url",
        "pages",
        "license",
        "downloaded_on",
        "bytes",
        "sha256"
    ]

    with open(
        MANIFEST,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        for row in records.values():

            writer.writerow(row)

    print("\nManifest updated:", MANIFEST)


# ==============================
# Generate README dataset table
# ==============================

def update_readme(records):

    if not os.path.exists(README):

        print("README.md not found")

        return

    with open(
        README,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read()

    start = "<!-- DATASET_START -->"

    end = "<!-- DATASET_END -->"

    if start not in content or end not in content:

        print("Dataset markers missing in README")

        return

    rows = []

    rows.append(
        "| File | Source URL | Pages | Licence / terms | Downloaded on |"
    )

    rows.append(
        "|---|---|---:|---|---|"
    )

    for row in records.values():

        filename = os.path.basename(
            row["file"]
        )

        source = row["source_url"]

        pages = row["pages"]

        license_name = row["license"]

        downloaded = row["downloaded_on"]

        rows.append(
            f"| {filename} | "
            f"[Source]({source}) | "
            f"{pages} | "
            f"{license_name} | "
            f"{downloaded} |"
        )

    table = "\n".join(rows)

    before = content.split(start)[0]

    after = content.split(end)[1]

    updated = (
        before
        + start
        + "\n\n"
        + table
        + "\n\n"
        + end
        + after
    )

    with open(
        README,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(updated)

    print("README dataset table updated")


# ==============================
# Main
# ==============================

def main(list_file):

    os.makedirs(
        RAW,
        exist_ok=True
    )

    records = read_manifest()

    with open(
        list_file,
        "r",
        encoding="utf-8"
    ) as file:

        urls = [
            line.strip()
            for line in file
        ]

    print("SeedPitch Dataset Downloader")

    print("Total URLs:", len(urls))

    for url in urls:

        if not url or url.startswith("#"):

            continue

        download_pdf(
            url,
            records
        )

    save_manifest(records)

    update_readme(records)

    print("\nDataset process completed")

    print("PDF folder:", RAW)

    print("Manifest:", MANIFEST)

    print("README:", README)


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print("Usage: python tools/download.py urls.txt")

        sys.exit(1)

    main(sys.argv[1])
