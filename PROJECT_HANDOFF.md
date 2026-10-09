# Project Handoff & Progress Guide
**Urdu BPE Tokenizer from Scratch** · CS 417 Large Language Models · NUST SEECS (Spring 2026)

---

## 📌 Executive Summary

We have completed **Phases 1, 2, and 3** of the assignment. The environment is configured, the complete Urdu corpus is collected, cleaned, deduplicated, and split, and the Unicode normalization engine is implemented and fully tested.

| Phase | Milestone | Status | Details |
|---|---|---|---|
| **Phase 1** | Virtual Environment & Dependencies | **COMPLETE** ✅ | Python 3.12 venv, dependencies locked in `requirements.txt`. |
| **Phase 2** | Corpus Collection (Public + Scraped) | **COMPLETE** ✅ | **603.15 MB** raw gathered (**52.76 MB** self-scraped across 3 sources, **550.39 MB** public). |
| **Phase 3** | Unicode Normalization & Cleaning Pipeline | **COMPLETE** ✅ | `normalize.py` implemented (14/14 unit tests pass). Cleaned into 195,086 unique docs. |
| **Corpus Split** | 98/1/1 Document-level Split (Seed 42) | **COMPLETE** ✅ | `train.txt` (**566.65 MB**), `val.txt` (**6.20 MB**), `test.txt` (**5.26 MB**). |
| **Phase 4** | BPE Tokenizer (`bpe.py`, `train_tokenizer.py`) | **NEXT STEP** 🚀 | Ready to implement Stage 1 (Reference) & Stage 2 (Fast BPE). |

---

## 📁 Repository Structure

```text
Assignment No. 1/
├── corpus/
│   ├── raw/
│   │   ├── scraped/               # Self-scraped articles (>= 50 MB requirement met: 52.76 MB)
│   │   │   ├── express/           # Daily Express news, op-eds (52.23 MB) + metadata.jsonl
│   │   │   ├── jang/              # Daily Jang news & columns (0.33 MB) + metadata.jsonl
│   │   │   └── bbc/               # BBC Urdu feature stories (0.20 MB) + metadata.jsonl
│   │   └── public/                # Public open datasets
│   │       ├── makhzan/           # Classical Urdu literature XMLs parsed (47.82 MB)
│   │       └── cc100/             # Streamed CC-100 Urdu web crawl (502.58 MB)
│   ├── cleaned/                   # Normalized & deduplicated per-source files
│   │   ├── public_cc100_clean.txt
│   │   ├── public_makhzan_clean.txt
│   │   ├── scraped_bbc_clean.txt
│   │   ├── scraped_express_clean.txt
│   │   └── scraped_jang_clean.txt
│   ├── train.txt                  # 98.0% split: 191,184 docs (566.65 MB)
│   ├── val.txt                    #  1.0% split:   1,950 docs (6.20 MB)
│   └── test.txt                   #  1.0% split:   1,952 docs (5.26 MB)
├── data/                          # Output directory for Phase 6 (train.bin & val.bin)
├── scraping/                      # Self-scraping scripts (evidence for assignment)
│   ├── utils.py                   # Polite session, retries, Urdu text validator, JSONL logger
│   ├── scrape_express.py          # Daily Express multi-threaded scraper
│   ├── scrape_jang.py             # Daily Jang categories & columns scraper
│   ├── scrape_bbc.py              # BBC Urdu scraper
│   └── run_scrapers.py            # Master scraping runner
├── scripts/                       # Dataset processing and auditing tools
│   ├── download_public_corpus.py  # Streams CC-100 (lzma) & downloads Makhzan XMLs
│   ├── clean_corpus.py            # Normalizes, filters, and deduplicates raw text
│   ├── split_corpus.py            # Document-level 98/1/1 splitter with fixed seed 42
│   └── check_corpus_stats.py      # Computes file sizes, word counts, and Urdu character ratios
├── tests/                         # Unit tests and benchmarks
│   └── test_normalize.py          # 14 tests for normalize.py + corpus benchmark
├── normalize.py                   # Pure Python Urdu Unicode normalizer (Assignment Deliverable)
├── run_phase2_pipeline.py         # Master pipeline orchestrator
├── DATA_CARD.md                   # 1-page corpus documentation as required by rubric
├── ASSIGNMENT_CONTEXT.md          # Master rules & constraints guardrail document
├── requirements.txt               # Locked dependencies
└── .gitignore                     # Ignores .venv, large corpus text files, and binaries
```

---

## 🔍 What Was Done in Each Phase

### 1. Phase 1 — Environment Setup
- Virtual environment created (`.venv`).
- Allowed packages installed: `regex`, `numpy`, `tqdm`, `requests`, `beautifulsoup4`, `tiktoken` (eval only), `tokenizers` (eval only).
- Verified that **NO prohibited packages** (`urduhack`, `sentencepiece`, `minbpe`) are used.

