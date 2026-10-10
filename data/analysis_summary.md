# Tokenizer Analysis & Empirical Benchmarks
> CS 417: Large Language Models · NUST SEECS · Spring 2026

## Question 1: Merges Analysis

### 1.1 Merges 1 to 50
| Merge # | Token ID | Pair | Decoded Text | Valid UTF-8? | Hex Bytes |
|---|---|---|---|---|---|
| 1 | 257 | `[216, 167]` | `ا` | ✅ | `0xD8 0xA7` |
| 2 | 258 | `[219, 140]` | `ی` | ✅ | `0xDB 0x8C` |
| 3 | 259 | `[32, 216]` | `\\x20\\xd8` | ❌ | `0x20 0xD8` |
| 4 | 260 | `[218, 169]` | `ک` | ✅ | `0xDA 0xA9` |
| 5 | 261 | `[32, 217]` | `\\x20\\xd9` | ❌ | `0x20 0xD9` |
| 6 | 262 | `[216, 177]` | `ر` | ✅ | `0xD8 0xB1` |
| 7 | 263 | `[217, 136]` | `و` | ✅ | `0xD9 0x88` |
| 8 | 264 | `[219, 129]` | `ہ` | ✅ | `0xDB 0x81` |
| 9 | 265 | `[219, 146]` | `ے` | ✅ | `0xDB 0x92` |
| 10 | 266 | `[32, 260]` | ` ک` | ✅ | `0x20 0xDA 0xA9` |
| 11 | 267 | `[217, 134]` | `ن` | ✅ | `0xD9 0x86` |
| 12 | 268 | `[257, 216]` | `\\xd8\\xa7\\xd8` | ❌ | `0xD8 0xA7 0xD8` |
| 13 | 269 | `[217, 132]` | `ل` | ✅ | `0xD9 0x84` |
| 14 | 270 | `[217, 133]` | `م` | ✅ | `0xD9 0x85` |
| 15 | 271 | `[218, 186]` | `ں` | ✅ | `0xDA 0xBA` |
| 16 | 272 | `[261, 133]` | ` م` | ✅ | `0x20 0xD9 0x85` |
| 17 | 273 | `[32, 257]` | ` ا` | ✅ | `0x20 0xD8 0xA7` |
| 18 | 274 | `[216, 170]` | `ت` | ✅ | `0xD8 0xAA` |
| 19 | 275 | `[32, 264]` | ` ہ` | ✅ | `0x20 0xDB 0x81` |
| 20 | 276 | `[258, 271]` | `یں` | ✅ | `0xDB 0x8C 0xDA 0xBA` |
| 21 | 277 | `[216, 179]` | `س` | ✅ | `0xD8 0xB3` |
| 22 | 278 | `[216, 175]` | `د` | ✅ | `0xD8 0xAF` |
| 23 | 279 | `[259, 179]` | ` س` | ✅ | `0x20 0xD8 0xB3` |
| 24 | 280 | `[218, 190]` | `ھ` | ✅ | `0xDA 0xBE` |
| 25 | 281 | `[259, 168]` | ` ب` | ✅ | `0x20 0xD8 0xA8` |
| 26 | 282 | `[218, 175]` | `گ` | ✅ | `0xDA 0xAF` |
| 27 | 283 | `[261, 190]` | ` پ` | ✅ | `0x20 0xD9 0xBE` |
| 28 | 284 | `[266, 258]` | ` کی` | ✅ | `0x20 0xDA 0xA9 0xDB 0x8C` |
| 29 | 285 | `[266, 265]` | ` کے` | ✅ | `0x20 0xDA 0xA9 0xDB 0x92` |
| 30 | 286 | `[261, 134]` | ` ن` | ✅ | `0x20 0xD9 0x86` |
| 31 | 287 | `[257, 267]` | `ان` | ✅ | `0xD8 0xA7 0xD9 0x86` |
| 32 | 288 | `[216, 168]` | `ب` | ✅ | `0xD8 0xA8` |
| 33 | 289 | `[263, 262]` | `ور` | ✅ | `0xD9 0x88 0xD8 0xB1` |
| 34 | 290 | `[259, 170]` | ` ت` | ✅ | `0x20 0xD8 0xAA` |
| 35 | 291 | `[259, 172]` | ` ج` | ✅ | `0x20 0xD8 0xAC` |
| 36 | 292 | `[257, 262]` | `ار` | ✅ | `0xD8 0xA7 0xD8 0xB1` |
| 37 | 293 | `[219, 148]` | `۔` | ✅ | `0xDB 0x94` |
| 38 | 294 | `[32, 268]` | `\\x20\\xd8\\xa7\\xd8` | ❌ | `0x20 0xD8 0xA7 0xD8` |
| 39 | 295 | `[259, 175]` | ` د` | ✅ | `0x20 0xD8 0xAF` |
| 40 | 296 | `[272, 276]` | ` میں` | ✅ | `0x20 0xD9 0x85 0xDB 0x8C 0xDA 0xBA` |
| 41 | 297 | `[217, 129]` | `ف` | ✅ | `0xD9 0x81` |
| 42 | 298 | `[217, 130]` | `ق` | ✅ | `0xD9 0x82` |
| 43 | 299 | `[217, 185]` | `ٹ` | ✅ | `0xD9 0xB9` |
| 44 | 300 | `[261, 136]` | ` و` | ✅ | `0x20 0xD9 0x88` |
| 45 | 301 | `[216, 185]` | `ع` | ✅ | `0xD8 0xB9` |
| 46 | 302 | `[266, 262]` | ` کر` | ✅ | `0x20 0xDA 0xA9 0xD8 0xB1` |
| 47 | 303 | `[257, 269]` | `ال` | ✅ | `0xD8 0xA7 0xD9 0x84` |
| 48 | 304 | `[275, 265]` | ` ہے` | ✅ | `0x20 0xDB 0x81 0xDB 0x92` |
| 49 | 305 | `[263, 271]` | `وں` | ✅ | `0xD9 0x88 0xDA 0xBA` |
| 50 | 306 | `[217, 190]` | `پ` | ✅ | `0xD9 0xBE` |

