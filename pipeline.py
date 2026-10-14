"""
Główny potok ekspedycji archeologii cyfrowej.
Zarządza pracą Szperacza, Analityka i Archiwisty w trybie cichym.
Wszystkie szczegółowe dane, binarne logi i linki zapisywane są wyłącznie do plików:
- archeologia.log (pełny dziennik zdarzeń)
- postep.json (aktualny stan, statystyki i raporty kamieni milowych)
- znaleziska/metadata.json (kompletna baza artefaktów)
- znaleziska/katalog.md (katalog z podglądem)

Na konsolę (stdout) wypisywane są wyłącznie zwięzłe podsumowania co 100 pobranych plików.
"""
import os
import sys
import time
import json
import logging
from datetime import datetime
from collections import Counter

# Bezpieczne kodowanie konsoli dla Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ZNALEZISKA_DIR = os.path.join(PROJECT_DIR, "znaleziska")
LOG_FILE = os.path.join(PROJECT_DIR, "archeologia.log")
POSTEP_FILE = os.path.join(PROJECT_DIR, "postep.json")

# Konfiguracja logowania wyłącznie do pliku
logger = logging.getLogger("archeologia")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

from scraper import get_exploration_targets, fetch_target_candidates
from archivist import Archivist

def update_postep(state_dict: dict):
    """Atomowy zapis stanu postępu do postep.json."""
    tmp_path = POSTEP_FILE + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)
        if os.path.exists(POSTEP_FILE):
            os.replace(tmp_path, POSTEP_FILE)
        else:
            os.rename(tmp_path, POSTEP_FILE)
    except Exception as e:
        logger.error("Blad zapisu postep.json: %s", e)

def run_archeology_expedition():
    logger.info("=" * 60)
    logger.info("ROZPOCZECIE SESJI ARCHEOLOGII CYFROWEJ")
    logger.info("=" * 60)

    archivist = Archivist(ZNALEZISKA_DIR)
    initial_total = len(archivist.archived_items)
    
    # Wyliczenie początkowego rozkładu formatów
    initial_counts = Counter(it.get('format', 'UNKNOWN') for it in archivist.archived_items)
    
    print(f"[START] Wznowiono ekspedycję archeologii cyfrowej. Stan bazy: {initial_total} plików.")
    sys.stdout.flush()

    session_downloaded = 0
    session_errors = 0
    session_junk = 0
    session_formats = Counter()
    
    # Liczniki dla bieżącej setki
    batch_formats = Counter()
    batch_errors = 0
    reports_history = []

    # Inicjalizacja stanu
    state = {
        "status": "running",
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "initial_total": initial_total,
        "current_total": initial_total,
        "session_downloaded": 0,
        "session_formats": dict(session_formats),
        "total_formats": dict(initial_counts),
        "session_errors": 0,
        "session_rejected_junk": 0,
        "last_report": None,
        "reports_history": reports_history,
        "current_target": "Rozruch"
    }
    update_postep(state)

    targets = get_exploration_targets()

    for target in targets:
        target_name = target['name']
        state['current_target'] = target_name
        state['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_postep(state)

        candidates = fetch_target_candidates(target)
        if not candidates:
            continue

        for item in candidates:
            res, status = archivist.fetch_and_archive(item)
            
            if status == 'SAVED':
                session_downloaded += 1
                fmt = res.get('format', 'UNKNOWN')
                session_formats[fmt] += 1
                batch_formats[fmt] += 1
                initial_counts[fmt] += 1

                # Czy osiągnięto kolejną pełną setkę pobranych plików?
                if session_downloaded % 100 == 0:
                    # Syntetyczne podsumowanie: np. „Pobrano: 40 SWF, 60 MIDI, 0 błędów”
                    fmt_parts = []
                    for f_name, count in sorted(batch_formats.items(), key=lambda x: -x[1]):
                        if count > 0:
                            fmt_parts.append(f"{count} {f_name}")
                    fmt_str = ", ".join(fmt_parts) if fmt_parts else "0 plików"
                    report_text = f"Pobrano: {fmt_str}, {batch_errors} błędów"
                    
                    # Wypisanie wyłącznie zwięzłego raportu na stdout
                    print(f"[RAPORT] {report_text}")
                    sys.stdout.flush()

                    reports_history.append({
                        "milestone": session_downloaded,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "report": report_text
                    })
                    state['last_report'] = report_text

                    # Reset liczników setki
                    batch_formats.clear()
                    batch_errors = 0

                    # Aktualizacja katalog.md
                    archivist.generate_catalog()

            elif status == 'DOWNLOAD_ERROR':
                session_errors += 1
                batch_errors += 1

            elif status == 'JUNK_REJECTED':
                session_junk += 1

            # Aktualizacja stanu w pliku
            state['current_total'] = initial_total + session_downloaded
            state['session_downloaded'] = session_downloaded
            state['session_formats'] = dict(session_formats)
            state['total_formats'] = dict(initial_counts)
            state['session_errors'] = session_errors
            state['session_rejected_junk'] = session_junk
            state['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_postep(state)

            # Polite delay
            time.sleep(0.3)

            if session_downloaded >= 50:
                print(f"[LIMIT] Osiągnięto limit {session_downloaded} nowych artefaktów w bieżącej sesji.")
                break

        if session_downloaded >= 50:
            break

    # Zakończenie pracy
    archivist.generate_catalog()
    state['status'] = 'completed'
    state['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    update_postep(state)

    fmt_parts = [f"{count} {f_name}" for f_name, count in sorted(session_formats.items(), key=lambda x: -x[1])]
    summary_str = ", ".join(fmt_parts) if fmt_parts else "0 nowych plików"
    print(f"[KONIEC] Sesja zakończona. Pobrano: {summary_str}, {session_errors} błędów.")
    sys.stdout.flush()

if __name__ == "__main__":
    run_archeology_expedition()
