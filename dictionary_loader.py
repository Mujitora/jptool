# dictionary_loader.py
import json


class DictionaryEntry:
    def __init__(self, kanji_list, reading_list, meanings, pos=None, tags=None):
        self.kanji_list = kanji_list or []        # list[str]
        self.reading_list = reading_list or []    # list[str]
        self.meanings = meanings or []            # list[str]
        self.pos = pos or []                      # list[str]
        self.tags = tags or []                    # list[str]

        # Convenience: primary form for printing
        self.kanji = self.kanji_list[0] if self.kanji_list else None
        self.reading = self.reading_list[0] if self.reading_list else ""

    def __repr__(self):
        return (
            f"DictionaryEntry(kanji_list={self.kanji_list}, "
            f"reading_list={self.reading_list}, "
            f"meanings={self.meanings}, pos={self.pos}, tags={self.tags})"
        )


class Dictionary:
    def __init__(self, json_path: str):
        self.entries = []
        self.by_kanji = {}
        self.by_reading = {}
        self.by_english = {}

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File '{json_path}' not found.")
            data = []
        except json.JSONDecodeError:
            print(f"Error: File '{json_path}' is not a valid JSON file.")
            data = []

        for raw in data:
            entry = DictionaryEntry(
                kanji_list=raw.get("kanji", []),
                reading_list=raw.get("readings", []),
                meanings=raw.get("meanings", []),
                pos=raw.get("pos"),
                tags=raw.get("tags"),
            )
            self.entries.append(entry)

            # Index by each kanji form
            for kanji in entry.kanji_list:
                self.by_kanji.setdefault(kanji, []).append(entry)

            # Index by each reading form
            for reading in entry.reading_list:
                self.by_reading.setdefault(reading, []).append(entry)

            # Index by English words
            for meaning in entry.meanings:
                words = (
                    meaning.lower()
                    .replace(";", " ")
                    .replace(",", " ")
                    .split()
                )
                for word in words:
                    self.by_english.setdefault(word, []).append(entry)



    def lookup_japanese(self, term: str, max_results: int = 10) -> list[DictionaryEntry]:
        """Look up a term assuming it's Japanese (matches kanji OR reading)."""
        term = term.strip()
        results: list[DictionaryEntry] = []

        if term in self.by_kanji:
            results.extend(self.by_kanji[term])

        if term in self.by_reading:
            for e in self.by_reading[term]:
                if e not in results:
                    results.append(e)

        # Just return the first few to avoid spamming
        return results[:max_results]



    def lookup_english(self, term: str, max_results: int = 10) -> list[DictionaryEntry]:
        term = term.lower().strip()
        entries = self.by_english.get(term, [])
        return entries[:max_results]


