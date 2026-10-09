"""
Urdu Unicode Normalizer
Implements canonical normalization rules for Urdu text as specified in CS 417 Assignment 1.
Rule Highlights:
1. Arabic character unification (ي/ى -> ی, ك -> ک, ه -> ہ).
2. Distinction preserved: Gol Heh (ہ U+06C1) vs Do-chashmi Heh (ھ U+06BE).
3. Stripping formatting junk: Tatweel (ـ), ZWJ (\\u200D), BOM (\\uFEFF), direction marks (LRM/RLM).
4. Configurable ZWNJ handling (\\u200C preserved for morphological compounds).
5. Digit standardization (Arabic digits -> Urdu digits).
6. Whitespace and newline collapsing.
"""

import re
import sys
from typing import Optional

# ---------------------------------------------------------------------------
# Unicode Character Mappings
# ---------------------------------------------------------------------------

# Arabic to Urdu character mapping
ARABIC_TO_URDU_CHAR_MAP = {
    # Yeh variants -> Urdu Yeh (U+06CC)
    '\u064A': '\u06CC',  # Arabic Yeh (ي) -> Urdu Yeh (ی)
    '\u0649': '\u06CC',  # Alef Maksura (ى) -> Urdu Yeh (ی)
    '\u06D2': '\u06D2',  # Bari Yeh (ے) -> keep as-is (valid Urdu)

    # Kaf variants -> Urdu Kaf (U+06A9)
    '\u0643': '\u06A9',  # Arabic Kaf (ك) -> Urdu Kaf (ک)

    # Heh variants -> Gol Heh (U+06C1)
    '\u0647': '\u06C1',  # Arabic Heh (ه) -> Urdu Gol Heh (ہ)
    '\u0629': '\u06C3',  # Arabic Teh Marbuta (ة) -> Urdu Teh Marbuta Goal (ۃ)
}

# Explicitly ensure Gol Heh and Do-Chashmi Heh remain distinct
# U+06C1: Gol Heh (ہ)
# U+06BE: Do-chashmi Heh (ھ)
# These MUST NEVER be conflated.

# Invisible formatting, tatweel, and direction marks to remove
REMOVE_CHARS = {
    '\u0640',  # Tatweel / Kashida (ـ)
    '\u200D',  # Zero Width Joiner (ZWJ)
    '\uFEFF',  # Byte Order Mark (BOM) / Zero Width No-Break Space
    '\u00AD',  # Soft Hyphen
    '\u200E',  # Left-to-Right Mark (LRM)
    '\u200F',  # Right-to-Left Mark (RLM)
    '\u202A',  # Left-to-Right Embedding (LRE)
    '\u202B',  # Right-to-Left Embedding (RLE)
    '\u202C',  # Pop Directional Formatting (PDF)
    '\u202D',  # Left-to-Right Override (LRO)
    '\u202E',  # Right-to-Left Override (RLO)
    '\u2066',  # Left-to-Right Isolate (LRI)
    '\u2067',  # Right-to-Left Isolate (RLI)
    '\u2068',  # First Strong Isolate (FSI)
    '\u2069',  # Pop Directional Isolate (PDI)
}

# Translation table for instant single-pass character normalization and deletion
_TRANSLATION_TABLE = str.maketrans({
    **ARABIC_TO_URDU_CHAR_MAP,
    **{c: None for c in REMOVE_CHARS}
})

# ---------------------------------------------------------------------------
# Digit Mappings
# ---------------------------------------------------------------------------

# Arabic digits (U+0660 - U+0669) -> Urdu/Eastern Arabic-Indic digits (U+06F0 - U+06F9)
ARABIC_TO_URDU_DIGITS = {
    '\u0660': '\u06F0',  # ٠ -> ۰
    '\u0661': '\u06F1',  # ١ -> ۱
    '\u0662': '\u06F2',  # ٢ -> ۲
    '\u0663': '\u06F3',  # ٣ -> ۳
    '\u0664': '\u06F4',  # ٤ -> ۴
    '\u0665': '\u06F5',  # ٥ -> ۵
    '\u0666': '\u06F6',  # ٦ -> ۶
    '\u0667': '\u06F7',  # ٧ -> ۷
    '\u0668': '\u06F8',  # ٨ -> ۸
    '\u0669': '\u06F9',  # ٩ -> ۹
}

