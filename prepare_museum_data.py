"""
Generuje plik muzeum_data.js ze wszystkimi artefaktami z bazy,
wzbogaconymi o kategorie, skrzydła muzeum, klasyfikację Lost Media (Tier 1/2/3),
dynamicznie rozpoznane domeny i oczyszczone tytuły.
"""
import os
import json
import re
import urllib.parse
from analyze_lost_media import classify_item

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ZNALEZISKA_DIR = os.path.join(PROJECT_DIR, "znaleziska")
METADATA_FILE = os.path.join(ZNALEZISKA_DIR, "metadata.json")
OUTPUT_JS = os.path.join(PROJECT_DIR, "muzeum_data.js")

SPECIAL_CINEMA_FILES = {
    '20040929_sen_zlotowlosej_dziewczynki.swf': (
        "Sen Złotowłosej Dziewczynki (2004)",
        "Autorska poetycka animacja Flash z muzyką, opublikowana na Republice we wrześniu 2004 roku."
    ),
    '20031101_film.swf': (
        "Etiuda Filmowa Flash (2003)",
        "Krótkometrażowa etiuda animowana ocalona z prywatnej strony na Republice."
    ),
    '20040911_tasmafilm.swf': (
        "Taśma Filmowa (400 klatek, 2004)",
        "Polska animacja stylizowana na klasyczną taśmę celuloidową z 400 klatkami płynnego ruchu (Flash v5)."
    ),
    '20050225_gryzinskiatom.swf': (
        "Model Atomu Gryzińskiego (2005)",
        "Naukowa animacja dydaktyczna prezentująca model atomu według prof. Michała Gryzińskiego."
    ),
    '20041128_adam3,1.swf': (
        "Projekt Adam 3.1 (2004)",
        "Autorski cykl animacji Flash o przygodach Adama z archiwum Republiki."
    ),
    '20040616_bird.swf': (
        "Bird Animation (2004)",
        "Wektorowa animacja ornitologiczna z płynnym lotem ptaka ocalona z Webparku."
    ),
    '20021027_animegirl.swf': (
        "Anime Girl (Październik 2002)",
        "Wczesna animacja postaci w stylu anime z 2002 roku z archiwum GeoCities."
    ),
    '20040822_gamer.swf': (
        "Gamer (FlashZone 2004)",
        "Kultowa kreskówka o perypetiach zapalonego gracza z 2004 roku (555 KB, 1469 klatek)."
    ),
    '20040428_robaczek.swf': (
        "Robaczek (FlashZone 2004)",
        "Wybitna polska autorska animacja Flash (900 KB, 4734 klatki płynnego ruchu) z kwietnia 2004 roku."
    ),
    '20030820_emeryt.swf': (
        "Emeryt (FlashZone 2003)",
        "Satyryczna kreskówka z FlashZone o życiu polskiego emeryta (297 KB, 604 klatki)."
    ),
    '20031114_czolg.swf': (
        "Czołg (FlashZone 2003)",
        "Militarna animacja wektorowa z efektami dźwiękowymi z listopada 2003 roku."
    ),
    '20031114_edward.swf': (
        "Edward (FlashZone 2003)",
        "Autorska etiuda animowana z 2003 roku z FlashZone (460 KB, 402 klatki)."
    )
}

BLACKLISTED_NSFW_FILES = {
    '20030410_lowca.swf',
    '20030725_charli.swf',
    '20030512_bb3.swf',
    '20040522_baby.swf',
    '20051208_dancing_girl.swf',
    '20060310_baby.mid',
    '2007_sextremalna_katapulta.swf',
    '20030523_strona.swf'
}

def make_clean_title(filename: str) -> str:
    """Wyciąga i oczyszcza tytuł z nazwy pliku, usuwając prefiks daty i rozszerzenie."""
    raw = filename.split('_', 1)[1] if '_' in filename else filename
    no_ext = re.sub(r'\.[a-zA-Z0-9]+$', '', raw)
    clean = no_ext.replace('%20', ' ').replace('_', ' ')
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean if clean else filename

