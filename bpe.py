"""
Byte-Pair Encoding (BPE) Tokenizer for Urdu from Scratch
CS 417: Large Language Models · NUST SEECS · Spring 2026

Vocabulary Specification (50,000 total tokens):
- IDs 0–255: Raw byte values (base vocabulary).
- ID 256: `<|endoftext|>` special token (never split, never merged).
- IDs 257–49,999: Up to 49,743 learned merges in sequential order.

Key Features & Guardrails:
1. Lossless property: decode(encode(text)) == text for any Unicode string.
2. Custom Urdu pre-tokenization regex: preserves Urdu letters, combining diacritics
   (\\p{M}), internal morphological ZWNJ (\\u200C), numbers, and leading spaces.
3. Deterministic tie-breaking: on equal pair frequency, merges the lexicographically
   greater pair comparing them as integer tuples (id1, id2).
4. Stage 1 (Reference recount-all) and Stage 2 (Fast BPE with word-frequency weighting
   and pair-to-words inverted index).
5. Fast word-level token encoding cache during corpus encoding.
6. JSON serialization: save(path) and load(path).
"""

import json
import heapq
from typing import Dict, List, Optional, Set, Tuple, Union
import regex


# Default Urdu-aware pre-tokenization regex pattern.
# Supports Urdu letters with combining diacritics (\p{M}) and internal ZWNJ (\u200C),
# numbers, punctuation, and leading space attachment.
URDU_BPE_PATTERN = (
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?[\p{L}\p{M}]+(?:\u200c+[\p{L}\p{M}]+)*| ?\p{N}+| ?[^\s\p{L}\p{M}\p{N}]+|\s+(?!\S)|\s+"""
)

SPECIAL_TOKEN = "<|endoftext|>"
SPECIAL_TOKEN_ID = 256


def merge_word(tokens: List[int], pair: Tuple[int, int], new_id: int) -> List[int]:
    """
    Replaces non-overlapping, left-to-right occurrences of `pair` in `tokens` with `new_id`.
    """
    new_tokens: List[int] = []
    i = 0
    n = len(tokens)
    p0, p1 = pair
    while i < n:
        if i < n - 1 and tokens[i] == p0 and tokens[i + 1] == p1:
            new_tokens.append(new_id)
            i += 2
        else:
            new_tokens.append(tokens[i])
            i += 1
    return new_tokens


class BPETokenizer:
    """
    Byte-level BPE Tokenizer for Urdu from scratch.
    """

    def __init__(
        self,
        vocab_size: int = 50000,
        pattern: Optional[str] = None,
        special_token: str = SPECIAL_TOKEN,
        special_token_id: int = SPECIAL_TOKEN_ID,
    ):
        self.target_vocab_size = vocab_size
        self.pattern_str = pattern if pattern is not None else URDU_BPE_PATTERN
        self.compiled_pattern = regex.compile(self.pattern_str)
        self.special_token = special_token
        self.special_token_id = special_token_id

        # Merges stored as (pair) -> new_id and ordered list [(pair, new_id), ...]
        self.merges: Dict[Tuple[int, int], int] = {}
        self.merges_list: List[Tuple[Tuple[int, int], int]] = []

        # Byte representation per token ID
        self.vocab_bytes: Dict[int, bytes] = {}
        self.special_tokens: Dict[str, int] = {self.special_token: self.special_token_id}
        self.inverse_special_tokens: Dict[int, str] = {self.special_token_id: self.special_token}

        # Optimization 3: Word-level encoding cache
        self.word_cache: Dict[str, List[int]] = {}

        self._init_base_vocab()

    def _init_base_vocab(self) -> None:
        """Initializes raw byte tokens 0..255 and clears learned merges."""
        self.vocab_bytes = {i: bytes([i]) for i in range(256)}
        self.merges.clear()
        self.merges_list.clear()
        self.word_cache.clear()

    @property
    def vocab(self) -> Dict[int, Union[bytes, str]]:
        """Returns the full vocabulary mapping IDs to bytes or special token strings."""
        full_vocab: Dict[int, Union[bytes, str]] = dict(self.vocab_bytes)
        for token_str, token_id in self.special_tokens.items():
            full_vocab[token_id] = token_str
        return full_vocab

    @property
    def vocab_size(self) -> int:
        """Current total vocabulary size."""
        return len(self.vocab)

    def pre_tokenize(self, text: str) -> List[str]:
        """
        Splits text into words using the compiled pre-tokenization regex.
        Never splits across `<|endoftext|>`.
        """
        words = []
        parts = regex.split(r"(<\|endoftext\|>)", text)
        for part in parts:
            if part == self.special_token:
                words.append(part)
            elif part:
                words.extend(self.compiled_pattern.findall(part))
        return words

    def _set_merges(self, merges_list: List[Tuple[Tuple[int, int], int]]) -> None:
        """Configures merges and rebuilds byte vocabularies."""
        self._init_base_vocab()
        for pair, new_id in merges_list:
            self.merges[pair] = new_id
            self.merges_list.append((pair, new_id))
            p0, p1 = pair
            self.vocab_bytes[new_id] = self.vocab_bytes[p0] + self.vocab_bytes[p1]

    def train_stage1(
        self,
        text: str,
        vocab_size: Optional[int] = None,
        min_frequency: int = 1,
        verbose: bool = False,
    ) -> List[Tuple[Tuple[int, int], int]]:
        """
        Stage 1: Reference BPE implementation.
        Recounts all byte-pair frequencies across all words from scratch after every merge.
        Tie-breaking: on equal frequency, picks the lexicographically greater integer tuple.
        """
        target_size = vocab_size if vocab_size is not None else self.target_vocab_size
        max_merges = target_size - 257
        if max_merges <= 0:
            return []

        # Split on special token to ensure boundaries are never crossed
        docs = text.split(self.special_token)
        words_list: List[List[int]] = []
        for doc in docs:
            if not doc:
                continue
            for match in self.compiled_pattern.finditer(doc):
                w = match.group()
                words_list.append(list(w.encode("utf-8")))

        self._init_base_vocab()
        learned_merges: List[Tuple[Tuple[int, int], int]] = []
        next_id = 257

        for step in range(max_merges):
            # Recount all pairs from scratch across every word
            stats: Dict[Tuple[int, int], int] = {}
            for word in words_list:
                n = len(word)
                for i in range(n - 1):
                    p = (word[i], word[i + 1])
                    stats[p] = stats.get(p, 0) + 1

            if not stats:
                break

            # Deterministic tie-breaking: max frequency, then lexicographically greater tuple
            best_pair = max(stats.keys(), key=lambda p: (stats[p], p))
            if stats[best_pair] < min_frequency:
                break

            learned_merges.append((best_pair, next_id))
            self.merges[best_pair] = next_id
            p0, p1 = best_pair
            self.vocab_bytes[next_id] = self.vocab_bytes[p0] + self.vocab_bytes[p1]

            # Update words that contain p0
            for idx in range(len(words_list)):
                if p0 in words_list[idx]:
                    words_list[idx] = merge_word(words_list[idx], best_pair, next_id)

            if verbose and (step + 1) % 500 == 0:
                print(f"[Stage 1] Merge {step + 1}/{max_merges}: {best_pair} -> {next_id} (freq={stats[best_pair]})")

            next_id += 1

        self.merges_list = learned_merges
        self.word_cache.clear()
        return learned_merges

    def train_stage2(
        self,
        text: str,
        vocab_size: Optional[int] = None,
        min_frequency: int = 1,
        verbose: bool = False,
    ) -> List[Tuple[Tuple[int, int], int]]:
        """
        Stage 2: Fast BPE implementation with 3 core optimizations:
        1. Word-frequency weighting: Count distinct words once, weighting pairs by word frequency.
        2. Inverted index: Pair-to-words index updating only words containing the merged pair.
        3. Lazy max-heap: O(log K) extraction with deterministic tie-breaking.
        """
        target_size = vocab_size if vocab_size is not None else self.target_vocab_size
        max_merges = target_size - 257
        if max_merges <= 0:
            return []

        # 1. Pre-tokenize and aggregate word frequencies
        docs = text.split(self.special_token)
        word_freqs: Dict[str, int] = {}
        num_docs = len(docs)
        if verbose:
            print(f"  [Stage 2] Pre-tokenizing {num_docs:,} documents with custom regex...")

        for doc_idx, doc in enumerate(docs):
            if not doc:
                continue
            for match in self.compiled_pattern.finditer(doc):
                w = match.group()
                word_freqs[w] = word_freqs.get(w, 0) + 1
            if verbose and (doc_idx + 1) % 50000 == 0:
                print(f"  [Stage 2] Pre-tokenized {doc_idx + 1:,}/{num_docs:,} documents ({len(word_freqs):,} unique words)...")

        if verbose:
            print(f"  [Stage 2] Aggregated {len(word_freqs):,} unique words. Building inverted index...")

        # Represent distinct words as lists of token IDs and their weights
        word_tokens: List[List[int]] = []
        word_counts: List[int] = []
        for w, freq in word_freqs.items():
            word_tokens.append(list(w.encode("utf-8")))
            word_counts.append(freq)

        num_words = len(word_tokens)

        # 2. Build initial pair frequencies and inverted index
        pair_counts: Dict[Tuple[int, int], int] = {}
        pair_to_words: Dict[Tuple[int, int], Set[int]] = {}

        for w_idx in range(num_words):
            tokens = word_tokens[w_idx]
            freq = word_counts[w_idx]
            n = len(tokens)
            for i in range(n - 1):
                p = (tokens[i], tokens[i + 1])
                pair_counts[p] = pair_counts.get(p, 0) + freq
                if p not in pair_to_words:
                    pair_to_words[p] = set()
                pair_to_words[p].add(w_idx)

        # 3. Min-heap for max extraction: (-count, (-p0, -p1), pair)
        # This guarantees deterministic tie-breaking matching Stage 1 exactly.
        heap: List[Tuple[int, Tuple[int, int], Tuple[int, int]]] = []
        for p, count in pair_counts.items():
            heapq.heappush(heap, (-count, (-p[0], -p[1]), p))

        if verbose:
            print(f"  [Stage 2] Inverted index built ({len(pair_counts):,} pairs). Starting merges...")

        self._init_base_vocab()
        learned_merges: List[Tuple[Tuple[int, int], int]] = []
        next_id = 257

        for step in range(max_merges):
            # Extract current best pair from heap
            best_pair: Optional[Tuple[int, int]] = None
            best_count = 0
            while heap:
                neg_c, neg_p, p = heap[0]
                cur_c = pair_counts.get(p, 0)
                if cur_c == -neg_c:
                    best_pair = p
                    best_count = cur_c
                    break
                heapq.heappop(heap)

            if best_pair is None or best_count < min_frequency:
                break

            learned_merges.append((best_pair, next_id))
            self.merges[best_pair] = next_id
            p0, p1 = best_pair
            self.vocab_bytes[next_id] = self.vocab_bytes[p0] + self.vocab_bytes[p1]

            # Inverted index: update only words containing best_pair
            affected_words = pair_to_words.get(best_pair, set()).copy()

            pair_delta: Dict[Tuple[int, int], int] = {}
            pair_words_add: Dict[Tuple[int, int], List[int]] = {}
            pair_words_remove: Dict[Tuple[int, int], List[int]] = {}

            for w_idx in affected_words:
                tokens = word_tokens[w_idx]
                freq = word_counts[w_idx]
                n_old = len(tokens)

                # Count old pairs in word
                old_p_counts: Dict[Tuple[int, int], int] = {}
                for i in range(n_old - 1):
                    p = (tokens[i], tokens[i + 1])
                    old_p_counts[p] = old_p_counts.get(p, 0) + 1

                # Merge
                new_tokens = merge_word(tokens, best_pair, next_id)
                word_tokens[w_idx] = new_tokens
                n_new = len(new_tokens)

                # Count new pairs in word
                new_p_counts: Dict[Tuple[int, int], int] = {}
                for i in range(n_new - 1):
                    p = (new_tokens[i], new_tokens[i + 1])
                    new_p_counts[p] = new_p_counts.get(p, 0) + 1

                # Track pairs whose counts in this word changed
                affected_pairs = set(old_p_counts.keys()) | set(new_p_counts.keys())
                for p in affected_pairs:
                    c_old = old_p_counts.get(p, 0)
                    c_new = new_p_counts.get(p, 0)
                    if c_new != c_old:
                        pair_delta[p] = pair_delta.get(p, 0) + (c_new - c_old) * freq
                        if c_new > 0 and c_old == 0:
                            if p not in pair_words_add:
                                pair_words_add[p] = []
                            pair_words_add[p].append(w_idx)
                        elif c_new == 0 and c_old > 0:
                            if p not in pair_words_remove:
                                pair_words_remove[p] = []
                            pair_words_remove[p].append(w_idx)

            # Apply aggregated changes once per unique pair
            for p, diff in pair_delta.items():
                new_total = pair_counts.get(p, 0) + diff
                if new_total > 0:
                    pair_counts[p] = new_total
                    heapq.heappush(heap, (-new_total, (-p[0], -p[1]), p))
                else:
                    pair_counts.pop(p, None)

            for p, w_list in pair_words_add.items():
                if p not in pair_to_words:
                    pair_to_words[p] = set()
                pair_to_words[p].update(w_list)

            for p, w_list in pair_words_remove.items():
                if p in pair_to_words:
                    pair_to_words[p].difference_update(w_list)

            pair_to_words.pop(best_pair, None)
            pair_counts.pop(best_pair, None)

            interval = verbose if isinstance(verbose, int) and verbose > 0 else (500 if verbose else 0)
            if interval > 0 and (step + 1) % interval == 0:
                print(f"[Stage 2] Merge {step + 1}/{max_merges}: {best_pair} -> {next_id} (freq={best_count})")

            next_id += 1

        self.merges_list = learned_merges
        self.word_cache.clear()
        return learned_merges

    def train(
        self,
        text: str,
        vocab_size: Optional[int] = None,
        method: str = "fast",
        min_frequency: int = 1,
        verbose: bool = False,
    ) -> List[Tuple[Tuple[int, int], int]]:
        """
        Master training interface.
        method: 'fast' (Stage 2 default) or 'reference' (Stage 1).
        """
        if method == "fast":
            return self.train_stage2(
                text=text,
                vocab_size=vocab_size,
                min_frequency=min_frequency,
                verbose=verbose,
            )
        elif method == "reference":
            return self.train_stage1(
                text=text,
                vocab_size=vocab_size,
                min_frequency=min_frequency,
                verbose=verbose,
            )
        else:
            raise ValueError(f"Unknown training method: {method}. Choose 'fast' or 'reference'.")

    def _encode_word(self, tokens: List[int]) -> List[int]:
        """
        Encodes a single word (as byte token IDs) by applying merges in order of minimum rank.
        """
        if len(tokens) < 2:
            return tokens

        while len(tokens) >= 2:
            min_pair: Optional[Tuple[int, int]] = None
            min_rank = float("inf")
            n = len(tokens)
            for i in range(n - 1):
                p = (tokens[i], tokens[i + 1])
                rank = self.merges.get(p)
                if rank is not None and rank < min_rank:
                    min_rank = rank
                    min_pair = p

            if min_pair is None:
                break

            tokens = merge_word(tokens, min_pair, int(min_rank))

        return tokens

    def encode(self, text: str, allowed_special: bool = True) -> List[int]:
        """
        Encodes any Unicode string into a list of token IDs.
        Guaranteed to be lossless: decode(encode(text)) == text.
        """
        if not text:
            return []

        tokens: List[int] = []

        if allowed_special and self.special_token in text:
            parts = regex.split(r"(<\|endoftext\|>)", text)
            for part in parts:
                if part == self.special_token:
                    tokens.append(self.special_token_id)
                elif part:
                    for match in self.compiled_pattern.finditer(part):
                        w = match.group()
                        cached = self.word_cache.get(w)
                        if cached is not None:
                            tokens.extend(cached)
                        else:
                            w_bytes = list(w.encode("utf-8"))
                            encoded_word = self._encode_word(w_bytes)
                            self.word_cache[w] = encoded_word
                            tokens.extend(encoded_word)
        else:
            for match in self.compiled_pattern.finditer(text):
                w = match.group()
                cached = self.word_cache.get(w)
                if cached is not None:
                    tokens.extend(cached)
                else:
                    w_bytes = list(w.encode("utf-8"))
                    encoded_word = self._encode_word(w_bytes)
                    self.word_cache[w] = encoded_word
                    tokens.extend(encoded_word)

        return tokens

    def decode(self, ids: List[int]) -> str:
        """
        Decodes a list of token IDs back into a Unicode string.
        Guaranteed lossless for any sequence produced by encode().
        """
        if not ids:
            return ""

        parts: List[str] = []
        byte_chunks = bytearray()

        for token_id in ids:
            if token_id == self.special_token_id:
                if byte_chunks:
                    parts.append(byte_chunks.decode("utf-8", errors="replace"))
                    byte_chunks.clear()
                parts.append(self.special_token)
            elif token_id in self.vocab_bytes:
                byte_chunks.extend(self.vocab_bytes[token_id])
            else:
                raise ValueError(f"Unknown token ID: {token_id}")

        if byte_chunks:
            parts.append(byte_chunks.decode("utf-8", errors="replace"))

        return "".join(parts)

    def save(self, path: str, metadata: Optional[Dict] = None) -> None:
        """
        Saves the tokenizer vocabulary, merges, and regex configuration to a JSON file.
        """
        vocab_map = {}
        for b in range(256):
            vocab_map[str(b)] = self.vocab_bytes[b].decode("utf-8", errors="replace")
        vocab_map[str(self.special_token_id)] = self.special_token
        for pair, new_id in self.merges_list:
            vocab_map[str(new_id)] = self.vocab_bytes[new_id].decode("utf-8", errors="replace")

        data = {
            "version": "1.0",
            "vocab_size": self.vocab_size,
            "target_vocab_size": self.target_vocab_size,
            "special_tokens": self.special_tokens,
            "pattern": self.pattern_str,
            "vocab": vocab_map,
            "merges": [
                {"pair": list(pair), "id": new_id}
                for pair, new_id in self.merges_list
            ],
        }
        if metadata is not None:
            data["metadata"] = metadata

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, path: str) -> "BPETokenizer":
        """
        Loads the tokenizer configuration from a saved JSON file into this instance.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.target_vocab_size = data.get("target_vocab_size", data.get("vocab_size", 50000))
        self.pattern_str = data.get("pattern", URDU_BPE_PATTERN)
        self.compiled_pattern = regex.compile(self.pattern_str)
        self.special_tokens = data.get("special_tokens", {SPECIAL_TOKEN: SPECIAL_TOKEN_ID})
        self.inverse_special_tokens = {v: k for k, v in self.special_tokens.items()}

        merges_list = [
            (tuple(item["pair"]), item["id"])
            for item in data.get("merges", [])
        ]
        self._set_merges(merges_list)
        return self

    @classmethod
    def from_file(cls, path: str) -> "BPETokenizer":
        """
        Constructs a new BPETokenizer loaded from a JSON file.
        """
        tokenizer = cls()
        tokenizer.load(path)
        return tokenizer
