"""
BBC Urdu (bbc.com/urdu) Scraper
Extracts journalistic news and feature articles from BBC Urdu RSS feeds and topic archives.
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

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/urdu/rss.xml",
]

TOPIC_PAGES = [
    "https://www.bbc.com/urdu/topics/cjgn7n9zzqet",  # Pakistan
    "https://www.bbc.com/urdu/topics/cl8l9mveql2t",  # World
    "https://www.bbc.com/urdu/topics/c340q03z54vt",  # Sport
    "https://www.bbc.com/urdu/topics/ckdxnw959n7t",  # Science
    "https://www.bbc.com/urdu/topics/c11019rwnv6t",  # Entertainment
]

OUTPUT_DIR = os.path.join("corpus", "raw", "scraped", "bbc")
METADATA_FILE = os.path.join(OUTPUT_DIR, "scrape_metadata.jsonl")


def get_bbc_story_urls(session, max_urls=5000):
    """Retrieve story URLs from BBC Urdu RSS and topic pages."""
    print("[BBC Urdu] Fetching article URLs...")
    urls = []

    # 1. RSS Feed
    for rss in RSS_FEEDS:
        try:
            r = session.get(rss, timeout=12)
            found = re.findall(r'<link>(https://www\.bbc\.com/urdu/articles/[a-zA-Z0-9]+)</link>', r.text)
            if not found:
                found = re.findall(r'<guid[^>]*>(https://www\.bbc\.com/urdu/[^<]+)</guid>', r.text)
            urls.extend(found)
        except Exception as e:
            print(f"[BBC Urdu] Error fetching RSS {rss}: {e}")

    # 2. Topic Pages
    url_pattern = re.compile(r'href=[\"\'](/urdu/articles/[a-zA-Z0-9]+)[\"\']')
    for topic in TOPIC_PAGES:
        try:
            r = session.get(topic, timeout=12)
            found = url_pattern.findall(r.text)
            for path in found:
                urls.append(f"https://www.bbc.com{path}")
        except Exception as e:
            print(f"[BBC Urdu] Error fetching topic {topic}: {e}")

    urls = list(dict.fromkeys(urls))
    print(f"[BBC Urdu] Total unique story URLs found: {len(urls)}")
    return urls[:max_urls]


def scrape_bbc_article(session, url, logger, output_file_lock, output_file_path):
    """Fetch and parse single BBC Urdu article."""
    try:
        r = session.get(url, timeout=12)
        if r.status_code != 200:
            return 0

        soup = BeautifulSoup(r.content, "html.parser")
        title_el = soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else ""

        # BBC articles have paragraphs inside <main>
        main_tag = soup.find("main")
        if main_tag:
            paras = [p.get_text(strip=True) for p in main_tag.find_all("p") if len(p.get_text(strip=True)) > 20]
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
            "source": "bbc.com/urdu",
            "url": url,
            "title": title,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bytes": byte_count,
            "char_count": len(doc_payload)
        })

        return byte_count
    except Exception:
        return 0


def run_bbc_scraper(target_mb=10.0, max_workers=5):
    """Run BBC Urdu scraper until target_mb reached or URLs exhausted."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    raw_corpus_path = os.path.join(OUTPUT_DIR, "bbc_raw_corpus.txt")
    logger = CorpusMetadataLogger(METADATA_FILE)

    session = get_polite_session()
    urls = get_bbc_story_urls(session)

    import threading
    lock = threading.Lock()

    target_bytes = int(target_mb * 1024 * 1024)
    collected_bytes = 0
    if os.path.exists(raw_corpus_path):
        collected_bytes = os.path.getsize(raw_corpus_path)
        print(f"[BBC Urdu] Existing corpus detected: {collected_bytes / (1024*1024):.2f} MB")

    if collected_bytes >= target_bytes:
        print(f"[BBC Urdu] Target {target_mb} MB already met!")
        return collected_bytes

    print(f"[BBC Urdu] Scraping to reach target {target_mb} MB ({target_bytes} bytes) with {max_workers} threads...")
    pbar = tqdm(total=target_bytes, initial=collected_bytes, unit="B", unit_scale=True, desc="BBC Urdu")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_bbc_article, session, u, logger, lock, raw_corpus_path): u for u in urls}
        for future in as_completed(futures):
            b = future.result()
            if b > 0:
                collected_bytes += b
                pbar.update(b)
                if collected_bytes >= target_bytes:
                    print(f"\n[BBC Urdu] Target reached! Total: {collected_bytes / (1024*1024):.2f} MB")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    pbar.close()
    return collected_bytes


if __name__ == "__main__":
    mb = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
    run_bbc_scraper(target_mb=mb)
