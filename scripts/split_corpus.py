"""
Corpus Splitting Pipeline (scripts/split_corpus.py)
Implements Section 8 document-level splitting requirements:
- Splits by document (NOT by line).
- Fixed random seed (seed=42) for 100% deterministic reproducibility.
- Proportions: 98% train.txt, 1% val.txt, 1% test.txt.
- Every document is terminated with <|endoftext|>.
"""

import os
import sys
import glob
import random
from tqdm import tqdm

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CLEANED_DIR = os.path.join(PROJECT_ROOT, "corpus", "cleaned")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "corpus")

SEED = 42
TRAIN_RATIO = 0.98
VAL_RATIO = 0.01
TEST_RATIO = 0.01


def load_all_clean_documents():
    """Load all cleaned documents across all cleaned files."""
    cleaned_files = glob.glob(os.path.join(CLEANED_DIR, "*.txt"))
    all_documents = []

    print(f"[Split] Found {len(cleaned_files)} cleaned corpus files.")
    for fpath in cleaned_files:
        print(f"  Reading {os.path.basename(fpath)}...")
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        docs = content.split("<|endoftext|>")
        valid_docs = [d.strip() for d in docs if len(d.strip()) > 30]
        print(f"    Loaded {len(valid_docs):,} valid documents.")
        all_documents.extend(valid_docs)

    print(f"[Split] Total documents collected across all sources: {len(all_documents):,}")
    return all_documents


def split_and_save_documents(documents):
    """Shuffle with fixed seed and write 98/1/1 splits."""
    random.seed(SEED)
    print(f"[Split] Shuffling {len(documents):,} documents with fixed seed={SEED}...")
    random.shuffle(documents)

    total = len(documents)
    n_train = int(total * TRAIN_RATIO)
    n_val = int(total * VAL_RATIO)
    n_test = total - n_train - n_val

    train_docs = documents[:n_train]
    val_docs = documents[n_train:n_train + n_val]
    test_docs = documents[n_train + n_val:]

    print(f"\n[Split] Split distribution:")
    print(f"  Train: {len(train_docs):,} docs ({len(train_docs)/total*100:.1f}%)")
    print(f"  Val:   {len(val_docs):,} docs ({len(val_docs)/total*100:.1f}%)")
    print(f"  Test:  {len(test_docs):,} docs ({len(test_docs)/total*100:.1f}%)")

    splits = [
        ("train.txt", train_docs),
        ("val.txt", val_docs),
        ("test.txt", test_docs),
    ]

    for fname, doc_list in splits:
        out_path = os.path.join(OUTPUT_DIR, fname)
        print(f"\n[Split] Writing {fname}...")
        written_bytes = 0
        with open(out_path, "w", encoding="utf-8") as f:
            for doc in tqdm(doc_list, desc=f"Writing {fname}"):
                payload = doc + "\n\n<|endoftext|>\n\n"
                f.write(payload)
                written_bytes += len(payload.encode("utf-8"))

        size_mb = written_bytes / (1024 * 1024)
        print(f"  Saved {out_path}: {size_mb:.2f} MB ({len(doc_list):,} docs)")


def main():
    print("=" * 70)
    print("             DOCUMENT-LEVEL CORPUS SPLITTING (98/1/1)")
    print("=" * 70)

    docs = load_all_clean_documents()
    if not docs:
        print("[Error] No cleaned documents found! Run scripts/clean_corpus.py first.")
        return

    split_and_save_documents(docs)
    print("\n" + "=" * 70)
    print("SPLITTING COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