### 1.2 Every 5,000th Merge
| Merge # | Token ID | Pair | Decoded Text | Byte Length | Hex Bytes |
|---|---|---|---|---|---|
| 5000 | 5256 | `[1918, 299]` | ` اسٹیٹ` | 11 | `0x20 0xD8 0xA7 0xD8 0xB3 0xD9 0xB9 0xDB 0x8C 0xD9 0xB9` |
| 10000 | 10256 | `[308, 1716]` | ` ریسٹ` | 9 | `0x20 0xD8 0xB1 0xDB 0x8C 0xD8 0xB3 0xD9 0xB9` |
| 15000 | 15256 | `[1605, 2986]` | ` رحمانی` | 13 | `0x20 0xD8 0xB1 0xD8 0xAD 0xD9 0x85 0xD8 0xA7 0xD9 0x86 0xDB 0x8C` |
| 20000 | 20256 | `[343, 650]` | ` فورٹ` | 9 | `0x20 0xD9 0x81 0xD9 0x88 0xD8 0xB1 0xD9 0xB9` |
| 25000 | 25256 | `[3227, 378]` | ` پچھلا` | 11 | `0x20 0xD9 0xBE 0xDA 0x86 0xDA 0xBE 0xD9 0x84 0xD8 0xA7` |
| 30000 | 30256 | `[1905, 14160]` | ` سائنسداں` | 17 | `0x20 0xD8 0xB3 0xD8 0xA7 0xD8 0xA6 0xD9 0x86 0xD8 0xB3 0xD8 0xAF 0xD8 0xA7 0xDA 0xBA` |
| 35000 | 35256 | `[2018, 488]` | ` حدیثِ` | 11 | `0x20 0xD8 0xAD 0xD8 0xAF 0xDB 0x8C 0xD8 0xAB 0xD9 0x90` |
| 40000 | 40256 | `[14082, 190]` | ` ﴾` | 4 | `0x20 0xEF 0xB4 0xBE` |
| 45000 | 45256 | `[5045, 38062]` | ` Republic` | 9 | `0x20 0x52 0x65 0x70 0x75 0x62 0x6C 0x69 0x63` |

