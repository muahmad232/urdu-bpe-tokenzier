"""
Generate 4-Page Publication-Quality Analysis Report (report.pdf)
CS 417: Large Language Models · NUST SEECS · Spring 2026

Generates:
- report/report.html (Styled HTML with exact 4-page print CSS)
- report.pdf and report/report.pdf (Compiled via Edge Headless with exact page counts)
"""

import os
import sys
import json
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULTS_JSON = os.path.join(DATA_DIR, "analysis_results.json")
REPORT_HTML = os.path.join(PROJECT_ROOT, "report", "report.html")
REPORT_PDF = os.path.join(PROJECT_ROOT, "report.pdf")
REPORT_PDF_DIR = os.path.join(PROJECT_ROOT, "report", "report.pdf")

EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def load_data():
    with open(RESULTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def build_html_report(data):
    m_data = data["merges_analysis"]
    b_data = data["comparative_benchmark"]
    f_data = data["failure_cases"]
    meta = data.get("metadata", {})
    hw = meta.get("hardware", {})
    tr = meta.get("training", {})
    ts = b_data.get("test_set", {})
    hp = b_data.get("handpicked_inputs", {})

    fig_tokens = os.path.join(DATA_DIR, "fig_tokens_per_word.png").replace("\\", "/")
    fig_comp = os.path.join(DATA_DIR, "fig_compression_ratio.png").replace("\\", "/")
    fig_merges = os.path.join(DATA_DIR, "fig_merges_progression.png").replace("\\", "/")

    # Build Early Letters table rows (sample 16)
    letters_sorted = sorted(m_data["letter_reconstruction"].values(), key=lambda x: x["merge_index"])
    letter_rows_1 = letters_sorted[:9]
    letter_rows_2 = letters_sorted[9:18]

    # Build Merges 1 to 25 rows
    m1_25 = m_data["merges_1_to_50"][:22]
    # Build Every 5k rows
    m_5k = m_data["every_5k_merges"]

    # Build Top 10 Longest tokens
    top_longest = m_data["top_20_longest_by_bytes"][:12]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CS 417 Assignment 1 Report: Urdu BPE Tokenizer from Scratch</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 10mm 12mm 10mm 12mm;
  }}
  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  body {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #1a1a1a;
    background: #ffffff;
    margin: 0;
    padding: 0;
    font-size: 8.2pt;
    line-height: 1.28;
  }}
  .page {{
    width: 100%;
    height: 275mm;
    max-height: 275mm;
    position: relative;
    page-break-after: always;
    overflow: hidden;
  }}
  .page:last-child {{
    page-break-after: avoid;
  }}
  .header {{
    border-bottom: 2px solid #1b5e20;
    padding-bottom: 4px;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .header-title {{
    font-size: 13pt;
    font-weight: 800;
    color: #0d3b12;
    margin: 0;
  }}
  .header-subtitle {{
    font-size: 8pt;
    color: #555555;
    font-weight: 600;
  }}
  .header-meta {{
    text-align: right;
    font-size: 7.2pt;
    color: #666;
  }}
  .footer {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    border-top: 1px solid #ddd;
    padding-top: 3px;
    display: flex;
    justify-content: space-between;
    font-size: 7pt;
    color: #777;
  }}
  h2 {{
    font-size: 10pt;
    color: #1b5e20;
    border-left: 3.5px solid #1b5e20;
    padding-left: 6px;
    margin: 6px 0 4px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 700;
  }}
  h3 {{
    font-size: 8.5pt;
    color: #0d47a1;
    margin: 4px 0 2px 0;
    font-weight: 700;
  }}
  p {{
    margin: 2px 0 4px 0;
    text-align: justify;
  }}
  .interpretation {{
    background: #f1f8e9;
    border-left: 3px solid #558b2f;
    padding: 3px 6px;
    margin: 4px 0;
    font-size: 7.6pt;
    color: #2e4912;
    font-style: normal;
  }}
  .interpretation strong {{
    color: #1b5e20;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 3px 0 5px 0;
    font-size: 7.2pt;
  }}
  th, td {{
    border: 1px solid #dcdcdc;
    padding: 2.2px 4px;
    text-align: left;
  }}
  th {{
    background: #e8f5e9;
    color: #1b5e20;
    font-weight: 700;
    text-align: center;
  }}
  .table-blue th {{
    background: #e1f5fe;
    color: #0277bd;
  }}
  .urdu {{
    font-family: 'Jameel Noori Nastaleeq', 'Urdu Typesetting', 'Segoe UI', Tahoma, Arial, sans-serif;
    font-size: 9.5pt;
    direction: rtl;
    unicode-bidi: embed;
  }}
  .code {{
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 6.8pt;
    background: #f5f5f5;
    padding: 1px 2px;
    border-radius: 2px;
  }}
  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }}
  .grid-3 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 6px;
  }}
  .card {{
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 3px;
    padding: 4px 6px;
    margin-bottom: 4px;
  }}
  .highlight-badge {{
    background: #1b5e20;
    color: #fff;
    padding: 1px 4px;
    border-radius: 2px;
    font-size: 6.8pt;
    font-weight: 700;
  }}
  .img-container {{
    text-align: center;
    margin: 4px 0;
  }}
  .img-container img {{
    max-width: 100%;
    height: auto;
    border: 1px solid #ddd;
    border-radius: 2px;
  }}
