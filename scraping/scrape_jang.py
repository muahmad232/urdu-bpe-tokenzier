"""
Daily Jang (jang.com.pk) Urdu Scraper
Extracts news articles and editorial columns from Jang Pakistan across multiple categories and paginated archives.
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

CATEGORIES = [
    "https://jang.com.pk/category/national",
    "https://jang.com.pk/category/world",
    "https://jang.com.pk/category/sports",
    "https://jang.com.pk/category/business",
    "https://jang.com.pk/category/columns",
    "https://jang.com.pk/category/entertainment",
    "https://jang.com.pk/category/health",
]

OUTPUT_DIR = os.path.join("corpus", "raw", "scraped", "jang")
METADATA_FILE = os.path.join(OUTPUT_DIR, "scrape_metadata.jsonl")


def get_jang_story_urls(session, max_pages_per_cat=15, max_urls=10000):
    """Retrieve story URLs from Jang category pages and paginated archives."""
    print("[Jang] Fetching story URLs from categories...")
    urls = []
    url_pattern = re.compile(r'https://jang\.com\.pk/news/\d+')

    for cat in CATEGORIES:
        for page in range(1, max_pages_per_cat + 1):
            page_url = f"{cat}?page={page}" if page > 1 else cat
            try:
                r = session.get(page_url, timeout=12)
                if r.status_code != 200:
                    break
                found = url_pattern.findall(r.text)
                urls.extend(found)
                if len(urls) >= max_urls:
                    break
            except Exception as e:
                print(f"[Jang] Error on {page_url}: {e}")
                break

    urls = list(dict.fromkeys(urls))
    print(f"[Jang] Total unique story URLs found: {len(urls)}")
    return urls[:max_urls]


def scrape_jang_article(session, url, logger, output_file_lock, output_file_path):
    """Fetch and parse a single Jang article or column."""
    try:
        r = session.get(url, timeout=12)
        if r.status_code != 200:
            return 0

        soup = BeautifulSoup(r.content, "html.parser")
        title_el = soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else ""

        # Content is typically in detail-content or story-detail or p tags
        content_el = (
            soup.find("div", class_="detail-content") or
            soup.find("div", class_="content-detail") or
            soup.find("div", class_="detail-view")
        )

        if content_el:
            paras = [p.get_text(strip=True) for p in content_el.find_all("p") if len(p.get_text(strip=True)) > 20]
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
            "source": "jang.com.pk",
            "url": url,
            "title": title,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bytes": byte_count,
            "char_count": len(doc_payload)
        })

        return byte_count
    except Exception:
        return 0


def run_jang_scraper(target_mb=15.0, max_workers=6):
    """Run Jang scraper until target_mb reached or URLs exhausted."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    raw_corpus_path = os.path.join(OUTPUT_DIR, "jang_raw_corpus.txt")
    logger = CorpusMetadataLogger(METADATA_FILE)

    session = get_polite_session()
    urls = get_jang_story_urls(session, max_pages_per_cat=25, max_urls=8000)

    import threading
    lock = threading.Lock()

    target_bytes = int(target_mb * 1024 * 1024)
    collected_bytes = 0
    if os.path.exists(raw_corpus_path):
        collected_bytes = os.path.getsize(raw_corpus_path)
        print(f"[Jang] Existing corpus detected: {collected_bytes / (1024*1024):.2f} MB")

    if collected_bytes >= target_bytes:
        print(f"[Jang] Target {target_mb} MB already met!")
        return collected_bytes

    print(f"[Jang] Scraping to reach target {target_mb} MB ({target_bytes} bytes) with {max_workers} threads...")
    pbar = tqdm(total=target_bytes, initial=collected_bytes, unit="B", unit_scale=True, desc="Jang.com.pk")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_jang_article, session, u, logger, lock, raw_corpus_path): u for u in urls}
        for future in as_completed(futures):
            b = future.result()
            if b > 0:
                collected_bytes += b
                pbar.update(b)
                if collected_bytes >= target_bytes:
                    print(f"\n[Jang] Target reached! Total: {collected_bytes / (1024*1024):.2f} MB")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    pbar.close()
    return collected_bytes


if __name__ == "__main__":
    mb = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
    run_jang_scraper(target_mb=mb)
