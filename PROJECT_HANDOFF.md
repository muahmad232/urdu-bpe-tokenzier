# Project Handoff & Progress Guide
**Urdu BPE Tokenizer from Scratch** · CS 417 Large Language Models · NUST SEECS (Spring 2026)

---

## 📌 Executive Summary

We have completed **Phases 1, 2, 3, 4, and 5** of the assignment. The environment is configured, the complete Urdu corpus is collected, cleaned, deduplicated, and split, the Unicode normalization engine is verified, the Byte-Pair Encoding (BPE) tokenizer from scratch is implemented and tested, the full **50,000-token vocabulary** is trained on `corpus/train.txt`, and both training and validation corpora are encoded into flat NumPy `uint16` binary files.

| Phase | Milestone | Status | Details |
|---|---|---|---|
| **Phase 1** | Virtual Environment & Dependencies | **COMPLETE** ✅ | Python 3.12+ venv, dependencies locked in `requirements.txt`. Zero prohibited libraries. |
| **Phase 2** | Corpus Collection (Public + Scraped) | **COMPLETE** ✅ | **603.15 MB** raw gathered (**52.76 MB** self-scraped across Express, Jang, BBC; **550.39 MB** public). |
| **Phase 3** | Unicode Normalization & Cleaning Pipeline | **COMPLETE** ✅ | `normalize.py` implemented (14/14 tests pass). Cleaned into 195,086 unique docs. |
| **Corpus Split** | 98/1/1 Document-level Split (Seed 42) | **COMPLETE** ✅ | `train.txt` (**566.65 MB**), `val.txt` (**6.20 MB**), `test.txt` (**5.26 MB**). All docs end with `<|endoftext|>`. |
| **Phase 4** | BPE Tokenizer Implementation & Test Suite | **COMPLETE** ✅ | `bpe.py`, `train_tokenizer.py`, `encode_corpus.py`, and `tests/test_bpe.py` (10/10 tests pass). 1 MB dry run verified. |
| **Phase 5** | Full Model Training & Binary Corpus Encoding | **COMPLETE** ✅ | Trained 50,000 vocab in 7m 17s on `train.txt` (49,743 merges). Encoded `data/train.bin` (81.1M tokens, 154.7 MB) and `data/val.bin` (885.8k tokens, 1.69 MB). |
| **Phase 6** | Part C Analysis & Final Deliverables | **NEXT STEP** 🚀 | Benchmark vs `gpt2` / `o200k_base`, compile ≤ 4-page `report.pdf`, write `README.md`. |

---

## 📁 Repository Structure

```text
urdu-bpe-tokenzier/
├── corpus/
│   ├── raw/                       # Self-scraped articles (>= 50 MB requirement met: 52.76 MB)
│   │   ├── scraped/
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
│   ├── train.txt                  # 98.0% split: 191,184 docs (566.65 MB, ~70.8M words)
│   ├── val.txt                    #  1.0% split:   1,950 docs (6.20 MB, ~775k words)
│   └── test.txt                   #  1.0% split:   1,952 docs (5.26 MB, ~657k words)
├── data/                          # Phase 5 binary outputs
│   ├── train.bin                  # Flat NumPy uint16: 81,123,563 tokens (154.73 MB)
│   └── val.bin                    # Flat NumPy uint16: 885,862 tokens (1.69 MB)
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
├── tests/                         # Unit test suites
│   ├── test_normalize.py          # 14 tests for normalize.py + idempotency checks (PASS)
│   └── test_bpe.py                # 10 tests for bpe.py, tie-breaking, equivalence & roundtrip (PASS)
├── normalize.py                   # Pure Python Urdu Unicode normalizer (Phase 3 Deliverable)
├── bpe.py                         # BPETokenizer class from scratch (Phase 4 Deliverable)
├── train_tokenizer.py             # CLI training runner with hardware profiling (Phase 4 Deliverable)
├── encode_corpus.py               # Streaming uint16 binary encoder with word cache (Phase 4 Deliverable)
├── tokenizer.json                 # Complete 50,000-token tokenizer with 49,743 merges (Phase 5 Deliverable)
├── run_phase2_pipeline.py         # Master Phase 2 pipeline orchestrator
├── DATA_CARD.md                   # 1-page corpus documentation as required by rubric
├── ASSIGNMENT_CONTEXT.md          # Master rules & constraints guardrail document
├── PROJECT_HANDOFF.md             # This document — authoritative project roadmap
├── requirements.txt               # Locked dependencies
└── .gitignore                     # Ignores .venv, binary data, and large caches
```

