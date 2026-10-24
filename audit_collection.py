"""
Skrypt audytu bazy znalezisk i migracji metadanych:
1. Migracja nazw plików (usunięcie %20 i spacji na dysku i w metadata.json).
2. Normalizacja local_path do postaci 'znaleziska/<filename>'.
3. Wsteczna weryfikacja binarna nagłówków (verify_magic_bytes).
4. Wsteczna filtracja szablonowych śmieci WWW i mikro-przycisków SWF (is_repetitive_asset).
5. Zachowanie autorskich opisów gier w polu 'details'.
"""
import os
import sys
import re
import json
import urllib.parse
import subprocess
from analyst import verify_magic_bytes, is_repetitive_asset

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ZNALEZISKA_DIR = os.path.join(PROJECT_DIR, "znaleziska")
METADATA_FILE = os.path.join(ZNALEZISKA_DIR, "metadata.json")

STANDARD_PREFIXES = (
    "Macromedia Flash SWF",
    "Standard MIDI File",
    "Obraz JPEG",
    "Animacja/Obraz",
    "Mapa bitowa BMP",
    "Amiga / PC Tracker MOD"
)

def clean_filename(fn: str) -> str:
    """Zamienia %20 i spacje oraz wielokrotne podkreślenia na pojedyncze _."""
    unquoted = urllib.parse.unquote(fn)
    cleaned = re.sub(r'[% \s]+', '_', unquoted)
    cleaned = re.sub(r'_+', '_', cleaned)
    return cleaned

def run_audit():
    if not os.path.exists(METADATA_FILE):
        print(f"Błąd: Brak pliku {METADATA_FILE}")
        return

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"=== ROZPOCZĘCIE AUDYTU BAZY ({len(items)} artefaktów) ===")

    audited_items = []
    renamed_count = 0
    swf_updated_count = 0
    invalid_magic_removed = []
    junk_removed = []
    missing_files = []

    for it in items:
        old_fn = it.get('filename', '')
        new_fn = clean_filename(old_fn)

        old_disk_path = os.path.join(ZNALEZISKA_DIR, old_fn)
        new_disk_path = os.path.join(ZNALEZISKA_DIR, new_fn)

        # 1. Migracja nazw plików (%20 i spacje -> _)
        if old_fn != new_fn:
            renamed_count += 1
            print(f"MIGRACJA NAZWY: {old_fn} -> {new_fn}")
            if os.path.exists(old_disk_path):
                try:
                    res = subprocess.run(
                        ["git", "mv", old_disk_path, new_disk_path],
                        capture_output=True,
                        text=True,
                        cwd=PROJECT_DIR
                    )
                    if res.returncode != 0:
                        os.rename(old_disk_path, new_disk_path)
                except Exception:
                    os.rename(old_disk_path, new_disk_path)
            it['filename'] = new_fn
            fn = new_fn
        else:
            fn = old_fn

        disk_path = os.path.join(ZNALEZISKA_DIR, fn)
        new_local_path = f"znaleziska/{fn}"
        it['local_path'] = new_local_path

        if not os.path.exists(disk_path):
            missing_files.append(fn)
            print(f"Brak pliku na dysku: {disk_path}")
            continue

        with open(disk_path, "rb") as f:
            data = f.read()

        # 2. Weryfikacja nagłówków binarnych
        is_valid, detected_fmt, new_details = verify_magic_bytes(data)
        if not is_valid:
            invalid_magic_removed.append((fn, new_details))
            print(f"ODRZUCONO (błędne magic bytes): {fn} -> {new_details}")
            try:
                os.remove(disk_path)
            except Exception as e:
                print(f"Błąd usuwania {disk_path}: {e}")
            continue

        # 3. Aktualizacja pola 'details' z zachowaniem autorskich opisów
        old_details = it.get('details', '')
        if any(old_details.startswith(p) for p in STANDARD_PREFIXES):
            if it.get('format') == 'SWF' and 'klatek' in new_details and 'klatek' not in old_details:
                swf_updated_count += 1
            it['details'] = new_details
        else:
            # Zachowaj autorski opis (np. z add_new_games.py)
            pass

        # 4. Wsteczna filtracja powtarzalnych śmieci WWW i mikro-przycisków SWF
        file_size = it.get('size_bytes', len(data))
        orig_url = it.get('original_url', '')
        is_junk, reason = is_repetitive_asset(orig_url, file_size, new_details)

        if is_junk:
            junk_removed.append((fn, reason))
            print(f"ODRZUCONO ŚMIEĆ WWW: {fn} ({file_size} B) -> {reason}")
            try:
                os.remove(disk_path)
            except Exception as e:
                print(f"Błąd usuwania {disk_path}: {e}")
            continue

        audited_items.append(it)

    tmp_file = f"{METADATA_FILE}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(audited_items, f, indent=2, ensure_ascii=False)
    os.replace(tmp_file, METADATA_FILE)

    print("\n=== PODSUMOWANIE AUDYTU ===")
    print(f"Początkowa liczba artefaktów:      {len(items)}")
    print(f"Zmigrowane nazwy (%20 / spacje):   {renamed_count}")
    print(f"Odrzucone (nieprawidłowe nagłówki): {len(invalid_magic_removed)}")
    print(f"Odrzucone (śmieci WWW/mikro-SWF):   {len(junk_removed)}")
    print(f"Zaktualizowane pliki Flash (FPS):   {swf_updated_count}")
    print(f"Pozostało w bazie po audycie:       {len(audited_items)}")

    if junk_removed:
        print("\nLista usuniętych śmieci WWW:")
        for fn, r in junk_removed:
            print(f"  * {fn}: {r}")

if __name__ == "__main__":
    run_audit()