def detect_domain(original_url: str) -> str:
    """Rozpoznaje domenę pochodzenia artefaktu lub wyciąga hosta dynamicznie."""
    orig_lower = original_url.lower()
    if "republika.pl" in orig_lower:
        return "republika.pl"
    elif "polbox" in orig_lower:
        return "free.polbox.pl"
    elif "webpark.pl" in orig_lower:
        return "webpark.pl"
    elif "interia.pl" in orig_lower or "miasto.interia.pl" in orig_lower:
        return "miasto.interia.pl"
    elif "friko.pl" in orig_lower:
        return "friko.pl"
    elif "gery.pl" in orig_lower:
        return "gery.pl"
    elif "kki.net.pl" in orig_lower:
        return "kki.net.pl"
    elif "prv.pl" in orig_lower:
        return "prv.pl"
    elif "wp.pl" in orig_lower:
        return "wp.pl"
    elif "geocities.com" in orig_lower:
        return "geocities.com"
    elif "czaha.pl" in orig_lower:
        return "czaha.pl"
    elif "100lat.info" in orig_lower:
        return "100lat.info"
    elif "joemonster.org" in orig_lower:
        return "joemonster.org"
    elif "neostrada.pl" in orig_lower:
        return "cda / neostrada"
    elif "plocman.pl" in orig_lower or "flashzone" in orig_lower:
        return "flashzone.pl"

    # Dynamiczne wyciągnięcie hosta z URL
    try:
        parsed = urllib.parse.urlsplit(original_url)
        host = (parsed.hostname or parsed.netloc or "").split(':')[0].lower()
        if host.startswith("www."):
            host = host[4:]
        if host:
            return host
    except Exception:
        pass

    return "Internet z epoki"

