# convert_jmdict_to_json.py
import xml.etree.ElementTree as ET
import json

INPUT_XML = "data/JMdict.xml"      # local name
OUTPUT_JSON = "data/jmdict.json"

def main():
    tree = ET.parse(INPUT_XML)
    root = tree.getroot()

    entries = []

    for entry in root.findall("entry"):
        # Kanji elements (k_ele/keb)
        kanji_list = [keb.text for keb in entry.findall("k_ele/keb") if keb.text]

        # Reading elements (r_ele/reb)
        reading_list = [reb.text for reb in entry.findall("r_ele/reb") if reb.text]

        meanings = []
        pos_tags = set()
        priority_codes = []

        for priority in entry.findall(".//ke_pri") + entry.findall(".//re_pri"):
            if priority.text and priority.text not in priority_codes:
                priority_codes.append(priority.text)

        for sense in entry.findall("sense"):
            # English glosses
            for gloss in sense.findall("gloss"):
                lang = gloss.get("lang", "eng")
                if lang == "eng" and gloss.text:
                    meanings.append(gloss.text)

            # Part-of-speech tags (optional)
            for pos in sense.findall("pos"):
                if pos.text:
                    pos_tags.add(pos.text)

        # Only keep entries that actually have English meanings
        if not meanings:
            continue

        entries.append({
            "kanji": kanji_list,
            "readings": reading_list,
            "meanings": meanings,
            "pos": sorted(pos_tags),
            "tags": [],
            "priority": priority_codes,
        })

    print(f"Parsed {len(entries)} entries")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"Wrote JSON to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
