# translator.py
from dictionary_loader import Dictionary, DictionaryEntry
from language_detect import detect_language


class TranslationResult:
    def __init__(self, language: str, query: str, entries: list[DictionaryEntry]):
        self.language = language  # "ja" | "en" | "unknown"
        self.query = query
        self.entries = entries


class Translator:
    def __init__(self, dictionary: Dictionary):
        self.dictionary = dictionary

    def translate_word(self, text: str, max_results: int = 15) -> TranslationResult:
        text = text.strip()
        lang = detect_language(text)

        if lang == "ja":
            entries = self.dictionary.lookup_japanese(text, max_results=max_results)
        elif lang == "en":
            entries = self.dictionary.lookup_english(text, max_results=max_results)
        else:
            entries = []

        return TranslationResult(lang, text, entries)
