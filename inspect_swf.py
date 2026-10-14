"""
Uniwersalny inspektor CLI plików Macromedia/Adobe Flash SWF.
Służy do analizy nagłówków, FPS, liczby klatek, skryptów ActionScript oraz wyodrębniania napisów.
Użycie: python inspect_swf.py <sciezka_do_pliku.swf>
"""
import os
import sys
import re
import zlib
import struct

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def inspect_swf(file_path: str):
    if not os.path.exists(file_path):
        print(f"Błąd: Plik '{file_path}' nie istnieje.")
        sys.exit(1)

    with open(file_path, "rb") as f:
        data = f.read()

    file_size = len(data)
    size_str = f"{file_size} bajtów ({round(file_size / 1024, 1)} KB)" if file_size < 1024*1024 else f"{round(file_size / (1024*1024), 2)} MB"

    if len(data) < 8:
        print(f"Błąd: Plik za mały na poprawny nagłówek SWF ({len(data)} bajtów).")
        sys.exit(1)

    sig = data[:3].decode('latin1', errors='ignore')
    if sig not in ('FWS', 'CWS', 'ZWS'):
        print(f"Błąd: Nieprawidłowa sygnatura SWF: {sig}")
        sys.exit(1)

    ver = data[3]
    uncompressed_len = struct.unpack('<I', data[4:8])[0]
    compression = "nieskompresowany" if sig == 'FWS' else "zlib" if sig == 'CWS' else "lzma"

    body = data[8:]
    if sig == 'CWS':
        try:
            body = zlib.decompress(body)
        except Exception as e:
            print(f"Ostrzeżenie: Błąd dekompresji zlib: {e}")

    fps = 0.0
    frames = 0
    rect_str = "nieznane"

    if len(body) >= 5:
        try:
            first = body[0]
            nbits = first >> 3
            offset = (5 + 4 * nbits + 7) // 8
            if len(body) >= offset + 4:
                fps_raw = struct.unpack('<H', body[offset:offset+2])[0]
                fps = fps_raw / 256.0
                frames = struct.unpack('<H', body[offset+2:offset+4])[0]
        except Exception:
            pass

    fps_display = str(int(fps)) if fps.is_integer() else f"{fps:.1f}"

    print(f"=== RAPORT INSPEKCJI SWF ===")
    print(f"Plik:         {file_path}")
    print(f"Rozmiar:      {size_str} (rozpakowany: {uncompressed_len} bajtów)")
    print(f"Nagłówek:     {sig} Flash v{ver} ({compression})")
    print(f"Klatki / FPS: {frames} klatek, {fps_display} FPS")

    # Wyszukiwanie słów kluczowych ActionScript
    body_to_search = data[:8] + body
    as_keywords = [
        'Key.isDown', 'Key.SPACE', 'hitTest', 'startDrag', 'stopDrag', 'score', 'punkty',
        'predkosc', 'speed', 'level', 'poziom', 'paliwo', 'fuel', 'czas', 'time',
        'gameover', 'koniec', 'enterFrame', 'autobus', 'hamulec', 'gaz',
        'pilka', 'paletka', 'torpeda', 'los', 'random', 'Math.round', 'Math.random',
        'Mouse.hide', 'zbite_jaja', 'skucha', 'kosz_pos', 'sound_pik'
    ]

    lower_body = body_to_search.lower()
    found_kw = [k for k in as_keywords if k.lower().encode('latin1') in lower_body]

    print(f"\nWykryte słowa kluczowe ActionScript ({len(found_kw)}):")
    if found_kw:
        print("  " + ", ".join(found_kw))
    else:
        print("  Brak typowych słów kluczowych gier.")

    # Ekstrakcja napisów
    raw_strings = re.findall(b'[\x20-\x7e\xc0-\xff]{3,}', body_to_search)
    clean_strings = []
    for rs in raw_strings:
        try:
            s = rs.decode('latin1', errors='ignore').strip()
            if len(s) >= 3 and any(c.isalpha() for c in s) and s not in clean_strings:
                clean_strings.append(s)
        except Exception:
            pass

    display_strings = [s for s in clean_strings if not s.startswith('http') and len(s) > 2]
    print(f"\nWyodrębnione napisy (pokazano {min(len(display_strings), 35)} z {len(display_strings)}):")
    for s in display_strings[:35]:
        print(f"  * {s}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Użycie: python inspect_swf.py <sciezka_do_pliku.swf>")
        sys.exit(1)
    inspect_swf(sys.argv[1])
