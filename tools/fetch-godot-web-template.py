#!/usr/bin/env python3
"""Fetch the official no-threads release template without the 1 GB full download."""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zipfile


def read_range(url, byte_range):
    with tempfile.TemporaryDirectory() as directory:
        headers, data = Path(directory) / "headers", Path(directory) / "data"
        subprocess.run(
            ["curl", "-fsSL", "--retry", "2", "--max-time", "120",
             "-r", byte_range, "-D", str(headers), "-o", str(data), url],
            check=True,
        )
        matches = re.findall(r"(?im)^content-range: bytes (\d+)-(\d+)/(\d+)", headers.read_text())
        if not matches:
            raise ValueError("The official template mirror did not honor the byte range")
        start, end, total = map(int, matches[-1])
        contents = data.read_bytes()
        if len(contents) != end - start + 1:
            raise ValueError("Incomplete template archive response")
        return start, total, contents


def fetch(version, output):
    url = f"https://downloads.godotengine.org/?version={version}&flavor=stable&slug=export_templates.tpz&platform=templates"
    beginning, size, tail = read_range(url, "-131072")
    with tempfile.TemporaryFile() as archive:
        # Only the end of central directory and one member are populated.
        archive.truncate(size)
        archive.seek(beginning)
        archive.write(tail)
        with zipfile.ZipFile(archive) as bundle:
            info = bundle.getinfo("templates/web_nothreads_release.zip")
            end = info.header_offset + 30 + len(info.filename) + 1024 + info.compress_size - 1
            start, expected_size, segment = read_range(url, f"{info.header_offset}-{end}")
            if start != info.header_offset or expected_size != size:
                raise ValueError("Template archive changed while downloading")
            archive.seek(start)
            archive.write(segment)
            # zipfile verifies the official central directory's CRC.
            template = bundle.read(info)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(template)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fetch(args.version, args.output)