---

## 🔍 What Has Been Done Completely

### 1. Phase 1 — Environment Setup & Compliance
- Virtual environment configured with zero prohibited packages (`minbpe`, `tokenizers`, `sentencepiece`, `urduhack`).
- Allowed packages locked in `requirements.txt`: `regex`, `numpy`, `tqdm`, `requests`, `beautifulsoup4`, with `tiktoken` and `tokenizers` strictly isolated for Part C comparative benchmarks.

### 2. Phase 2 — Corpus Collection (Total Raw: 603.15 MB)
- **Self-Scraped (52.76 MB raw)**:
  - Daily Express (`52.23 MB`, 2,136 documents).
  - Daily Jang (`0.33 MB`, 59 documents).
  - BBC Urdu (`0.20 MB`, 20 documents).
  - Detailed metadata logged in `.jsonl` files (URLs, timestamps, byte sizes).
- **Public Datasets (550.39 MB raw)**:
  - Makhzan Classical Literature (`47.82 MB`, 6,300 documents across novels, essays, and poetry).
  - CC-100 Urdu Web Corpus (`502.58 MB`, 199,212 documents streamed via Python LZMA).
- **Audit**: `python scripts/check_corpus_stats.py` confirms compliance with the ≥ 50 MB self-scraped rule.

### 3. Phase 3 — Unicode Normalization (`normalize.py`)
- Pure Python standard-library implementation covering canonical normalization:
  - Arabic to Urdu mapping: `ي` & `ى` $\to$ `ی`, `ك` $\to$ `ک`, `ه` $\to$ `ہ`.
  - Strictly preserves Gol Heh (`ہ` U+06C1) vs Do-chashmi Heh (`ھ` U+06BE) as distinct letters.
  - Strips Tatweel (`ـ`), ZWJ (`\u200D`), BOM (`\uFEFF`), and directional marks (`\u200E`, `\u200F`, etc.).
  - Preserves Zero-Width Non-Joiner (`\u200C`) for morphological compound words (e.g. `بے‌چین`), strips stray occurrences.
  - Standardizes Arabic digits (`٠-٩`) to Urdu digits (`۰-۹`).
  - Collapses non-breaking/exotic spaces to ASCII space; normalizes line breaks.
- Verified: `tests/test_normalize.py` passes all 14 unit and idempotency tests in 0.011s.

### 4. Corpus Cleaning & Splitting
- `scripts/clean_corpus.py`: Passed raw texts through `normalize.py`, validated Urdu density, dropped exact SHA-256 duplicates $\to$ **195,086 unique clean documents**.
- `scripts/split_corpus.py`: Shuffled with fixed seed `42`, partitioned by document into:
  - `corpus/train.txt`: **566.65 MB** (191,184 documents, ~70.8M words) — 98.0%
  - `corpus/val.txt`: **6.20 MB** (1,950 documents, ~775k words) — 1.0%
  - `corpus/test.txt`: **5.26 MB** (1,952 documents, ~657k words) — 1.0%
  - Every document terminates with `<|endoftext|>`.

### 5. Phase 4 — BPE Tokenizer Implementation (`bpe.py`)
Implemented `BPETokenizer` entirely from scratch following all rubric specifications:
- **Vocabulary Specification (50,000 tokens)**:
  - IDs `0–255`: 256 raw bytes (`0x00`–`0xFF`).
  - ID `256`: `<|endoftext|>` special token (isolated from merges, never split into bytes).
  - IDs `257–49,999`: 49,743 learned merges in exact sequential order.
