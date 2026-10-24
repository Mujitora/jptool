# dictionary_loader.py
import json


class DictionaryEntry:
    def __init__(self, kanji_list, reading_list, meanings, pos=None, tags=None, priority=None):
        self.kanji_list = kanji_list or []        # list[str]
        self.reading_list = reading_list or []    # list[str]
        self.meanings = meanings or []            # list[str]
        self.pos = pos or []                      # list[str]
        self.tags = tags or []                    # list[str]
        self.priority = priority or []            # JMdict priority codes

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
                priority=raw.get("priority", []),
            )
            self.entries.append(entry)

            # Index by each kanji form
            for kanji in entry.kanji_list:
                self.by_kanji.setdefault(kanji, []).append(entry)

            # Index by each reading form
            for reading in entry.reading_list:
                self.by_reading.setdefault(reading, []).append(entry)

            # Index by English words
            indexed_words = set()
            for meaning in entry.meanings:
                words = (
                    meaning.lower()
                    .replace(";", " ")
                    .replace(",", " ")
                    .split()
                )
                for word in words:
                    if word not in indexed_words:
                        self.by_english.setdefault(word, []).append(entry)
                        indexed_words.add(word)



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

        def relevance(entry: DictionaryEntry) -> tuple[int, int, int, int]:
            meanings = [meaning.strip().lower().strip(" .;,:!") for meaning in entry.meanings]
            meaning_bases = [meaning.split(" (", 1)[0].strip(" .;,:!") for meaning in meanings]
            primary_meaning = meanings[0] if meanings else ""
            primary_base = meaning_bases[0] if meaning_bases else ""
            exact_glosses = {term, f"to {term}"}

            if primary_base in exact_glosses:
                rank = 0
            elif any(meaning in exact_glosses for meaning in meaning_bases):
                rank = 1
            elif primary_meaning.startswith(f"to {term} ") or primary_meaning.startswith(f"{term} "):
                rank = 2
            else:
                rank = 3

            priority_tiers = {
                "ichi1": 0, "ichi2": 1,
                "news1": 2, "news2": 3,
                "spec1": 4, "spec2": 5,
                "gai1": 6, "gai2": 7,
            }
            tier = min((priority_tiers.get(code, 99) for code in entry.priority), default=99)
            frequencies = [int(code[2:]) for code in entry.priority if code.startswith("nf") and code[2:].isdigit()]
            frequency = min(frequencies, default=999)

            return rank, tier, frequency, 0 if entry.kanji_list else 1

        return sorted(entries, key=relevance)[:max_results]


