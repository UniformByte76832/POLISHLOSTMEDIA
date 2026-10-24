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
        "local_path": "znaleziska/20060511_mistrz_autobusu.swf",
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
        "local_path": "znaleziska/20060412_kaczki.swf",
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
        "local_path": "znaleziska/20060301_aczy_trabka.swf",
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
        "local_path": "znaleziska/20061018_nalej_ruska_wodka.swf",
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
        "filename": "killvader2.0.rar",
        "local_path": "znaleziska/killvader2.0.rar",
        "original_url": "http://czaha.pl/killvader2.0.rar",
        "archive_url": "https://web.archive.org/web/20060301235829id_/http://czaha.pl/killvader2.0.rar",
        "timestamp": "20060301",
        "date_str": "2006-03-01 23:58:29",
        "format": "RAR",
        "details": "Polska gra PC Borland Delphi: Kill Vader 2.0 by Czaha (2.6 MB, pełna wersja z dźwiękiem i tabelą rekordów)",
        "size_bytes": 2604212,
        "size_str": "2.48 MB",
        "digest": "27b3f5e6170b9c1a"
    },
    {
        "filename": "2005_jm_nu_pagadi.swf",
        "local_path": "znaleziska/2005_jm_nu_pagadi.swf",
        "original_url": "http://download.joemonster.org/flash/Gierki/nu_pagadi.swf",
        "archive_url": "https://web.archive.org/web/20141208020010id_/http://download.joemonster.org/flash/Gierki/nu_pagadi.swf",
        "timestamp": "20050602",
        "date_str": "2005-06-02 01:25:13",
        "format": "SWF",
        "details": "Polska gra Flash v5: Wilk i Zając: Jajka (Nu, Pogodi!) z JoeMonster (ActionScript: zbite_jaja, skucha, kosz_pos, punkty)",
        "size_bytes": 66067,
        "size_str": "64.5 KB",
        "digest": "308d7490ece521e2"
    },
    {
        "filename": "20070130_jm_killerquiz.swf",
        "local_path": "znaleziska/20070130_jm_killerquiz.swf",
        "original_url": "http://download.joemonster.org/flash/Gierki/killerquiz.swf",
        "archive_url": "https://web.archive.org/web/20070130004806id_/http://download.joemonster.org/flash/Gierki/killerquiz.swf",
        "timestamp": "20070130",
        "date_str": "2007-01-30 00:48:06",
        "format": "SWF",
        "details": "Gra Flash v5: Killer Quiz - Coder or Cannibal? z Joe Monster (Bertrand Meyer, Gerald Sussman, David Berkowitz)",
        "size_bytes": 267018,
        "size_str": "260.8 KB",
        "digest": "e8e55b4d4ff5855b"
    },
    {
        "filename": "2002_fz_batyskaf.swf",
        "local_path": "znaleziska/2002_fz_batyskaf.swf",
        "original_url": "http://flashzone.plocman.pl/open_source/swfy/batyskaf.swf",
        "archive_url": "https://web.archive.org/web/20020823000000id_/http://flashzone.plocman.pl/open_source/swfy/batyskaf.swf",
        "timestamp": "20020616",
        "date_str": "2002-06-16 00:00:00",
        "format": "SWF",
        "details": "Polska gra Flash v5 z czerwca 2002 r.: Batyskaf by Marcin L. (FlashZone Open Source, 140 KB, 6 dźwięków, torpedy na spację)",
        "size_bytes": 140506,
        "size_str": "137.2 KB",
        "digest": "352d18dd1663a9e9"
    },
    {
        "filename": "2002_fz_arkanoid.swf",
        "local_path": "znaleziska/2002_fz_arkanoid.swf",
        "original_url": "http://flashzone.plocman.pl/open_source/swfy/arkanoid.swf",
        "archive_url": "https://web.archive.org/web/20020823000000id_/http://flashzone.plocman.pl/open_source/swfy/arkanoid.swf",
        "timestamp": "20020616",
        "date_str": "2002-06-16 00:00:00",
        "format": "SWF",
        "details": "Polska gra Flash v5 z czerwca 2002 r.: Arkanoid by Piotr K. Praga (FlashZone, 60 FPS, sterowanie myszką, punkty, kulki)",
        "size_bytes": 14748,
        "size_str": "14.4 KB",
        "digest": "1d6aae9dd5b55667"
    },
    {
        "filename": "2002_fz_zgadnij_liczbe.swf",
        "local_path": "znaleziska/2002_fz_zgadnij_liczbe.swf",
        "original_url": "http://flashzone.plocman.pl/open_source/swfy/zgadnij_liczbe.swf",
        "archive_url": "https://web.archive.org/web/20020823000000id_/http://flashzone.plocman.pl/open_source/swfy/zgadnij_liczbe.swf",
        "timestamp": "20020616",
        "date_str": "2002-06-16 00:00:00",
        "format": "SWF",
        "details": "Polska gra Flash v5 z czerwca 2002 r.: Zgadnij Liczbę by Jarek Głowacki (FlashZone, losowanie liczb, enter, backspace)",
        "size_bytes": 20270,
        "size_str": "19.8 KB",
        "digest": "77fff87aafb8d4e1"
    }
]

item_by_filename = {it['filename']: it for it in items}
added = 0
updated = 0

for ng in new_games:
    fn = ng['filename']
    if fn in item_by_filename:
        target = item_by_filename[fn]
        target['local_path'] = ng['local_path']
        target['timestamp'] = ng['timestamp']
        target['date_str'] = ng['date_str']
        target['details'] = ng['details']
        updated += 1
    else:
        items.append(ng)
        item_by_filename[fn] = ng
        added += 1

with open(METADATA_FILE, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

print(f"Zaktualizowano {updated} artefaktów, dodano {added} nowych. Łącznie: {len(items)} artefaktów.")
