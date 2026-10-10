# Urdu BPE Tokenizer from Scratch

**Course**: CS 417: Large Language Models (Spring 2026)  
**Institution**: National University of Sciences and Technology (NUST), SEECS  
**CLO**: CLO 3 — Develop and apply LLM-based solutions for practical NLP problems using suitable interaction and adaptation strategies.

---

## 📌 Project Overview

This repository contains an end-to-end implementation of a **Byte-Pair Encoding (BPE) tokenizer for the Urdu language built entirely from scratch**, without relying on external tokenizer libraries (`minbpe`, `tokenizers`, `sentencepiece`) or external Urdu NLP packages (`urduhack`).

### Key Highlights
- **Corpus**: >600 MB raw text collected across 3 distinct sources and 2 genres (News/Op-eds, Classical Literature/Poetry, and Diverse Web Crawl). Includes **52.76 MB** self-scraped data (Daily Express, Daily Jang, BBC Urdu).
- **Cleaned Data**: **578.11 MB** total cleaned UTF-8 text (195,086 documents) partitioned with fixed seed 42 into `train.txt` (566.65 MB, 98%), `val.txt` (6.20 MB, 1%), and `test.txt` (5.26 MB, 1%).
- **Unicode Normalization**: Pure Python idempotent normalizer unifying Arabic lookalikes, strictly preserving Gol Heh (`ہ`) vs. Do-Chashmi Heh (`ھ`), stripping formatting artifacts (Tatweel, ZWJ, BOM, direction marks), and standardizing digits.
- **Tokenizer Architecture**: Byte-level BPE with 256 base byte tokens (`0–255`), `<|endoftext|>` special token (`256`), and 49,743 learned merges (`257–49,999`) totaling **50,000 tokens**.
- **Urdu Pre-Tokenization**: Regex pattern preserving Urdu letters, combining diacritics (`\p{M}`), and internal ZWNJ (`\u200C`) while attaching leading whitespace GPT-2 style.
- **Tie-Breaking**: Lexicographically greater integer tuple `(id1, id2)` ensuring 100% deterministic training.
- **Performance**: Stage 2 Fast BPE trained on 566 MB in **7m 05s** (116.96 merges/s) on standard 8-core CPU.
- **Compression**: Achieves **1.155 tokens per word** on the Urdu test set (**5.24x more compact than GPT-2**, and **1.38x more compact than GPT-4o's o200k_base**).

---

## 📁 Repository Structure

```text
urdu-bpe-tokenzier/
├── corpus/
│   ├── raw/                       # Self-scraped articles & downloaded public text
│   │   ├── scraped/               # Express (52.23 MB), Jang (0.33 MB), BBC (0.20 MB) + metadata.jsonl
│   │   └── public/                # Makhzan literature XMLs (47.82 MB) + streamed CC-100 (502.58 MB)
│   ├── cleaned/                   # Per-source normalized and deduplicated files
│   ├── train.txt                  # 98.0% split: 191,184 docs (566.65 MB, ~70.8M words)
│   ├── val.txt                    #  1.0% split:   1,950 docs (6.20 MB, ~775k words)
│   └── test.txt                   #  1.0% split:   1,952 docs (5.26 MB, ~657k words)
├── data/                          # Binary outputs and analysis artifacts
│   ├── train.bin                  # Flat NumPy uint16: 81,123,563 tokens (154.73 MB)
│   ├── val.bin                    # Flat NumPy uint16: 885,862 tokens (1.69 MB)
│   ├── analysis_results.json      # Structured empirical benchmark data
│   ├── analysis_summary.md        # Comprehensive markdown analysis report
│   ├── fig_tokens_per_word.png    # Tokens/word comparative bar chart
│   ├── fig_compression_ratio.png  # Compression efficiency bar chart
│   └── fig_merges_progression.png # Progression curve of learned token byte lengths
├── report/                        # Final PDF and styled HTML report
│   ├── report.pdf                 # Exact 4-page technical analysis report
│   └── report.html                # Print-styled report template
├── scraping/                      # Self-scraping scripts (evidence for >= 50 MB requirement)
│   ├── utils.py                   # Polite session, retries, Urdu text validator, JSONL logger
│   ├── scrape_express.py          # Daily Express multi-threaded scraper
│   ├── scrape_jang.py             # Daily Jang categories & columns scraper
│   ├── scrape_bbc.py              # BBC Urdu scraper
│   └── run_scrapers.py            # Master scraping runner
├── scripts/                       # Dataset processing and analysis tools
│   ├── download_public_corpus.py  # Streams CC-100 (lzma) & downloads Makhzan XMLs
│   ├── clean_corpus.py            # Normalizes, filters, and deduplicates raw text
│   ├── split_corpus.py            # Document-level 98/1/1 splitter with fixed seed 42
│   ├── check_corpus_stats.py      # Computes file sizes, word counts, and Urdu character ratios
│   ├── analyze_tokenizer.py       # Part C analysis & benchmark script (Questions 1, 2, 3)
│   ├── generate_plots.py          # Generates high-res comparison figures
│   └── generate_report_pdf.py     # Compiles 4-page PDF via headless browser
├── tests/                         # Unit test suites
│   ├── test_normalize.py          # 14 tests for normalize.py + idempotency checks (PASS)
│   └── test_bpe.py                # 10 tests for bpe.py, tie-breaking, equivalence & roundtrip (PASS)
├── normalize.py                   # Pure Python Urdu Unicode normalizer (Assignment Deliverable)
├── bpe.py                         # BPETokenizer class from scratch (Assignment Deliverable)
├── train_tokenizer.py             # CLI training runner with hardware profiling (Assignment Deliverable)
├── encode_corpus.py               # Streaming uint16 binary encoder with word cache (Assignment Deliverable)
├── tokenizer.json                 # Complete 50,000-token tokenizer with 49,743 merges (Assignment Deliverable)
├── report.pdf                     # Final 4-page analysis report (Root Deliverable)
├── DATA_CARD.md                   # 1-page data documentation as required by rubric
├── ASSIGNMENT_CONTEXT.md          # Master rules & constraints guardrail document
├── PROJECT_HANDOFF.md             # Development handoff notes & milestones
├── requirements.txt               # Locked dependencies
└── .gitignore                     # Ignores .venv, binary data, and large caches
```

---

## 🚀 Reproduction Instructions

To reproduce all results, train the tokenizer from `corpus/train.txt`, encode binary files, and generate the analysis report:

### 1. Environment Setup
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # Windows (.venv/bin/activate on Linux/macOS)

# Install locked dependencies
pip install -r requirements.txt
```

### 2. Verify Unit Tests
```powershell
# Test Unicode normalization engine (14 tests)
python tests/test_normalize.py

# Test BPE tokenizer, lossless roundtrip & tie-breaking (10 tests)
python tests/test_bpe.py
```

### 3. (Optional) Re-run Data Collection & Preprocessing
```powershell
# Download public datasets (Makhzan & stream CC-100)
python scripts/download_public_corpus.py --cc100-mb 500.0

# Run scrapers for >= 50 MB self-collected data
python scraping/run_scrapers.py --express-mb 52.0

# Clean, normalize, and deduplicate
python scripts/clean_corpus.py

# Split by document into 98% train, 1% val, 1% test (seed 42)
python scripts/split_corpus.py

# Audit corpus statistics
python scripts/check_corpus_stats.py
```

### 4. Train Tokenizer on `corpus/train.txt` (50,000 Tokens)
```powershell
python train_tokenizer.py --input corpus/train.txt --vocab-size 50000 --output tokenizer.json --log-interval 5000
```
*Trained in 7 minutes 05 seconds on 8-core CPU. Saves all 49,743 merges to `tokenizer.json`.*

### 5. Encode Corpora to Flat `uint16` Binary Files
```powershell
python encode_corpus.py --tokenizer tokenizer.json --train-in corpus/train.txt --val-in corpus/val.txt --train-out data/train.bin --val-out data/val.bin
```
*Produces `data/train.bin` (81,123,563 tokens, 154.73 MB) and `data/val.bin` (885,862 tokens, 1.69 MB).*

### 6. Run Part C Analysis & Benchmarking
```powershell
# Run merges analysis and comparative benchmark vs GPT-2 and o200k_base
python scripts/analyze_tokenizer.py

# Generate comparison plots
python scripts/generate_plots.py

# Compile 4-page analysis report (PDF)
python scripts/generate_report_pdf.py
```

---

## 📊 Summary of Benchmark Results

| Metric | Custom Urdu BPE (Ours) | OpenAI o200k_base (GPT-4o) | OpenAI GPT-2 (Baseline) |
|---|---|---|---|
| **Vocabulary Budget** | **50,000 tokens** | 200,000 tokens | 50,257 tokens |
| **Total Test Tokens (`test.txt`)** | **749,843** | 1,038,413 | 3,928,540 |
| **Tokens per Word (Lower is Better)** | **1.155 tok/word** | 1.599 tok/word | 6.050 tok/word |
| **Compression (Bytes per Token)** | **7.320 B/tok** | 5.286 B/tok | 1.397 B/tok |
| **Relative Efficiency vs GPT-2** | **5.24x more compact** | 3.78x more compact | 1.00x (Baseline) |
| **Relative Efficiency vs o200k_base** | **1.38x more compact** | 1.00x | 0.26x |

### Domain Breakdown (Tokens / Word):
- **News**: **1.04** (Custom) vs 1.26 (o200k) vs 6.11 (GPT-2)
- **Poetry**: **1.14** (Custom) vs 1.68 (o200k) vs 5.65 (GPT-2)
- **Code-Mixing**: **1.31** (Custom) vs 1.58 (o200k) vs 5.42 (GPT-2)
- **Personal Names**: **1.15** (Custom) vs 1.73 (o200k) vs 5.81 (GPT-2)
- **Numbers & Dates**: **1.22** (Custom) vs 1.70 (o200k) vs 6.09 (GPT-2)
- **Classical Diacritics**: **3.57** (Custom) vs 5.79 (o200k) vs 9.29 (GPT-2)
- **Roman Urdu**: 2.64 (Custom) vs **1.68** (o200k) vs 2.11 (GPT-2) *(Expected out-of-domain case)*

---

## 📜 Compliance & Verification Checklist

- [x] **Zero Prohibited Libraries**: Pure Python implementation; no `minbpe`, `tokenizers`, `sentencepiece`, or `urduhack` used in tokenizer or normalizer.
- [x] **Vocabulary Specification**: Exactly 50,000 tokens. Base bytes 0–255, `<|endoftext|>` at 256, merges 257–49,999.
- [x] **Deterministic Tie-Breaking**: Implemented comparing integer tuples `(id1, id2)`.
- [x] **Lossless Invariant**: `decode(encode(text)) == text` verified across Unicode test cases.
- [x] **Corpus Volume**: `train.txt` is 566.65 MB (exceeds 500 MB minimum).
- [x] **Self-Scraped Volume**: 52.76 MB raw across 3 sources (exceeds 50 MB minimum).
- [x] **Binary Encoding**: Flat `uint16` NumPy arrays in `data/train.bin` and `data/val.bin`.
- [x] **Report**: `report.pdf` is strictly **4 pages** answering Questions 1, 2, and 3 with figures and interpretations.
