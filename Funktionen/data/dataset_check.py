"""Funktion zur Überprüfung des Datensatzes im Vergleich zum WhoTracks.Me-Datensatz"""
import json

# Wert aus Karaj et al. 2019 Abschnitt 5.1
TOP1330_REFERENZ_ALLE = 8.0
TOP1330_REFERENZ_GETRACKT = 13.0


def _domain_prevalence(df):
    """Prevalence auf Domain-Ebene + Top-1330-Vergleich mit Karaj et al."""
    domain_df = df[["domain", "tracker_count"]].drop_duplicates(subset=["domain"])
    eigene_mean_alle = domain_df["tracker_count"].mean()
    eigene_mean_getrackt = domain_df.loc[domain_df["tracker_count"] > 0, "tracker_count"].mean()
    eigene_prevalence = (domain_df["tracker_count"] > 0).mean() * 100

    top1330_domains = df["domain"].value_counts().head(1330).index
    top1330_df = domain_df[domain_df["domain"].isin(top1330_domains)]
    top1330_mean_alle = top1330_df["tracker_count"].mean()
    top1330_mean_getrackt = top1330_df.loc[top1330_df["tracker_count"] > 0, "tracker_count"].mean()  # nur getrackte in Top-1330

    return {
        "eigene_mean_alle": round(eigene_mean_alle, 2),
        "eigene_mean_getrackt": round(eigene_mean_getrackt, 2),
        "eigene_prevalence_prozent": round(eigene_prevalence, 2),
        "top1330_mean_alle": round(top1330_mean_alle, 2),
        "top1330_referenz_alle": TOP1330_REFERENZ_ALLE,
        "top1330_mean_getrackt": round(top1330_mean_getrackt, 2),
        "top1330_referenz_getrackt": TOP1330_REFERENZ_GETRACKT,
    }


def _tranco_check(mapping, tranco_path):
    """Prüft ungetrackte Domains gegen Tranco Top 1 Mio --> ob kein Tracker an fehlender Zuordnung liegt oder echt untracked ist."""
    with open(tranco_path) as f:
        tranco_set = set(line.strip().lower() for line in f)
    untracked = [d for d, trackers in mapping.items() if len(trackers) == 0]
    in_tranco = [d for d in untracked if d in tranco_set]
    tranco_anteil = (len(in_tranco) / len(untracked) * 100) if untracked else 0.0

    return {
        "ungetrackt_gesamt": len(untracked),
        "ungetrackt_in_tranco": len(in_tranco),
        "ungetrackt_in_tranco_prozent": round(tranco_anteil, 2),
    }


def _event_prevalence(df):
    """Event-gewichtete Prevalence --> wie viel Prozent der TATSÄCHLICHEN Aufrufe betreffen getrackte Domains."""
    events_gesamt = len(df)
    events_getrackt = int((df["tracker_count"] > 0).sum())
    event_prevalence = (events_getrackt / events_gesamt * 100) if events_gesamt else 0.0

    return {
        "events_gesamt": events_gesamt,
        "events_getrackt": events_getrackt,
        "event_prevalence_prozent": round(event_prevalence, 2),
    }


def dataset_check(df, mapping, output_path, tranco_path="Data/datensatz/tranco_2019-02-18.txt"):
    """Berechnet Kennzahlen zum Datensatz-Vergleich mit WhoTracks.Me und schreibt als JSON."""
    # Kopie, damit der df nicht verändert wird.
    df = df.copy()
    df["tracker_count"] = df["domain"].map(lambda d: len(mapping.get(d, [])))

    werte = {
        # Zenodo-Datensatz joint mit wtm-Daten
        **_domain_prevalence(df),
        # ungetrackte Domains gegen Tranco Top 1 Mio
        **_tranco_check(mapping, tranco_path),
        # Event-gewichtete Prevalence
        **_event_prevalence(df),
    }

    # Datei öffnen
    with open(output_path, "w", encoding="utf-8") as f:
        # Werte speichern
        json.dump(werte, f, indent=2, ensure_ascii=False)
    return werte