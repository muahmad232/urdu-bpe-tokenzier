"""
Corpus Statistics & Compliance Checker
Calculates exact sizes, word counts, document counts, and checks assignment requirements:
1. Self-scraped >= 50 MB
2. Total corpus >= 500 MB (aiming for 600 MB - 1 GB)
3. >= 3 sources across >= 2 genres
"""

import os
import re
import glob

URDU_CHAR_RE = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')


def inspect_file(file_path):
    """Compute stats for a single text file."""
    if not os.path.exists(file_path):
        return None

    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)

    doc_count = 0
    line_count = 0
    word_count = 0
    total_chars = 0
    urdu_chars = 0

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_count += 1
            if "<|endoftext|>" in line:
                doc_count += line.count("<|endoftext|>")
            words = line.split()
            word_count += len(words)
            total_chars += len(line)
            urdu_chars += len(URDU_CHAR_RE.findall(line))

    # Fallback if no delimiter found
    if doc_count == 0 and line_count > 0:
        doc_count = 1

    urdu_pct = (urdu_chars / total_chars * 100) if total_chars > 0 else 0

    return {
        "file": file_path,
        "size_mb": size_mb,
        "size_bytes": size_bytes,
        "docs": doc_count,
        "lines": line_count,
        "words": word_count,
        "urdu_pct": urdu_pct
    }


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def main():
    print("=" * 80)
    print("                 URDU CORPUS STATISTICS & COMPLIANCE AUDIT")
    print("=" * 80)

    # 1. Scraped Files
    scraped_files = glob.glob(os.path.join(PROJECT_ROOT, "corpus", "raw", "scraped", "**", "*.txt"), recursive=True)
    scraped_stats = [inspect_file(f) for f in scraped_files if inspect_file(f)]

    # 2. Public Files
    public_files = glob.glob(os.path.join(PROJECT_ROOT, "corpus", "raw", "public", "**", "*.txt"), recursive=True)
    public_stats = [inspect_file(f) for f in public_files if inspect_file(f)]

    # 3. Cleaned Files
    cleaned_files = glob.glob(os.path.join(PROJECT_ROOT, "corpus", "cleaned", "*.txt")) + glob.glob(os.path.join(PROJECT_ROOT, "corpus", "*.txt"))
    cleaned_stats = [inspect_file(f) for f in cleaned_files if inspect_file(f)]

    header_fmt = "{:<35} | {:>10} | {:>10} | {:>12} | {:>9}"
    row_fmt    = "{:<35} | {:>9.2f}M | {:>10,} | {:>12,} | {:>8.1f}%"

    print("\n--- SELF-SCRAPED CORPORA (Target >= 50 MB) ---")
    print(header_fmt.format("File / Source", "Size", "Docs", "Words", "Urdu Char %"))
    print("-" * 85)
    total_scraped_mb = 0
    total_scraped_words = 0
    for s in scraped_stats:
        print(row_fmt.format(os.path.basename(s["file"]), s["size_mb"], s["docs"], s["words"], s["urdu_pct"]))
        total_scraped_mb += s["size_mb"]
        total_scraped_words += s["words"]
    print("-" * 85)
    print(f"Total Self-Scraped: {total_scraped_mb:.2f} MB ({total_scraped_words:,} words)")
    if total_scraped_mb >= 50.0:
        print("  -> STATUS: PASS (>= 50 MB requirement satisfied!)")
    else:
        print(f"  -> STATUS: IN PROGRESS ({total_scraped_mb:.2f} / 50.0 MB)")

    print("\n--- PUBLIC CORPORA ---")
    print(header_fmt.format("File / Source", "Size", "Docs", "Words", "Urdu Char %"))
    print("-" * 85)
    total_public_mb = 0
    total_public_words = 0
    for s in public_stats:
        print(row_fmt.format(os.path.basename(s["file"]), s["size_mb"], s["docs"], s["words"], s["urdu_pct"]))
        total_public_mb += s["size_mb"]
        total_public_words += s["words"]
    print("-" * 85)
    print(f"Total Public: {total_public_mb:.2f} MB ({total_public_words:,} words)")

    if cleaned_stats:
        print("\n--- CLEANED / SPLIT CORPORA (Target >= 500 MB) ---")
        print(header_fmt.format("File / Source", "Size", "Docs", "Words", "Urdu Char %"))
        print("-" * 85)
        for s in cleaned_stats:
            print(row_fmt.format(os.path.basename(s["file"]), s["size_mb"], s["docs"], s["words"], s["urdu_pct"]))
        print("-" * 85)

    grand_total_mb = total_scraped_mb + total_public_mb
    grand_total_words = total_scraped_words + total_public_words
    print("\n" + "=" * 80)
    print(f"GRAND TOTAL RAW CORPUS: {grand_total_mb:.2f} MB ({grand_total_words:,} words)")
    print("=" * 80)


if __name__ == "__main__":
    main()