def prepare_data():
    if not os.path.exists(METADATA_FILE):
        print(f"Błąd: Brak pliku {METADATA_FILE}")
        return

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    curated = []
    wing_counts = {}

    for it in items:
        fn = it.get('filename', '')
        if fn in BLACKLISTED_NSFW_FILES:
            continue
        fmt = it.get('format', '')
        orig = it.get('original_url', '')
        size_str = it.get('size_str', '')
        date_str = it.get('date_str', '')
        details = it.get('details', '')
        local_rel = f"znaleziska/{fn}"

        # 1. Dynamiczne rozpoznanie domeny
        domain = detect_domain(orig)

        # 2. Rok powstania
        year = date_str[:4] if len(date_str) >= 4 else "2000"

        # 3. Klasyfikacja Lost Media (Tier 1/2/3)
        tier, category, why_lost = classify_item(it, PROJECT_DIR)

        # 4. Tytuł bazowy
        clean_title = make_clean_title(fn)

        # 5. Przypisanie do skrzydeł muzeum oraz dedykowanych opisów
        if fn == "2002_fz_batyskaf.swf":
            wing = "arcade"
            title = "Batyskaf (Czerwiec 2002 by Marcin L.)"
            desc = "Najstarsza zachowana polska gra Flash (16 czerwca 2002, Flash v5) z legendarnego portalu FlashZone.pl. Sterowanie batyskafem, omijanie podwodnych skał i torpedy na Spację (Key.SPACE). Prawdziwy przełom archeologiczny!"
        elif fn == "2002_fz_arkanoid.swf":
            wing = "arcade"
            title = "Arkanoid (Czerwiec 2002 by Piotr K. Praga)"
            desc = "Polski zręcznościowy Arkanoid z 16 czerwca 2002 roku (Flash v5, 60 FPS) autorstwa Piotra K. (nokturnal.prv.pl / FlashZone). Zaawansowany silnik kolizji piłki, sterowanie paletką myszką i zbijanie klocków."
        elif fn == "2002_fz_zgadnij_liczbe.swf":
            wing = "arcade"
            title = "Zgadnij Liczbę (Czerwiec 2002 by Jarek Głowacki)"
            desc = "Interaktywna gra logiczna z 16 czerwca 2002 roku (Flash v5, 24 FPS) autorstwa Jarka Głowackiego (plonsk.prv.pl / FlashZone). Cyfrowy kalkulator z losowaniem liczb (Math.random) i licznikiem prób."
        elif fn == "20030408_snakearena.swf":
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
        elif "killvader2.0.rar" in fn:
            wing = "archive"
            title = "Kill Vader 2.0 (Gra PC Delphi by Czaha)"
            desc = "Oryginalna instalacja gry na PC w Delphi (2.5 MB) autorstwa Czahy (czaha.pl) z maja 2006 roku, zachowana w całości z dźwiękiem i instalatorem."
        elif "saper.swf" in fn:
            wing = "arcade"
            title = "Saper Flash (FlashZone 2003)"
            desc = "Polska adaptacja klasycznego Minesweepera z listopada 2003 roku z FlashZone.pl. Oznaczanie min i bezpieczne odkrywanie pól."
        elif "mini_golf1.swf" in fn:
            wing = "arcade"
            title = "Mini Golf (FlashZone 2003)"
            desc = "Polska gra w minigolfa z grudnia 2003 roku z symulacją fizyki toczenia piłki, celowaniem i siłą uderzenia (241 KB, 80 klatek)."
        elif "snakearena.swf" in fn:
            wing = "arcade"
            title = "Snake Arena (FlashZone 2003)"
            desc = "Zręcznościowa gra w węża z FlashZone.pl z listopada 2003 roku (74.7 KB)."
        elif "osteroids3.swf" in fn:
            wing = "arcade"
            title = "Osteroids 3 (FlashZone 2003)"
            desc = "Kosmiczna strzelanka zręcznościowa w stylu Asteroids z listopada 2003 roku (43.8 KB, 40 FPS)."
        elif "quizik.swf" in fn:
            wing = "arcade"
            title = "Quizik (FlashZone 2003)"
            desc = "Interaktywny teleturniej z wiedzy ogólnej z listopada 2003 roku z punktacją i pytaniami wielokrotnego wyboru."
        elif "snotshot.swf" in fn:
            wing = "arcade"
            title = "Snot Shot (FlashZone 2004)"
            desc = "Zręcznościowa minigra celownicza z sierpnia 2004 roku ocalona z portalu FlashZone."
        elif fn == "2005_jm_nu_pagadi.swf":
            wing = "arcade"
            title = "Wilk i Zając: Jajka (Nu, Pogodi! Flash 2005)"
            desc = "Kultowy radziecki klasyk z jajkami w polskiej wersji Flash z JoeMonster. Silnik z polskimi zmiennymi (zbite_jaja, skucha, kosz_pos), 4 koszyki i oryginalne dźwięki pikaczy."
        elif fn == "20070130_jm_killerquiz.swf":
            wing = "arcade"
            title = "Killer Quiz: Coder or Cannibal? (Joe Monster 2005)"
            desc = "Legendarny wirusowy quiz z Joe Monster: odgadnij czy postać to programista (twórca Scheme/Eiffel/Haskell) czy seryjny morderca. Oryginalne audio i punktacja."
        elif fn == "20060412_kaczki.swf":
            wing = "arcade"
            title = "Kaczki (Flash 2006)"
            desc = "Satyryczna polska produkcja Flash z kwietnia 2006 roku ocalona z serwera 100lat.info/kaczki."
        elif fn == "20050507_jm_clinicgame.swf":
            wing = "arcade"
            title = "Clinic Game (Joe Monster 2005)"
            desc = "Satyryczna minigra medyczno-zręcznościowa z Joe Monster (maj 2005): dyżur lekarski z licznikiem punktów (score), poziomami trudności i upływającym czasem."
        elif fn == "20030528_Unreal_Tournament.swf":
            wing = "arcade"
            title = "Unreal Tournament Flash (Maj 2003)"
            desc = "Kultowy FPS w wersji Flash 2D ocalony z klanowej strony na Republice. Interaktywna minigra z uniwersum UT z 401 klatkami animacji broni i pojedynków."
        elif fn == "20040914_FirstStrike.swf":
            wing = "arcade"
            title = "First Strike (Wrzesień 2004)"
            desc = "Dynamiczna minigra zręcznościowa / symulator walki powietrznej ocalony z prywatnej witryny na Republice (104 klatki, Flash v4)."
        elif fn == "20030927_matematikon.swf":
            wing = "arcade"
            title = "Matematikon (Wrzesień 2003)"
            desc = "Polska gra logiczno-edukacyjna sprawdzająca refleks i umiejętności matematyczne pod presją uciekającego czasu (Flash v5)."
        elif fn == "20041025_gra.swf":
            wing = "arcade"
            title = "Szkolna Gra Zręcznościowa (Liceum Kossutha 2004)"
            desc = "Unikatowa amatorska minigra Flash v3 stworzona przez uczniów warszawskiego liceum im. Kossutha na platformie Webpark."
        elif fn == "20040616_growl_karaokie.swf":
            wing = "arcade"
            title = "Growl Karaoke (Czerwiec 2004)"
            desc = "Muzyczna gra interaktywna w stylu deathmetalowego karaoke z serwera 100lat.info/webpark.pl (526 KB, 678 klatek). Wokalne wyzwanie epoki!"
        elif fn in SPECIAL_CINEMA_FILES:
            wing = "cinema"
            title, desc = SPECIAL_CINEMA_FILES[fn]
        elif fmt == 'SWF':
            if category == "🎮 Zaginiona Gra Flash":
                wing = "arcade"
                title = f"Gra Flash: {clean_title}"
                desc = f"Interaktywna gra Flash z epoki ({details}) z domeny {domain}."
            elif "100lat.info" in orig.lower():
                wing = "cinema"
                title = f"100lat.info: Skecz {clean_title}"
                desc = f"Polska satyryczna etiuda Flash z kultowego portalu 100lat.info z maja 2006 roku ({details})."
            elif category == "🎬 Autorska Animacja / Kreskówka" or any(k in fn.lower() for k in ['nauczyciel', 'laska', 'prezentacja', 'intro', 'movie', 'animacja', 'projekt', 'film']):
                wing = "cinema"
                title = f"Animacja Flash: {clean_title}"
                desc = f"Historyczna etiuda/animacja multimedialna z epoki ({details}) z domeny {domain}."
            else:
                wing = "flash_artifacts"
                title = f"Projekt Flash: {clean_title}"
                desc = f"Interaktywny komponent lub intro WWW z domeny {domain} ({details})."
        elif fmt == 'MIDI':
            wing = "jukebox"
            if "alanp" in orig.lower():
                title = f"The Alan Parsons Project – {clean_title} (KKI Kraków 2000)"
                desc = f"Archiwalna aranżacja MIDI utworu The Alan Parsons Project ocalona z serwera KKI Kraków (maj-lipiec 2000). {details}."
            elif "closer" in fn.lower():
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
                title = f"Utwór MIDI: {clean_title}"
                desc = f"Ścieżka dźwiękowa epoki ({details}) z domeny {domain}."
        elif fmt in ('GIF', 'JPEG', 'BMP'):
            wing = "gallery"
            title = f"Grafika archiwalna: {clean_title}"
            desc = f"Rozmiar: {details}, pochodzenie: {domain}."
        else:
            wing = "archive"
            if "amkonw" in fn.lower():
                title = "AmKonw (Konwerter Znaków Amiga/PC 1999)"
                desc = "Narzędzie konwertujące polskie strony kodowe (AmigaPL / Mazovia / CP1250) z serwera KKI z października 1999 r."
            elif "amslowo" in fn.lower():
                title = "AmSłowo (Baza Słownikowa Amiga 1999)"
                desc = "Archiwalne narzędzie tekstowe dla Amigi z serwera krakowskiego KKI z maja 1999 r."
            elif "stars" in fn.lower():
                title = "Stars Demo (Demoscena KKI 1999)"
                desc = "Animacja gwiazdowa z archiwum demosceny KKI z listopada 1999 r."
            else:
                title = clean_title
                desc = details

        wing_counts[wing] = wing_counts.get(wing, 0) + 1

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
            'archive_url': it.get('archive_url', ''),
            'tier': tier,
            'category': category,
            'why_lost': why_lost
        })

    js_content = f"// Wygenerowano automatycznie dla Muzeum Archeologii Cyfrowej\nwindow.MUSEUM_DATA = {json.dumps(curated, indent=2, ensure_ascii=False)};\n"
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Zapisano dane do {OUTPUT_JS} ({len(curated)} pozycji).")
    print("Rozkład eksponatów pomiędzy skrzydła:")
    for w, count in sorted(wing_counts.items(), key=lambda x: -x[1]):
        print(f"  * Skrzydło '{w}': {count} eksponatów")

if __name__ == "__main__":
    prepare_data()
