"""
Part C Tokenizer Analysis and Comparative Benchmarking Script
CS 417: Large Language Models · NUST SEECS · Spring 2026

Performs all empirical analyses required for Part C of the assignment:
1. Merges Analysis (Question 1):
   - Merges 1 to 50 decoded.
   - Every 5,000th merge thereafter (5,000, 10,000, ..., 45,000).
   - Early 2-byte Urdu letter rebuilding merges.
   - Non-valid UTF-8 intermediate single-token merges.
   - First complete Urdu word merge index.
   - Top 20 longest learned tokens.
2. Comparative Benchmark (Question 2):
   - Custom Urdu Tokenizer vs GPT-2 (gpt2) vs Multilingual (o200k_base) on corpus/test.txt.
   - 7 hand-picked test inputs across distinct linguistic genres.
3. Failure Cases (Question 3):
   - 3 specific inputs handled poorly with explanations.

Outputs:
- data/analysis_results.json (structured data for report tables & plots)
- data/analysis_summary.md (human-readable markdown summary)
"""

import os
import sys
import json
import time
import regex
import tiktoken
from typing import Dict, List, Tuple, Any

# Ensure project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bpe import BPETokenizer, SPECIAL_TOKEN, SPECIAL_TOKEN_ID


# ---------------------------------------------------------------------------
# Urdu Alphabet Definitions for 2-Byte Letter Analysis
# ---------------------------------------------------------------------------
# Standard Urdu alphabet characters in UTF-8
URDU_LETTERS = {
    'ا': '\u0627', 'آ': '\u0622', 'ب': '\u0628', 'پ': '\u067E',
    'ت': '\u062A', 'ٹ': '\u0679', 'ث': '\u062B', 'ج': '\u062C',
    'چ': '\u0686', 'ح': '\u062D', 'خ': '\u062E', 'د': '\u062F',
    'ڈ': '\u0688', 'ذ': '\u0630', 'ر': '\u0631', 'ڑ': '\u0691',
    'ز': '\u0632', 'ژ': '\u0698', 'س': '\u0633', 'ش': '\u0634',
    'ص': '\u0635', 'ض': '\u0636', 'ط': '\u0637', 'ظ': '\u0638',
    'ع': '\u0639', 'غ': '\u063A', 'ف': '\u0641', 'ق': '\u0642',
    'ک': '\u06A9', 'گ': '\u06AF', 'ل': '\u0644', 'م': '\u0645',
    'ن': '\u0646', 'ں': '\u06BA', 'و': '\u0648', 'ہ': '\u06C1',
    'ھ': '\u06BE', 'ء': '\u0621', 'ی': '\u06CC', 'ے': '\u06D2',
}

# ---------------------------------------------------------------------------
# 7 Hand-Picked Test Inputs for Question 2
# ---------------------------------------------------------------------------
BENCHMARK_TEST_INPUTS = {
    "news": (
        "قومی اسمبلی میں آئینی ترمیم کے حوالے سے گرما گرم بحث جاری ہے اور حکومت نے تمام اتحادی جماعتوں کو اعتماد میں لینے کا فیصلہ کیا ہے۔"
    ),
    "poetry": (
        "ہزاروں خواہشیں ایسی کہ ہر خواہش پہ دم نکلے\nبہت نکلے مرے ارمان لیکن پھر بھی کم نکلے\nنکلنا خلد سے آدم کا سنتے آئے ہیں لیکن\nبہت بے آبرو ہو کر ترے کوچے سے ہم نکلے"
    ),
    "code_mixing": (
        "آج کل کے دور میں Artificial Intelligence اور Deep Learning کے جدید ماڈلز کمپیوٹر سائنس اور سافٹ ویئر انجینئرنگ میں گیم چینجر ثابت ہو رہے ہیں۔"
    ),
    "roman_urdu": (
        "Mujhe lagta hai ke yeh naya machine learning model bohat acha perform karega lekin Roman Urdu samajhne me thora masla ho sakta hai kyunki spelling mukhtalif hoti hai."
    ),
    "numbers_dates": (
        "پاکستان کا قیام ۱۵ اگست ۱۹۴۷ کو عمل میں آیا تھا، اور ۲۰۲۶ میں شرح نمو تقریباً ۴.۵ فیصد رہنے کی توقع ہے۔"
    ),
    "diacritics": (
        "اَلْحَمْدُ لِلّٰهِ رَبِّ الْعٰلَمِیْنَ۔ قَطْرَۂ نِیسَاں اَزْ بَحْرِ وُجُودْ و عِشْقِ حَقِیقِی زِنْدَہ بَاد۔"
    ),
    "personal_names": (
        "ڈاکٹر علامہ محمد اقبال، مرزا اسد اللہ خان غالب، خواجہ میر درد، اور سید احمد خان برصغیر پاک و ہند کی تاریخ کے درخشاں ستارے ہیں۔"
    )
}