- **Custom Urdu Pre-Tokenization Regex**:
  `r"""'s|'t|'re|'ve|'m|'ll|'d| ?[\p{L}\p{M}]+(?:\u200c+[\p{L}\p{M}]+)*| ?\p{N}+| ?[^\s\p{L}\p{M}\p{N}]+|\s+(?!\S)|\s+"""`
  - Preserves Urdu letters, combining diacritics (`\p{M}`), and internal ZWNJ (`\u200C`).
  - Attaches leading whitespace (` ?`) to words, GPT-2 style.
  - Merges never cross word boundaries.
- **Deterministic Tie-Breaking**:
  - Compares pairs as integer tuples `(id1, id2)` via a lazy min-heap key `(-count, (-p0, -p1), pair)` to ensure 100% reproducible training.
- **Two-Stage Architecture**:
  - Stage 1 Reference (`train_stage1`): recount-all pair frequencies after each merge.
  - Stage 2 Fast (`train_stage2`): word-frequency weighting + pair-to-words inverted index + lazy max-heap + aggregated delta updates.
- **Lossless Invariant**:
  - `decode(encode(text)) == text` holds character-for-character for arbitrary Unicode text.
- **Serialization**: Complete `save(path)` and `BPETokenizer.from_file(path)` methods.

### 6. Training & Encoding Pipeline Scripts
- **`train_tokenizer.py`**:
  - Automatically profiles hardware (CPU model, core count, RAM in GB, OS platform, Python version).
  - Runs Stage 2 Fast BPE on the input text, emits progress logs every interval, and saves `tokenizer.json` with execution telemetry.
- **`encode_corpus.py`**:
  - Streams text in 1 MB chunks to prevent memory spikes.
  - Uses an in-memory word cache (`word_cache`) to achieve **~230,000–500,000 tokens/sec** encoding throughput.
  - Maps `<|endoftext|>` strictly to token ID 256.
  - Writes flat 1D NumPy arrays of type `uint16` (`file_size = num_tokens * 2` bytes).
  - Validates written binary files using `np.fromfile()`.

### 7. Unit Testing & Dry Run
- **Test Suite (`tests/test_bpe.py`)**:
  - Passes 10/10 tests in 16.06s: vocabulary layout, special token isolation, tie-breaking, Urdu diacritics & ZWNJ roundtrips, emojis, edge cases, and JSON serialization.
  - **Stage 1 vs. Stage 2 Equivalence Test**: Confirms both versions produce the **exact identical sequence of merges** on a 1 MB sample of `corpus/train.txt`.
- **End-to-End Dry Run**:
  - Trained 43 merges on 1 MB in 7.65s.
  - Encoded to `data/test_train.bin` (892,722 tokens, 1.70 MB file, 2.07 bytes/token compression ratio).
  - Validated 100% lossless roundtrip decoding character-for-character.

### 8. Phase 5 — Full Tokenizer Training (`tokenizer.json`)
- **Command Executed**:
  ```powershell
  python train_tokenizer.py --input corpus/train.txt --vocab-size 50000 --output tokenizer.json --log-interval 5000
  ```
- **Execution Telemetry**:
  - Input: `corpus/train.txt` (566.65 MB, 335,145,273 characters across 191,184 documents).
  - Unique words aggregated: **627,748**.
  - Merges learned: **49,743 / 49,743** (exact 50,000 vocabulary size).
  - Total training time: **00h 07m 05.29s** (425.29s).
  - Total wall-clock time: **00h 07m 17.67s** (437.67s).
  - Throughput: **116.96 merges/sec**.
  - Saved: `tokenizer.json` (**5.52 MB**).
  - Hardware recorded: Intel64 Family 6 Model 142 Stepping 10 (8 cores), 7.85 GB RAM, Windows 11.

### 9. Phase 5 — Binary Corpus Encoding (`train.bin` & `val.bin`)
- **Command Executed**:
  ```powershell
  python encode_corpus.py --tokenizer tokenizer.json --train-in corpus/train.txt --val-in corpus/val.txt --train-out data/train.bin --val-out data/val.bin
  ```
