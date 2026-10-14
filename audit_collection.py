"""
Skrypt audytu bazy znalezisk i migracji metadanych:
1. Normalizacja local_path do postaci 'znaleziska/<filename>'.
2. Wsteczna weryfikacja binarna nagłówków (verify_magic_bytes).
3. Wsteczna filtracja szablonowych śmieci WWW (is_repetitive_asset).
4. Zachowanie autorskich opisów gier w polu 'details'.
"""
import os
import sys
import json
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

def run_audit():
    if not os.path.exists(METADATA_FILE):
        print(f"Błąd: Brak pliku {METADATA_FILE}")
        return

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"=== ROZPOCZĘCIE AUDYTU BAZY ({len(items)} artefaktów) ===")

    audited_items = []
    swf_updated_count = 0
    invalid_magic_removed = []
    junk_removed = []
    missing_files = []

    for it in items:
        fn = it.get('filename', '')
        old_local_path = it.get('local_path', '')
        new_local_path = f"znaleziska/{fn}"
        it['local_path'] = new_local_path

        disk_path = os.path.join(ZNALEZISKA_DIR, fn)
        if not os.path.exists(disk_path):
            missing_files.append(fn)
            print(f"Brak pliku na dysku: {disk_path}")
            continue

        with open(disk_path, "rb") as f:
            data = f.read()

        # 1. Weryfikacja nagłówków binarnych
        is_valid, detected_fmt, new_details = verify_magic_bytes(data)
        if not is_valid:
            invalid_magic_removed.append((fn, new_details))
            print(f"ODRZUCONO (błędne magic bytes): {fn} -> {new_details}")
            try:
                os.remove(disk_path)
            except Exception as e:
                print(f"Błąd usuwania {disk_path}: {e}")
            continue

        # 2. Aktualizacja pola 'details' z zachowaniem autorskich opisów
        old_details = it.get('details', '')
        if any(old_details.startswith(p) for p in STANDARD_PREFIXES):
            if it.get('format') == 'SWF' and 'klatek' in new_details and 'klatek' not in old_details:
                swf_updated_count += 1
            it['details'] = new_details
        else:
            # Zachowaj autorski opis (np. z add_new_games.py)
            pass

        # 3. Wsteczna filtracja powtarzalnych śmieci WWW
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

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(audited_items, f, indent=2, ensure_ascii=False)

    print("\n=== PODSUMOWANIE AUDYTU ===")
    print(f"Początkowa liczba artefaktów:      {len(items)}")
    print(f"Odrzucone (nieprawidłowe nagłówki): {len(invalid_magic_removed)}")
    print(f"Odrzucone (śmieci WWW/szablony):    {len(junk_removed)}")
    print(f"Zaktualizowane pliki Flash (FPS):   {swf_updated_count}")
    print(f"Pozostało w bazie po audycie:       {len(audited_items)}")

    if junk_removed:
        print("\nLista usuniętych śmieci WWW:")
        for fn, r in junk_removed:
            print(f"  * {fn}: {r}")

if __name__ == "__main__":
    run_audit()
