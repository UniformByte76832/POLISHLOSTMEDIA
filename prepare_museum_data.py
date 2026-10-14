"""
Generuje plik muzeum_data.js ze wszystkimi 315 artefaktami, wzbogaconymi o kategorie,
tytuły ekspozycji, opisy i metadane dla interfejsu Muzeum Archeologii Cyfrowej.
"""
import os
import json
import re

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ZNALEZISKA_DIR = os.path.join(PROJECT_DIR, "znaleziska")
METADATA_FILE = os.path.join(ZNALEZISKA_DIR, "metadata.json")
OUTPUT_JS = os.path.join(PROJECT_DIR, "muzeum_data.js")

def prepare_data():
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    curated = []

    for it in items:
        fn = it.get('filename', '')
        fmt = it.get('format', '')
        orig = it.get('original_url', '')
        size_str = it.get('size_str', '')
        date_str = it.get('date_str', '')
        details = it.get('details', '')
        local_rel = f"znaleziska/{fn}"

        # Ekstrakcja domeny
        domain = "Nieznana"
        if "republika.pl" in orig: domain = "republika.pl"
        elif "polbox" in orig: domain = "free.polbox.pl"
        elif "webpark.pl" in orig: domain = "webpark.pl"
        elif "geocities.com" in orig: domain = "geocities.com"
        elif "czaha.pl" in orig: domain = "czaha.pl"
        elif "100lat.info" in orig: domain = "100lat.info"
        elif "joemonster.org" in orig: domain = "joemonster.org"
        elif "neostrada.pl" in orig: domain = "cda / neostrada"

        # Rok
        year = date_str[:4] if len(date_str) >= 4 else "2000"

        # Kategoryzacja do skrzydeł muzeum
        if fn == "20030408_snakearena.swf":
            wing = "arcade"
            title = "Snake Arena 1.0 (UMK Toruń)"
            desc = "Autorska gra w węża z kwietnia 2003 roku z trybem single i multiplayer dla 2 graczy na 1 klawiaturze. Autor: TALEE (UMK Toruń)."
        elif fn == "20060511_mistrz_autobusu.swf":
            wing = "arcade"
            title = "Mistrz Autobusu (MPK 2006 by Czaha)"
            desc = "Kultowy polski symulator kierowcy autobusu miejskiego (luty 2006) z silnikiem kolizji hitTest, prędkościomierzem i czasem do przystanku. Autor: Czaha (czaha.pl)."
        elif fn == "20060301_aczy_trabka.swf":
            wing = "arcade"
            title = "'A' czy TRĄBKA ? (Elektryczna gra 2003/2006 by Czaha)"
            desc = "Kultowa polska gra towarzyska w wersji cyfrowej. Zgadnij co wypadnie: A czy trąbka? Silnik punktacji, losowania, 9 interaktywnych przycisków i unikalny humor Czahy."
        elif fn == "20061018_nalej_ruska_wodka.swf":
            wing = "arcade"
            title = "Podziel Ruską Wódkę (CDA / Milanos 2006)"
            desc = "Zręcznościowa minigra Flash polegająca na precyzyjnym rozlewaniu wódki do kieliszków. Zachowana z archiwum Milanos i CDA."
        elif fn == "2007_sextremalna_katapulta.swf":
            wing = "arcade"
            title = "Sextremalna Katapulta (JoeMonster 2007)"
            desc = "Fizyczna minigra zręcznościowa z katapultą i zbieraniem dopalaczy, zachowana z archiwum pobieralni Joe Monster."
        elif fn == "killvader2.0.rar":
            wing = "archive"
            title = "Kill Vader 2.0 (Gra PC Delphi by Czaha)"
            desc = "Oryginalna instalacja gry na PC w Delphi (2.6 MB) autorstwa Czahy z 2003 roku, zachowana w całości z dźwiękiem i tabelą rekordów."
        elif fn == "20060412_kaczki.swf":
            wing = "arcade"
            title = "Kaczki (Flash 2006)"
            desc = "Satyryczna polska produkcja Flash z kwietnia 2006 roku ocalona z serwera 100lat.info/kaczki."
        elif fmt == 'SWF':
            if any(k in fn.lower() for k in ['nauczyciel', 'laska', 'prezentacja', 'intro', 'movie', 'animacja']):
                wing = "cinema"
                title = f"Animacja Flash: {fn}"
                desc = f"Historyczna etiuda/animacja multimedialna z epoki ({details})."
            else:
                wing = "flash_artifacts"
                title = f"Projekt Flash: {fn}"
                desc = f"Interaktywny komponent lub intro WWW z domeny {domain} ({details})."
        elif fmt == 'MIDI':
            wing = "jukebox"
            if "closer" in fn.lower():
                title = "Nine Inch Nails – Closer (Sequenced by Warren Rice 1994)"
                desc = "Wybitna amatorska aranżacja na syntezator Roland SCC-1 z zaszytymi znacznikami tekstu karaoke z GeoCities SunsetStrip."
            elif "enjoy" in fn.lower():
                title = "Depeche Mode – Enjoy the Silence (Analog Synth Arr.)"
                desc = "16-ścieżkowa kompozycja syntezatorowa z GeoCities Tokyo."
            elif "orlacien" in fn.lower():
                title = "Varius Manx – Orła Cień (Dial-up Web Arr.)"
                desc = "Polska kompozycja z serwerów Polboxa, zoptymalizowana pod autoodtwarzanie w tle domowej witryny."
            elif "enterthedragon" in fn.lower():
                title = "Lalo Schifrin – Enter the Dragon (Wejście Smoka)"
                desc = "18-ścieżkowa orkiestrowa partytura z japońskimi znacznikami tekstowymi Shift-JIS."
            elif "backfutr" in fn.lower():
                title = "Alan Silvestri – Powrót do Przyszłości (Back to the Future)"
                desc = "Symfoniczny motyw orkiestrowy na 11 ścieżek z sekcją dętą i smyczkami."
            elif "batman" in fn.lower():
                title = "Batman Theme (Republika MIDI)"
                desc = "Kultowy motyw Batmana pobrany ze strony użytkownika adamczaja na Republice."
            elif "muppets" in fn.lower():
                title = "Muppet Show Theme"
                desc = "Motyw ze słynnego show ocalony ze strony agape_os na Republice."
            else:
                clean_title = fn.split('_')[-1].replace('.mid', '').replace('.MID', '')
                title = f"Utwór MIDI: {clean_title}"
                desc = f"Ścieżka dźwiękowa epoki ({details}) z domeny {domain}."
        elif fmt in ('GIF', 'JPEG', 'BMP'):
            wing = "gallery"
            clean_title = fn.split('_')[-1]
            title = f"Grafika archiwalna: {clean_title}"
            desc = f"Rozmiar: {details}, pochodzenie: {domain}."
        else:
            wing = "archive"
            title = fn
            desc = details

        curated.append({
            'filename': fn,
            'title': title,
            'desc': desc,
            'format': fmt,
            'wing': wing,
            'domain': domain,
            'year': year,
            'size_str': size_str,
            'date_str': date_str,
            'rel_path': local_rel,
            'details': details,
            'original_url': orig,
            'archive_url': it.get('archive_url', '')
        })

    js_content = f"// Wygenerowano automatycznie dla Muzeum Archeologii Cyfrowej\nwindow.MUSEUM_DATA = {json.dumps(curated, indent=2, ensure_ascii=False)};\n"
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Zapisano dane do {OUTPUT_JS} ({len(curated)} pozycji).")

if __name__ == "__main__":
    prepare_data()
