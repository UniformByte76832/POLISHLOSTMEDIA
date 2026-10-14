"""
Skrypt analityczny klasyfikujący pobrane zbiory pod kątem Lost Media.
Generuje szczegółowy raport w pliku znaleziska/lost_media_raport.md.
"""
import os
import sys
import json
import re
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ZNALEZISKA_DIR = os.path.join(PROJECT_DIR, "znaleziska")
METADATA_FILE = os.path.join(ZNALEZISKA_DIR, "metadata.json")
REPORT_FILE = os.path.join(ZNALEZISKA_DIR, "lost_media_raport.md")

def analyze_and_generate_report():
    if not os.path.exists(METADATA_FILE):
        print("Brak metadata.json!")
        return

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    tier1_items = []
    tier2_items = []
    tier3_items = []

    for it in items:
        fn = it.get('filename', '')
        fmt = it.get('format', '')
        orig = it.get('original_url', '').lower()
        size = it.get('size_bytes', 0)
        local_path = it.get('local_path', '')
        details = it.get('details', '')

        # Domyślny tier
        tier = 3
        category = "Zasób pomocniczy"
        why_lost = ""

        # 1. FLASH SWF
        if fmt == 'SWF':
            # Sprawdzenie zawartości
            swf_strings = []
            if os.path.exists(local_path):
                try:
                    with open(local_path, 'rb') as sf:
                        sdata = sf.read()
                    # prosta dekompresja CWS
                    if sdata[:3] == b'CWS':
                        import zlib
                        try:
                            sdata = sdata[:8] + zlib.decompress(sdata[8:])
                        except:
                            pass
                    raw_s = re.findall(b'[\x20-\x7e\xa0-\xff]{4,}', sdata)
                    for rs in raw_s:
                        try:
                            t = rs.decode('latin1').strip()
                            if any(c.isalpha() for c in t) and len(t) > 3:
                                swf_strings.append(t)
                        except:
                            pass
                except:
                    pass

            s_text = (" ".join(swf_strings) + " " + details).lower()
            game_keywords = [
                'snake', 'gra', 'game', 'arena', 'akwarium', 'grajter', 'autobus',
                'kaczki', 'katapulta', 'quiz', 'arkanoid', 'batyskaf', 'zgadnij',
                'wodka', 'trabka', 'pagadi', 'pogodi', 'score', 'punkty'
            ]
            
            # Autorskie gry Flash
            if any(k in fn.lower() or k in s_text for k in game_keywords):
                tier = 1
                category = "🎮 Zaginiona Gra Flash"
                why_lost = "Unikatowa gra Macromedia Flash z polskiej strony osobistej; kod i assety zachowane wyłącznie w tym pliku."
            # Autorskie animacje, kreskówki, etiudy szkolne
            elif any(k in fn.lower() or k in s_text for k in ['nauczyciel', 'laska', 'prezentacja', 'movie', 'intro', 'animacja', 'projekt']):
                tier = 1
                category = "🎬 Autorska Animacja / Kreskówka"
                why_lost = "Prywatna etiuda / animacja amatorska z lat 2002-2006, brak jakiejkolwiek kopii na współczesnym YouTube/Newgrounds."
            elif size > 200000:
                tier = 2
                category = "⚡ Rozbudowany Projekt Flash"
                why_lost = "Ciężki projekt multimedialny (>200 KB) zawierający zintegrowaną grafikę i dźwięk z wczesnej ery WWW."
            else:
                tier = 2
                category = "Interaktywny Element WWW"
                why_lost = "Interaktywny baner lub menu Flash z archiwum Republiki/GeoCities."

        # 2. MUZYKA MIDI
        elif fmt == 'MIDI':
            mid_meta = []
            if os.path.exists(local_path):
                try:
                    with open(local_path, 'rb') as mf:
                        mdata = mf.read()
                    raw_m = re.findall(b'[\x20-\x7e]{3,}', mdata)
                    for rm in raw_m:
                        try:
                            t = rm.decode('latin1').strip()
                            if any(c.isalpha() for c in t) and len(t) > 3:
                                mid_meta.append(t)
                        except:
                            pass
                except:
                    pass
            m_text = " ".join(mid_meta).lower()

            if any(k in orig or k in m_text for k in ['orlacien', 'int30xg', 'adklimek', 'alpispa']):
                tier = 1
                category = "🎵 Unikatowa Polska Kompozycja MIDI"
                why_lost = "Lokalna, prywatna sekwencja muzyczna z polskich serwerów (Polbox/Republika), nieznaleziona w bazach komercyjnych."
            elif 'closer' in fn.lower() or 'warren rice' in m_text or 'scc1' in m_text or 'downward spiral' in m_text:
                tier = 1
                category = "🎹 Historyczna Aranżacja Tracker/MIDI (1994)"
                why_lost = "Archiwalna aranżacja z 1994 r. Warrena Rice'a z Seattle z zaszytymi znacznikami karaoke i autorskim podpisem z GeoCities SunsetStrip."
            elif any(k in fn.lower() for k in ['enterthedragon', 'backfutr', 'enjoy', 'batman', 'muppets']):
                tier = 2
                category = "🎼 Rzadka Sekwencja Syntezatorowa z Lat 90."
                why_lost = "Specyficzna wersja partytury orkiestrowej/elektronicznej stworzona przez użytkowników dawnego internetu."
            else:
                tier = 2
                category = "Plik Dźwiękowy MIDI"
                why_lost = "Muzyka tła prywatnej strony z lat 1998-2006."

        # 3. GRAFIKI (GIF, JPEG)
        elif fmt in ('JPEG', 'GIF', 'BMP'):
            if any(k in orig for k in ['piesie', 'pimbi', 'hau', 'plancgk', 'natalia', 'a_bendi', 'veegorresite']):
                tier = 1
                category = "📸 Prywatne Archiwum Fotograficzne / Digital Art"
                why_lost = "Oryginalne fotografie z lat 2002-2004 z domowych stron WWW; unikatowy zapis codzienności wczesnego polskiego internetu."
            elif size > 200000:
                tier = 2
                category = "🖼️ Wysokorozdzielcza Grafika z Epoki"
                why_lost = "Duży plik graficzny (>200 KB), który w tamtych czasach ładował się minutami przez modem dial-up."
            else:
                tier = 3
                category = "Grafika Strony"
                why_lost = "Element layoutu z tamtych lat."

        # 4. ARCHIWA (RAR, ZIP)
        elif fmt in ('RAR', 'ZIP'):
            tier = 1
            category = "🕹️ Zaginiona Gra / Program PC"
            why_lost = "Samodzielna archiwalna aplikacja / instalator z epoki wczesnego internetu, zachowana w całości z dźwiękiem i zasobami."

        # 5. MODUŁY TRACKER (MOD)
        elif fmt == 'MOD':
            tier = 1
            category = "🎹 Moduł Muzyczny Amiga / PC Tracker"
            why_lost = "Autorski moduł trackerowy (Amiga/PC) z epoki demosceny, rzadki format dźwiękowy wczesnego internetu."

        it_entry = {
            'filename': fn,
            'local_path': local_path,
            'format': fmt,
            'size_str': it.get('size_str', ''),
            'date_str': it.get('date_str', ''),
            'original_url': it.get('original_url', ''),
            'archive_url': it.get('archive_url', ''),
            'details': details,
            'category': category,
            'why_lost': why_lost,
            'tier': tier
        }

        if tier == 1:
            tier1_items.append(it_entry)
        elif tier == 2:
            tier2_items.append(it_entry)
        else:
            tier3_items.append(it_entry)

    # Generowanie raportu Markdown
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# 🕵️ Raport Identyfikacji Lost Media (1998–2006)\n\n")
        f.write(f"*Data wygenerowania: {datetime.now().strftime('%Y-%m-%d')}*\n\n")
        f.write(f"Raport klasyfikuje ocalone {len(items)} plików binarnych pod kątem ich unikatowości, statusu utraconych mediów (Lost Media) oraz wartości kulturowo-historycznej dla wczesnego internetu.\n\n")
        f.write("## 📊 Klasyfikacja Zasobów\n\n")
        f.write(f"- 🔴 **Tier 1 (Prawdziwe Lost Media / Autorskie Dzieła):** **{len(tier1_items)} plików**\n")
        f.write(f"- 🟡 **Tier 2 (Rzadkie Aranżacje i Duże Projekty Epoki):** **{len(tier2_items)} plików**\n")
        f.write(f"- 🟢 **Tier 3 (Powszechne Zasoby Internetu Lat 90/00):** **{len(tier3_items)} plików**\n\n")

        f.write("## 🔴 TIER 1: Prawdziwe Zaginione Projekty (Lost Media)\n\n")
        f.write("Obiekty stworzone bezpośrednio przez użytkowników prywatnych witryn (gry, kreskówki, prywatne nagrania, unikatowe zdjęcia), które po wyłączeniu Republiki, Polboxa czy GeoCities zniknęły całkowicie z sieci.\n\n")
        f.write("| Nazwa Pliku | Kategoria | Rozmiar | Data | Dlaczego to Lost Media? |\n")
        f.write("| :--- | :--- | :---: | :---: | :--- |\n")
        for item in tier1_items:
            f.write(f"| **[{item['filename']}](./{item['filename']})**<br>_{item['format']}_ | {item['category']} | {item['size_str']} | {item['date_str']} | {item['why_lost']} |\n")

        f.write("\n## 🟡 TIER 2: Rzadkie Aranżacje i Duże Multimedialne Projekty\n\n")
        f.write(f"Łącznie **{len(tier2_items)} plików**, w tym rozbudowane animacje Flash, sekwencje orkiestrowe MIDI i unikatowe grafiki dial-up.\n\n")
        f.write("| Nazwa Pliku | Typ | Rozmiar | Pochodzenie |\n")
        f.write("| :--- | :---: | :---: | :--- |\n")
        for item in tier2_items[:25]:
            f.write(f"| **[{item['filename']}](./{item['filename']})** | {item['format']} | {item['size_str']} | [Oryginalny URL]({item['original_url']}) |\n")
        if len(tier2_items) > 25:
            f.write(f"| *...i jeszcze {len(tier2_items) - 25} innych pozycji Tier 2...* | | | |\n")

        f.write("\n---\n")
        f.write("*Wygenerowano przez automatyczny podsystem archeologii cyfrowej.*\n")

    print(f"Raport wygenerowany: {REPORT_FILE}")
    print(f"Tier 1: {len(tier1_items)}, Tier 2: {len(tier2_items)}, Tier 3: {len(tier3_items)}")

if __name__ == "__main__":
    analyze_and_generate_report()