# ASCII digits (0-9) -> Urdu digits (۰-۹)
ASCII_TO_URDU_DIGITS = {
    str(i): chr(0x06F0 + i) for i in range(10)
}

# Arabic digits (U+0660 - U+0669) -> ASCII digits (0-9)
ARABIC_TO_ASCII_DIGITS = {
    chr(0x0660 + i): str(i) for i in range(10)
}

# Urdu digits (۰-۹) -> ASCII digits (0-9)
URDU_TO_ASCII_DIGITS = {
    chr(0x06F0 + i): str(i) for i in range(10)
}

_DIGIT_TABLE_TO_URDU = str.maketrans(ARABIC_TO_URDU_DIGITS)
_DIGIT_TABLE_ALL_TO_URDU = str.maketrans({**ARABIC_TO_URDU_DIGITS, **ASCII_TO_URDU_DIGITS})
_DIGIT_TABLE_ALL_TO_ASCII = str.maketrans({**ARABIC_TO_ASCII_DIGITS, **URDU_TO_ASCII_DIGITS})

# Various Unicode whitespace characters to collapse to standard ASCII space (U+0020)
UNICODE_SPACES_RE = re.compile(r'[\u00A0\u1680\u2000-\u200A\u202F\u205F\u3000]')
HORIZONTAL_WHITESPACE_RUNS_RE = re.compile(r'[ \t]+')
NEWLINE_STANDARDIZE_RE = re.compile(r'\r\n|\r')
CONSECUTIVE_NEWLINES_RE = re.compile(r'\n{3,}')


# ---------------------------------------------------------------------------
# Normalization Pipeline
# ---------------------------------------------------------------------------

def normalize_characters(text: str) -> str:
    """
    Applies character replacement and removal:
    - Converts Arabic Yeh, Alef Maksura, Kaf, and Heh to Urdu equivalents.
    - Strips Tatweel, ZWJ, BOM, and direction marks.
    - Preserves Gol Heh (ہ) and Do-chashmi Heh (ھ).
    """
    return text.translate(_TRANSLATION_TABLE)


def normalize_zwnj(text: str, preserve: bool = True) -> str:
    """
    Zero-Width Non-Joiner (ZWNJ, U+200C) Handling:
    - In Urdu, ZWNJ acts as an essential orthographic/morphological separator
      for compound words (e.g., 'بے‌چین', 'علی‌گڑھ') preventing unwanted letter joining.
    - If preserve=True:
        Retains ZWNJ only when it appears between two letters.
        Strips isolated or stray ZWNJ adjacent to whitespace/punctuation.
    - If preserve=False:
        Replaces ZWNJ with a space if between letters, otherwise deletes it.
    """
    if preserve:
        # Keep ZWNJ only if flanked by non-whitespace/letter-like chars
        # Remove stray ZWNJ at start/end of line, or adjacent to space/punctuation
        text = re.sub(r'(?<=\s)\u200C|\u200C(?=\s)', '', text)
        text = re.sub(r'^\u200C+|\u200C+$', '', text, flags=re.MULTILINE)
        # Collapse repeated ZWNJs
        text = re.sub(r'\u200C{2,}', '\u200C', text)
        return text
    else:
        # Replace ZWNJ with space between letters
        return text.replace('\u200C', ' ')


