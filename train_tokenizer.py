"""
BPE Tokenizer Training Script
CS 417: Large Language Models · NUST SEECS · Spring 2026

Trains a byte-level BPE tokenizer on the Urdu corpus using Stage 2 Fast BPE.
CLI Flags:
  --input: Path to training text file (default: 'corpus/train.txt')
  --vocab-size: Target vocabulary size (default: 50000)
  --output: Path to save trained tokenizer JSON (default: 'tokenizer.json')
  --sample-mb: MB of corpus to sample (default: 0.0, 0 = full file)
  --log-interval: Interval between merge progress logs (default: 5000)
"""

import argparse
import ctypes
import os
import platform
import sys
import time
from typing import Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from bpe import BPETokenizer, SPECIAL_TOKEN


def get_hardware_info() -> Dict[str, Any]:
    """Collects system hardware and execution environment specifications."""
    info = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
        "total_ram_gb": None,
    }

    # Attempt to read RAM using psutil or Windows ctypes
    try:
        import psutil
        info["total_ram_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except Exception:
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            info["total_ram_gb"] = round(stat.ullTotalPhys / (1024 ** 3), 2)
        except Exception:
            pass

    return info


def format_duration(seconds: float) -> str:
    """Formats duration in seconds to hh:mm:ss string."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}h {int(m):02d}m {s:05.2f}s"


def main():
    parser = argparse.ArgumentParser(description="Train Urdu BPE Tokenizer from scratch.")
    parser.add_argument("--input", type=str, default="corpus/train.txt", help="Input training text file")
    parser.add_argument("--vocab-size", type=int, default=50000, help="Target vocabulary size (default: 50000)")
    parser.add_argument("--output", type=str, default="tokenizer.json", help="Output tokenizer JSON path")
    parser.add_argument("--sample-mb", type=float, default=0.0, help="MB sample to train on (0 = full file)")
    parser.add_argument("--log-interval", type=int, default=5000, help="Progress logging interval for merges")

    args = parser.parse_args()

    print("=" * 70)
    print(" Urdu BPE Tokenizer Trainer (Stage 2 Fast BPE)")
    print("=" * 70)
    print(f" Input File:       {args.input}")
    print(f" Target Vocab:     {args.vocab_size:,}")
    print(f" Output File:      {args.output}")
    print(f" Sample Mode:      {'Full File' if args.sample_mb <= 0 else f'{args.sample_mb:.2f} MB'}")
    print("=" * 70)

    # 1. System Information
    hw_info = get_hardware_info()
    print("[Hardware Specifications]")
    print(f"  OS / Platform:   {hw_info['platform']}")
    print(f"  CPU / Processor: {hw_info['processor']} ({hw_info['cpu_count']} cores)")
    print(f"  Total RAM:       {hw_info['total_ram_gb']} GB")
    print(f"  Python:          {hw_info['python_version']}")
    print("-" * 70)

    if not os.path.exists(args.input):
        print(f"ERROR: Input file '{args.input}' not found!", file=sys.stderr)
        sys.exit(1)

    file_size_bytes = os.path.getsize(args.input)
    file_size_mb = file_size_bytes / (1024 * 1024)

    # 2. Reading Corpus
    print(f"[Loading Corpus] {args.input} (Total size: {file_size_mb:.2f} MB)...")
    load_start = time.time()

    if args.sample_mb > 0:
        sample_bytes = int(args.sample_mb * 1024 * 1024)
        with open(args.input, "r", encoding="utf-8", errors="replace") as f:
            corpus_text = f.read(sample_bytes)
        print(f"  Read sample: {len(corpus_text):,} characters ({len(corpus_text.encode('utf-8')) / (1024*1024):.2f} MB)")
    else:
        with open(args.input, "r", encoding="utf-8", errors="replace") as f:
            corpus_text = f.read()
        print(f"  Read full corpus: {len(corpus_text):,} characters ({file_size_mb:.2f} MB)")

    load_time = time.time() - load_start
    print(f"  Corpus loaded in {load_time:.2f}s.")

    # 3. Document statistics
    num_docs = corpus_text.count(SPECIAL_TOKEN)
    print(f"  Detected {num_docs:,} documents delimited by '{SPECIAL_TOKEN}'.")
    print("-" * 70)

    # 4. Tokenizer Training
    tokenizer = BPETokenizer(vocab_size=args.vocab_size)
    target_merges = args.vocab_size - 257

    interval = args.log_interval
    if target_merges < interval:
        interval = max(1, target_merges // 10)

    print(f"[Training BPE] Learning up to {target_merges:,} merges using Stage 2...")
    train_start = time.time()

    learned_merges = tokenizer.train_stage2(
        text=corpus_text,
        vocab_size=args.vocab_size,
        verbose=interval,
    )

    train_time = time.time() - train_start
    total_time = load_time + train_time

    print("-" * 70)
    print("[Training Complete]")
    print(f"  Learned Merges:    {len(learned_merges):,} / {target_merges:,}")
    print(f"  Final Vocab Size:  {tokenizer.vocab_size:,}")
    print(f"  Training Time:     {format_duration(train_time)} ({train_time:.2f}s)")
    print(f"  Total Wall-Clock:  {format_duration(total_time)} ({total_time:.2f}s)")
    if train_time > 0 and len(learned_merges) > 0:
        print(f"  Throughput:        {len(learned_merges) / train_time:.2f} merges/sec")
    print("-" * 70)

    # 5. Save Tokenizer with Hardware & Execution Metadata
    metadata = {
        "hardware": hw_info,
        "training": {
            "input_file": args.input,
            "sample_mb": args.sample_mb,
            "characters_trained": len(corpus_text),
            "documents_trained": num_docs,
            "target_vocab_size": args.vocab_size,
            "actual_vocab_size": tokenizer.vocab_size,
            "merges_count": len(learned_merges),
            "load_time_seconds": round(load_time, 3),
            "train_time_seconds": round(train_time, 3),
            "total_time_seconds": round(total_time, 3),
            "formatted_train_time": format_duration(train_time),
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    }

    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    print(f"[Saving Tokenizer] Saving to '{args.output}'...")
    tokenizer.save(args.output, metadata=metadata)
    out_size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"  Successfully saved {args.output} ({out_size_mb:.2f} MB).")
    print("=" * 70)


if __name__ == "__main__":
    main()