- **Encoding Telemetry**:
  - `data/train.bin`:
    - Processed 563.98 MB in 5m 51s (351.34s) at 230,900 tokens/s.
    - Total tokens: **81,123,563** (154.73 MB file).
    - Compression ratio: **7.29 bytes/token**.
    - Token ID range: [1, 49999].
  - `data/val.bin`:
    - Processed 6.17 MB in 4.02s at 220,314 tokens/s.
    - Total tokens: **885,862** (1.69 MB file).
    - Compression ratio: **7.31 bytes/token**.
    - Token ID range: [4, 49997].
  - Verification:
    - Byte size strictly equals `num_tokens * 2`.
    - First document decoded from `data/train.bin` matches `corpus/train.txt` **100% losslessly**.

---

## 🚀 Next Milestone: Phase 6 (Part C Analysis & Deliverables)

The next step is to conduct the empirical analysis on the trained tokenizer and compile the final submission report:

### Step 1: Implement `scripts/analyze_tokenizer.py`
To answer the 3 rubric questions programmatically:
1. **Question 1: Merges Analysis**:
   - Extract and decode merges 1 to 50, and every 5,000th merge thereafter (5,000, 10,000, ..., 45,000).
   - Identify early 2-byte letter rebuilding merges (e.g. `(0xD8, 0xA7) -> ا`).
   - Identify non-valid UTF-8 single-token intermediate merges.
   - Determine the exact merge index where the first complete Urdu word emerges.
   - Find the top 20 longest learned tokens (by character length and byte length).
2. **Question 2: Comparative Benchmark**:
   - Evaluate tokens-per-word on `corpus/test.txt` and the 7 hand-picked inputs:
     1. News story (`news`)
     2. Classical poetry (`poetry`)
     3. Urdu + English code-mixing (`code_mixing`)
     4. Roman Urdu (`roman_urdu`)
     5. Numbers and dates (`numbers_dates`)
     6. Extensive diacritics / Aerab (`diacritics`)
     7. Personal names (`personal_names`)
   - Compare tokens/word of our Urdu BPE vs **GPT-2** (`gpt2`) and **GPT-4o** (`o200k_base`) via `tiktoken`.
3. **Question 3: Failure Cases**:
   - Identify and document 3 inputs handled sub-optimally (e.g., heavily misspelled Roman Urdu, non-normalized Arabic ligatures, or rare Unicode control characters) with detailed linguistic and algorithmic explanations.

### Step 2: Final Report & Documentation
1. **`report.pdf`**:
   - Maximum 4 pages.
   - Tables and visualizations for Questions 1, 2, and 3, accompanied by 2–3 sentences of interpretation per question.
2. **`README.md`**:
   - Exact, reproducible commands to reproduce tokenizer training and corpus encoding from `corpus/train.txt`.
3. **Submission Archive Packaging**:
   - Code: `normalize.py`, `bpe.py`, `train_tokenizer.py`, `encode_corpus.py`, `scraping/`, `scripts/`, `tests/`.
   - Data artifacts: `tokenizer.json`, `DATA_CARD.md`, `README.md`, `report.pdf`.
   - Shared Drive links for large binary files: `train.txt`, `val.txt`, `test.txt`, `train.bin`, `val.bin`.

---

## 🛠️ Quick Command Reference

```powershell
# 1. Run all unit test suites
python tests/test_normalize.py
python tests/test_bpe.py

# 2. Re-train tokenizer from scratch (if needed)
python train_tokenizer.py --input corpus/train.txt --vocab-size 50000 --output tokenizer.json --log-interval 5000

# 3. Re-encode datasets to flat uint16 binaries (if needed)
python encode_corpus.py --tokenizer tokenizer.json --train-in corpus/train.txt --val-in corpus/val.txt --train-out data/train.bin --val-out data/val.bin

# 4. Check status and file sizes
python -c "import numpy as np, os; t=np.fromfile('data/train.bin', dtype=np.uint16); v=np.fromfile('data/val.bin', dtype=np.uint16); print(f'Train: {len(t):,} tokens ({os.path.getsize(\"data/train.bin\")/(1024*1024):.2f} MB)'); print(f'Val:   {len(v):,} tokens ({os.path.getsize(\"data/val.bin\")/(1024*1024):.2f} MB)')"
```
