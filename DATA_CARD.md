# DATA CARD — Urdu Corpus Documentation
> Course: CS 417 Large Language Models · NUST SEECS · Spring 2026  
> Assignment 1: Urdu BPE Tokenizer from Scratch

---

## 1. Corpus Overview

This corpus is created for training a byte-level Byte-Pair Encoding (BPE) tokenizer for the Urdu language from scratch. The dataset combines modern journalistic news, editorial essays, classical Urdu literature, and diverse web prose to ensure broad vocabulary coverage across formal, literary, and contemporary colloquial registers.

- **Target Size**: ≥ 500 MB cleaned UTF-8 Urdu text (~50–60 million words).
- **Target Vocabulary Size**: Exactly 50,000 tokens (IDs 0–49,999).
- **Special Token**: `<|endoftext|>` at ID 256.

---

## 2. Data Sources & Licensing

| Source Name | Genre | Access URL | License / Terms of Use | Collection Method | Target Raw Size | Target Cleaned Size |
|---|---|---|---|---|---|---|
| **Daily Express** (`express.pk`) | Modern News, Op-Eds, Sports, Sci-Tech | `https://www.express.pk` | Academic/Fair Use (Respects `robots.txt`) | Direct scraping via sitemaps & articles | ~30–35 MB | ~25–30 MB |
| **Daily Jang** (`jang.com.pk`) | News, Politics, Columns | `https://jang.com.pk` | Academic/Fair Use (Respects `robots.txt`) | Direct scraping via categories & columns | ~15–20 MB | ~12–15 MB |
| **BBC Urdu** (`bbc.com/urdu`) | High-register International Journalism | `https://www.bbc.com/urdu` | Academic/Fair Use (Respects `robots.txt`) | Direct scraping via RSS feeds & topic pages | ~10–12 MB | ~8–10 MB |
| **Makhzan Urdu Literature** | Classical Urdu Fiction, Essays, Poetry | `https://github.com/zeerakahmed/makhzan` | Creative Commons Attribution (CC-BY 4.0) | Automated XML dump parsing (6,300+ docs) | ~56 MB | ~45–50 MB |
| **CC-100 Urdu** | Web crawl (blogs, forums, educational) | `http://data.statmt.org/cc-100/ur.txt.xz` | Creative Commons CC-BY-SA 4.0 | Direct LZMA streaming | ~500–600 MB | ~450–500 MB |

**Self-Scraped Total**: ≥ 55 MB raw (Satisfies mandatory ≥ 50 MB requirement).  
**Combined Corpus Target**: ≥ 600 MB raw / ≥ 500 MB cleaned.

---

## 3. Scraping & Ethics Compliance

1. **Robots.txt & Rate Limiting**: All scrapers implement connection pooling, polite exponential backoffs, and concurrent worker limits to avoid server pressure.
2. **Exclusion of Personal Data**: Private messages, social media comments, and paywalled personal profiles are excluded.
3. **No Unlicensed Redistribution**: Raw and processed corpora are retained strictly for academic evaluation within the CS 417 course environment.
4. **Reproducibility Evidence**:
   - Scraping code is maintained in `scraping/` (`scrape_express.py`, `scrape_jang.py`, `scrape_bbc.py`, `run_scrapers.py`).
   - Per-document scraping metadata is recorded in `.jsonl` files (`scrape_metadata.jsonl`) detailing exact article URLs, fetch timestamps, byte sizes, and titles.

---

## 4. Corpus Cleaning Pipeline Specification

All collected texts pass through a multi-stage cleaning pipeline:

1. **Document-Level Parsing**: Extract main article body, stripping navigation menus, scripts, stylesheets, advertisements, and social sharing links.
2. **Unicode Normalization** (`normalize.py`):
   - Normalize Arabic lookalikes to canonical Urdu codepoints (`ي`, `ى` → `ی`; `ك` → `ک`; `ه` → `ہ`).
   - Preserve distinction between Gol Heh (`ہ`) and Do-Chashmi Heh (`ھ`).
   - Strip tatweel (`ـ`), ZWJ (`\u200D`), direction markers (LRM/RLM), and byte order marks (BOM).
   - Standardize whitespace and collapse runs of spaces and redundant line breaks.
3. **Language Filtering**:
   - Verify Urdu/Persian-Arabic script density (`[\u0600-\u06FF...]`).
   - Retain natural English code-mixing commonly present in Urdu technical and political discourse.
   - Discard boilerplate banners, English-only navigation blocks, and corrupt fragments.
4. **Deduplication**:
   - Exact duplicate removal at document level.
5. **Document Boundary Delimitation**:
   - Every document terminates with `<|endoftext|>`.

---

## 5. Splits & Data Statistics

- **Total Documents Processed**: 195,086 unique cleaned documents
- **Train Split (`corpus/train.txt`)**: 191,184 documents (98.0%) — **566.65 MB** (~70.8M words)
- **Validation Split (`corpus/val.txt`)**: 1,950 documents (1.0%) — **6.20 MB** (~775k words)
- **Test Split (`corpus/test.txt`)**: 1,952 documents (1.0%) — **5.26 MB** (~657k words)
- **Total Cleaned Corpus Size**: **578.11 MB** (exceeds the 500 MB minimum requirement)
- **Seed**: `42` (ensures 100% deterministic reproducibility)

---

## 6. Known Gaps & Biases

1. **Genre Skew**: News and journalistic discourse represent the largest proportion of modern web Urdu text, which may lead to higher frequency of political and administrative vocabulary relative to colloquial spoken dialects.
2. **Dialect & Script Variations**: Includes both Pakistani standardized Urdu orthography and historical orthographic styles present in Makhzan classical literature.
3. **Roman Urdu**: The training corpus focuses primarily on Nastaliq / Perso-Arabic script Urdu; transliterated Roman Urdu is treated as out-of-domain evaluation data.
