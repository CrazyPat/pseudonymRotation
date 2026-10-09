"""
Verworfener Ansatz eines realen Domain-Tracker-Mappings in Abschnitt 4.1.2.
Ordnet den Domains des Zenodo-Datensatzes über WhoTracks.Me Drittanbieter-Tracker zu
und berechnet die Kennzahlen, mit denen der Ansatz verworfen wurde.
Voraussetzung!! preprocessing.py ausführen.
"""

import json
from pathlib import Path

import pandas as pd

data_dir = Path(__file__).resolve().parents[1] / "Data"
# Karaj et al. betrachten die 1.330 meistbesuchten Webseiten (S. 8)
top_n = 1330

def load_wtm() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lädt die WhoTracks.Me-Daten aus dem whotracksme-Paket."""
    # In der def weil sonst dauerhafte infos in der Simulation geladen werden.
    from whotracksme.data.loader import DataSource
    # Iteritems für Series patchen
    pd.Series.iteritems = getattr(pd.Series, "iteritems", pd.Series.items)
    # Iteritems für DataFrame patchen
    pd.DataFrame.iteritems = getattr(pd.DataFrame, "iteritems", pd.DataFrame.items)
    ds = DataSource()
    return ds.sites_trackers.df, ds.trackers.df

def build_mapping(st_df: pd.DataFrame, t_df: pd.DataFrame) -> dict[str, list[str]]:
    """Erstellt ein Mapping von Domains zu Trackern."""
    # Relationstabelle
    st_df = st_df[["site", "tracker"]].copy()
    # Site Spalte normalisieren
    st_df["site"] = st_df["site"].astype(str).str.lower().str.strip()
    # Tracker Spalte normalisieren
    st_df["tracker"] = st_df["tracker"].astype(str).str.strip()

    # Metadatentabelle --> notwendig um Kategorien zu filtern.
    t_df = t_df[["tracker", "category"]].copy()
    # Tracker normalisieren
    t_df["tracker"] = t_df["tracker"].astype(str).str.strip()
    # Kategorie normalisieren
    t_df["category"] = t_df["category"].astype(str).str.strip()
    # Duplikate entfernen
    t_df = t_df.drop_duplicates(subset=["tracker"], keep="last")
    # Alle Dienste die Ausgeschlossen werden, weil sie nicht relevant sind (v)
    # Unterscheidung zwischen Infrastruktur und verhaltensbasierten Trackern.
    # CND = Content Delivery Network (sorgen für schnellere Ladezeiten von zb Bildern), customer_interaktions = zb. Live-Chat-Fenster für Nutzer, audio_video_player = zb. iFrames, extensions = Browser-Extensions Aufrufe nicht webseite.
    ausgeschlossene_kategorien = {"cdn", "hosting", "customer_interaction", "audio_video_player", "extensions"}

    # Tabellen per Left-Join verknüpfen
    merged = pd.merge(st_df, t_df, on="tracker", how="left")
    merged = merged[~merged["category"].isin(ausgeschlossene_kategorien)]

    # Eindeutige Tracker pro Site
    return {site: sorted(set(group["tracker"].dropna())) for site, group in merged.groupby("site")}

if __name__ == "__main__":
    domains = pd.read_csv(data_dir / "datensatz" / "browsing_clean.csv", usecols=["domain"])["domain"]
    wtm_map = build_mapping(*load_wtm())

    # Domains ohne Eintrag bei WhoTracks.Me bekommen eine leere Liste (ungemappt)
    mapping = {d: wtm_map.get(d, []) for d in domains.unique()}
    with open(data_dir / "datensatz" / "domain_tracker_mapping.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    trackers = pd.Series({d: len(t) for d, t in mapping.items()})
    top = trackers[domains.value_counts().index[:top_n]]

    # Abgleich der ungemappten Domains mit der Tranco-Top-1-Million
    tranco = set((data_dir / "datensatz" / "tranco_2019-02-18.txt").read_text().split())
    unmapped = trackers[trackers == 0].index

    stats = {
        "domains": len(trackers),
        "tracker_pro_domain": trackers.mean(),
        f"top_{top_n}_tracker_pro_domain": top.mean(),
        f"top_{top_n}_tracker_pro_gemappter_domain": top[top > 0].mean(),
        "ungemappte_domains": len(unmapped),
        "ungemappt_in_tranco_pct": unmapped.isin(tranco).mean() * 100,
    }
    with open(data_dir / "ergebnisse" / "tracker_mapping_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))