### 1.3 Early Merges Rebuilding 2-Byte Urdu Letters
| Urdu Letter | Unicode | Merge # | Token ID | UTF-8 Byte Pair |
|---|---|---|---|---|
| ا | `U+0627` | 1 | 257 | `0xD8 0xA7` |
| ی | `U+06CC` | 2 | 258 | `0xDB 0x8C` |
| ک | `U+06A9` | 4 | 260 | `0xDA 0xA9` |
| ر | `U+0631` | 6 | 262 | `0xD8 0xB1` |
| و | `U+0648` | 7 | 263 | `0xD9 0x88` |
| ہ | `U+06C1` | 8 | 264 | `0xDB 0x81` |
| ے | `U+06D2` | 9 | 265 | `0xDB 0x92` |
| ن | `U+0646` | 11 | 267 | `0xD9 0x86` |
| ل | `U+0644` | 13 | 269 | `0xD9 0x84` |
| م | `U+0645` | 14 | 270 | `0xD9 0x85` |
| ں | `U+06BA` | 15 | 271 | `0xDA 0xBA` |
| ت | `U+062A` | 18 | 274 | `0xD8 0xAA` |
| س | `U+0633` | 21 | 277 | `0xD8 0xB3` |
| د | `U+062F` | 22 | 278 | `0xD8 0xAF` |
| ھ | `U+06BE` | 24 | 280 | `0xDA 0xBE` |
| گ | `U+06AF` | 26 | 282 | `0xDA 0xAF` |
| ب | `U+0628` | 32 | 288 | `0xD8 0xA8` |
| ف | `U+0641` | 41 | 297 | `0xD9 0x81` |
| ق | `U+0642` | 42 | 298 | `0xD9 0x82` |
| ٹ | `U+0679` | 43 | 299 | `0xD9 0xB9` |
| ع | `U+0639` | 45 | 301 | `0xD8 0xB9` |
| پ | `U+067E` | 50 | 306 | `0xD9 0xBE` |
| چ | `U+0686` | 53 | 309 | `0xDA 0x86` |
| ش | `U+0634` | 56 | 312 | `0xD8 0xB4` |
| ز | `U+0632` | 57 | 313 | `0xD8 0xB2` |
| ج | `U+062C` | 59 | 315 | `0xD8 0xAC` |
| ح | `U+062D` | 68 | 324 | `0xD8 0xAD` |
| ڈ | `U+0688` | 78 | 334 | `0xDA 0x88` |
| ص | `U+0635` | 88 | 344 | `0xD8 0xB5` |
| خ | `U+062E` | 98 | 354 | `0xD8 0xAE` |
| ڑ | `U+0691` | 101 | 357 | `0xDA 0x91` |
| ط | `U+0637` | 106 | 362 | `0xD8 0xB7` |
| ظ | `U+0638` | 127 | 383 | `0xD8 0xB8` |
| ض | `U+0636` | 143 | 399 | `0xD8 0xB6` |
| غ | `U+063A` | 184 | 440 | `0xD8 0xBA` |
| ث | `U+062B` | 199 | 455 | `0xD8 0xAB` |
| ذ | `U+0630` | 207 | 463 | `0xD8 0xB0` |
| آ | `U+0622` | 267 | 523 | `0xD8 0xA2` |
| ء | `U+0621` | 537 | 793 | `0xD8 0xA1` |
| ژ | `U+0698` | 1220 | 1476 | `0xDA 0x98` |

### 1.4 Non-Valid UTF-8 Single-Token Merges
- **Total Non-Valid UTF-8 Intermediate Merges**: 114
- **Interpretation**: These merges represent intermediate byte-pair steps where a high-frequency prefix byte (such as a leading space `0x20` or a first UTF-8 byte `0xD8`/`0xD9`) joins with an incomplete continuation byte. Because BPE is purely byte-level, these tokens serve as algorithmic stepping stones toward complete characters and words.
| Merge # | Token ID | Pair | Byte Length | Raw Hex |
|---|---|---|---|---|
| 3 | 259 | `[32, 216]` | 2 | `0x20 0xD8` |
| 5 | 261 | `[32, 217]` | 2 | `0x20 0xD9` |
| 12 | 268 | `[257, 216]` | 3 | `0xD8 0xA7 0xD8` |
| 38 | 294 | `[32, 268]` | 4 | `0x20 0xD8 0xA7 0xD8` |
| 100 | 356 | `[226, 128]` | 2 | `0xE2 0x80` |
| 135 | 391 | `[273, 217]` | 4 | `0x20 0xD8 0xA7 0xD9` |
| 453 | 709 | `[257, 217]` | 3 | `0xD8 0xA7 0xD9` |
| 464 | 720 | `[32, 356]` | 3 | `0x20 0xE2 0x80` |
| 635 | 891 | `[32, 219]` | 2 | `0x20 0xDB` |
| 904 | 1160 | `[177, 219]` | 2 | `0xB1 0xDB` |
| 1224 | 1480 | `[32, 239]` | 2 | `0x20 0xEF` |
| 1458 | 1714 | `[891, 1160]` | 4 | `0x20 0xDB 0xB1 0xDB` |
| 1513 | 1769 | `[32, 194]` | 2 | `0x20 0xC2` |
| 1522 | 1778 | `[239, 186]` | 2 | `0xEF 0xBA` |
| 1617 | 1873 | `[183, 186]` | 2 | `0xB7 0xBA` |