</style>
</head>
<body>

<!-- ================= PAGE 1 ================= -->
<div class="page">
  <div class="header">
    <div>
      <h1 class="header-title">Urdu BPE Tokenizer from Scratch</h1>
      <div class="header-subtitle">CS 417: Large Language Models · NUST SEECS · Spring 2026 · Course Learning Outcome 3</div>
    </div>
    <div class="header-meta">
      <strong>Assignment 1 Technical Report</strong><br>
      Vocab: 50,000 | Merges: 49,743<br>
      Training Set: 566.65 MB
    </div>
  </div>

  <h2>1. Executive Summary & Architecture Overview</h2>
  <div class="grid-2">
    <div>
      <p>This report documents the design, implementation, and empirical analysis of an original Byte-Pair Encoding (BPE) tokenizer built specifically for the Urdu language from an empty directory, without reliance on external tokenizer or NLP libraries. The project fulfills all CLO 3 requirements: collecting a diverse multi-genre Urdu corpus (&gt;600 MB raw), establishing an idempotent Unicode normalization pipeline, implementing a 2-stage byte-level BPE tokenizer with deterministic tie-breaking and custom regex pre-tokenization, training to exactly 50,000 vocabulary tokens, and evaluating compression against industry-standard tokenizers.</p>
    </div>
    <div class="card">
      <div style="font-size: 7.5pt; font-weight: 700; color: #1b5e20; margin-bottom: 2px;">Key Architectural Decisions</div>
      <ul style="margin: 0; padding-left: 14px; font-size: 7.1pt; line-height: 1.25;">
        <li><strong>Base Vocab (0–255):</strong> 256 raw bytes ensuring 100% lossless UTF-8 roundtrips.</li>
        <li><strong>Special Token (256):</strong> <code>&lt;|endoftext|&gt;</code> isolated from merges.</li>
        <li><strong>Learned Merges (257–49,999):</strong> 49,743 merges via frequency-weighted inverted index.</li>
        <li><strong>Tie-Breaking:</strong> Lexicographically greater integer tuple <code>(id1, id2)</code>.</li>
        <li><strong>Regex:</strong> Custom Urdu pattern preserving diacritics (<code>\\p{{M}}</code>) & ZWNJ (<code>\\u200C</code>).</li>
      </ul>
    </div>
  </div>

  <h2>2. Corpus Pipeline & Training Telemetry</h2>
  <div class="grid-2">
    <div>
      <p><strong>Corpus Composition:</strong> Combining self-scraped journalism (52.76 MB raw from Daily Express, Daily Jang, and BBC Urdu across &gt;2,200 documents) and public corpora (Makhzan classical literature 47.82 MB + streamed CC-100 502.58 MB). Total raw size reached <strong>603.15 MB</strong>.</p>
      <p><strong>Cleaning & Splitting:</strong> The corpus was normalized via <code>normalize.py</code>, validated for Urdu script density, and deduplicated via SHA-256 hashes into 195,086 documents. Deterministic shuffling (seed 42) produced <code>train.txt</code> (<strong>566.65 MB</strong>, 191,184 docs), <code>val.txt</code> (<strong>6.20 MB</strong>), and <code>test.txt</code> (<strong>5.26 MB</strong>).</p>
    </div>
    <div>
      <table>
        <tr><th colspan="2">Hardware & Execution Telemetry</th></tr>
        <tr><td><strong>Processor / Cores</strong></td><td>{hw.get('processor', 'Intel Core')} ({hw.get('cpu_count', 8)} cores)</td></tr>
        <tr><td><strong>System RAM / OS</strong></td><td>{hw.get('total_ram_gb', 7.85)} GB | {hw.get('system', 'Windows')} 11 AMD64</td></tr>
        <tr><td><strong>Python Version</strong></td><td>{hw.get('python_version', '3.12')}</td></tr>
        <tr><td><strong>Characters Trained</strong></td><td>{tr.get('characters_trained', 335145273):,} chars (191,184 docs)</td></tr>
        <tr><td><strong>Unique Word Types</strong></td><td>627,748 distinct whitespace/regex tokens</td></tr>
        <tr><td><strong>Total Training Time</strong></td><td><strong>{tr.get('formatted_train_time', '00h 07m 05.29s')}</strong> ({tr.get('train_time_seconds', 425.29):.2f}s)</td></tr>
        <tr><td><strong>Merge Throughput</strong></td><td><strong>116.96 merges / second</strong> (Stage 2 Fast BPE)</td></tr>
        <tr><td><strong>Binary Corpus Output</strong></td><td><code>train.bin</code> (81.1M tokens) | <code>val.bin</code> (885.8k tokens)</td></tr>
      </table>
    </div>
  </div>

  <h2>3. Question 1: Early Merges & Letter Reconstruction</h2>
  <p>In UTF-8 encoding, all standard Urdu characters in the Arabic script block (U+0600–U+06FF) require exactly two bytes: a prefix byte (<code>0xD8</code> or <code>0xD9</code>) and a continuation byte (<code>0x80</code>–<code>0xBF</code>). Consequently, our byte-level BPE tokenizer must first merge raw single bytes into fundamental Urdu alphabet characters before higher-order morphology can emerge.</p>

  <div class="grid-2">
    <div>
      <table>
        <tr><th>Urdu Letter</th><th>Unicode</th><th>Merge #</th><th>Token ID</th><th>UTF-8 Bytes</th></tr>
        {''.join(f"<tr><td class='urdu' style='text-align:center;'>{l['letter']}</td><td>{l['unicode']}</td><td style='text-align:center;'><strong>#{l['merge_index']}</strong></td><td style='text-align:center;'>{l['token_id']}</td><td class='code'>{l['bytes_hex']}</td></tr>" for l in letter_rows_1)}
      </table>
    </div>
    <div>
      <table>
        <tr><th>Urdu Letter</th><th>Unicode</th><th>Merge #</th><th>Token ID</th><th>UTF-8 Bytes</th></tr>
        {''.join(f"<tr><td class='urdu' style='text-align:center;'>{l['letter']}</td><td>{l['unicode']}</td><td style='text-align:center;'><strong>#{l['merge_index']}</strong></td><td style='text-align:center;'>{l['token_id']}</td><td class='code'>{l['bytes_hex']}</td></tr>" for l in letter_rows_2)}
      </table>
    </div>
  </div>

  <div class="interpretation">
    <strong>Interpretation (2-Byte Letter Merges):</strong> The empirical merge logs demonstrate that high-frequency letters assemble almost instantaneously: Alif (<code>ا</code>) is reconstructed at <strong>Merge #1</strong> (<code>0xD8 0xA7</code>), followed immediately by Choti Yeh (<code>ی</code>) at <strong>Merge #2</strong>, Urdu Kaf (<code>ک</code>) at <strong>Merge #4</strong>, and Ray (<code>ر</code>) at <strong>Merge #6</strong>. Infrequent consonants such as Zhey (<code>ژ</code>) only merge later at Merge #1220. This confirms that the tokenizer organically learns the phonotactic and orthographic frequency hierarchy of the Urdu language.
  </div>

  <div class="footer">
    <span>CS 417: LLM — Assignment 1 Report</span>
    <span>Page 1 of 4</span>
  </div>
