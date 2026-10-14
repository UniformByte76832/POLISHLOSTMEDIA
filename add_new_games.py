import os
import json

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ZNALEZISKA_DIR = os.path.join(PROJECT_DIR, "znaleziska")
METADATA_FILE = os.path.join(ZNALEZISKA_DIR, "metadata.json")

with open(METADATA_FILE, "r", encoding="utf-8") as f:
    items = json.load(f)

existing_filenames = set(it['filename'] for it in items)

new_games = [
    {
        "filename": "20060511_mistrz_autobusu.swf",
        "local_path": os.path.join(ZNALEZISKA_DIR, "20060511_mistrz_autobusu.swf"),
        "original_url": "http://czaha.pl:80/autobus/autobus6.swf",
        "archive_url": "https://web.archive.org/web/20060511224445id_/http://czaha.pl:80/autobus/autobus6.swf",
        "timestamp": "20060511",
        "date_str": "2006-05-11 22:44:45",
        "format": "SWF",
        "details": "Polska gra Flash v6: Mistrz Autobusu (MPK) by Czaha (1073 klatki, 786 KB)",
        "size_bytes": 804971,
        "size_str": "786.1 KB",
        "digest": "MEU423ASAQVLS5Q7YSPM3TRIMZR3RDXM"
    },
    {
        "filename": "20060412_kaczki.swf",
        "local_path": os.path.join(ZNALEZISKA_DIR, "20060412_kaczki.swf"),
        "original_url": "http://100lat.info:80/kaczki/kaczki.swf",
        "archive_url": "https://web.archive.org/web/20060412113914id_/http://100lat.info:80/kaczki/kaczki.swf",
        "timestamp": "20060412",
        "date_str": "2006-04-12 11:39:14",
        "format": "SWF",
        "details": "Polska produkcja Flash v6 (532 KB) ocalona z 100lat.info",
        "size_bytes": 544739,
        "size_str": "532.0 KB",
        "digest": "FUKV2I5AZDFNL2LXRF3J6C33J5KWBRZM"
    },
    {
        "filename": "20060301_aczy_trabka.swf",
        "local_path": os.path.join(ZNALEZISKA_DIR, "20060301_aczy_trabka.swf"),
        "original_url": "http://czaha.pl/aczy.swf",
        "archive_url": "https://web.archive.org/web/20060301235829id_/http://czaha.pl/aczy.swf",
        "timestamp": "20060301",
        "date_str": "2006-03-01 23:58:29",
        "format": "SWF",
        "details": "Polska gra Flash v6: 'A' czy TRĄBKA? by Czaha (Subik, Jacek, Khaktooff, Zawur) (226 klatek, 9 przycisków, licznik punktów)",
        "size_bytes": 24669,
        "size_str": "24.1 KB",
        "digest": "1287954169838ad0"
    },
    {
        "filename": "20061018_nalej_ruska_wodka.swf",
        "local_path": os.path.join(ZNALEZISKA_DIR, "20061018_nalej_ruska_wodka.swf"),
        "original_url": "http://dorotka-cda.neostrada.pl/nalej.swf",
        "archive_url": "https://web.archive.org/web/20061018015428id_/http://dorotka-cda.neostrada.pl:80/nalej.swf",
        "timestamp": "20061018",
        "date_str": "2006-10-18 01:54:28",
        "format": "SWF",
        "details": "Polska gra Flash v7: Podziel Ruską Wódkę (CDA / Milanos 2006)",
        "size_bytes": 7918,
        "size_str": "7.7 KB",
        "digest": "170dfa54b3fb4170"
    },
    {
        "filename": "2007_sextremalna_katapulta.swf",
        "local_path": os.path.join(ZNALEZISKA_DIR, "2007_sextremalna_katapulta.swf"),
        "original_url": "http://download.joemonster.org/h/sextremalnakatapulta.swf",
        "archive_url": "https://web.archive.org/web/20140929131512id_/http://download.joemonster.org/h/sextremalnakatapulta.swf",
        "timestamp": "20071120",
        "date_str": "2007-11-20 00:00:00",
        "format": "SWF",
        "details": "Gra Flash v8: Sextremalna Katapulta z JoeMonster (1.1 MB, silnik fizyki)",
        "size_bytes": 1119715,
        "size_str": "1.07 MB",
        "digest": "8e7b2290d052f646"
    },
    {
        "filename": "killvader2.0.rar",
        "local_path": os.path.join(ZNALEZISKA_DIR, "killvader2.0.rar"),
        "original_url": "http://czaha.pl/killvader2.0.rar",
        "archive_url": "https://web.archive.org/web/20060301235829id_/http://czaha.pl/killvader2.0.rar",
        "timestamp": "20060301",
        "date_str": "2006-03-01 23:58:29",
        "format": "RAR",
        "details": "Polska gra PC Borland Delphi: Kill Vader 2.0 by Czaha (2.6 MB, pełna wersja z dźwiękiem i tabelą rekordów)",
        "size_bytes": 2604212,
        "size_str": "2.48 MB",
        "digest": "27b3f5e6170b9c1a"
    }
]

added = 0
for ng in new_games:
    if ng['filename'] not in existing_filenames:
        items.append(ng)
        existing_filenames.add(ng['filename'])
        added += 1

with open(METADATA_FILE, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f"Dodano {added} nowych zweryfikowanych artefaktów do metadata.json. Łącznie: {len(items)} artefaktów.")