### 1.5 First Complete Urdu Word Merge
- **First Complete Word**: ` کی`
- **Merge Index**: **#28** (Token ID `284`)
- **Byte Length**: 5 bytes (0x20 0xDA 0xA9 0xDB 0x8C)
- **Interpretation**: The very first complete word merged is `کی`, appearing at merge index #28. This demonstrates that high-frequency Urdu functional prepositions and conjunctions are assembled immediately after basic 2-byte letter reconstruction.

### 1.6 Top 20 Longest Learned Tokens (by UTF-8 Bytes)
| Rank | Token ID | Decoded String | Byte Length | Character Length |
|---|---|---|---|---|
| 1 | 28048 | `۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔` | 64 | 32 |
| 2 | 42536 | `۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔` | 52 | 26 |
| 3 | 44360 | ` ------------------------------------------` | 43 | 43 |
| 4 | 13450 | `۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔۔` | 32 | 16 |
| 5 | 47863 | `ٍٍٍٍٍٍٍٍٍٍٍٍٍٍٍٍ` | 32 | 16 |
| 6 | 48808 | ` الْمُشْرِکِیْنَ` | 31 | 16 |
| 7 | 49908 | ` الْمُؤْمِنِیْنَ` | 31 | 16 |
| 8 | 47858 | `چندرابابونائیڈو` | 30 | 15 |
| 9 | 28896 | ` انسائیکلوپیڈیا` | 29 | 15 |
| 10 | 38870 | ` الصلوٰۃوالسلام` | 29 | 15 |
| 11 | 42496 | ` کاربوہائیڈریٹس` | 29 | 15 |
| 12 | 49475 | `۔۔۔۔۔۔۔۔۔۔۔۔۔۔` | 28 | 14 |
| 13 | 16222 | ` خیبرپختونخواہ` | 27 | 14 |
| 14 | 33564 | ` انگیزانکشافات` | 27 | 14 |
| 15 | 33667 | ` پارلیمنٹیرینز` | 27 | 14 |
| 16 | 35261 | ` لاہورہائیکورٹ` | 27 | 14 |
| 17 | 41132 | ` غیرجانبدارانہ` | 27 | 14 |
| 18 | 34580 | ` -------------------------` | 26 | 26 |
| 19 | 33024 | `خیبرپختونخواہ` | 26 | 13 |
| 20 | 41273 | `لاہورہائیکورٹ` | 26 | 13 |

## Question 2: Comparative Benchmark

### 2.1 Full Test Set Benchmark (`corpus/test.txt`)
- **Total Test Volume**: 3,112,488 characters, 649,343 words, 5.23 MB

| Tokenizer | Total Tokens | Tokens / Word | Bytes / Token (Compression) | Compression vs GPT-2 |
|---|---|---|---|---|
| **Custom Urdu BPE** | **749,843** | **1.155** | **7.32 B/tok** | **5.24x more compact** |
| **OpenAI o200k_base** | 1,038,413 | 1.599 | 5.286 B/tok | 3.78x more compact |
| **OpenAI GPT-2** | 3,928,540 | 6.05 | 1.397 B/tok | 1.00x (Baseline) |

