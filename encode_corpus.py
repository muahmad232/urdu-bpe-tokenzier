"""
Corpus Binary Encoding Pipeline
CS 417: Large Language Models · NUST SEECS · Spring 2026

Encodes Urdu text corpora (train.txt, val.txt) into flat NumPy uint16 binary files.
CLI Flags:
  --tokenizer: Path to tokenizer JSON file (default: 'tokenizer.json')
  --train-in: Path to input training text (default: 'corpus/train.txt')
  --val-in: Path to input validation text (default: 'corpus/val.txt')
  --train-out: Path to output training binary (default: 'data/train.bin')
  --val-out: Path to output validation binary (default: 'data/val.bin')
  --sample-mb: Process only sample MB for testing (default: 0.0, 0 = full file)
"""

import argparse
import os
import sys
import time
from typing import Optional
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from bpe import BPETokenizer, SPECIAL_TOKEN, SPECIAL_TOKEN_ID


def format_duration(seconds: float) -> str:
    """Formats duration in seconds to hh:mm:ss string."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}h {int(m):02d}m {s:05.2f}s"


def encode_file_to_binary(
    tokenizer: BPETokenizer,
    input_path: str,
    output_path: str,
    sample_mb: float = 0.0,
    buffer_tokens: int = 100_000,
) -> dict:
    """
    Streams and encodes a text file into a flat uint16 binary file.
    Uses word-level caching and direct special-token handling.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    file_size_bytes = os.path.getsize(input_path)
    max_bytes = int(sample_mb * 1024 * 1024) if sample_mb > 0 else file_size_bytes

    print(f"\n[Encoding] {input_path} -> {output_path}")
    print(f"  Target Data: {'Full file' if sample_mb <= 0 else f'{sample_mb:.2f} MB'} "
          f"({min(file_size_bytes, max_bytes) / (1024*1024):.2f} MB)")

    start_time = time.time()
    total_tokens = 0
    total_bytes_read = 0
    total_docs = 0
    token_buffer = []

    # Stream file in chunks, splitting on <|endoftext|>
    read_chunk_size = 1024 * 1024  # 1 MB read blocks
    remainder = ""

    with open(input_path, "r", encoding="utf-8", errors="replace") as fin, \
         open(output_path, "wb") as fout:

        while True:
            chunk = fin.read(read_chunk_size)
            if not chunk:
                break

            chunk_bytes = len(chunk.encode("utf-8"))
            total_bytes_read += chunk_bytes
            remainder += chunk

            if sample_mb > 0 and total_bytes_read >= max_bytes:
                break

            docs = remainder.split(SPECIAL_TOKEN)
            # Process all complete documents
            for doc in docs[:-1]:
                if doc:
                    doc_tokens = tokenizer.encode(doc, allowed_special=False)
                    token_buffer.extend(doc_tokens)
                token_buffer.append(SPECIAL_TOKEN_ID)
                total_docs += 1

                # Flush buffer to binary file when full
                if len(token_buffer) >= buffer_tokens:
                    arr = np.array(token_buffer, dtype=np.uint16)
                    fout.write(arr.tobytes())
                    total_tokens += len(token_buffer)
                    token_buffer.clear()

            remainder = docs[-1]

        # Flush any remaining text in buffer
        if remainder:
            docs = remainder.split(SPECIAL_TOKEN)
            for i, doc in enumerate(docs):
                if doc:
                    doc_tokens = tokenizer.encode(doc, allowed_special=False)
                    token_buffer.extend(doc_tokens)
                if i < len(docs) - 1:
                    token_buffer.append(SPECIAL_TOKEN_ID)
                    total_docs += 1

        if token_buffer:
            arr = np.array(token_buffer, dtype=np.uint16)
            fout.write(arr.tobytes())
            total_tokens += len(token_buffer)
            token_buffer.clear()

    elapsed = time.time() - start_time
    out_size_bytes = os.path.getsize(output_path)
    expected_bytes = total_tokens * 2  # 2 bytes per uint16

    # Validation: assert exact binary size
    assert out_size_bytes == expected_bytes, (
        f"File size mismatch: {out_size_bytes} bytes != {expected_bytes} bytes expected"
    )

    # Verification: read back a slice with NumPy
    verify_slice_len = min(10_000, total_tokens)
    verified_arr = np.fromfile(output_path, dtype=np.uint16, count=verify_slice_len)
    assert len(verified_arr) == verify_slice_len
    assert verified_arr.dtype == np.uint16
    if total_tokens > 0:
        assert int(verified_arr.max()) < tokenizer.vocab_size

    mb_read = total_bytes_read / (1024 * 1024)
    tokens_per_sec = total_tokens / elapsed if elapsed > 0 else 0
    mb_per_sec = mb_read / elapsed if elapsed > 0 else 0
    compression_ratio = total_bytes_read / total_tokens if total_tokens > 0 else 0

    print(f"  Processed {mb_read:.2f} MB in {format_duration(elapsed)} ({elapsed:.2f}s)")
    print(f"  Documents:         {total_docs:,}")
    print(f"  Total Tokens:      {total_tokens:,}")
    print(f"  Binary File Size:  {out_size_bytes / (1024*1024):.2f} MB")
    print(f"  Compression Ratio: {compression_ratio:.2f} bytes/token")
    print(f"  Throughput:        {tokens_per_sec:,.0f} tokens/s ({mb_per_sec:.2f} MB/s)")
    print(f"  Unique Cached:     {len(tokenizer.word_cache):,} words in cache")

    return {
        "input_path": input_path,
        "output_path": output_path,
        "total_docs": total_docs,
        "total_tokens": total_tokens,
        "bytes_read": total_bytes_read,
        "binary_size_bytes": out_size_bytes,
        "elapsed_seconds": round(elapsed, 2),
        "compression_ratio": round(compression_ratio, 3),
    }