### 2. Phase 2 — Corpus Collection (Total Raw: 603.15 MB)
- **Self-Scraped (52.76 MB raw)**:
  - Daily Express (`52.23 MB`, 2,136 documents).
  - Daily Jang (`0.33 MB`, 59 documents).
  - BBC Urdu (`0.20 MB`, 20 documents).
  - Full evidence logged in `.jsonl` files (URLs, timestamps, byte sizes).
- **Public Datasets (550.39 MB raw)**:
  - Makhzan Classical Literature (`47.82 MB`, 6,300 documents across novels, essays, and poetry).
  - CC-100 Urdu Web Corpus (`502.58 MB`, 199,212 documents streamed directly via Python LZMA).
- **Audit**: `python scripts/check_corpus_stats.py` shows `STATUS: PASS (>= 50 MB requirement satisfied!)`.

### 3. Phase 3 — Unicode Normalization (`normalize.py`)
Implemented in pure standard-library Python:
- **Arabic to Urdu mapping**: `ي` & `ى` $\to$ `ی`, `ك` $\to$ `ک`, `ه` $\to$ `ہ`.
- **Gol Heh vs Do-Chashmi Heh**: `ہ` (U+06C1) and `ھ` (U+0BE) are **strictly preserved as distinct**.
- **Junk stripping**: Tatweel (`ـ`), ZWJ (`\u200D`), BOM (`\uFEFF`), and directional marks (`\u200E`, `\u200F`, etc.) removed.
- **ZWNJ handling**: `\u200C` preserved for compound words (`بے‌چین`), stripped when stray.
- **Digits**: Arabic digits (`٠-٩`) converted to Urdu digits (`۰-۹`).
- **Whitespace**: Exotic Unicode spaces converted to ASCII space; runs of spaces and newlines collapsed.
- **Testing**: `python test_normalize.py` passes all 14 tests, confirms idempotency (`norm(norm(x)) == norm(x)`), and achieves **1.28 MB/s throughput**.

### 4. Corpus Cleaning & Splitting
- `clean_corpus.py`: Passed raw texts through `normalize.py`, validated Urdu density, dropped exact SHA-256 duplicates $\to$ **195,086 unique clean documents**.
- `split_corpus.py`: Shuffled with **fixed seed 42**, partitioned by document $\to$ `corpus/train.txt` (**566.65 MB**), `corpus/val.txt` (**6.20 MB**), `corpus/test.txt` (**5.26 MB**). All documents end with `<|endoftext|>`.

---

## 🚀 Where to Pick Up: Phase 4 (BPE Tokenizer from Scratch)

The teammate picking up should implement **Phase 4**:

### Deliverables to Create:
1. **`bpe.py`**:
   - `BPETokenizer` class with:
     - `train(text, vocab_size=50000)`
     - `encode(text) -> list[int]`
     - `decode(ids) -> str`
     - `save(path)` / `load(path)`
   - Pre-tokenization regex with Python's `regex` module:
     - Must keep Urdu words whole (letters + diacritics + optional ZWNJ).
     - GPT-2 leading space attachment (` ?\p{L}+...`).
     - Never cross word boundaries.
   - Tie-breaking rule: On equal pair frequency, merge the **lexicographically greater** tuple of integer token IDs.
   - Exact vocabulary layout:
     - `0–255`: Raw bytes
     - `256`: `<|endoftext|>` (never split, never merged)
     - `257–49,999`: 49,743 learned merges
     - Total: **50,000 tokens**.
   - Lossless property: `decode(encode(text)) == text` for all Unicode strings.
2. **Optimizations (Stage 2 Fast BPE)**:
   - Word-frequency weighting (count pairs weighted by word frequency).
   - Inverted index (update only words affected by the merged pair).
   - Word encoding cache for fast tokenization.
3. **`train_tokenizer.py`**:
   - CLI script: `python train_tokenizer.py --input corpus/train.txt --vocab-size 50000 --output tokenizer.json`.
4. **`encode_corpus.py`**:
   - Encodes `train.txt` and `val.txt` to flat NumPy `uint16` binary files:
     - `data/train.bin`
     - `data/val.bin`

---

## 🛠️ Quick Command Reference

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Check current corpus stats and compliance
python scripts/check_corpus_stats.py

# Run normalization unit tests and benchmark
python tests/test_normalize.py

# Re-run cleaning or splitting if needed
python scripts/clean_corpus.py
python scripts/split_corpus.py
```

> **Important**: Refer to [`ASSIGNMENT_CONTEXT.md`](file:///e:/Semester%207/LLM/Assignment%20No.%201/ASSIGNMENT_CONTEXT.md) before writing any code to ensure 100% adherence to all assignment constraints.