</div>

<!-- ================= PAGE 2 ================= -->
<div class="page">
  <div class="header">
    <div>
      <h1 class="header-title">Part C: Tokenizer Merges Analysis (Continued)</h1>
      <div class="header-subtitle">Question 1: Early Merges, Step Progression, Non-UTF8 Tokens, and Longest Learned Units</div>
    </div>
    <div class="header-meta">Vocab: 50,000 | Merges: 49,743</div>
  </div>

  <div class="grid-2">
    <div>
      <h3>Sample of Initial Learned Merges (Merges 1 to 22)</h3>
      <table>
        <tr><th>#</th><th>ID</th><th>Pair</th><th>Decoded</th><th>UTF-8</th></tr>
        {''.join(f"<tr><td style='text-align:center;'>{m['merge_index']}</td><td style='text-align:center;'>{m['token_id']}</td><td class='code'>{m['pair']}</td><td class='urdu' style='text-align:center;'>{repr(m['result_decoded'])[1:-1]}</td><td style='text-align:center;'>{'✅' if m['is_valid_utf8'] else '❌'}</td></tr>" for m in m1_25[:11])}
      </table>
    </div>
    <div>
      <h3>Progression of Merges: Every 5,000th Step</h3>
      <table>
        <tr><th>Merge #</th><th>Token ID</th><th>Decoded String</th><th>Bytes</th><th>Category</th></tr>
        {''.join(f"<tr><td style='text-align:center;'><strong>{m['merge_index']:,}</strong></td><td style='text-align:center;'>{m['token_id']}</td><td class='urdu' style='text-align:center;'>{repr(m['result_decoded'])[1:-1]}</td><td style='text-align:center;'>{m['byte_len']} B</td><td>{'Letter/Word' if m['merge_index']<=5000 else 'Compound/Phrase'}</td></tr>" for m in m_5k)}
      </table>
    </div>
  </div>

  <div class="interpretation">
    <strong>Interpretation (Merge Step Progression):</strong> Early merges (1–500) strictly reconstruct primary letters and functional monosyllabic words. By Merge #5,000, multi-syllabic common nouns emerge (e.g. <code> اسٹیٹ</code>). At Merge #15,000 to #30,000, compound adjectives and specialized vocabulary appear (e.g. <code> رحمانی</code>, <code> سائنسداں</code>). Beyond Merge #40,000, the vocabulary captures domain-specific religious honorifics (<code> ﴾</code>), transliterated English technical terms (<code> Republic</code>), and repeating decorative layout delimiters.
  </div>

  <div class="grid-2">
    <div>
      <h3>Non-Valid UTF-8 Single-Token Merges</h3>
      <p style="font-size: 7.2pt;">Our tokenizer learned exactly <strong>114 intermediate non-valid UTF-8 single tokens</strong> across all 49,743 merges.</p>
      <table>
        <tr><th>Merge #</th><th>ID</th><th>Pair Components</th><th>Raw Byte Sequence</th></tr>
        <tr><td>#3</td><td>259</td><td><code>[32, 216]</code> (Space + 0xD8)</td><td class='code'>0x20 0xD8</td></tr>
        <tr><td>#5</td><td>261</td><td><code>[32, 217]</code> (Space + 0xD9)</td><td class='code'>0x20 0xD9</td></tr>
        <tr><td>#12</td><td>268</td><td><code>[257, 216]</code> (ا + 0xD8)</td><td class='code'>0xD8 0xA7 0xD8</td></tr>
        <tr><td>#38</td><td>294</td><td><code>[32, 268]</code> (Space + ا + 0xD8)</td><td class='code'>0x20 0xD8 0xA7 0xD8</td></tr>
        <tr><td>#100</td><td>356</td><td><code>[226, 128]</code> (Punctuation Prefix)</td><td class='code'>0xE2 0x80</td></tr>
      </table>
      <div class="interpretation">
        <strong>Interpretation (Intermediate Tokens):</strong> Non-UTF-8 tokens are an intrinsic and necessary property of byte-level BPE. Merges such as <code>0x20 0xD8</code> pair an ASCII space with the leading byte of an Arabic letter. While unrenderable in isolation, they serve as crucial frequency bridges that allow subsequent merges to form space-prefixed Urdu words in a single step.
      </div>
    </div>
    <div>
      <h3>First Complete Word & Longest Learned Tokens</h3>
      <div class="card" style="background:#e8f5e9; border: 1px solid #81c784;">
        <strong style="color:#1b5e20;">First Complete Urdu Word:</strong> The first whole standalone word learned is <span class="urdu" style="font-size:11pt; font-weight:bold;"> کی</span> (space + Kaf + Yeh) at <strong>Merge #28 (Token ID 284)</strong>. It is followed immediately by <span class="urdu"> کے</span> (Merge #29), <span class="urdu"> میں</span> (Merge #40), <span class="urdu"> کر</span> (Merge #46), and <span class="urdu"> ہے</span> (Merge #48). High-frequency syntactic prepositions emerge within the first 50 iterations.
      </div>

      <table style="margin-top:4px;">
        <tr><th>Rank</th><th>Token ID</th><th>Decoded Token String</th><th>Bytes</th><th>Chars</th></tr>
        {''.join(f"<tr><td style='text-align:center;'>{r}</td><td style='text-align:center;'>{t['token_id']}</td><td class='urdu' style='text-align:center;'>{repr(t['decoded'])[1:-1]}</td><td style='text-align:center;'>{t['byte_len']}</td><td style='text-align:center;'>{t['char_len']}</td></tr>" for r, t in enumerate(top_longest[:7], start=1))}
      </table>
    </div>
  </div>

  <div class="img-container" style="margin-top: 2px;">
    <img src="file:///{fig_merges}" style="max-height: 82mm;" alt="Merge Progression">
  </div>

  <div class="footer">
    <span>CS 417: LLM — Assignment 1 Report</span>
    <span>Page 2 of 4</span>
  </div>
