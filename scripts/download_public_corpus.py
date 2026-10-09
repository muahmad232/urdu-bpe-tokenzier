"""
Downloader and Extractor for Public Urdu Corpora
Handles:
1. Makhzan Classical Urdu Literature (books, essays, poetry) from GitHub (6,300+ XML files).
2. CC-100 Urdu Web Corpus (diverse web crawl) streamed via LZMA.
"""

import os
import io
import sys
import zipfile
import urllib.request
import lzma
import argparse
import xml.etree.ElementTree as ET
from tqdm import tqdm

MAKHZAN_ZIP_URL = "https://github.com/zeerakahmed/makhzan/archive/refs/heads/master.zip"
CC100_UR_URL = "http://data.statmt.org/cc-100/ur.txt.xz"

PUBLIC_DIR = os.path.join("corpus", "raw", "public")
MAKHZAN_DIR = os.path.join(PUBLIC_DIR, "makhzan")
CC100_DIR = os.path.join(PUBLIC_DIR, "cc100")


def extract_makhzan_literature():
    """Download and extract clean text documents from Makhzan XML files."""
    os.makedirs(MAKHZAN_DIR, exist_ok=True)
    out_file = os.path.join(MAKHZAN_DIR, "makhzan_literature.txt")

    if os.path.exists(out_file) and os.path.getsize(out_file) > 10 * 1024 * 1024:
        size_mb = os.path.getsize(out_file) / (1024 * 1024)
        print(f"[Makhzan] Found existing extracted corpus: {size_mb:.2f} MB. Skipping.")
        return size_mb

    print(f"[Makhzan] Downloading archive from {MAKHZAN_ZIP_URL}...")
    req = urllib.request.Request(MAKHZAN_ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()

    print(f"[Makhzan] Downloaded {len(content) / (1024*1024):.2f} MB zip. Parsing XML files...")
    doc_count = 0
    total_bytes = 0

    with zipfile.ZipFile(io.BytesIO(content)) as z, open(out_file, "w", encoding="utf-8") as f_out:
        xml_files = [name for name in z.namelist() if name.endswith(".xml") and "text/" in name]
        for name in tqdm(xml_files, desc="Makhzan XMLs"):
            try:
                xml_data = z.read(name).decode("utf-8", errors="replace")
                root = ET.fromstring(xml_data)

                # Extract title
                title_el = root.find(".//title")
                title = title_el.text.strip() if title_el is not None and title_el.text else ""

                # Extract all text from body
                body_el = root.find(".//body")
                if body_el is not None:
                    paragraphs = []
                    for elem in body_el.iter():
                        if elem.text and elem.text.strip():
                            txt = elem.text.strip()
                            if len(txt) > 5:
                                paragraphs.append(txt)
                    body_text = "\n".join(paragraphs)
                else:
                    # Fallback to all text in root
                    body_text = "".join(root.itertext()).strip()

                if len(body_text) < 50:
                    continue

                doc = ""
                if title:
                    doc += title + "\n\n"
                doc += body_text + "\n\n<|endoftext|>\n\n"

                f_out.write(doc)
                total_bytes += len(doc.encode("utf-8"))
                doc_count += 1
            except Exception:
                continue

    size_mb = total_bytes / (1024 * 1024)
    print(f"[Makhzan] Extracted {doc_count} documents ({size_mb:.2f} MB) to {out_file}")
    return size_mb


def stream_cc100_corpus(target_mb=500.0):
    """
    Stream Urdu documents from CC-100 xz archive until target_mb is reached.
    Avoids saving the full 926 MB archive by streaming and decompressing in memory.
    """
    os.makedirs(CC100_DIR, exist_ok=True)
    out_file = os.path.join(CC100_DIR, "cc100_urdu.txt")

    target_bytes = int(target_mb * 1024 * 1024)
    existing_bytes = 0
    if os.path.exists(out_file):
        existing_bytes = os.path.getsize(out_file)
        print(f"[CC-100] Existing corpus detected: {existing_bytes / (1024*1024):.2f} MB")
        if existing_bytes >= target_bytes:
            print(f"[CC-100] Target {target_mb} MB already met! Skipping.")
            return existing_bytes / (1024 * 1024)

    print(f"[CC-100] Streaming and decompressing from {CC100_UR_URL} to reach {target_mb} MB...")
    req = urllib.request.Request(CC100_UR_URL, headers={"User-Agent": "Mozilla/5.0"})

    pbar = tqdm(total=target_bytes, initial=existing_bytes, unit="B", unit_scale=True, desc="CC-100 Urdu")
    written_bytes = existing_bytes

    with urllib.request.urlopen(req, timeout=30) as resp:
        with lzma.open(resp, mode="rt", encoding="utf-8", errors="replace") as xz_stream:
            with open(out_file, "a", encoding="utf-8") as f_out:
                current_doc_lines = []
                for line in xz_stream:
                    # In CC-100, documents or paragraphs are separated by newlines
                    stripped = line.strip()
                    if not stripped:
                        if current_doc_lines:
                            doc_str = "\n".join(current_doc_lines) + "\n\n<|endoftext|>\n\n"
                            f_out.write(doc_str)
                            b = len(doc_str.encode("utf-8"))
                            written_bytes += b
                            pbar.update(b)
                            current_doc_lines = []
                            if written_bytes >= target_bytes:
                                break
                    else:
                        current_doc_lines.append(stripped)

                if current_doc_lines and written_bytes < target_bytes:
                    doc_str = "\n".join(current_doc_lines) + "\n\n<|endoftext|>\n\n"
                    f_out.write(doc_str)
                    b = len(doc_str.encode("utf-8"))
                    written_bytes += b
                    pbar.update(b)

    pbar.close()
    final_mb = written_bytes / (1024 * 1024)
    print(f"[CC-100] Successfully wrote {final_mb:.2f} MB to {out_file}")
    return final_mb


def main():
    parser = argparse.ArgumentParser(description="Download public Urdu corpora (Makhzan & CC-100).")
    parser.add_argument("--skip-makhzan", action="store_true", help="Skip Makhzan download")
    parser.add_argument("--cc100-mb", type=float, default=500.0, help="Target MB to stream from CC-100")
    args = parser.parse_args()

    print("=" * 60)
    print("        PUBLIC URDU CORPUS DOWNLOADER")
    print("=" * 60)

    if not args.skip_makhzan:
        print("\n>>> [1/2] Processing Makhzan Literature...")
        extract_makhzan_literature()

    print(f"\n>>> [2/2] Streaming CC-100 Urdu ({args.cc100_mb} MB)...")
    stream_cc100_corpus(target_mb=args.cc100_mb)

    print("\n" + "=" * 60)
    print("PUBLIC CORPUS DOWNLOAD FINISHED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
