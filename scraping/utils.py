"""
Scraping utilities for Urdu corpus collection.
Provides polite HTTP session, retry logic, HTML parsing, Urdu text validation,
and metadata logging for DATA_CARD evidence.
"""

import os
import re
import time
import json
import logging
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

# Urdu Unicode ranges:
# Arabic script: \u0600-\u06FF
# Arabic Supplement: \u0750-\u077F
# Arabic Extended-A: \u08A0-\u08FF
# Arabic Presentation Forms-A: \uFB50-\uFDFF
# Arabic Presentation Forms-B: \uFE70-\uFEFF
URDU_CHAR_RE = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')

# Default headers mimicking a standard modern desktop browser
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ur,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate",
}


def get_polite_session(
    retries: int = 3,
    backoff_factor: float = 0.5,
    timeout: int = 15,
) -> requests.Session:
    """Create a requests session with retries and realistic headers."""
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def is_predominantly_urdu(text: str, min_ratio: float = 0.4, min_urdu_chars: int = 30) -> bool:
    """
    Check if a text string contains predominantly Urdu/Arabic-script characters.
    Allows for natural English code-mixing while discarding English-only / code / junk blocks.
    """
    if not text:
        return False
    urdu_chars = len(URDU_CHAR_RE.findall(text))
    if urdu_chars < min_urdu_chars:
        return False
    total_non_space = len(re.sub(r'\s+', '', text))
    if total_non_space == 0:
        return False
    return (urdu_chars / total_non_space) >= min_ratio


def extract_clean_article_text(soup: BeautifulSoup) -> List[str]:
    """
    Extract meaningful article paragraphs from BeautifulSoup,
    stripping nav, scripts, styles, footers, and ad widgets.
    """
    # Remove unwanted tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
        tag.decompose()

    paragraphs = []
    # Collect text from paragraph tags
    for p in soup.find_all(["p", "div"]):
        # Only take text from leaf-like or clean paragraph containers
        txt = p.get_text(separator=" ", strip=True)
        # Skip very short snippets, disclaimers, or empty paragraphs
        if len(txt) >= 40 and is_predominantly_urdu(txt, min_ratio=0.3, min_urdu_chars=20):
            paragraphs.append(txt)

    # Deduplicate consecutive identical paragraphs
    deduped = []
    for para in paragraphs:
        if not deduped or para != deduped[-1]:
            deduped.append(para)

    return deduped


class CorpusMetadataLogger:
    """Logs scraped document metadata (URL, timestamp, bytes, characters) for DATA_CARD evidence."""
    def __init__(self, log_path: str):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def log_document(self, meta: Dict[str, Any]):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")