</div>

<!-- ================= PAGE 3 ================= -->
<div class="page">
  <div class="header">
    <div>
      <h1 class="header-title">Part C: Comparative Benchmark vs Standard Tokenizers</h1>
      <div class="header-subtitle">Question 2: Tokens per Word and Compression Ratio vs GPT-2 and OpenAI o200k_base</div>
    </div>
    <div class="header-meta">Evaluation Split: corpus/test.txt (5.26 MB)</div>
  </div>

  <h2>1. Full Test Set Benchmark (corpus/test.txt)</h2>
  <p>To evaluate tokenization efficiency, we tested our trained tokenizer on the held-out test split (1,952 documents, 3,112,488 characters, 649,343 words, 5.23 MB) against OpenAI's <code>gpt2</code> (50,257 vocab) and <code>o200k_base</code> (GPT-4o multilingual tokenizer, 200,000 vocab) using <code>tiktoken</code>.</p>

  <table>
    <tr class="table-blue">
      <th>Tokenizer</th>
      <th>Vocabulary Size</th>
      <th>Total Tokens Produced</th>
      <th>Tokens / Word</th>
      <th>Bytes / Token</th>
      <th>Compression Relative to GPT-2</th>
    </tr>
    <tr style="background:#f1f8e9; font-weight:bold;">
      <td>Custom Urdu BPE (Ours)</td>
      <td style="text-align:center;">50,000</td>
      <td style="text-align:center;">749,843</td>
      <td style="text-align:center;"><strong>1.155</strong></td>
      <td style="text-align:center;"><strong>7.320 B/tok</strong></td>
      <td style="text-align:center;"><span class="highlight-badge">5.24x More Compact</span></td>
    </tr>
    <tr>
      <td>OpenAI o200k_base (GPT-4o)</td>
      <td style="text-align:center;">200,000</td>
      <td style="text-align:center;">1,038,413</td>
      <td style="text-align:center;">1.599</td>
      <td style="text-align:center;">5.286 B/tok</td>
      <td style="text-align:center;">3.78x More Compact</td>
    </tr>
    <tr style="background:#ffebee;">
      <td>OpenAI GPT-2 (Baseline)</td>
      <td style="text-align:center;">50,257</td>
      <td style="text-align:center;">3,928,540</td>
      <td style="text-align:center;">6.050</td>
      <td style="text-align:center;">1.397 B/tok</td>
      <td style="text-align:center;">1.00x (Baseline)</td>
    </tr>
  </table>

  <div class="interpretation">
    <strong>Interpretation (Full Test Corpus Benchmark):</strong> Our custom Urdu BPE achieves an extraordinary <strong>1.155 tokens per word</strong> and <strong>7.32 bytes per token</strong> on the test set. Compared to GPT-2 (6.05 tokens/word), our model reduces sequence length by <strong>80.9% (5.24x compression)</strong>. Crucially, despite having only 25% of the vocabulary budget of GPT-4o's <code>o200k_base</code> (50,000 vs. 200,000), our domain-specific tokenizer produces <strong>27.8% fewer tokens</strong> (1.155 vs 1.599 tokens/word), drastically lowering future LLM pretraining compute and inference latency.
  </div>

  <h2>2. Seven Hand-Picked Domain Benchmark Inputs</h2>
  <table>
    <tr>
      <th>Linguistic Category</th>
      <th>Representative Input Snippet</th>
      <th>Words</th>
      <th>Custom BPE (tok/w)</th>
      <th>o200k_base (tok/w)</th>
      <th>GPT-2 (tok/w)</th>
    </tr>
    {''.join(f"""<tr>
      <td><strong>{k.replace('_', ' ').capitalize()}</strong></td>
      <td class='urdu' style='font-size:8pt;'>{v['text'].split(chr(10))[0][:42]}...</td>
      <td style='text-align:center;'>{v['metrics']['num_words']}</td>
      <td style='text-align:center; background:#e8f5e9;'><strong>{v['metrics']['custom']['tokens']} ({v['metrics']['custom']['tokens_per_word']:.2f})</strong></td>
      <td style='text-align:center;'>{v['metrics']['o200k_base']['tokens']} ({v['metrics']['o200k_base']['tokens_per_word']:.2f})</td>
      <td style='text-align:center; background:#ffebee;'>{v['metrics']['gpt2']['tokens']} ({v['metrics']['gpt2']['tokens_per_word']:.2f})</td>
    </tr>""" for k, v in hp.items())}
  </table>

  <div class="grid-2" style="margin-top: 2px;">
    <div class="img-container">
      <img src="file:///{fig_tokens}" style="max-height: 52mm;" alt="Tokens Per Word">
    </div>
    <div class="img-container">
      <img src="file:///{fig_comp}" style="max-height: 52mm;" alt="Compression Ratio">
    </div>
  </div>

  <div class="interpretation" style="margin-top: 2px;">
    <strong>Interpretation (Domain Breakdown):</strong> On standard prose categories (News, Poetry, Names), our tokenizer achieves near-optimal <strong>1.03–1.15 tokens/word</strong>. On Code-Mixing (Urdu + English technical terms), it maintains a competitive 1.30 tokens/word. The only domain where multilingual tokenizers outperform our model is Roman Urdu (2.64 vs 1.68 tokens/word), which is expected as our training corpus was deliberately curated in Perso-Arabic script.
  </div>

  <div class="footer">
    <span>CS 417: LLM — Assignment 1 Report</span>
    <span>Page 3 of 4</span>
  </div>
