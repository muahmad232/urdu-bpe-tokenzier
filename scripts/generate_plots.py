"""
Generate High-Quality Figures for Tokenizer Analysis Report
CS 417: Large Language Models · NUST SEECS · Spring 2026

Generates:
1. data/fig_tokens_per_word.png: Comparative bar chart of tokens/word across categories
2. data/fig_compression_ratio.png: Bytes per token (compression efficiency) comparison
3. data/fig_merges_progression.png: Merge sequence progression and token byte lengths
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JSON_PATH = os.path.join(PROJECT_ROOT, "data", "analysis_results.json")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def load_analysis_data():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def plot_tokens_per_word(data):
    """Bar chart comparing tokens per word on test set + 7 handpicked categories."""
    bench = data["comparative_benchmark"]
    test_set = bench["test_set"]
    handpicked = bench["handpicked_inputs"]

    categories = ["Test Set\n(5.23 MB)"]
    custom_vals = [test_set["custom"]["tokens_per_word"]]
    o200k_vals = [test_set["o200k_base"]["tokens_per_word"]]
    gpt2_vals = [test_set["gpt2"]["tokens_per_word"]]

    cat_labels = {
        "news": "News",
        "poetry": "Poetry",
        "code_mixing": "Code\nMixing",
        "roman_urdu": "Roman\nUrdu",
        "numbers_dates": "Numbers\n& Dates",
        "diacritics": "Diacritics\n(Aerab)",
        "personal_names": "Personal\nNames"
    }

    for cat_key, label in cat_labels.items():
        if cat_key in handpicked:
            m = handpicked[cat_key]["metrics"]
            categories.append(label)
            custom_vals.append(m["custom"]["tokens_per_word"])
            o200k_vals.append(m["o200k_base"]["tokens_per_word"])
            gpt2_vals.append(m["gpt2"]["tokens_per_word"])

    x = np.arange(len(categories))
    width = 0.26

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)

    rects1 = ax.bar(x - width, custom_vals, width, label="Custom Urdu BPE (Ours)", color="#1b5e20", edgecolor="#0e3311", linewidth=0.8)
    rects2 = ax.bar(x, o200k_vals, width, label="OpenAI o200k_base (GPT-4o)", color="#0288d1", edgecolor="#01579b", linewidth=0.8)
    rects3 = ax.bar(x + width, gpt2_vals, width, label="OpenAI GPT-2 (Baseline)", color="#d32f2f", edgecolor="#8e0000", linewidth=0.8)

    ax.set_ylabel("Tokens per Word (Lower is More Compact)", fontsize=11, fontweight="bold")
    ax.set_title("Comparative Tokenization Efficiency: Tokens per Word by Domain", fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=9.5)
    ax.legend(frameon=True, facecolor="#fafafa", edgecolor="#cccccc", fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    # Add value labels above bars for test set
    for rect in [rects1[0], rects2[0], rects3[0]]:
        height = rect.get_height()
        ax.annotate(f"{height:.2f}",
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    out_path = os.path.join(DATA_DIR, "fig_tokens_per_word.png")
    plt.savefig(out_path)
    plt.close()
    print(f"[Plot] Saved: {out_path}")


def plot_compression_ratio(data):
    """Bar chart comparing bytes per token (compression efficiency)."""
    ts = data["comparative_benchmark"]["test_set"]

    tokenizers = ["Custom Urdu BPE\n(50k Vocab)", "OpenAI o200k_base\n(200k Vocab)", "OpenAI GPT-2\n(50k Vocab)"]
    bytes_per_tok = [ts["custom"]["bytes_per_token"], ts["o200k_base"]["bytes_per_token"], ts["gpt2"]["bytes_per_token"]]
    colors = ["#2e7d32", "#0288d1", "#c62828"]

    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=300)
    bars = ax.bar(tokenizers, bytes_per_tok, color=colors, width=0.45, edgecolor="#333333", linewidth=1.0)

    ax.set_ylabel("Bytes per Token (Higher is More Compact)", fontsize=11, fontweight="bold")
    ax.set_title("Compression Efficiency on Urdu Test Corpus (Bytes / Token)", fontsize=12, fontweight="bold", pad=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"{h:.2f} B/tok",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

    # Add baseline annotation
    ax.text(0, bytes_per_tok[0] * 0.5, "5.24x more compact\nthan GPT-2", ha="center", va="center", color="white", fontweight="bold", fontsize=9.5)

    plt.tight_layout()
    out_path = os.path.join(DATA_DIR, "fig_compression_ratio.png")
    plt.savefig(out_path)
    plt.close()
    print(f"[Plot] Saved: {out_path}")


def plot_merges_progression():
    """Plots learned merge token byte lengths over iteration indices."""
    with open(os.path.join(PROJECT_ROOT, "tokenizer.json"), "r", encoding="utf-8") as f:
        tok_data = json.load(f)

    vocab = tok_data.get("vocab", {})
    merges = tok_data.get("merges", [])

    # Sample merge byte lengths across every 100 merges
    sampled_indices = []
    sampled_lens = []
    for idx, item in enumerate(merges):
        if idx % 100 == 0 or idx == len(merges) - 1:
            token_id = str(item["id"])
            token_str = vocab.get(token_id, "")
            byte_len = len(token_str.encode("utf-8"))
            sampled_indices.append(idx + 1)
            sampled_lens.append(byte_len)

    fig, ax = plt.subplots(figsize=(8.5, 4.5), dpi=300)
    ax.plot(sampled_indices, sampled_lens, color="#1565c0", linewidth=1.2, alpha=0.85)

    # Moving average trendline
    window = 30
    if len(sampled_lens) > window:
        moving_avg = np.convolve(sampled_lens, np.ones(window)/window, mode="valid")
        ax.plot(sampled_indices[window-1:], moving_avg, color="#e65100", linewidth=2.0, label=f"Trend (Window {window*100} merges)")

    ax.set_xlabel("Merge Iteration Index (1 to 49,743)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Token Length in UTF-8 Bytes", fontsize=10, fontweight="bold")
    ax.set_title("Progression of Learned Token Length Across BPE Training", fontsize=12, fontweight="bold", pad=10)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True, fontsize=9.5)

    # Annotate milestones
    ax.annotate("Early: 2-byte letter merges\n(e.g., ا, ی, ک, ر)",
                xy=(1, 2), xytext=(3000, 15),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=5),
                fontsize=8.5, fontweight="bold")

    ax.annotate("Late: Compound phrases &\nlong words (up to 30+ bytes)",
                xy=(45000, 20), xytext=(28000, 26),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=5),
                fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    out_path = os.path.join(DATA_DIR, "fig_merges_progression.png")
    plt.savefig(out_path)
    plt.close()
    print(f"[Plot] Saved: {out_path}")


def main():
    print("=" * 60)
    print("      GENERATING REPORT VISUALIZATIONS & PLOTS")
    print("=" * 60)
    data = load_analysis_data()
    plot_tokens_per_word(data)
    plot_compression_ratio(data)
    plot_merges_progression()
    print("=" * 60)
    print("ALL PLOTS GENERATED SUCCESSFULLY IN data/ DIRECTORY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
