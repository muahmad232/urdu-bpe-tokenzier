"""
Corpus Cleaning Pipeline (scripts/clean_corpus.py)
Implements Section 8 cleaning steps:
1. Load raw documents from corpus/raw/scraped/ and corpus/raw/public/.
2. Apply Unicode normalization via normalize.py.
3. Language filtering: verify Urdu content (retaining natural English code-mixing).
4. Deduplication: exact document deduplication via SHA-256 hash set.
5. Save cleaned documents into corpus/cleaned/ per source.
"""

import os
import sys
import glob
import hashlib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tqdm import tqdm
from normalize import normalize
from scraping.utils import is_predominantly_urdu

RAW_DIR = os.path.join(PROJECT_ROOT, "corpus", "raw")
CLEANED_DIR = os.path.join(PROJECT_ROOT, "corpus", "cleaned")


def clean_source_file(input_path: str, output_path: str, seen_hashes: set):
    """Clean a single raw text corpus file and append unique, normalized docs."""
    print(f"\n[Cleaning] Processing {input_path} -> {output_path}...")
    if not os.path.exists(input_path):
        print(f"  [Warning] File {input_path} not found. Skipping.")
        return 0, 0, 0

    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Split into individual documents via <|endoftext|>
    raw_docs = content.split("<|endoftext|>")
    print(f"  Loaded {len(raw_docs):,} raw document chunks.")

    cleaned_count = 0
    duplicate_count = 0
    filtered_count = 0
    total_written_bytes = 0

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f_out:
        for doc in tqdm(raw_docs, desc=f"Cleaning {os.path.basename(input_path)}"):
            doc = doc.strip()
            if not doc:
                continue

            # 1. Unicode Normalization
            norm_doc = normalize(doc)
            if len(norm_doc) < 40:
                filtered_count += 1
                continue

            # 2. Urdu Density Verification (allows English code-mixing)
            if not is_predominantly_urdu(norm_doc, min_ratio=0.35, min_urdu_chars=25):
                filtered_count += 1
                continue

            # 3. Deduplication via hash
            doc_hash = hashlib.sha256(norm_doc.encode("utf-8")).hexdigest()
            if doc_hash in seen_hashes:
                duplicate_count += 1
                continue
            seen_hashes.add(doc_hash)

            # Write clean document with standard delimiter
            payload = norm_doc + "\n\n<|endoftext|>\n\n"
            f_out.write(payload)
            total_written_bytes += len(payload.encode("utf-8"))
            cleaned_count += 1

    mb = total_written_bytes / (1024 * 1024)
    print(f"  Done: {cleaned_count:,} docs retained ({mb:.2f} MB), {duplicate_count:,} duplicates removed, {filtered_count:,} junk/filtered.")
    return cleaned_count, duplicate_count, total_written_bytes


def main():
    print("=" * 70)
    print("            CORPUS CLEANING & NORMALIZATION PIPELINE")
    print("=" * 70)

    os.makedirs(CLEANED_DIR, exist_ok=True)
    seen_hashes = set()

    sources = [
        # Scraped
        (os.path.join(RAW_DIR, "scraped", "express", "express_raw_corpus.txt"), os.path.join(CLEANED_DIR, "scraped_express_clean.txt")),
        (os.path.join(RAW_DIR, "scraped", "jang", "jang_raw_corpus.txt"), os.path.join(CLEANED_DIR, "scraped_jang_clean.txt")),
        (os.path.join(RAW_DIR, "scraped", "bbc", "bbc_raw_corpus.txt"), os.path.join(CLEANED_DIR, "scraped_bbc_clean.txt")),
        # Public
        (os.path.join(RAW_DIR, "public", "makhzan", "makhzan_literature.txt"), os.path.join(CLEANED_DIR, "public_makhzan_clean.txt")),
        (os.path.join(RAW_DIR, "public", "cc100", "cc100_urdu.txt"), os.path.join(CLEANED_DIR, "public_cc100_clean.txt")),
    ]

    total_docs = 0
    total_dupes = 0
    total_bytes = 0

    for in_file, out_file in sources:
        d, dup, b = clean_source_file(in_file, out_file, seen_hashes)
        total_docs += d
        total_dupes += dup
        total_bytes += b

    print("\n" + "=" * 70)
    print(f"ALL CLEANING COMPLETED!")
    print(f"Total Unique Clean Documents: {total_docs:,}")
    print(f"Total Exact Duplicates Dropped: {total_dupes:,}")
    print(f"Total Cleaned Corpus Size: {total_bytes / (1024*1024):.2f} MB")
    print("=" * 70)


if __name__ == "__main__":
    main()