### 2.2 Seven Hand-Picked Benchmark Inputs
| Category | Input Description / Snippet | Words | Custom BPE (tok/word) | o200k_base (tok/word) | GPT-2 (tok/word) |
|---|---|---|---|---|---|
| **News** | قومی اسمبلی میں آئینی ترمیم کے حوالے سے گرما ... | 27 | **28** (1.037) | 34 (1.259) | 165 (6.111) |
| **Poetry** | ہزاروں خواہشیں ایسی کہ ہر خواہش پہ دم نکلے... | 37 | **42** (1.135) | 62 (1.676) | 209 (5.649) |
| **Code_mixing** | آج کل کے دور میں Artificial Intelligence اور ... | 26 | **34** (1.308) | 41 (1.577) | 141 (5.423) |
| **Roman_urdu** | Mujhe lagta hai ke yeh naya machine learning ... | 28 | **74** (2.643) | 47 (1.679) | 59 (2.107) |
| **Numbers_dates** | پاکستان کا قیام ۱۵ اگست ۱۹۴۷ کو عمل میں آیا ت... | 23 | **28** (1.217) | 39 (1.696) | 140 (6.087) |
| **Diacritics** | اَلْحَمْدُ لِلّٰهِ رَبِّ الْعٰلَمِیْنَ۔ قَطْر... | 14 | **50** (3.571) | 81 (5.786) | 130 (9.286) |
| **Personal_names** | ڈاکٹر علامہ محمد اقبال، مرزا اسد اللہ خان غال... | 26 | **30** (1.154) | 45 (1.731) | 151 (5.808) |

## Question 3: Failure Cases Analysis

### 3.1 Failure Case: Irregular Roman Urdu Slang
- **Input String**: `yrrr plzzzzz mujhy btao ye assignment kb tk submit krwani h wrna scene off hojana`
- **Word Count**: 15 words
- **Token Counts**: **Custom BPE = 42 tokens** (2.8 tok/word) | o200k_base = 25 | GPT-2 = 29
- **Token Breakdown**: `yr | r | r |  pl | z | z | z | z | z |  m | uj | hy |  b | ta | o`...
- **Analysis**: Because the 566 MB training corpus consists strictly of Perso-Arabic Nastaliq script, colloquial Roman Urdu words with character repetitions ('yrrr', 'plzzzzz', 'kb tk', 'wrna') are completely absent from the vocabulary. Each letter is fragmented into individual single-byte ASCII tokens, causing extreme token inflation.

### 3.2 Failure Case: Complex Multi-Diacritic Combining Sequences
- **Input String**: `مُسْتَشْفَیَاتٌ (Mustashfayatun) بِالْإِضَافَةِ إِلَى تَسْخِیرِ الطَّاقَاتِ`
- **Word Count**: 6 words
- **Token Counts**: **Custom BPE = 39 tokens** (6.5 tok/word) | o200k_base = 49 | GPT-2 = 77
- **Token Breakdown**: `م | ُس | ْتَ | ش | ْف | َی | َات | ٌ |  ( | M | ust | ash | f | ay | at`...
- **Analysis**: Rare Arabic loanwords adorned with full vowel diacritics (zabar, zer, pesh, sukun, tanween, tashdeed) in stacked combinations break whole-word merges. Since normal training text rarely retains exhaustive aerab, the tokenizer falls back to splitting every diacritic mark into its 2-byte Unicode representation.

### 3.3 Failure Case: Rare Arabic Honorific Ligatures & Archaic Glyphs
- **Input String**: `نبی کریم ﷺ اور صحابہ کرام ؓ و ؑ کے ارشادات مبارکہ`
- **Word Count**: 12 words
- **Token Counts**: **Custom BPE = 12 tokens** (1.0 tok/word) | o200k_base = 22 | GPT-2 = 59
- **Token Breakdown**: `نبی |  کریم |  ﷺ |  اور |  صحابہ |  کرام |  ؓ |  و |  ؑ |  کے |  ارشادات |  مبارکہ`
- **Analysis**: Special Unicode presentation-form ligatures like Sallallah-o-Alaihi-Wasallam (ﷺ U+FDFA) and Razi-Allahu-Anhu (ؓ U+0618 / ؑ U+0619) require 3 to 4 bytes in UTF-8. Because these characters are sparse relative to plain text equivalents, they fail to form single unified tokens and fragment into isolated byte fragments.