def normalize_digits(text: str, convention: str = "urdu") -> str:
    """
    Standardize digits across Arabic, Urdu, and ASCII conventions:
    - 'urdu' (default): Converts Arabic digits (٠-٩) to standard Urdu digits (۰-۹).
      Preserves ASCII digits for numbers/code.
    - 'all_urdu': Converts both Arabic and ASCII digits to Urdu digits (۰-۹).
    - 'ascii': Converts all Arabic and Urdu digits to ASCII (0-9).
    - 'none': Leaves digits as-is.
    """
    if convention == "urdu":
        return text.translate(_DIGIT_TABLE_TO_URDU)
    elif convention == "all_urdu":
        return text.translate(_DIGIT_TABLE_ALL_TO_URDU)
    elif convention == "ascii":
        return text.translate(_DIGIT_TABLE_ALL_TO_ASCII)
    elif convention == "none":
        return text
    else:
        raise ValueError(f"Unknown digit convention: {convention}. Choose 'urdu', 'all_urdu', 'ascii', or 'none'.")


def normalize_whitespace(text: str) -> str:
    """
    Collapses non-breaking and unusual Unicode spaces to standard ASCII space,
    collapses runs of horizontal whitespace, normalizes line breaks, and
    strips trailing spaces.
    """
    # 1. Normalize line breaks to \n
    text = NEWLINE_STANDARDIZE_RE.sub('\n', text)

    # 2. Convert special Unicode spaces to standard space
    text = UNICODE_SPACES_RE.sub(' ', text)

    # 3. Collapse multiple horizontal spaces/tabs to a single space
    text = HORIZONTAL_WHITESPACE_RUNS_RE.sub(' ', text)

    # 4. Strip whitespace at the beginning and end of each line
    lines = [line.strip(' \t') for line in text.split('\n')]
    text = '\n'.join(lines)

    # 5. Collapse excessive empty newlines (max 2 consecutive newlines)
    text = CONSECUTIVE_NEWLINES_RE.sub('\n\n', text)

    return text.strip()


def normalize(
    text: str,
    digit_convention: str = "urdu",
    preserve_zwnj: bool = True
) -> str:
    """
    Master Urdu Normalization Function.
    Executes the complete canonical normalization sequence:
    1. Character mappings (Arabic to Urdu, strip tatweel, direction marks, BOM).
    2. ZWNJ normalization (preserve morphological boundaries, strip stray).
    3. Digit standardization.
    4. Whitespace and newline normalization.

    Args:
        text: Raw input string.
        digit_convention: 'urdu' (default), 'all_urdu', 'ascii', or 'none'.
        preserve_zwnj: Whether to retain morphological ZWNJs (default True).

    Returns:
        Clean, canonically normalized Urdu string.
    """
    if not text:
        return ""

    # Step 1: Characters & formatting marks
    text = normalize_characters(text)

    # Step 2: ZWNJ handling
    text = normalize_zwnj(text, preserve=preserve_zwnj)

    # Step 3: Digits
    text = normalize_digits(text, convention=digit_convention)

    # Step 4: Whitespace
    text = normalize_whitespace(text)

    return text


# ---------------------------------------------------------------------------
# CLI Usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 2:
        in_path, out_path = sys.argv[1], sys.argv[2]
        print(f"[Normalizer] Processing {in_path} -> {out_path}...")
        with open(in_path, "r", encoding="utf-8", errors="replace") as fin:
            raw = fin.read()
        cleaned = normalize(raw)
        with open(out_path, "w", encoding="utf-8") as fout:
            fout.write(cleaned)
        print(f"[Normalizer] Done! Raw: {len(raw)} chars, Cleaned: {len(cleaned)} chars.")
    elif len(sys.argv) == 2:
        in_path = sys.argv[1]
        with open(in_path, "r", encoding="utf-8", errors="replace") as fin:
            print(normalize(fin.read()))
    else:
        sample = "تـحـقیـق  اور  تجزيہ:  كتاب  میں  هزاروں  صفحات  ہیں۔ 123  اور  ٤٥٦"
        print("Sample raw:")
        print(sample)
        print("\nSample normalized:")
        print(normalize(sample))
