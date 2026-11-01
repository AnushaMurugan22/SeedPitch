
import csv
import hashlib
import os
import sys
import time
from datetime import date
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

RAW = "data/raw"
MANIFEST = "data/manifest.csv"

HEADERS = {
    "User-Agent": "ExamateStudentProject/1.0 (learning project; contact: your-email@example.com)"
}

DELAY = 2
robots = {}


def allowed(url):
    origin = "{0.scheme}://{0.netloc}".format(urlparse(url))

    if origin not in robots:
        rp = RobotFileParser(origin + "/robots.txt")

        try:
            rp.read()
        except Exception:
            rp = None

        robots[origin] = rp

    rp = robots[origin]

    return rp is None or rp.can_fetch(HEADERS["User-Agent"], url)


def name_for(url):
    name = os.path.basename(urlparse(url).path) or "index.html"
    return name.replace(" ", "_")


def main(list_file):
    os.makedirs(RAW, exist_ok=True)

    new_manifest = not os.path.exists(MANIFEST)

    with open(MANIFEST, "a", newline="", encoding="utf-8") as mf:
        log = csv.writer(mf)

        if new_manifest:
            log.writerow(
                ["file", "source_url", "downloaded_on", "bytes", "sha256"]
            )

        with open(list_file, encoding="utf-8") as fh:
            urls = [u.strip() for u in fh]

        for url in urls:
            if not url or url.startswith("#"):
                continue

            path = os.path.join(RAW, name_for(url))

            if os.path.exists(path):
                print("skip (already have)", path)
                continue

            if not allowed(url):
                print("BLOCKED by robots.txt, not downloading:", url)
                continue

            try:
                r = requests.get(url, headers=HEADERS, timeout=30)

                if r.status_code != 200:
                    print("failed", r.status_code, url)
                    continue

                with open(path, "wb") as f:
                    f.write(r.content)

                digest = hashlib.sha256(r.content).hexdigest()[:16]

                log.writerow(
                    [
                        path,
                        url,
                        date.today().isoformat(),
                        len(r.content),
                        digest,
                    ]
                )

                print("saved", path, len(r.content), "bytes")

                time.sleep(DELAY)

            except requests.RequestException as exc:
                print("download error:", url, exc)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/download.py urls.txt")
        sys.exit(1)

    main(sys.argv[1])
