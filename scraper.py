"""
Moduł Szperacza (Scraper) - FALA 5:
Poszukiwanie polskiego dziedzictwa cyfrowego (1997–2006) z naciskiem na:
- Autorskie animacje i satyry (100lat.info)
- Pionierskie serwery i demoscena lat 90. (KKI.net.pl, Free.polbox.pl)
- Archiwalne moduły dźwiękowe i MIDI (Webpark.pl, Polbox, KKI)
- Polskie gry Flash i projekty epoki (Gery.pl, Interia Miasto, Friko.pl, Republika.pl)
Zoptymalizowany pod kątem CDX API (collapse, fl, retry backoff, pre-filtering min_length i anty-śmieć).
"""
import urllib.request
import urllib.parse
import json
import ssl
import time
import urllib.error
import http.client
import logging

from analyst import is_repetitive_asset

logger = logging.getLogger("archeologia")

CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) DigitalArchaeologyBot/3.0'
}

def query_cdx(url_target: str, params: dict, timeout: int = 35) -> list[dict]:
    """Wysyła zapytanie do CDX API z ponawianiem prób i parametrami optymalizacyjnymi."""
    base_params = {
        'url': url_target,
        'output': 'json',
        'from': '19980101',
        'to': '20061231',
        'collapse': 'digest',
        'fl': 'timestamp,original,mimetype,digest,length'
    }
    base_params.update(params)

    query_str = urllib.parse.urlencode(base_params, doseq=True)
    full_url = f"{CDX_ENDPOINT}?{query_str}"
    
    ctx = ssl.create_default_context()
    req = urllib.request.Request(full_url, headers=DEFAULT_HEADERS)
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
                data = json.loads(resp.read().decode('utf-8', errors='replace'))
                if not data or len(data) <= 1:
                    return []
                
                headers = data[0]
                results = []
                for row in data[1:]:
                    item = dict(zip(headers, row))
                    results.append(item)
                logger.debug("CDX OK [%s]: %d wynikow", url_target, len(results))
                return results
        except (TimeoutError, urllib.error.URLError, ssl.SSLError, http.client.IncompleteRead, http.client.RemoteDisconnected, ConnectionResetError) as e:
            logger.warning("CDX Timeout/Sieć [proba %d/3] [%s]: %s", attempt + 1, url_target, e)
            if attempt < 2:
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.warning("CDX Błąd [%s]: %s", url_target, e)
            return []
    return []

def get_exploration_targets():
    """Zwraca cele poszukiwawcze dla Fali 5 (1997–2006) zoptymalizowane pod kątem szybkości i unikatowości."""
    targets = [
        # 1. 100lat.info - kultowe polskie animacje satyryczne i etiudy Flash
        {
            'url': '100lat.info',
            'matchType': 'domain',
            'url_regex': r'original:.*\.(swf|rar|zip)$',
            'min_length': 2048,
            'name': '100lat.info Flash/Archiwa',
            'limit': 30
        },

        # 2. KKI.net.pl - pionierski krakowski serwer lat 90., demoscena, MOD i MIDI
        {
            'url': 'kki.net.pl',
            'matchType': 'domain',
            'url_regex': r'original:.*\.(swf|mid|mod|rar|zip)$',
            'min_length': 1024,
            'name': 'KKI.net.pl Retro Multimedia',
            'limit': 30
        },

        # 3. Free.polbox.pl - legendarny wczesny polski webhosting lat 1997-2002
        {
            'url': 'free.polbox.pl',
            'matchType': 'domain',
            'url_regex': r'original:.*\.(swf|mid|mod)$',
            'min_length': 1024,
            'name': 'Free.polbox.pl Retro Multimedia',
            'limit': 30
        },

        # 4. Webpark.pl (Dźwięk MIDI)
        {
            'url': 'webpark.pl',
            'matchType': 'domain',
            'mimetype': 'audio/midi',
            'min_length': 1024,
            'name': 'Webpark.pl MIDI',
            'limit': 30
        },

        # 5. Gry i animacje z polskich portali i serwerów
        {
            'url': 'gery.pl',
            'matchType': 'domain',
            'url_regex': r'original:.*(gra|gry|game|malysz|skoki|kulki|arkanoid|tetris|snake|strzel|wyscig|kreskowk|animacj|intro|film).*\.swf$',
            'min_length': 10240,
            'name': 'Gery.pl Gry i Animacje Flash',
            'limit': 40
        },
        {
            'url': 'miasto.interia.pl',
            'matchType': 'domain',
            'url_regex': r'original:.*(gra|gry|game|malysz|skoki|kulki|arkanoid|tetris|snake|strzel|wyscig|kreskowk|animacj|intro|film).*\.swf$',
            'min_length': 10240,
            'name': 'Interia Miasto Gry i Animacje Flash',
            'limit': 40
        },
        {
            'url': 'friko.pl',
            'matchType': 'domain',
            'url_regex': r'original:.*(gra|gry|game|malysz|skoki|kulki|arkanoid|tetris|snake|strzel|wyscig|kreskowk|animacj|intro|film).*\.swf$',
            'min_length': 10240,
            'name': 'Friko.pl Gry i Animacje Flash',
            'limit': 40
        },
        {
            'url': 'republika.pl',
            'matchType': 'domain',
            'url_regex': r'original:.*(gra|gry|game|malysz|skoki|kulki|arkanoid|tetris|snake|strzel|wyscig|kreskowk|animacj|intro|film).*\.swf$',
            'min_length': 10240,
            'name': 'Republika.pl Gry i Animacje Flash',
            'limit': 50
        },
        {
            'url': 'webpark.pl',
            'matchType': 'domain',
            'url_regex': r'original:.*(gra|gry|game|malysz|skoki|kulki|arkanoid|tetris|snake|strzel|wyscig|kreskowk|animacj|intro|film).*\.swf$',
            'min_length': 10240,
            'name': 'Webpark.pl Gry i Animacje Flash',
            'limit': 40
        }
    ]
    return targets

def fetch_target_candidates(target_config: dict) -> list[dict]:
    """Pobiera i wstępnie filtruje kandydatów z CDX API wg parametrów celu."""
    filters = ['statuscode:200']
    if 'mimetype' in target_config:
        filters.append(f"mimetype:{target_config['mimetype']}")
    if 'url_regex' in target_config:
        rgx = target_config['url_regex']
        if not rgx.startswith('original:'):
            rgx = f"original:{rgx}"
        filters.append(rgx)

    params = {
        'filter': filters,
        'limit': str(target_config.get('limit', 50))
    }
    if 'matchType' in target_config:
        params['matchType'] = target_config['matchType']

    logger.info("Szperacz: badanie celu %s (%s)", target_config['name'], target_config['url'])
    rows = query_cdx(target_config['url'], params)
    
    min_length = target_config.get('min_length', 1024)
    valid_candidates = []
    
    for r in rows:
        orig = r.get('original', '')
        raw_len = r.get('length', 0)
        try:
            length = int(raw_len) if raw_len else 0
        except (ValueError, TypeError):
            length = 0

        # Pre-filtr 1: Minimalny rozmiar pliku
        if length < min_length:
            continue

        # Pre-filtr 2: Szablony i śmieci WWW
        is_junk, _ = is_repetitive_asset(orig, length)
        if is_junk:
            continue

        r['target_name'] = target_config['name']
        valid_candidates.append(r)
        
    return valid_candidates