# ---------------------------------------------------------------------------
# 3 Specific Failure Cases for Question 3
# ---------------------------------------------------------------------------
FAILURE_CASES = [
    {
        "category": "Irregular Roman Urdu Slang",
        "input": "yrrr plzzzzz mujhy btao ye assignment kb tk submit krwani h wrna scene off hojana",
        "explanation": "Because the 566 MB training corpus consists strictly of Perso-Arabic Nastaliq script, colloquial Roman Urdu words with character repetitions ('yrrr', 'plzzzzz', 'kb tk', 'wrna') are completely absent from the vocabulary. Each letter is fragmented into individual single-byte ASCII tokens, causing extreme token inflation."
    },
    {
        "category": "Complex Multi-Diacritic Combining Sequences",
        "input": "مُسْتَشْفَیَاتٌ (Mustashfayatun) بِالْإِضَافَةِ إِلَى تَسْخِیرِ الطَّاقَاتِ",
        "explanation": "Rare Arabic loanwords adorned with full vowel diacritics (zabar, zer, pesh, sukun, tanween, tashdeed) in stacked combinations break whole-word merges. Since normal training text rarely retains exhaustive aerab, the tokenizer falls back to splitting every diacritic mark into its 2-byte Unicode representation."
    },
    {
        "category": "Rare Arabic Honorific Ligatures & Archaic Glyphs",
        "input": "نبی کریم ﷺ اور صحابہ کرام ؓ و ؑ کے ارشادات مبارکہ",
        "explanation": "Special Unicode presentation-form ligatures like Sallallah-o-Alaihi-Wasallam (ﷺ U+FDFA) and Razi-Allahu-Anhu (ؓ U+0618 / ؑ U+0619) require 3 to 4 bytes in UTF-8. Because these characters are sparse relative to plain text equivalents, they fail to form single unified tokens and fragment into isolated byte fragments."
    }
]


def decode_token_safe(vocab_bytes: Dict[int, bytes], token_id: int) -> Tuple[str, bool, str]:
    """
    Safely decodes a token ID.
    Returns: (decoded_text_or_hex, is_valid_utf8, hex_representation)
    """
    if token_id == SPECIAL_TOKEN_ID:
        return SPECIAL_TOKEN, True, "<special>"
    raw = vocab_bytes.get(token_id, b"")
    hex_repr = " ".join(f"0x{b:02X}" for b in raw)
    try:
        text = raw.decode("utf-8")
        return text, True, hex_repr
    except UnicodeDecodeError:
        # Fallback representation showing byte escapes
        escaped = "".join(f"\\x{b:02x}" for b in raw)
        return escaped, False, hex_repr


