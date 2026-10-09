"""
Master Phase 2 Execution Script
Runs the complete Phase 2 data collection pipeline:
1. Public corpora download (Makhzan classical literature + CC-100 Urdu stream)
2. Self-scraped corpora (Daily Express + Daily Jang + BBC Urdu >= 50 MB)
3. Audit and verification of corpus compliance
"""

import sys
import os
import argparse
import subprocess

PYTHON_EXE = os.path.join(".venv", "Scripts", "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = "python"


def run_step(cmd, desc):
    print("\n" + "=" * 70)
    print(f"STEP: {desc}")
    print(f"COMMAND: {' '.join(cmd)}")
    print("=" * 70)
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"[WARNING] Step '{desc}' exited with code {res.returncode}")
    return res.returncode


def main():
    parser = argparse.ArgumentParser(description="Master runner for Phase 2 Corpus Collection.")
    parser.add_argument("--scrape-only", action="store_true", help="Only run self-scraping")
    parser.add_argument("--public-only", action="store_true", help="Only run public corpus downloads")
    parser.add_argument("--cc100-mb", type=float, default=500.0, help="Target MB to stream from CC-100 (default 500)")
    parser.add_argument("--express-mb", type=float, default=30.0, help="Target MB for Express.pk (default 30)")
    parser.add_argument("--jang-mb", type=float, default=15.0, help="Target MB for Jang (default 15)")
    parser.add_argument("--bbc-mb", type=float, default=10.0, help="Target MB for BBC Urdu (default 10)")
    parser.add_argument("--workers", type=int, default=6, help="Thread count for scrapers")
    args = parser.parse_args()

    print("*" * 70)
    print("     PHASE 2: URDU CORPUS COLLECTION PIPELINE")
    print("*" * 70)

    # Step 1: Public Corpus
    if not args.scrape_only:
        cmd_public = [
            PYTHON_EXE,
            os.path.join("scripts", "download_public_corpus.py"),
            "--cc100-mb", str(args.cc100_mb)
        ]
        run_step(cmd_public, "Downloading Public Corpora (Makhzan & CC-100)")

    # Step 2: Self-Scraped Corpus
    if not args.public_only:
        cmd_scrape = [
            PYTHON_EXE,
            os.path.join("scraping", "run_scrapers.py"),
            "--express-mb", str(args.express_mb),
            "--jang-mb", str(args.jang_mb),
            "--bbc-mb", str(args.bbc_mb),
            "--workers", str(args.workers)
        ]
        run_step(cmd_scrape, "Running Self-Scraped Urdu Corpora (Target >= 50 MB)")

    # Step 3: Audit & Stats
    cmd_audit = [
        PYTHON_EXE,
        os.path.join("scripts", "check_corpus_stats.py")
    ]
    run_step(cmd_audit, "Auditing Corpus Size and Compliance")


if __name__ == "__main__":
    main()
