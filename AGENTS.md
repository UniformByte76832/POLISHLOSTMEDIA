# 🏛️ Konstytucja Projektu: Muzeum Archeologii Cyfrowej (`AGENTS.md`)

Niniejszy dokument stanowi bezwzględną specyfikację architektoniczną oraz zbiór reguł technicznych obowiązujących wszystkich agentów AI i programistów pracujących w tym repozytorium.

---

## 1. Architektura Potoku Badawczo-Archiwizacyjnego (Pipeline)

Wszystkie operacje poszukiwania, weryfikacji i włączania cyfrowych artefaktów (1997–2006) do Muzeum muszą przebiegać przez zunifikowany potok:

1. **`scraper.py` (Szperacz / Explorer):**
   - Odpytuje endpoint CDX API Internet Archive (`https://web.archive.org/cdx/search/cdx`).
   - Zawsze stosuje parametry optymalizacyjne: `collapse=digest`, `fl=timestamp,original,mimetype,digest,length`, `from=19980101`, `to=20061231`.
   - Domyślny `timeout=35` s, pętla ponawiania (do 3 prób z wykładniczym backoffem).
   - Wykonuje **pre-filtrowanie rekordów PRZED pobraniem** (odrzucanie plików poniżej `min_length` oraz pasujących do `is_repetitive_asset`).
2. **`analyst.py` (Analityk / Verifier):**
   - Weryfikuje autentyczność nagłówków binarnych (`verify_magic_bytes`): Macromedia Flash SWF (`FWS`/`CWS`/`ZWS`), MIDI (`MThd`), Amiga/PC Tracker MOD, archiwa RAR (`Rar!\x1a\x07`) i ZIP (`PK\x03\x04`), grafiki JPEG, GIF87a/89a, BMP.
   - Odczytuje z nagłówków SWF: wersję, typ kompresji, liczbę klatek oraz klatkaż FPS (8.8 fixed-point).
   - Odrzuca powtarzalne śmieci WWW i elementy szablonów (`is_repetitive_asset`) w oparciu o precyzyjne granice słów w adresach URL oraz wymiary banerów.
3. **`archivist.py` (Archiwista / Keeper):**
   - Pobiera czyste pliki binarne z bezpośredniego endpointu `id_` Wayback Machine (`https://web.archive.org/web/{ts}id_/{orig}`).
   - Reużywa kontekst SSL (`self.ssl_ctx`), stosuje retry (do 3 prób z backoffem 1.5 * 2^attempt).
   - Zapobiega kolizjom i nadpisywaniu plików – w przypadku duplikatu nazwy dopisuje 6-znakowy skrót `digest` lub hash MD5.
   - Zapisuje metadane do `znaleziska/metadata.json` i generuje `znaleziska/katalog.md`.
4. **`analyze_lost_media.py` (Klasyfikator Lost Media):**
   - Klasyfikuje zbiory do trzech poziomów unikatowości:
     - 🔴 **Tier 1:** Prawdziwe Lost Media / Autorskie Dzieła (gry Flash, gry PC, kreskówki, animacje, unikatowe utwory muzyczne, prywatne archiwa foto).
     - 🟡 **Tier 2:** Rzadkie aranżacje, rozbudowane projekty epoki, muzyka tła stron.
     - 🟢 **Tier 3:** Powszechne elementy layoutów, tła i ikony.
   - Generuje zaktualizowany raport `znaleziska/lost_media_raport.md`.
5. **`prepare_museum_data.py` (Eksporter Frontendu):**
   - Przetwarza `metadata.json` i generuje `muzeum_data.js` dla interfejsu WWW.
   - Przypisuje eksponaty do odpowiednich skrzydeł (`arcade`, `cinema`, `jukebox`, `gallery`, `archive`).
6. **Oficjalne Narzędzia Narzędziowe (CLI):**
   - `python inspect_swf.py <sciezka.swf>` – uniwersalna inspekcja nagłówka SWF, FPS, klatek, zmiennych ActionScript i napisów.
   - `python audit_collection.py` – całościowy audyt bazy `metadata.json`, sanitacja ścieżek i odrzucanie śmieci.

---

## 2. Bezwzględne Zasady i Zakazy (Code & Privacy Standards)

1. **ZAKAZ prywatnych ścieżek systemowych:**
   - Pole `'local_path'` w plikach JSON (`metadata.json`) oraz JS (`muzeum_data.js`) musi ZAWSZE mieć postać względną `"znaleziska/<filename>"` z ukośnikiem `/`.
   - W repozytorium, commitach i raportach nie może znaleźć się żadna bezwzględna ścieżka systemowa (z literą dysku i katalogiem domowym użytkownika).
2. **ZAKAZ jednorazowych skryptów badawczych:**
   - Nie twórz skryptów typu `analyze_autobus.py`, `check_gra.py` dla pojedynczych plików.
   - Zawsze używaj `python inspect_swf.py <sciezka>`.
3. **ZAKAZ nadpisywania autorskich opisów artefaktów:**
   - Podczas automatycznego audytu (`audit_collection.py`) pole `details` może być aktualizowane wyłącznie, jeśli zaczyna się od generycznego prefiksu maszynowego (`"Macromedia Flash SWF"`, `"Standard MIDI File"`, `"Obraz JPEG"`, `"Animacja/Obraz"`, `"Mapa bitowa BMP"`, `"Amiga / PC Tracker MOD"`).
   - Autorskie opisy (np. `"Polska gra Flash..."`, `"Kultowy symulator..."`) muszą pozostać nienaruszone.
4. **ZAKAZ używania flagi `--assume-unchanged` w Gicie:**
   - Nigdy nie ukrywaj zmian w plikach przed Gitem (`git update-index --assume-unchanged`). Wszystkie pliki metadanych, katalogi i zbiory mają być jawnie śledzone w commitach.

---

## 3. Obowiązkowa Lista Kontrolna po Każdej Sesji Wykopalisk

Po pobraniu, zmodyfikowaniu lub dodaniu jakichkolwiek artefaktów, KAŻDY agent ma obowiązek wykonać po kolei następujące 4 polecenia:

```bash
python audit_collection.py
python -c "from archivist import Archivist; Archivist('znaleziska').generate_catalog()"
python analyze_lost_media.py
python prepare_museum_data.py
```

Następnie należy sprawdzić poprawność ścieżek (brak `"Users"` i `"C:"`), zatwierdzić zmiany w Gicie i wypchnąć na gałąź `main`:

```bash
git add znaleziska/ metadata.json muzeum_data.js ...
git commit -m "..."
git push origin main
```
