"""
Moduł Archiwisty (Archivist):
Pobiera surowe pliki z endpointu id_ Wayback Machine,
współpracuje z Analitykiem w celu odrzucenia śmieci i zapisuje czyste znaleziska w ./znaleziska/
oraz generuje katalog.md i aktualizuje metadata.json.
Wszystkie operacje logowane są wyłącznie do archeologia.log.
Brak wyjścia na stdout.
"""
import os
import sys
import re
import ssl
import json
import time
import hashlib
import logging
import urllib.request
import urllib.parse
from datetime import datetime

from analyst import verify_magic_bytes, is_repetitive_asset

logger = logging.getLogger("archeologia")

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) DigitalArchaeologyBot/2.0'
}

def sanitize_filename(filename: str) -> str:
    """Oczyszcza nazwę pliku z niedozwolonych znaków w systemie Windows."""
    clean = re.sub(r'[\\/*?:"<>|]', '_', filename)
    clean = clean.strip()
    return clean if clean else "unnamed_artifact"

def format_timestamp(ts: str) -> str:
    """Formatuje timestamp Wayback np. 20040822103156 na czytelną datę."""
    try:
        dt = datetime.strptime(ts[:14], "%Y%m%d%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts

def format_size(size_bytes: int) -> str:
    """Formatuje rozmiar w bajtach na KB / MB."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

class Archivist:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.catalog_path = os.path.join(output_dir, "katalog.md")
        self.state_path = os.path.join(output_dir, "metadata.json")
        self.ssl_ctx = ssl.create_default_context()
        os.makedirs(output_dir, exist_ok=True)
        self.archived_items = []
        self.seen_signatures = set()
        self.seen_digests = set()
        
        # Wczytanie sygnatur z Fali 1 (ocalonych i zarchiwizowanych na GitHubie)
        fala1_path = os.path.join(os.path.dirname(output_dir), "metadata_fala1.json")
        if os.path.exists(fala1_path):
            try:
                with open(fala1_path, "r", encoding="utf-8") as f:
                    fala1_items = json.load(f)
                    for it in fala1_items:
                        orig = it.get('original_url')
                        if orig: self.seen_signatures.add(orig)
                        dig = it.get('digest')
                        if dig and dig != "unknown": self.seen_digests.add(dig)
                logger.info("Archiwista: wczytano %d sygnatur z Fali 1 (GitHub)", len(self.seen_signatures))
            except Exception as e:
                logger.warning("Nie udalo sie wczytac metadata_fala1.json: %s", e)

        # Wczytanie poprzednich znalezisk bieżącej sesji jeśli istnieją
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    self.archived_items = json.load(f)
                    for it in self.archived_items:
                        orig = it.get('original_url')
                        if orig:
                            self.seen_signatures.add(orig)
                        dig = it.get('digest')
                        if dig and dig != "unknown":
                            self.seen_digests.add(dig)
                logger.info("Archiwista: wczytano %d istniejacych artefaktow z bazy", len(self.archived_items))
            except Exception as e:
                logger.error("Archiwista: blad wczytywania metadata.json: %s", e)
                self.archived_items = []

    def fetch_and_archive(self, item: dict) -> tuple[dict | None, str]:
        """
        Pobiera plik z Archive.org używając endpointu id_,
        weryfikuje binarne nagłówki i filtruje śmieci.
        Zwraca (record | None, status_code_string).
        Status code: 'SAVED', 'ALREADY_SEEN', 'DOWNLOAD_ERROR', 'INVALID_MAGIC', 'JUNK_REJECTED'
        """
        original_url = item.get('original', '')
        digest = item.get('digest', '')

        if original_url in self.seen_signatures:
            return None, 'ALREADY_SEEN'
        
        if digest and digest in self.seen_digests:
            return None, 'ALREADY_SEEN'
            
        timestamp = item.get('timestamp', '')
        clean_url = f"https://web.archive.org/web/{timestamp}id_/{original_url}"

        # Ekstrakcja podstawowej nazwy pliku
        url_path = urllib.parse.urlsplit(original_url).path
        base_name = os.path.basename(url_path)
        if not base_name or '.' not in base_name:
            ext = item.get('mimetype', '').split('/')[-1]
            base_name = f"artifact_{timestamp}.{ext}"

        safe_name = f"{timestamp[:8]}_{sanitize_filename(base_name)}"
        local_path = os.path.join(self.output_dir, safe_name)

        if os.path.exists(local_path):
            short_hash = digest[:6] if digest and digest != "unknown" else hashlib.md5(original_url.encode('utf-8')).hexdigest()[:6]
            name_part, ext_part = os.path.splitext(safe_name)
            safe_name = f"{name_part}_{short_hash}{ext_part}"
            local_path = os.path.join(self.output_dir, safe_name)

        logger.debug("Pobieranie id_: %s -> %s", clean_url, safe_name)
        req = urllib.request.Request(clean_url, headers=DEFAULT_HEADERS)
        content = None

        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=15) as resp:
                    content = resp.read()
                    break
            except Exception as e:
                logger.warning("Blad pobierania [proba %d/3] [%s]: %s", attempt + 1, clean_url, e)
                if attempt < 2:
                    time.sleep(1.5 * (2 ** attempt))

        if content is None:
            return None, 'DOWNLOAD_ERROR'

        # KROK 1: Weryfikacja nagłówków binarnych (Magic Bytes)
        is_valid, detected_fmt, details = verify_magic_bytes(content)
        if not is_valid:
            logger.debug("Odrzucono naglowki binarne [%s]: %s - %s", original_url, detected_fmt, details)
            return None, 'INVALID_MAGIC'

        # KROK 2: Analiza powtarzalności (odrzucanie logotypów, przycisków, bannerów)
        is_junk, reason = is_repetitive_asset(original_url, len(content), details)
        if is_junk:
            logger.debug("Odrzucono smiec WWW [%s]: %s", original_url, reason)
            return None, 'JUNK_REJECTED'

        # KROK 3: Zapis na dysku
        try:
            with open(local_path, "wb") as f:
                f.write(content)
        except Exception as e:
            logger.error("Blad zapisu pliku %s: %s", local_path, e)
            return None, 'DOWNLOAD_ERROR'

        record = {
            'filename': safe_name,
            'local_path': f"znaleziska/{safe_name}",
            'original_url': original_url,
            'archive_url': clean_url,
            'timestamp': timestamp,
            'date_str': format_timestamp(timestamp),
            'format': detected_fmt.upper(),
            'details': details,
            'size_bytes': len(content),
            'size_str': format_size(len(content)),
            'digest': digest
        }
        self.archived_items.append(record)
        self.seen_signatures.add(original_url)
        if digest:
            self.seen_digests.add(digest)

        logger.info("Zabezpieczono znalezisko: %s (%s, %s)", safe_name, record['size_str'], details)
        
        # Zapis stanu do metadata.json
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(self.archived_items, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Nie udalo sie zapisac metadata.json: %s", e)

        return record, 'SAVED'

    def generate_catalog(self):
        """Generuje katalog.md z podsumowaniem, miniaturami i metadanymi."""
        try:
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                f.write("# 🏛️ Muzeum Archeologii Cyfrowej: Katalog Znalezisk (1998–2006)\n\n")
                f.write(f"*Ostatnia aktualizacja ekspedycji: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                f.write("Niniejszy katalog dokumentuje ocalone artefakty multimedialne z epoki wczesnego polskiego i światowego internetu (m.in. `republika.pl`, `free.polbox.pl`, `webpark.pl` i `geocities.com`). Pliki zostały pobrane w oryginalnej, czystej postaci binarnej przy użyciu bezpośredniego endpointu `id_` na Internet Archive Wayback Machine.\n\n")
                
                f.write("## 📊 Podsumowanie Kolekcji\n\n")
                f.write(f"- **Łączna liczba zabezpieczonych obiektów:** {len(self.archived_items)}\n")
                total_bytes = sum(i['size_bytes'] for i in self.archived_items)
                f.write(f"- **Łączny rozmiar archiwum:** {format_size(total_bytes)}\n\n")

                f.write("## 🗂️ Tabela Znalezisk\n\n")
                f.write("| Podgląd / Typ | Plik i Opis | Rozmiar | Data Archiwizacji | Źródłowy URL & Archiwum |\n")
                f.write("| :---: | :--- | :---: | :---: | :--- |\n")

                for item in self.archived_items:
                    fname = item['filename']
                    fmt = item['format']
                    
                    if fmt in ('JPEG', 'GIF', 'BMP'):
                        preview = f"<img src=\"./{fname}\" width=\"100\" alt=\"{fname}\">"
                    elif fmt == 'MIDI':
                        preview = "🎵 **MIDI**"
                    elif fmt == 'SWF':
                        preview = "⚡ **FLASH**"
                    elif fmt == 'MOD':
                        preview = "💾 **MOD**"
                    else:
                        preview = f"📦 {fmt}"

                    f.write(f"| {preview} | **[{fname}](./{fname})**<br>_{item['details']}_ | {item['size_str']} | {item['date_str']} | [Oryginał]({item['original_url']})<br>[Wayback id_]({item['archive_url']}) |\n")

                f.write("\n---\n")
                f.write("*Wygenerowano automatycznie przez podsystem archeologii cyfrowej.*\n")
            logger.info("Katalog.md zaktualizowany pomyslnie (%d pozycji)", len(self.archived_items))
        except Exception as e:
            logger.error("Blad generowania katalog.md: %s", e)
