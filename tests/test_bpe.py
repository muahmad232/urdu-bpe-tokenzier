"""
Comprehensive Test Suite for Urdu BPE Tokenizer
CS 417: Large Language Models · NUST SEECS · Spring 2026

Test Suite Highlights:
1. Lossless Roundtrip Guarantee: decode(encode(text)) == text for:
   - Modern and classical Urdu
   - English and code-mixed text
   - Urdu diacritics (aerab / combining marks \\p{M})
   - Zero-Width Non-Joiner (ZWNJ \\u200C)
   - ASCII and Urdu numerals
   - Multi-byte UTF-8 emojis and symbols
   - Empty string and boundary whitespaces
2. Special Token Handling:
   - <|endoftext|> encodes strictly to token ID 256 without splitting or merging.
3. Deterministic Tie-Breaking:
   - When pair frequencies match, the lexicographically greater integer tuple is merged.
4. Stage 1 vs Stage 2 Equivalence:
   - Verified on a 1 MB sample of corpus/train.txt to produce identical merges.
5. Vocabulary Layout & Integrity:
   - IDs 0-255: raw bytes, ID 256: special token, IDs 257+: merges.
6. Serialization (save and load roundtrip).
"""

import os
import sys
import tempfile
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bpe import BPETokenizer, SPECIAL_TOKEN, SPECIAL_TOKEN_ID