def analyze_merges(tok: BPETokenizer) -> Dict[str, Any]:
    """Analyzes the learned merges in tokenizer.json to answer Question 1."""
    print("\n[Analysis] Running Merges Analysis (Question 1)...")
    merges_list = tok.merges_list
    vocab_bytes = tok.vocab_bytes

    # 1. Merges 1 to 50
    merges_1_to_50 = []
    for idx, (pair, new_id) in enumerate(merges_list[:50], start=1):
        dec_text, is_valid, hex_repr = decode_token_safe(vocab_bytes, new_id)
        p0_text, _, _ = decode_token_safe(vocab_bytes, pair[0])
        p1_text, _, _ = decode_token_safe(vocab_bytes, pair[1])
        merges_1_to_50.append({
            "merge_index": idx,
            "token_id": new_id,
            "pair": list(pair),
            "pair_decoded": [p0_text, p1_text],
            "result_decoded": dec_text,
            "is_valid_utf8": is_valid,
            "hex": hex_repr,
            "byte_len": len(vocab_bytes.get(new_id, b""))
        })

    # 2. Every 5,000th merge
    every_5k_merges = []
    step = 5000
    for idx in range(step, len(merges_list) + 1, step):
        pair, new_id = merges_list[idx - 1]
        dec_text, is_valid, hex_repr = decode_token_safe(vocab_bytes, new_id)
        every_5k_merges.append({
            "merge_index": idx,
            "token_id": new_id,
            "pair": list(pair),
            "result_decoded": dec_text,
            "is_valid_utf8": is_valid,
            "hex": hex_repr,
            "byte_len": len(vocab_bytes.get(new_id, b""))
        })

    # 3. Early merges rebuilding 2-byte Urdu letters
    letter_reconstruction = {}
    for letter_name, char in URDU_LETTERS.items():
        char_bytes = char.encode("utf-8")
        if len(char_bytes) == 2:
            # Look for the merge that produced this exact 2-byte sequence
            b0, b1 = char_bytes[0], char_bytes[1]
            for idx, (pair, new_id) in enumerate(merges_list, start=1):
                if pair == (b0, b1):
                    letter_reconstruction[char] = {
                        "letter": char,
                        "merge_index": idx,
                        "token_id": new_id,
                        "bytes_hex": f"0x{b0:02X} 0x{b1:02X}",
                        "unicode": f"U+{ord(char):04X}"
                    }
                    break

    # 4. Non-valid UTF-8 single-token merges
    invalid_utf8_merges = []
    for idx, (pair, new_id) in enumerate(merges_list, start=1):
        raw = vocab_bytes.get(new_id, b"")
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            p0_text, _, _ = decode_token_safe(vocab_bytes, pair[0])
            p1_text, _, _ = decode_token_safe(vocab_bytes, pair[1])
            invalid_utf8_merges.append({
                "merge_index": idx,
                "token_id": new_id,
                "pair": list(pair),
                "pair_decoded": [p0_text, p1_text],
                "byte_len": len(raw),
                "hex": " ".join(f"0x{b:02X}" for b in raw)
            })

    # 5. First complete Urdu word
    # A complete word in GPT-2 style pre-tokenization is preceded by space, or starts after space
    # and consists of whole letters. e.g. " کے", " میں", " ہے", " اور", " کی"
    first_word_info = None
    common_urdu_words = {
        " کے", " میں", " ہے", " اور", " کی", " کا", " سے", " کو", " پر", " نہیں",
        " ہیں", " بھی", " تو", " تھا", " تھی", " تھے", " نے", " یہ", " وہ", " جو"
    }
    for idx, (pair, new_id) in enumerate(merges_list, start=1):
        raw = vocab_bytes.get(new_id, b"")
        try:
            decoded = raw.decode("utf-8")
            if decoded in common_urdu_words or (decoded.startswith(" ") and len(decoded.strip()) >= 2 and all('\u0600' <= c <= '\u06FF' for c in decoded.strip())):
                first_word_info = {
                    "merge_index": idx,
                    "token_id": new_id,
                    "word": decoded,
                    "char_count": len(decoded),
                    "byte_len": len(raw),
                    "hex": " ".join(f"0x{b:02X}" for b in raw)
                }
                break
        except UnicodeDecodeError:
            continue

    # 6. Top 20 longest learned tokens (by UTF-8 byte length and by character length)
    learned_tokens = []
    for new_id in range(257, 50000):
        raw = vocab_bytes.get(new_id, b"")
        try:
            dec = raw.decode("utf-8")
            learned_tokens.append({
                "token_id": new_id,
                "decoded": dec,
                "byte_len": len(raw),
                "char_len": len(dec)
            })
        except UnicodeDecodeError:
            continue

    # Sort by byte length descending
    longest_by_bytes = sorted(learned_tokens, key=lambda x: (x["byte_len"], x["char_len"]), reverse=True)[:20]
    # Sort by character length descending
    longest_by_chars = sorted(learned_tokens, key=lambda x: (x["char_len"], x["byte_len"]), reverse=True)[:20]

    return {
        "merges_1_to_50": merges_1_to_50,
        "every_5k_merges": every_5k_merges,
        "letter_reconstruction": letter_reconstruction,
        "invalid_utf8_merges_count": len(invalid_utf8_merges),
        "invalid_utf8_merges_sample": invalid_utf8_merges[:15],
        "first_complete_word": first_word_info,
        "top_20_longest_by_bytes": longest_by_bytes,
        "top_20_longest_by_chars": longest_by_chars,
    }


