"""
Unit & Idempotency Test Suite for Urdu Normalizer
Run via: python tests/test_normalize.py
"""

import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from normalize import (
    normalize,
    normalize_characters,
    normalize_zwnj,
    normalize_digits,
    normalize_whitespace
)


class TestUrduNormalization(unittest.TestCase):

    def test_arabic_yeh_conversion(self):
        """Arabic Yeh (U+064A) and Alef Maksura (U+0649) must become Urdu Yeh (U+06CC)."""
        raw_yeh = "گاڑي چلي گئي"
        expected_yeh = "گاڑی چلی گئی"
        self.assertEqual(normalize(raw_yeh), expected_yeh)

        raw_maksura = "دعوى اور معنى"
        expected_maksura = "دعوی اور معنی"
        self.assertEqual(normalize(raw_maksura), expected_maksura)

    def test_arabic_kaf_conversion(self):
        """Arabic Kaf (U+0643) must become Urdu Kaf (U+06A9)."""
        raw_kaf = "كتاب كى كہانى"
        expected_kaf = "کتاب کی کہانی"
        self.assertEqual(normalize(raw_kaf), expected_kaf)

    def test_arabic_heh_conversion(self):
        """Arabic Heh (U+0647) must become Urdu Gol Heh (U+06C1)."""
        raw_heh = "هزاروں لوگ هنس پڑے"
        expected_heh = "ہزاروں لوگ ہنس پڑے"
        self.assertEqual(normalize(raw_heh), expected_heh)

    def test_gol_heh_vs_do_chashmi_heh_distinction(self):
        """
        CRITICAL RULE:
        Gol Heh (ہ U+06C1) and Do-chashmi Heh (ھ U+06BE) must remain strictly distinct!
        """
        text = "ہمارا گھر اور ہاتھ میں پھول ہیں"
        normalized = normalize(text)
        self.assertEqual(normalized, text)
        self.assertIn('\u06C1', normalized)
        self.assertIn('\u06BE', normalized)

    def test_tatweel_removal(self):
        """Tatweel / Kashida (U+0640) must be completely removed."""
        raw = "تــــحــــقــــیــــق اور جـــــســـــتـــــجـــــو"
        expected = "تحقیق اور جستجو"
        self.assertEqual(normalize(raw), expected)

    def test_zwj_removal(self):
        """Zero Width Joiner (U+200D) must be stripped."""
        raw = "اردو\u200Dزبان\u200D"
        expected = "اردوزبان"
        self.assertEqual(normalize(raw), expected)

    def test_bom_removal(self):
        """Byte Order Mark (U+FEFF) must be stripped."""
        raw = "\uFEFFپاکستان زندہ باد\uFEFF"
        expected = "پاکستان زندہ باد"
        self.assertEqual(normalize(raw), expected)

    def test_direction_marks_removal(self):
        """Directional formatting marks (LRM, RLM, etc.) must be stripped."""
        raw = "یہ \u200Eایک \u200Fجملہ \u202Aہے\u202C۔"
        expected = "یہ ایک جملہ ہے۔"
        self.assertEqual(normalize(raw), expected)

    def test_zwnj_handling(self):
        """Zero Width Non-Joiner (U+200C) preserved for morphological compounds."""
        compound = "بے\u200Cچین اور علی\u200Cگڑھ"
        self.assertEqual(normalize(compound, preserve_zwnj=True), "بے\u200Cچین اور علی\u200Cگڑھ")

        stray = " لفظ \u200C اور \u200Cدوسرا "
        self.assertEqual(normalize(stray, preserve_zwnj=True), "لفظ اور دوسرا")

    def test_digit_standardization(self):
        """Arabic digits (٠-٩) must be mapped to Urdu digits (۰-۹)."""
        raw_arabic_digits = "سال ٢٠٢٦ میں تاریخ ١٥ مارچ"
        expected_urdu_digits = "سال ۲۰۲۶ میں تاریخ ۱۵ مارچ"
        self.assertEqual(normalize(raw_arabic_digits, digit_convention="urdu"), expected_urdu_digits)

        self.assertEqual(
            normalize("تاریخ 2026 اور ٢٠٢٦", digit_convention="ascii"),
            "تاریخ 2026 اور 2026"
        )

    def test_whitespace_collapsing(self):
        """Runs of spaces, tabs, and non-breaking spaces must collapse to single space."""
        raw = "یہ\u00A0ایک    بہت\u202Fہی    اہم    بات   ہے۔"
        expected = "یہ ایک بہت ہی اہم بات ہے۔"
        self.assertEqual(normalize(raw), expected)

    def test_newline_normalization(self):
        """Carriage returns standardized; runs of >2 newlines collapsed to max 2."""
        raw = "پہلی سطر\r\n\r\n\r\n\r\nدوسری سطر\rتیسری سطر"
        expected = "پہلی سطر\n\nدوسری سطر\nتیسری سطر"
        self.assertEqual(normalize(raw), expected)

    def test_code_mixing_preserved(self):
        """Natural English words and punctuation in Urdu sentences preserved."""
        mixed = "ہم نے Python اور Machine Learning کے ماڈلز ٹرین کیے۔"
        self.assertEqual(normalize(mixed), mixed)

    def test_idempotency(self):
        """Idempotency property: normalize(normalize(x)) == normalize(x)."""
        test_strings = [
            "تـحـقیـق  اور  تجزيہ:  كتاب  میں  هزاروں  صفحات  ہیں۔ 123  اور  ٤٥٦",
            "بے\u200Cچین، علی\u200Cگڑھ، \uFEFFاور\u200E \u200Fپاکستان زندہ باد!",
            "گھوڑا، ہاتھی، ہاتھ، کھانا، بھالو",
            "Line 1   \n\n\n\n\nLine 2 with \u00A0 non-breaking spaces."
        ]
        for s in test_strings:
            once = normalize(s)
            twice = normalize(once)
            self.assertEqual(once, twice, f"Failed idempotency on: {s}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