def main():
    parser = argparse.ArgumentParser(description="Encode text corpus to flat uint16 binary files.")
    parser.add_argument("--tokenizer", type=str, default="tokenizer.json", help="Path to tokenizer JSON")
    parser.add_argument("--train-in", type=str, default="corpus/train.txt", help="Input train text")
    parser.add_argument("--val-in", type=str, default="corpus/val.txt", help="Input validation text")
    parser.add_argument("--train-out", type=str, default="data/train.bin", help="Output train binary")
    parser.add_argument("--val-out", type=str, default="data/val.bin", help="Output validation binary")
    parser.add_argument("--sample-mb", type=float, default=0.0, help="Sample MB for dry-run testing (0 = full)")

    args = parser.parse_args()

    print("=" * 70)
    print(" Urdu Corpus Binary Encoding Pipeline (NumPy uint16)")
    print("=" * 70)
    print(f" Tokenizer:   {args.tokenizer}")
    print(f" Train Split: {args.train_in} -> {args.train_out}")
    print(f" Val Split:   {args.val_in} -> {args.val_out}")
    print(f" Sample Mode: {'Full file' if args.sample_mb <= 0 else f'{args.sample_mb:.2f} MB'}")
    print("=" * 70)

    if not os.path.exists(args.tokenizer):
        print(f"ERROR: Tokenizer file '{args.tokenizer}' not found!", file=sys.stderr)
        sys.exit(1)

    print(f"[Loading Tokenizer] Loading from '{args.tokenizer}'...")
    tokenizer = BPETokenizer.from_file(args.tokenizer)
    print(f"  Loaded vocabulary of {tokenizer.vocab_size:,} tokens "
          f"({len(tokenizer.merges):,} merges).")

    # 1. Encode Training Split
    if os.path.exists(args.train_in):
        encode_file_to_binary(
            tokenizer=tokenizer,
            input_path=args.train_in,
            output_path=args.train_out,
            sample_mb=args.sample_mb,
        )
    else:
        print(f"Warning: Train input '{args.train_in}' does not exist, skipping.")

    # 2. Encode Validation Split
    if os.path.exists(args.val_in):
        # Val split is already small (~6.2 MB), so if sample-mb was set for testing, scale or use sample-mb
        encode_file_to_binary(
            tokenizer=tokenizer,
            input_path=args.val_in,
            output_path=args.val_out,
            sample_mb=args.sample_mb,
        )
    else:
        print(f"Warning: Val input '{args.val_in}' does not exist, skipping.")

    print("\n" + "=" * 70)
    print(" Corpus Encoding Pipeline Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