def benchmark_comparative(tok: BPETokenizer, test_file_path: str) -> Dict[str, Any]:
    """Runs comparative benchmark against GPT-2 and o200k_base to answer Question 2."""
    print("\n[Analysis] Running Comparative Benchmark (Question 2)...")
    enc_gpt2 = tiktoken.get_encoding("gpt2")
    enc_o200k = tiktoken.get_encoding("o200k_base")

    # Helper function to compute metrics
    def compute_metrics(text: str) -> Dict[str, Any]:
        words = text.split()
        num_words = max(len(words), 1)
        num_chars = len(text)
        num_bytes = len(text.encode("utf-8"))

        tokens_custom = tok.encode(text, allowed_special=True)
        tokens_gpt2 = enc_gpt2.encode(text, allowed_special={"<|endoftext|>"})
        tokens_o200k = enc_o200k.encode(text, allowed_special={"<|endoftext|>"})

        len_custom = max(len(tokens_custom), 1)
        len_gpt2 = max(len(tokens_gpt2), 1)
        len_o200k = max(len(tokens_o200k), 1)

        return {
            "num_chars": num_chars,
            "num_bytes": num_bytes,
            "num_words": num_words,
            "custom": {
                "tokens": len_custom,
                "tokens_per_word": round(len_custom / num_words, 3),
                "bytes_per_token": round(num_bytes / len_custom, 3),
            },
            "gpt2": {
                "tokens": len_gpt2,
                "tokens_per_word": round(len_gpt2 / num_words, 3),
                "bytes_per_token": round(num_bytes / len_gpt2, 3),
            },
            "o200k_base": {
                "tokens": len_o200k,
                "tokens_per_word": round(len_o200k / num_words, 3),
                "bytes_per_token": round(num_bytes / len_o200k, 3),
            },
        }

    # 1. Benchmark on 7 hand-picked inputs
    test_inputs_results = {}
    for key, text in BENCHMARK_TEST_INPUTS.items():
        test_inputs_results[key] = {
            "text": text,
            "metrics": compute_metrics(text)
        }

    # 2. Benchmark on full corpus/test.txt (or sampled if massive)
    test_set_results = None
    if os.path.exists(test_file_path):
        print(f"  Reading test set from {test_file_path}...")
        with open(test_file_path, "r", encoding="utf-8", errors="replace") as f:
            test_text = f.read()
        print(f"  Benchmarking on full test set ({len(test_text):,} chars, {len(test_text.encode('utf-8'))/(1024*1024):.2f} MB)...")
        test_set_results = compute_metrics(test_text)
    else:
        print(f"  [Warning] Test file {test_file_path} not found.")

    return {
        "handpicked_inputs": test_inputs_results,
        "test_set": test_set_results
    }


def analyze_failure_cases(tok: BPETokenizer) -> List[Dict[str, Any]]:
    """Evaluates the 3 failure cases to answer Question 3."""
    print("\n[Analysis] Analyzing 3 Failure Cases (Question 3)...")
    enc_gpt2 = tiktoken.get_encoding("gpt2")
    enc_o200k = tiktoken.get_encoding("o200k_base")

    results = []
    for item in FAILURE_CASES:
        inp = item["input"]
        words = inp.split()
        num_words = max(len(words), 1)

        custom_tokens = tok.encode(inp, allowed_special=True)
        gpt2_tokens = enc_gpt2.encode(inp, allowed_special={"<|endoftext|>"})
        o200k_tokens = enc_o200k.encode(inp, allowed_special={"<|endoftext|>"})

        decoded_pieces = [tok.decode([t]) for t in custom_tokens]

        results.append({
            "category": item["category"],
            "input": inp,
            "explanation": item["explanation"],
            "num_words": num_words,
            "custom_tokens": len(custom_tokens),
            "custom_tokens_per_word": round(len(custom_tokens) / num_words, 2),
            "gpt2_tokens": len(gpt2_tokens),
            "o200k_tokens": len(o200k_tokens),
            "custom_token_pieces": decoded_pieces
        })

    return results


