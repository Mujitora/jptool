# main.py
from dictionary_loader import Dictionary, DictionaryEntry
from translator import Translator

MAX_MEANINGS_SHOWN = 999  # per entry

def print_results(result):
    language = result.language
    query = result.query
    entries: list[DictionaryEntry] = result.entries

    print(f"\nDetected language: {language}")
    print(f"Query: {query!r}")

    if not entries:
        print("  (no matches)")
        return

    print(f"Showing {len(entries)} result(s):\n")

    for i, entry in enumerate(entries, start=1):
        kanji = entry.kanji if entry.kanji is not None else "(kana only)"
        reading = entry.reading
        pos = ", ".join(entry.pos) if entry.pos else "unknown"

        print(f"{i}) {kanji} ({reading})  [{pos}]")

        # Limit meanings per entry
        if entry.meanings:
            for j, m in enumerate(entry.meanings[:MAX_MEANINGS_SHOWN], start=1):
                print(f"   - {m}")
            if len(entry.meanings) > MAX_MEANINGS_SHOWN:
                remaining = len(entry.meanings) - MAX_MEANINGS_SHOWN
                print(f"   ... (+{remaining} more meanings)")
        else:
            print("   - (no meanings)")

def main():
    dict_path = "data/jmdict.json"
    dictionary = Dictionary(dict_path)
    translator = Translator(dictionary)

    print("JP↔EN offline dictionary")
    print("Type a word (Japanese or English), or 'quit' to exit.\n")

    while True:
        text = input("> ").strip()
        if text.lower() in {"q", "quit", "exit"}:
            break
        if not text:
            continue

        result = translator.translate_word(text)
        print_results(result)
        print()


if __name__ == "__main__":
    main()