class TestBPETokenizer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Build a small reference tokenizer trained on representative Urdu text
        cls.sample_urdu_corpus = (
            "یہ ایک جامع آزمائشی اردو متن ہے۔ "
            "اُردُو زبان میں بے‌چین دل کی کہانی بیان کی گئی ہے۔ "
            "کتاب میں 123 صفحات ہیں اور قیمت ۴۵۶ روپے ہے۔ "
            "پاکستان اور اسلام آباد میں خوش آمدید! "
            "تحقیق اور جستجو انسانی فطرت کا حصہ ہے۔ "
            "<|endoftext|> "
            "دوسری دستاویز: انگریزی الفاظ جیسے AI اور LLM بھی شامل ہیں۔ "
            "مختلف اشکال اور علامات: 🚀 ✨ 🔥! "
        )
        cls.tokenizer = BPETokenizer(vocab_size=320)
        cls.tokenizer.train_stage2(cls.sample_urdu_corpus, vocab_size=320)

    def test_vocabulary_layout(self):
        """
        Verify the exact vocabulary layout:
        - 0-255: Raw bytes
        - 256: Special token <|endoftext|>
        - 257+: Learned merges
        """
        vocab = self.tokenizer.vocab
        # Check raw bytes
        for b in range(256):
            self.assertIn(b, self.tokenizer.vocab_bytes)
            self.assertEqual(self.tokenizer.vocab_bytes[b], bytes([b]))

        # Check special token
        self.assertEqual(self.tokenizer.special_tokens[SPECIAL_TOKEN], SPECIAL_TOKEN_ID)
        self.assertEqual(vocab[SPECIAL_TOKEN_ID], SPECIAL_TOKEN)

        # Check learned merges start at 257
        for pair, new_id in self.tokenizer.merges_list:
            self.assertGreaterEqual(new_id, 257)
            self.assertIn(new_id, self.tokenizer.vocab_bytes)

    def test_special_token_encoding_strictly_id_256(self):
        """
        CRITICAL TEST:
        <|endoftext|> must encode strictly to ID 256 and never be split into pieces.
        """
        # Standalone special token
        encoded_single = self.tokenizer.encode("<|endoftext|>")
        self.assertEqual(encoded_single, [256])
        self.assertEqual(self.tokenizer.decode(encoded_single), "<|endoftext|>")

        # Multiple special tokens
        encoded_double = self.tokenizer.encode("<|endoftext|><|endoftext|>")
        self.assertEqual(encoded_double, [256, 256])
        self.assertEqual(self.tokenizer.decode(encoded_double), "<|endoftext|><|endoftext|>")

        # Flanked by Urdu text
        text_with_special = "پہلا حصہ<|endoftext|>دوسرا حصہ"
        encoded = self.tokenizer.encode(text_with_special)
        self.assertIn(256, encoded)
        # Verify 256 appears exactly once
        self.assertEqual(encoded.count(256), 1)
        self.assertEqual(self.tokenizer.decode(encoded), text_with_special)

    def test_lossless_roundtrip_urdu(self):
        """Lossless roundtrip on diverse Urdu sentences."""
        test_strings = [
            "قومی زبان اردو پاکستان کی شناخت ہے۔",
            "غالب کی شاعری میں سوز و گداز اور فلسفہ ملتا ہے۔",
            "تمام انسان آزاد اور حقوق و عزت کے اعتبار سے برابر پیدا ہوئے ہیں۔",
        ]
        for s in test_strings:
            encoded = self.tokenizer.encode(s)
            decoded = self.tokenizer.decode(encoded)
            self.assertEqual(decoded, s)

    def test_lossless_roundtrip_diacritics_and_zwnj(self):
        """Lossless roundtrip on Urdu combining diacritics and ZWNJ compound words."""
        test_strings = [
            "اُردُ و کی اِبتدا اور تَرقّی",  # combining marks \p{M}
            "بے‌چین اور با‌وقار اور علی‌گڑھ",  # internal ZWNJ \u200C
            "مَسْئَلَہ اور جَزَاءٌ",  # tanween, jazm, zabar
        ]
        for s in test_strings:
            encoded = self.tokenizer.encode(s)
            decoded = self.tokenizer.decode(encoded)
            self.assertEqual(decoded, s)

    def test_lossless_roundtrip_english_and_code_mixing(self):
        """Lossless roundtrip on English contractions and code-mixing."""
        test_strings = [
            "This is a test of English contractions: it's, they're, don't, we'll, I'm.",
            "Urdu اور English کی ملاوٹ: deep learning اور transformers ماڈلز۔",
            "Numbers: 1234567890 and Urdu digits: ۰۱۲۳۴۵۶۷۸۹۔",
        ]
        for s in test_strings:
            encoded = self.tokenizer.encode(s)
            decoded = self.tokenizer.decode(encoded)
            self.assertEqual(decoded, s)

    def test_lossless_roundtrip_emojis_and_symbols(self):
        """Lossless roundtrip on multi-byte UTF-8 emojis and ASCII symbols."""
        test_strings = [
            "🎉 🚀 🔥 ✨ 💡  Urdu with Emojis 😊",
            "!@#$%^&*()_+~`-=[]{}|;':\",./<>?",
            "Line 1\nLine 2\r\nLine 3\tTabbed content   extra spaces",
        ]
        for s in test_strings:
            encoded = self.tokenizer.encode(s)
            decoded = self.tokenizer.decode(encoded)
            self.assertEqual(decoded, s)

    def test_lossless_roundtrip_edge_cases(self):
        """Lossless roundtrip on empty string, single characters, and rare tokens."""
        edge_cases = [
            "",
            " ",
            "   ",
            "\n",
            "\t",
            "a",
            "ء",
            "\u200C",  # isolated ZWNJ
        ]
        for s in edge_cases:
            encoded = self.tokenizer.encode(s)
            decoded = self.tokenizer.decode(encoded)
            self.assertEqual(decoded, s)

    def test_deterministic_tie_breaking(self):
        """
        CRITICAL TIE-BREAKING TEST:
        When two byte-pairs have the exact same frequency,
        the lexicographically greater pair comparing them as integer tuples (id1, id2)
        must be merged first.
        """
        # 'cd' -> bytes (99, 100)
        # 'ab' -> bytes (97, 98)
        # Both appear exactly 2 times across documents without leading space interference.
        # (99, 100) > (97, 98), so 'cd' must merge before 'ab'.
        tie_text = "ab<|endoftext|>cd<|endoftext|>ab<|endoftext|>cd"
        tok = BPETokenizer(vocab_size=259)
        merges = tok.train_stage2(tie_text, vocab_size=259)

        self.assertEqual(len(merges), 2)
        first_pair = merges[0][0]
        second_pair = merges[1][0]

        self.assertEqual(first_pair, (ord('c'), ord('d')))
        self.assertEqual(second_pair, (ord('a'), ord('b')))

        # Test another pair with equal first byte: (99, 101) vs (99, 100)
        # 'ce' -> (99, 101), 'cd' -> (99, 100)
        tie_text2 = "cd<|endoftext|>ce<|endoftext|>cd<|endoftext|>ce"
        tok2 = BPETokenizer(vocab_size=258)
        merges2 = tok2.train_stage2(tie_text2, vocab_size=258)
        self.assertEqual(merges2[0][0], (ord('c'), ord('e')))

    def test_stage1_and_stage2_identical_on_1mb_sample(self):
        """
        CRITICAL STAGE 1 VS STAGE 2 EQUIVALENCE TEST:
        Stage 1 (Reference recount-all) and Stage 2 (Fast BPE) must produce
        the EXACT identical sequence of merges on a 1 MB sample of corpus/train.txt.
        """
        train_path = os.path.join(os.path.dirname(__file__), "..", "corpus", "train.txt")
        self.assertTrue(os.path.exists(train_path), f"Missing {train_path}")

        # Read 1 MB sample
        with open(train_path, "r", encoding="utf-8", errors="replace") as f:
            sample_1mb = f.read(1_000_000)

        num_merges = 20
        tok_stage1 = BPETokenizer()
        merges_stage1 = tok_stage1.train_stage1(sample_1mb, vocab_size=257 + num_merges)

        tok_stage2 = BPETokenizer()
        merges_stage2 = tok_stage2.train_stage2(sample_1mb, vocab_size=257 + num_merges)

        self.assertEqual(len(merges_stage1), num_merges)
        self.assertEqual(len(merges_stage2), num_merges)

        for i, (m1, m2) in enumerate(zip(merges_stage1, merges_stage2)):
            self.assertEqual(
                m1, m2,
                f"Mismatch at merge #{i+1}: Stage 1={m1} vs Stage 2={m2}"
            )

    def test_save_and_load_roundtrip(self):
        """Test JSON serialization and deserialization of tokenizer."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self.tokenizer.save(tmp_path)
            loaded_tok = BPETokenizer.from_file(tmp_path)

            self.assertEqual(loaded_tok.vocab_size, self.tokenizer.vocab_size)
            self.assertEqual(loaded_tok.merges_list, self.tokenizer.merges_list)
            self.assertEqual(loaded_tok.special_tokens, self.tokenizer.special_tokens)

            test_text = "یہ ایک لوڈ شدہ ٹوکنائزر کی جانچ ہے۔ <|endoftext|>"
            orig_encoded = self.tokenizer.encode(test_text)
            loaded_encoded = loaded_tok.encode(test_text)
            self.assertEqual(orig_encoded, loaded_encoded)
            self.assertEqual(loaded_tok.decode(loaded_encoded), test_text)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