def format_markdown_report(merges_data: Dict[str, Any], bench_data: Dict[str, Any], failures: List[Dict[str, Any]]) -> str:
    """Formats all extracted analysis into clean GitHub Markdown with tables."""
    md = []
    md.append("# Tokenizer Analysis & Empirical Benchmarks")
    md.append("> CS 417: Large Language Models · NUST SEECS · Spring 2026\n")

    # Section 1: Question 1
    md.append("## Question 1: Merges Analysis\n")

    md.append("### 1.1 Merges 1 to 50")
    md.append("| Merge # | Token ID | Pair | Decoded Text | Valid UTF-8? | Hex Bytes |")
    md.append("|---|---|---|---|---|---|")
    for m in merges_data["merges_1_to_50"]:
        text_disp = repr(m["result_decoded"])[1:-1]
        md.append(f"| {m['merge_index']} | {m['token_id']} | `{m['pair']}` | `{text_disp}` | {'✅' if m['is_valid_utf8'] else '❌'} | `{m['hex']}` |")

    md.append("\n### 1.2 Every 5,000th Merge")
    md.append("| Merge # | Token ID | Pair | Decoded Text | Byte Length | Hex Bytes |")
    md.append("|---|---|---|---|---|---|")
    for m in merges_data["every_5k_merges"]:
        text_disp = repr(m["result_decoded"])[1:-1]
        md.append(f"| {m['merge_index']} | {m['token_id']} | `{m['pair']}` | `{text_disp}` | {m['byte_len']} | `{m['hex']}` |")

    md.append("\n### 1.3 Early Merges Rebuilding 2-Byte Urdu Letters")
    md.append("| Urdu Letter | Unicode | Merge # | Token ID | UTF-8 Byte Pair |")
    md.append("|---|---|---|---|---|")
    sorted_letters = sorted(merges_data["letter_reconstruction"].values(), key=lambda x: x["merge_index"])
    for l in sorted_letters:
        md.append(f"| {l['letter']} | `{l['unicode']}` | {l['merge_index']} | {l['token_id']} | `{l['bytes_hex']}` |")

    md.append("\n### 1.4 Non-Valid UTF-8 Single-Token Merges")
    md.append(f"- **Total Non-Valid UTF-8 Intermediate Merges**: {merges_data['invalid_utf8_merges_count']}")
    md.append("- **Interpretation**: These merges represent intermediate byte-pair steps where a high-frequency prefix byte (such as a leading space `0x20` or a first UTF-8 byte `0xD8`/`0xD9`) joins with an incomplete continuation byte. Because BPE is purely byte-level, these tokens serve as algorithmic stepping stones toward complete characters and words.")
    md.append("| Merge # | Token ID | Pair | Byte Length | Raw Hex |")
    md.append("|---|---|---|---|---|")
    for m in merges_data["invalid_utf8_merges_sample"]:
        md.append(f"| {m['merge_index']} | {m['token_id']} | `{m['pair']}` | {m['byte_len']} | `{m['hex']}` |")

    md.append("\n### 1.5 First Complete Urdu Word Merge")
    fw = merges_data["first_complete_word"]
    if fw:
        md.append(f"- **First Complete Word**: `{fw['word']}`")
        md.append(f"- **Merge Index**: **#{fw['merge_index']}** (Token ID `{fw['token_id']}`)")
        md.append(f"- **Byte Length**: {fw['byte_len']} bytes ({fw['hex']})")
        md.append(f"- **Interpretation**: The very first complete word merged is `{fw['word'].strip()}`, appearing at merge index #{fw['merge_index']}. This demonstrates that high-frequency Urdu functional prepositions and conjunctions are assembled immediately after basic 2-byte letter reconstruction.")

    md.append("\n### 1.6 Top 20 Longest Learned Tokens (by UTF-8 Bytes)")
    md.append("| Rank | Token ID | Decoded String | Byte Length | Character Length |")
    md.append("|---|---|---|---|---|")
    for rank, tok in enumerate(merges_data["top_20_longest_by_bytes"], start=1):
        md.append(f"| {rank} | {tok['token_id']} | `{repr(tok['decoded'])[1:-1]}` | {tok['byte_len']} | {tok['char_len']} |")

    # Section 2: Question 2
    md.append("\n## Question 2: Comparative Benchmark\n")
    ts = bench_data["test_set"]
    if ts:
        md.append("### 2.1 Full Test Set Benchmark (`corpus/test.txt`)")
        md.append(f"- **Total Test Volume**: {ts['num_chars']:,} characters, {ts['num_words']:,} words, {ts['num_bytes']/(1024*1024):.2f} MB")
        md.append("\n| Tokenizer | Total Tokens | Tokens / Word | Bytes / Token (Compression) | Compression vs GPT-2 |")
        md.append("|---|---|---|---|---|")
        c_tok, g_tok, o_tok = ts["custom"]["tokens"], ts["gpt2"]["tokens"], ts["o200k_base"]["tokens"]
        md.append(f"| **Custom Urdu BPE** | **{c_tok:,}** | **{ts['custom']['tokens_per_word']}** | **{ts['custom']['bytes_per_token']} B/tok** | **{g_tok/c_tok:.2f}x more compact** |")
        md.append(f"| **OpenAI o200k_base** | {o_tok:,} | {ts['o200k_base']['tokens_per_word']} | {ts['o200k_base']['bytes_per_token']} B/tok | {g_tok/o_tok:.2f}x more compact |")
        md.append(f"| **OpenAI GPT-2** | {g_tok:,} | {ts['gpt2']['tokens_per_word']} | {ts['gpt2']['bytes_per_token']} B/tok | 1.00x (Baseline) |")

    md.append("\n### 2.2 Seven Hand-Picked Benchmark Inputs")
    md.append("| Category | Input Description / Snippet | Words | Custom BPE (tok/word) | o200k_base (tok/word) | GPT-2 (tok/word) |")
    md.append("|---|---|---|---|---|---|")
    for cat, item in bench_data["handpicked_inputs"].items():
        m = item["metrics"]
        short_txt = item["text"].split("\n")[0][:45] + "..."
        md.append(f"| **{cat.capitalize()}** | {short_txt} | {m['num_words']} | **{m['custom']['tokens']}** ({m['custom']['tokens_per_word']}) | {m['o200k_base']['tokens']} ({m['o200k_base']['tokens_per_word']}) | {m['gpt2']['tokens']} ({m['gpt2']['tokens_per_word']}) |")

    # Section 3: Question 3
    md.append("\n## Question 3: Failure Cases Analysis\n")
    for i, fc in enumerate(failures, start=1):
        md.append(f"### 3.{i} Failure Case: {fc['category']}")
        md.append(f"- **Input String**: `{fc['input']}`")
        md.append(f"- **Word Count**: {fc['num_words']} words")
        md.append(f"- **Token Counts**: **Custom BPE = {fc['custom_tokens']} tokens** ({fc['custom_tokens_per_word']} tok/word) | o200k_base = {fc['o200k_tokens']} | GPT-2 = {fc['gpt2_tokens']}")
        md.append(f"- **Token Breakdown**: `{' | '.join(repr(p)[1:-1] for p in fc['custom_token_pieces'][:15])}`" + ("..." if len(fc['custom_token_pieces']) > 15 else ""))
        md.append(f"- **Analysis**: {fc['explanation']}\n")

    return "\n".join(md)


