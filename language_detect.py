# language_detect.py

def detect_language(text: str) -> str:
    """
    Very simple heuristic language detector.
    Returns: "ja", "en", or "unknown".
    """
    text = text.strip()
    if not text:
        return "unknown"

    has_japanese = False
    has_ascii_letter = False

    for ch in text:
        code = ord(ch)
        # Hiragana
        if 0x3040 <= code <= 0x309F:
            has_japanese = True
        # Katakana
        elif 0x30A0 <= code <= 0x30FF:
            has_japanese = True
        # CJK unified ideographs (kanji)
        elif 0x4E00 <= code <= 0x9FFF:
            has_japanese = True
        # Basic ASCII letters
        elif ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
            has_ascii_letter = True

    if has_japanese:
        return "ja"
    if has_ascii_letter:
        return "en"
    return "unknown"
