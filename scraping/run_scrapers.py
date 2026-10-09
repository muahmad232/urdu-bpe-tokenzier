"""
Master Scraping Pipeline Orchestrator
Executes scrapers across all selected targets to collect ≥ 50 MB of raw Urdu articles.
"""

import os
import sys
import argparse

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scraping.scrape_express import run_express_scraper
from scraping.scrape_jang import run_jang_scraper
from scraping.scrape_bbc import run_bbc_scraper

TOTAL_TARGET_MB = 55.0


def main():
    parser = argparse.ArgumentParser(description="Run Urdu text scrapers to collect >= 50 MB.")
    parser.add_argument("--express-mb", type=float, default=30.0, help="Target MB for Express.pk")
    parser.add_argument("--jang-mb", type=float, default=15.0, help="Target MB for Jang.com.pk")
    parser.add_argument("--bbc-mb", type=float, default=10.0, help="Target MB for BBC Urdu")
    parser.add_argument("--workers", type=int, default=6, help="Thread count per scraper")
    args = parser.parse_args()

    print("=" * 60)
    print("           URDU SCRAPING PIPELINE (>= 50 MB)")
    print("=" * 60)
    print(f"Express.pk target: {args.express_mb} MB")
    print(f"Jang.com.pk target: {args.jang_mb} MB")
    print(f"BBC Urdu target:   {args.bbc_mb} MB")
    print(f"Concurrency:       {args.workers} threads")
    print("=" * 60)

    total_bytes = 0

    print("\n>>> [1/3] Running Daily Express Scraper...")
    b1 = run_express_scraper(target_mb=args.express_mb, max_workers=args.workers)
    total_bytes += b1

    print("\n>>> [2/3] Running Daily Jang Scraper...")
    b2 = run_jang_scraper(target_mb=args.jang_mb, max_workers=args.workers)
    total_bytes += b2

    print("\n>>> [3/3] Running BBC Urdu Scraper...")
    b3 = run_bbc_scraper(target_mb=args.bbc_mb, max_workers=args.workers)
    total_bytes += b3

    total_mb = total_bytes / (1024 * 1024)
    print("\n" + "=" * 60)
    print(f"SCRAPING COMPLETE!")
    print(f"Total Self-Scraped Corpus Size: {total_mb:.2f} MB")
    if total_mb >= 50.0:
        print("[SUCCESS] Meets the assignment requirement of >= 50 MB self-scraped data!")
    else:
        print(f"[INFO] Currently at {total_mb:.2f} MB. You can run again or increase targets to reach 50 MB.")
    print("=" * 60)


if __name__ == "__main__":
    main()