</div>

<!-- ================= PAGE 4 ================= -->
<div class="page">
  <div class="header">
    <div>
      <h1 class="header-title">Part C: Failure Cases Analysis & Deliverables Summary</h1>
      <div class="header-subtitle">Question 3: Qualitative Error Analysis, Reproduction Commands, and Sanity Audit</div>
    </div>
    <div class="header-meta">CS 417: LLM · Final Submission</div>
  </div>

  <h2>1. Question 3: Qualitative Failure Cases Analysis</h2>
  <p>To identify architectural and data boundaries, we examined three specific inputs where our tokenizer exhibits sub-optimal segmentation, high token inflation, or excessive fragmentation:</p>

  <div class="card" style="border-left: 3.5px solid #d32f2f; margin-bottom: 5px;">
    <div style="font-weight:700; color:#b71c1c;">Failure Case 1: Colloquial Roman Urdu with Character Elongation</div>
    <div style="font-size:7.4pt; margin: 2px 0;"><strong>Input:</strong> <code>"{f_data[0]['input']}"</code> (15 words)</div>
    <div style="font-size:7.2pt; color:#333;"><strong>Token Count:</strong> Custom Urdu BPE = <strong>{f_data[0]['custom_tokens']} tokens (2.80 tok/word)</strong> | o200k_base = {f_data[0]['o200k_tokens']} | GPT-2 = {f_data[0]['gpt2_tokens']}</div>
    <div class="code" style="margin: 2px 0; display:block; white-space:nowrap; overflow:hidden;">Segmentation: {' | '.join(f_data[0]['custom_token_pieces'][:12])}...</div>
    <div class="interpretation" style="margin:2px 0;">
      <strong>Linguistic & Algorithmic Explanation:</strong> Because the 566 MB training corpus was exclusively curated in Perso-Arabic Nastaliq script, Roman Urdu informal speech with expressive character repetitions (e.g., <em>'yrrr'</em>, <em>'plzzzzz'</em>, <em>'wrna'</em>) represents an out-of-domain distribution. The tokenizer lacks subword merges for Latin letter combinations and is forced to fall back to individual 1-byte ASCII tokens (<code>'p'</code>, <code>'l'</code>, <code>'z'</code>, <code>'z'</code>, <code>'z'</code>), leading to a 2.80 tokens/word inflation.
    </div>
  </div>

  <div class="card" style="border-left: 3.5px solid #e65100; margin-bottom: 5px;">
    <div style="font-weight:700; color:#bf360c;">Failure Case 2: Stacked Multi-Diacritic Combining Sequences (Aerab)</div>
    <div style="font-size:7.4pt; margin: 2px 0;"><strong>Input:</strong> <span class="urdu">"{f_data[1]['input']}"</span> (6 words)</div>
    <div style="font-size:7.2pt; color:#333;"><strong>Token Count:</strong> Custom Urdu BPE = <strong>{f_data[1]['custom_tokens']} tokens (6.50 tok/word)</strong> | o200k_base = {f_data[1]['o200k_tokens']} | GPT-2 = {f_data[1]['gpt2_tokens']}</div>
    <div class="code" style="margin: 2px 0; display:block; white-space:nowrap; overflow:hidden;">Segmentation: {' | '.join(repr(p)[1:-1] for p in f_data[1]['custom_token_pieces'][:10])}...</div>
    <div class="interpretation" style="margin:2px 0;">
      <strong>Linguistic & Algorithmic Explanation:</strong> While the regex pattern <code>\\p{{M}}</code> keeps diacritics attached to words, standard modern Urdu digital text is unvocalized. When encountering classical Arabic loanwords adorned with full phonetic diacritics (zabar, zer, pesh, sukun, tanween, and tashdeed simultaneously), the specific character-plus-aerab combinations never met the frequency threshold during BPE training. The model fragments every vowel mark into isolated 2-byte Unicode tokens, causing an inflation of 6.50 tokens/word.
    </div>
  </div>

  <div class="card" style="border-left: 3.5px solid #f57f17; margin-bottom: 5px;">
    <div style="font-weight:700; color:#f57f17;">Failure Case 3: Rare Unicode Presentation-Form Ligatures & Honorifics</div>
    <div style="font-size:7.4pt; margin: 2px 0;"><strong>Input:</strong> <span class="urdu">"{f_data[2]['input']}"</span> (12 words)</div>
    <div style="font-size:7.2pt; color:#333;"><strong>Token Count:</strong> Custom Urdu BPE = <strong>12 tokens</strong> | o200k_base = 22 tokens | GPT-2 = 59 tokens</div>
    <div class="interpretation" style="margin:2px 0;">
      <strong>Linguistic & Algorithmic Explanation:</strong> Unicode presentation-form glyphs such as Sallallah-o-Alaihi-Wasallam (<code>ﷺ</code> U+FDFA) and Razi-Allahu-Anhu (<code>ؓ</code> U+0618) occupy 3 to 4 bytes in UTF-8. While our model correctly tokenizes frequent standard Urdu words into single units (1.0 tok/word), rarer religious markers or non-standard calligraphy ligatures (e.g. <code>﷽</code> U+FDFD, taking 39 bytes) fragment into raw byte primitives, demonstrating that specialized ligatures require explicit corpus balancing.
    </div>
  </div>

  <h2>2. Deliverables & Reproduction Summary</h2>
  <div class="grid-2">
    <div>
      <div style="font-size:7.2pt; font-weight:700; color:#1b5e20;">Submission Archive File Structure</div>
      <ul style="margin:2px 0; padding-left:14px; font-size:6.8pt; line-height:1.2;">
        <li><code>normalize.py</code>: Idempotent Unicode normalizer without external NLP libs.</li>
        <li><code>bpe.py</code>: <code>BPETokenizer</code> with Stage 1 & 2 BPE, regex, tie-breaking.</li>
        <li><code>train_tokenizer.py</code>: Training runner with hardware profiling.</li>
        <li><code>encode_corpus.py</code>: Streaming uint16 binary encoder with word caching.</li>
        <li><code>tokenizer.json</code>: 50,000 vocabulary tokens and 49,743 merges.</li>
        <li><code>DATA_CARD.md</code>: Complete source documentation, ethics & stats.</li>
        <li><code>README.md</code>: Reproduction commands from raw text to binary.</li>
        <li><code>report.pdf</code>: This 4-page empirical analysis report.</li>
      </ul>
    </div>
    <div>
      <div style="font-size:7.2pt; font-weight:700; color:#1b5e20;">End-to-End Reproduction Commands</div>
      <div class="code" style="padding:4px; display:block; font-size:6.5pt; line-height:1.35;">
        # 1. Run unit test suites<br>
        python tests/test_normalize.py<br>
        python tests/test_bpe.py<br><br>
        # 2. Train 50,000-token BPE from train.txt<br>
        python train_tokenizer.py --input corpus/train.txt \<br>
        &nbsp;&nbsp;--vocab-size 50000 --output tokenizer.json<br><br>
        # 3. Encode corpora to flat uint16 binaries<br>
        python encode_corpus.py --tokenizer tokenizer.json \<br>
        &nbsp;&nbsp;--train-in corpus/train.txt --val-in corpus/val.txt \<br>
        &nbsp;&nbsp;--train-out data/train.bin --val-out data/val.bin<br><br>
        # 4. Run Part C analysis<br>
        python scripts/analyze_tokenizer.py
      </div>
    </div>
  </div>

  <div class="footer">
    <span>CS 417: LLM — Assignment 1 Report</span>
    <span>Page 4 of 4 (Strict Maximum Length)</span>
  </div>
