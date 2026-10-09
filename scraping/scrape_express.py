"""
Daily Express (express.pk) Urdu Article Scraper
Extracts news articles, op-eds, sports, and science reports from Express Pakistan sitemaps.
"""

import os
import re
import sys
import time
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from scraping.utils import (
    get_polite_session,
    extract_clean_article_text,
    CorpusMetadataLogger,
    is_predominantly_urdu
)

SITEMAP_INDEX = "https://www.express.pk/sitemap.xml"
OUTPUT_DIR = os.path.join("corpus", "raw", "scraped", "express")
METADATA_FILE = os.path.join(OUTPUT_DIR, "scrape_metadata.jsonl")


def get_express_story_urls(session, max_sitemaps=30, max_urls=10000):
    """Retrieve story URLs from Express sitemaps."""
    print("[Express] Fetching sitemap index...")
    r = session.get(SITEMAP_INDEX, timeout=15)
    sitemap_urls = re.findall(r'<loc>(https://www\.express\.pk/sitemap/posts-[0-9]+\.xml)</loc>', r.text)
    if not sitemap_urls:
        # Fallback to any post sitemaps
        sitemap_urls = re.findall(r'<loc>(https://www\.express\.pk/sitemap/[^<]+)</loc>', r.text)

    print(f"[Express] Found {len(sitemap_urls)} candidate sub-sitemaps. Checking up to {max_sitemaps}...")
    story_urls = []
    for sm in sitemap_urls[:max_sitemaps]:
        try:
            res = session.get(sm, timeout=15)
            urls = re.findall(r'<loc>(https://www\.express\.pk/story/[^<]+)</loc>', res.text)
            story_urls.extend(urls)
            if len(story_urls) >= max_urls:
                break
        except Exception as e:
            print(f"[Express] Error fetching {sm}: {e}")

    story_urls = list(dict.fromkeys(story_urls))  # preserve order, remove duplicates
    print(f"[Express] Total unique story URLs found: {len(story_urls)}")
    return story_urls[:max_urls]


def scrape_express_article(session, url, logger, output_file_lock, output_file_path):
    """Fetch and parse single Express story."""
    try:
        r = session.get(url, timeout=12)
        if r.status_code != 200:
            return 0

        soup = BeautifulSoup(r.content, "html.parser")
        title_el = soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else ""

        # Extract content from story-text or standard paragraphs
        story_body = soup.find("div", class_="story-text") or soup.find("div", class_="story-content")
        if story_body:
            paras = [p.get_text(strip=True) for p in story_body.find_all("p") if len(p.get_text(strip=True)) > 20]
        else:
            paras = extract_clean_article_text(soup)

        if not paras:
            return 0

        full_text = "\n".join(paras)
        if not is_predominantly_urdu(full_text, min_ratio=0.4, min_urdu_chars=50):
            return 0

        doc_payload = ""
        if title:
            doc_payload += title + "\n\n"
        doc_payload += full_text + "\n\n<|endoftext|>\n\n"

        byte_count = len(doc_payload.encode("utf-8"))

        with output_file_lock:
            with open(output_file_path, "a", encoding="utf-8") as f:
                f.write(doc_payload)

        logger.log_document({
            "source": "express.pk",
            "url": url,
            "title": title,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bytes": byte_count,
            "char_count": len(doc_payload)
        })

        return byte_count
    except Exception:
        return 0


def run_express_scraper(target_mb=30.0, max_workers=6):
    """Run Express scraper until target_mb reached or URLs exhausted."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    raw_corpus_path = os.path.join(OUTPUT_DIR, "express_raw_corpus.txt")
    logger = CorpusMetadataLogger(METADATA_FILE)

    session = get_polite_session()
    urls = get_express_story_urls(session, max_sitemaps=50, max_urls=15000)

    import threading
    lock = threading.Lock()

    target_bytes = int(target_mb * 1024 * 1024)
    collected_bytes = 0
    if os.path.exists(raw_corpus_path):
        collected_bytes = os.path.getsize(raw_corpus_path)
        print(f"[Express] Existing corpus detected: {collected_bytes / (1024*1024):.2f} MB")

    if collected_bytes >= target_bytes:
        print(f"[Express] Target {target_mb} MB already met!")
        return collected_bytes

    print(f"[Express] Scraping to reach target {target_mb} MB ({target_bytes} bytes) with {max_workers} threads...")
    pbar = tqdm(total=target_bytes, initial=collected_bytes, unit="B", unit_scale=True, desc="Express.pk")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_express_article, session, u, logger, lock, raw_corpus_path): u for u in urls}
        for future in as_completed(futures):
            b = future.result()
            if b > 0:
                collected_bytes += b
                pbar.update(b)
                if collected_bytes >= target_bytes:
                    print(f"\n[Express] Target reached! Total: {collected_bytes / (1024*1024):.2f} MB")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    pbar.close()
    return collected_bytes


if __name__ == "__main__":
    mb = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    run_express_scraper(target_mb=mb)
