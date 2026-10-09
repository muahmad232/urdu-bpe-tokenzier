# ASSIGNMENT CONTEXT — Urdu BPE Tokenizer from Scratch
> **Reference this file before making ANY decision or writing ANY code.**  
> Course: CS 417 Large Language Models · NUST SEECS · Spring 2026

---

## 1. ASSIGNMENT OBJECTIVE

Build a **Byte-Pair Encoding (BPE) tokenizer for Urdu** entirely from scratch:
- Collect and clean ≥ 500 MB of Urdu text corpus.
- Implement byte-level BPE in plain Python **without** any external tokenizer library.
- Train a vocabulary of exactly **50,000 tokens**.
- Analyze learned merges and benchmark against `gpt2` and `o200k_base` tokenizers.
- Write a ≤ 4-page analysis report.

---

## 2. HARD RULES & CONSTRAINTS

### ✅ ALLOWED Libraries
| Library | Allowed For |
|---|---|
| Python standard library | Everything |
| `regex` | Pre-tokenization pattern |
| `numpy` | Binary corpus encoding (`uint16`) |
| `tqdm` | Progress bars |
| `requests` | Web scraping |
| `beautifulsoup4` | HTML parsing |
| `tiktoken` | **Part C evaluation only** |
| `tokenizers` (HuggingFace) | **Part C evaluation only** |

### ❌ PROHIBITED Libraries (never use for tokenizer/normalizer)
- `tokenizers` (HuggingFace) — for training/encoding
- `sentencepiece`
- `tiktoken` — for training/encoding
- `minbpe`
- Any external Urdu NLP or normalization package

### ⚠️ Code Integrity
- Every line of tokenizer and normalizer must be **original student work**.
- A viva examination may be conducted to verify authorship.

---

## 3. VOCABULARY SPECIFICATION

| ID Range | Description |
|---|---|
| 0 – 255 | 256 raw byte values (base vocabulary) |
| 256 | `<|endoftext|>` special token — **never split, never merged** |
| 257 – 49,999 | 49,743 learned BPE merges (in order) |
| **Total** | **50,000 tokens** |

---

## 4. URDU NORMALIZATION RULES (mandatory in `normalize.py`)

| Issue | Action |
|---|---|
| Arabic yeh `ي` U+064A | → Urdu yeh `ی` U+06CC |
| Alef maksura `ى` U+0649 | → Urdu yeh `ی` U+06CC |
| Arabic kaf `ك` U+0643 | → Urdu kaf `ک` U+06A9 |
| Arabic heh `ه` U+0647 | → Gol heh `ہ` U+06C1 |
| Gol heh `ہ` U+06C1 | Keep as-is |
| Do-chashmi heh `ھ` U+06BE | Keep as-is (distinct from gol heh) |
| Tatweel `ـ` U+0640 | Remove entirely |
| ZWJ (U+200D) | Remove |
| Direction marks (LRM, RLM, etc.) | Remove |
| BOM (U+FEFF) | Remove |
| ZWNJ U+200C | **Decide and justify** (keep or remove — document choice) |
| Digits (Arabic/Persian/ASCII) | Standardize to one consistent convention (document choice) |
| Non-breaking spaces | Collapse to single space |
| Runs of spaces | Collapse to single space |
| Stray line breaks | Normalize to single newline |

---

## 5. PRE-TOKENIZATION REGEX CONSTRAINT

- Use Python's `regex` module (supports `\p{L}`, `\p{M}`, `\p{N}`).
- GPT-2's default regex **does not work** for Urdu — it breaks diacritics and ZWNJ.
- Design a **custom regex pattern** that:
  - Keeps Urdu words (with diacritics and optional ZWNJ) whole.
  - Attaches leading space to the following word (GPT-2 style).
  - Merges never cross word boundaries.

---

## 6. BPE TIE-BREAKING RULE

When two byte-pairs have the **exact same frequency**:
- Merge the **lexicographically greater** pair.
- Compare pairs as **tuples of integers** (byte values), not strings.
- This ensures 100% deterministic, reproducible training.

---

## 7. LOSSLESS PROPERTY

```
decode(encode(text)) == text
```
Must hold for **any** Unicode string: Urdu, English, emojis, newlines, empty string.
- Normalization lives **outside** the tokenizer; tokenizer itself is lossless.

---

## 8. CORPUS REQUIREMENTS

### Size & Split
| Split | File | Proportion |
|---|---|---|
| Train | `train.txt` | 98% |
| Validation | `val.txt` | 1% |
| Test | `test.txt` | 1% |

- Minimum **500 MB** total cleaned UTF-8 Urdu text (~50-60 million words).
- Aim for **1 GB** (corpus will be reused in Assignment 2).
- Split is **by document**, not by line. Use a **fixed random seed**.
- Append `<|endoftext|>` after **each document**.

