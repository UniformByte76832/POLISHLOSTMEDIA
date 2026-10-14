"""
Moduł Analityka:
Weryfikacja nagłówków binarnych (Magic Bytes), detekcja typów MIME,
oraz zaawansowane filtry odrzucające powtarzalne śmieci WWW (bannery, loga, przyciski, szablony).
"""
import re
import struct
import zlib

# Wzorce nazw plików i ścieżek typowych dla powtarzalnych elementów szablonów
REPETITIVE_PATTERNS = [
    r'(?:^|[/._-])(banner|baner|button|btn|logo|nav|counter|licznik|cnt|spacer|pixel|blank)(?:[/._\d-]|$)',
    r'(?:^|[/._-])(tlo|bg|background|line|bar|arrow|bullet|stat|statystyki|advert|reklama|gemius|hit[_-]?counter)(?:[/._\d-]|$)',
    r'(?:^|[/._-])(top[_-]?page|bottom|menu|header[_-]?bg|footer)(?:[/._\d-]|$)',
    r'(?:^|[/._-])(text\d+|button\d+|btn\d+)(?:[/._-]|$)',
    r'republika[_-]?(top|bottom|logo|pasek)',
    r'onet[_-]?(logo|baner|top)',
    r'/(?:filmy/)?(lowca|charli|bb3|baby|dancing_girl)\.swf'
]

COMPILED_REPETITIVE = re.compile('|'.join(REPETITIVE_PATTERNS), re.IGNORECASE)

def _parse_swf_header_info(sig: str, data: bytes) -> str:
    """Parsuje nagłówek SWF, wyznaczając wersję, kompresję, FPS i liczbę klatek."""
    version = data[3]
    compression = "nieskompresowany" if sig == 'FWS' else "zlib" if sig == 'CWS' else "lzma"
    try:
        if sig == 'CWS':
            body = zlib.decompress(data[8:])
        elif sig == 'FWS':
            body = data[8:]
        else:
            return f"Macromedia Flash SWF (ver {version}, {compression})"

        if len(body) >= 5:
            first = body[0]
            nbits = first >> 3
            offset = (5 + 4 * nbits + 7) // 8
            if len(body) >= offset + 4:
                fps_raw = struct.unpack('<H', body[offset:offset+2])[0]
                fps = fps_raw / 256.0
                frames = struct.unpack('<H', body[offset+2:offset+4])[0]
                fps_str = str(int(fps)) if fps.is_integer() else f"{fps:.1f}"
                return f"Macromedia Flash SWF (ver {version}, {compression}, {frames} klatek, {fps_str} FPS)"
    except Exception:
        pass
    return f"Macromedia Flash SWF (ver {version}, {compression})"

def verify_magic_bytes(data: bytes) -> tuple[bool, str, str]:
    """
    Weryfikuje nagłówki binarne (Magic Bytes) próbki.
    Zwraca (is_valid, detected_format, details).
    """
    if len(data) < 16:
        return False, "unknown", "Plik za mały (<16 bajtów)"

    # Wykrywanie stron błędów HTML/tekstowych zamiast binarnego pliku
    sample_text = data[:256].lower()
    if b'<!doctype' in sample_text or b'<html' in sample_text or b'<head' in sample_text or b'404 not found' in sample_text:
        return False, "html_error", "Odpowiedź HTML / Strona błędu Wayback"

    # MIDI: 'MThd' (0x4D 0x54 0x68 0x64)
    if data.startswith(b'MThd'):
        # Parsowanie formatu MIDI i liczby ścieżek
        try:
            length, fmt, tracks, division = struct.unpack('>IHHH', data[4:14])
            return True, "midi", f"Standard MIDI File (format {fmt}, tracks {tracks})"
        except Exception:
            return True, "midi", "Standard MIDI File"

    # SWF Flash: 'FWS' (uncompressed), 'CWS' (zlib compressed), 'ZWS' (lzma)
    if data[:3] in (b'FWS', b'CWS', b'ZWS'):
        sig = data[:3].decode('latin1')
        details = _parse_swf_header_info(sig, data)
        return True, "swf", details

    # Archiwa RAR: 'Rar!\x1a\x07'
    if data.startswith(b'Rar!\x1a\x07'):
        return True, "rar", "Archiwum RAR"

    # Archiwa ZIP: 'PK\x03\x04'
    if data.startswith(b'PK\x03\x04'):
        return True, "zip", "Archiwum ZIP"

    # ProTracker MOD check (sygnatura na offsecie 1080)
    if len(data) >= 1084:
        tag = data[1080:1084]
        if tag in (b'M.K.', b'M!K!', b'4CHN', b'FLT4', b'8CHN', b'6CHN', b'16CN', b'32CN', b'CD81', b'OKTA'):
            channels = 4
            if tag in (b'8CHN', b'CD81', b'OKTA'): channels = 8
            elif tag == b'6CHN': channels = 6
            return True, "mod", f"Amiga / PC Tracker MOD ({tag.decode('latin1', errors='ignore')}, {channels} channels)"

    # JPEG: 0xFFD8FF
    if data.startswith(b'\xff\xd8\xff'):
        return True, "jpeg", "Obraz JPEG"

    # GIF: GIF87a lub GIF89a
    if data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
        ver = data[:6].decode('ascii', errors='ignore')
        # Odczyt wymiarów z nagłówka
        w, h = struct.unpack('<HH', data[6:10])
        return True, "gif", f"Animacja/Obraz {ver} ({w}x{h} px)"

    # BMP: 'BM'
    if data.startswith(b'BM'):
        w, h = struct.unpack('<ii', data[18:26])
        return True, "bmp", f"Mapa bitowa BMP ({abs(w)}x{abs(h)} px)"

    return False, "unknown", "Nieznany format binarny"

def is_repetitive_asset(original_url: str, file_size: int, details: str = "") -> tuple[bool, str]:
    """
    Sprawdza, czy plik jest powtarzalnym elementem interfejsu/szablonu strony.
    """
    url_lower = original_url.lower()

    # Sprawdzenie wzorców w nazwie pliku i ścieżce
    match = COMPILED_REPETITIVE.search(url_lower)
    if match:
        return True, f"Wykryto wzorzec szablonu/reklamy: '{match.group(0)}' w URL"

    # Wykrywanie wymiarów typowych dla banerów w szczegółach obrazu
    banner_dimensions = ['468x60', '88x31', '120x600', '120x240', '234x60', '120x90', '125x125', '160x600']
    for dim in banner_dimensions:
        if dim in details:
            return True, f"Standardowy wymiar banera/przycisku WWW ({dim})"

    # Odrzucenie mikroskopijnych grafik poniżej 3KB (często ikony lub przezroczyste spacery)
    details_lower = details.lower()
    if ('gif' in details_lower or 'jpeg' in details_lower or 'bmp' in details_lower) and file_size < 3072:
        return True, f"Zbyt mały plik graficzny ({file_size} B) – prawdopodobnie ikona/spacer"

    # Odrzucenie mikroskopijnych plików SWF poniżej 2.5KB (pojedyncze przyciski menu, etykiety)
    if ('swf' in details_lower or '.swf' in url_lower) and file_size < 2560:
        return True, f"Zbyt mały plik SWF ({file_size} B) – pojedynczy przycisk/napis tekstowy"

    return False, "Unikatowy zasób"

