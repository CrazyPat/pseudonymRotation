"""
Monitoring Funktion.
"""

from datetime import datetime


def log_status(message: str, verbose: bool = True) -> None:
    """Gibt eine Statusmeldung mit Zeitstempel auf der Konsole aus."""
    if verbose:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)