def main():
    print("=" * 70)
    print("       PART C TOKENIZER ANALYSIS & COMPARATIVE BENCHMARK")
    print("=" * 70)

    tokenizer_path = os.path.join(PROJECT_ROOT, "tokenizer.json")
    test_file_path = os.path.join(PROJECT_ROOT, "corpus", "test.txt")
    out_json = os.path.join(PROJECT_ROOT, "data", "analysis_results.json")
    out_md = os.path.join(PROJECT_ROOT, "data", "analysis_summary.md")

    if not os.path.exists(tokenizer_path):
        print(f"[Error] Tokenizer file not found at {tokenizer_path}!")
        return

    print(f"Loading tokenizer from {tokenizer_path}...")
    tok = BPETokenizer.from_file(tokenizer_path)
    print(f"Loaded BPETokenizer with {tok.vocab_size} vocabulary tokens.")

    # 1. Run Question 1
    merges_data = analyze_merges(tok)

    # 2. Run Question 2
    bench_data = benchmark_comparative(tok, test_file_path)

    # 3. Run Question 3
    failures_data = analyze_failure_cases(tok)

    # Read metadata from tokenizer JSON
    with open(tokenizer_path, "r", encoding="utf-8") as f:
        tok_json_data = json.load(f)
    tok_metadata = tok_json_data.get("metadata", {})

    # Save structured results
    full_results = {
        "merges_analysis": merges_data,
        "comparative_benchmark": bench_data,
        "failure_cases": failures_data,
        "metadata": tok_metadata
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(full_results, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved] Structured analysis JSON -> {out_json}")

    # Generate Markdown Summary
    md_content = format_markdown_report(merges_data, bench_data, failures_data)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[Saved] Markdown summary report -> {out_md}")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
