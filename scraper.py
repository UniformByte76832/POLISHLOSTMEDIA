"""
Moduł Szperacza (Scraper) - FALA 2:
Poszukiwanie nowej partii lost media z naciskiem na polskie darmowe serwery:
- friko.pl
- polbox.com
- miasto.interia.pl
- gery.pl
- geocities.com (dzielnice Area51, TimesSquare)
Zoptymalizowany pod kątem oszczędności miejsca (odrzuca miniaturowe śmieci).
"""
import os
import sys
import urllib.request
import urllib.parse
import json
import ssl
import time
import urllib.error
import logging

from analyst import is_repetitive_asset

logger = logging.getLogger("archeologia")

CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) DigitalArchaeologyBot/2.5'
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
                data = json.loads(resp.read().decode('utf-8'))
                if not data or len(data) <= 1:
                    return []
                
                headers = data[0]
                results = []
                for row in data[1:]:
                    item = dict(zip(headers, row))
                    results.append(item)
                logger.debug("CDX OK [%s]: %d wynikow", url_target, len(results))
                return results
        except (TimeoutError, urllib.error.URLError) as e:
            logger.warning("CDX Timeout/URLError [proba %d/3] [%s]: %s", attempt + 1, url_target, e)
            if attempt < 2:
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.warning("CDX Błąd [%s]: %s", url_target, e)
            return []
    return []

def get_exploration_targets():
    """Zwraca nową partię celów poszukiwawczych (Fala 2)."""
    targets = [
        # 1. Friko.pl - kultowy polski darmowy hosting lat 2000-2005
        {
            'url': 'friko.pl',
            'matchType': 'domain',
            'mimetype': 'application/x-shockwave-flash',
            'name': 'Friko.pl SWF',
            'limit': 150
        },
        {
            'url': 'friko.pl',
            'matchType': 'domain',
            'mimetype': 'audio/midi',
            'name': 'Friko.pl MIDI',
            'limit': 150
        },

        # 2. Polbox.com (główna domena Polboxa)
        {
            'url': 'polbox.com',
            'matchType': 'domain',
            'mimetype': 'audio/midi',
            'name': 'Polbox.com MIDI',
            'limit': 150
        },
        {
            'url': 'polbox.com',
            'matchType': 'domain',
            'mimetype': 'application/x-shockwave-flash',
            'name': 'Polbox.com SWF',
            'limit': 100
        },

        # 3. Miasto.interia.pl
        {
            'url': 'miasto.interia.pl',
            'matchType': 'domain',
            'mimetype': 'application/x-shockwave-flash',
            'name': 'Interia Miasto SWF',
            'limit': 100
        },
        {
            'url': 'miasto.interia.pl',
            'matchType': 'domain',
            'mimetype': 'audio/midi',
            'name': 'Interia Miasto MIDI',
            'limit': 100
        },

        # 4. Gery.pl
        {
            'url': 'gery.pl',
            'matchType': 'domain',
            'mimetype': 'audio/midi',
            'name': 'Gery.pl MIDI',
            'limit': 80
        },

        # 5. GeoCities: Area51 & Hollywood
        {
            'url': 'geocities.com/Area51/*',
            'matchType': 'prefix',
            'mimetype': 'application/x-shockwave-flash',
            'name': 'GeoCities Area51 SWF',
            'limit': 100
        },
        {
            'url': 'geocities.com/Area51/*',
            'matchType': 'prefix',
            'mimetype': 'audio/midi',
            'name': 'GeoCities Area51 MIDI',
            'limit': 100
        }
    ]
    return targets

def fetch_target_candidates(target_config: dict) -> list[dict]:
    params = {
        'filter': [f"mimetype:{target_config['mimetype']}", 'statuscode:200'],
        'limit': str(target_config['limit'])
    }
    if 'matchType' in target_config:
        params['matchType'] = target_config['matchType']

    logger.info("Szperacz: badanie celu %s (%s)", target_config['name'], target_config['url'])
    rows = query_cdx(target_config['url'], params)
    valid_candidates = []
    for r in rows:
        orig = r.get('original', '')
        raw_len = r.get('length', 0)
        try:
            length = int(raw_len) if raw_len else 0
        except (ValueError, TypeError):
            length = 0

        is_junk, _ = is_repetitive_asset(orig, length)
        if is_junk:
            continue

        r['target_name'] = target_config['name']
        valid_candidates.append(r)
    return valid_candidates
