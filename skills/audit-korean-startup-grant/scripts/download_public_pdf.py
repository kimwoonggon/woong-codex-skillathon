#!/usr/bin/env python3
"""Download a public PDF notice for reproducible PDF-input validation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def download(url: str, out_path: Path, timeout: int) -> None:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 audit-korean-startup-grant/1.0",
            "Accept": "application/pdf,*/*",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        content = response.read()
    if not content.startswith(b"%PDF"):
        raise ValueError("downloaded file does not start with a PDF header")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Public PDF URL")
    parser.add_argument("--out", required=True, help="Local output PDF path")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        download(args.url, Path(args.out), args.timeout)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        print(f"PDF download failed: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