### Source Requirements
- ≥ 3 sources, from ≥ 2 genres (news, encyclopedia, literature, blogs, etc.).
- ≥ 50 MB collected yourself via scraping/API — provide evidence.
- Rest from public datasets (Urdu Wikipedia dumps, UFAL, CC-100/OSCAR, Makhzan, etc.).
- Record **license and terms of use** for every source.

### Collection Rules
- Obey `robots.txt` and terms of use.
- Skip login/paywall content.
- No personal data (private messages, social media profiles).
- Keep corpus internal to course; do not republish unredistributable text.

### Cleaning Pipeline Steps (in order)
1. Extract plain text: strip HTML, wiki markup, menus, ads, share buttons.
2. Unicode normalization via `normalize(text)`.
3. Filter non-Urdu lines (retain natural English code-mixing in Urdu sentences).
4. Deduplicate exact document duplicates and boilerplate lines.
5. Split by document (98/1/1) with fixed seed.
6. Append `<|endoftext|>` per document.

---

## 9. BPE IMPLEMENTATION STAGES

### Stage 1 — Reference Version
- Recount **every pair** after every single merge.
- Verify correctness on sanity checks and a **1 MB sample** of corpus.

### Stage 2 — Fast Version (3 required optimizations)
1. **Word-frequency weighting**: Count each distinct word once; weight pair frequencies by word count.
2. **Inverted index**: Maintain a pair-to-words index; update only words containing the merged pair.
3. **Encoding cache**: Cache token IDs of encoded words during corpus encoding.
- **Report**: Wall-clock execution time + hardware specs.

---

## 10. CORPUS ENCODING OUTPUT

- Encode `train.txt` → `train.bin`
- Encode `val.txt` → `val.bin`
- Format: flat **NumPy array of `uint16`** values.

---

## 11. ANALYSIS REQUIREMENTS (Part C — report.pdf)

Max **4 pages**. Each answer: table/plot + 2-3 sentences of interpretation.

| Question | What to Show |
|---|---|
| Merges Analysis | Merges 1–50 decoded; every 5,000th merge thereafter; early 2-byte letter rebuilding merges; non-valid UTF-8 single-token merges; first complete word merge index; top 20 longest tokens |
| Comparative Benchmark | Tokens/word on `test.txt` + 7 hand-picked inputs (news, poetry, Urdu+English, Roman Urdu, numbers/dates, diacritics, personal names) vs. `gpt2` and `o200k_base` |
| Failure Cases | 3 inputs handled poorly by your tokenizer, with explanation |

---

## 12. REQUIRED FILES (Submission Archive)

| File | Description |
|---|---|
| `normalize.py` | Unicode normalization function |
| `bpe.py` | `BPETokenizer` class with encode/decode/train |
| `train_tokenizer.py` | Script to train tokenizer on corpus |
| `encode_corpus.py` | Script to encode text files to `.bin` |
| Scraping scripts | Evidence of 50 MB self-collected data |
| Cleaning scripts | Full cleaning pipeline |
| `tokenizer.json` (or similar) | Saved 49,743 merges in order |
| `DATA_CARD.md` | 1-page data documentation |
| `report.pdf` | ≤ 4 page analysis report |
| `README.md` | Exact commands to reproduce everything from `train.txt` |

### Shared Drive (large files)
- `train.txt`, `val.txt`, `test.txt`
- `train.bin`, `val.bin`

---

## 13. DATA CARD REQUIREMENTS (`DATA_CARD.md`)

Must include:
- **Source table**: URL, licence, collection date, raw size, cleaned size (per source).
- **Corpus totals**: Total MB, document count, word count, unique word count.
- **Cleaning step details**: What each step removed (volume of text).
- **Known gaps and biases**: Dominant genres, underrepresented topics, etc.

---

## 14. README REQUIREMENTS

- Exact shell commands to rebuild the tokenizer from `train.txt` from scratch.
- Must be reproducible without manual intervention.

---

## 15. QUICK SANITY CHECKLIST (verify before submission)

- [ ] `decode(encode(text)) == text` passes for all test strings.
- [ ] Vocabulary has exactly 50,000 tokens (IDs 0–49,999).
- [ ] `<|endoftext|>` is ID 256, never merged.
- [ ] Merges are deterministic (same input → same output every run).
- [ ] `train.bin` and `val.bin` are `uint16` NumPy flat arrays.
- [ ] No prohibited library imported in `normalize.py` or `bpe.py`.
- [ ] `DATA_CARD.md` covers all required fields.
- [ ] `report.pdf` is ≤ 4 pages.
- [ ] `README.md` commands are reproducible.
- [ ] At least 50 MB was self-scraped (with evidence in submission).