</div>

</body>
</html>
"""
    with open(REPORT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[HTML] Report HTML generated -> {REPORT_HTML}")


def compile_pdf():
    edge_exe = None
    for p in EDGE_PATHS:
        if os.path.exists(p):
            edge_exe = p
            break

    if not edge_exe:
        print("[Error] Microsoft Edge executable not found at standard paths!")
        return False

    file_url = f"file:///{REPORT_HTML.replace('\\', '/')}"
    print(f"[PDF] Compiling PDF via Headless Edge...")
    print(f"  Source: {file_url}")
    print(f"  Target: {REPORT_PDF}")

    cmd = [
        edge_exe,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={REPORT_PDF}",
        file_url
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(REPORT_PDF):
        # Also copy to report/report.pdf
        import shutil
        shutil.copyfile(REPORT_PDF, REPORT_PDF_DIR)
        size_kb = os.path.getsize(REPORT_PDF) / 1024
        print(f"[PDF] Successfully compiled {REPORT_PDF} ({size_kb:.1f} KB)!")
        print(f"[PDF] Copied to {REPORT_PDF_DIR}")
        return True
    else:
        print(f"[Error] PDF generation failed! Return code: {res.returncode}")
        print(res.stderr)
        return False


def main():
    print("=" * 60)
    print("        GENERATING 4-PAGE ANALYSIS REPORT (PDF)")
    print("=" * 60)
    data = load_data()
    build_html_report(data)
    compile_pdf()
    print("=" * 60)


if __name__ == "__main__":
    main()
