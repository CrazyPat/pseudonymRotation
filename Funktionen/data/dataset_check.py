"""Funktion zur Überprüfung des Datensatzes im Vergleich zum WhoTracks.Me-Datensatz"""

import json


def dataset_check(df, mapping, output_path):
    df["tracker_count"] = df["domain"].map(lambda d: len(mapping.get(d, [])))
    domain_df = df[["domain", "tracker_count"]].drop_duplicates(subset=["domain"])
    eigene_mean_alle = domain_df["tracker_count"].mean()
    eigene_mean_getrackt = domain_df.loc[domain_df["tracker_count"] > 0, "tracker_count"].mean()
    eigene_prevalence = (domain_df["tracker_count"] > 0).mean() * 100

    top1330_domains = df["domain"].value_counts().head(1330).index
    top1330_df = domain_df[domain_df["domain"].isin(top1330_domains)]
    top1330_mean_alle = top1330_df["tracker_count"].mean()
    top1330_mean_getrackt = top1330_df.loc[top1330_df["tracker_count"] > 0, "tracker_count"].mean()  # Ø nur getrackte in Top-1330

    werte = {
        # Zenodo-Datensatz joint mit WhoTracks.Me-Daten
        "eigene_mean_alle": round(eigene_mean_alle, 2),
        "eigene_mean_getrackt": round(eigene_mean_getrackt, 2),
        "eigene_prevalence_prozent": round(eigene_prevalence, 2),
        # Wert aus Karaj et al. 2019, Abschnitt 5.1
        "top1330_mean_alle": round(top1330_mean_alle, 2),
        "top1330_referenz_alle": 8.0,
        "top1330_mean_getrackt": round(top1330_mean_getrackt, 2),
        "top1330_referenz_getrackt": 13.0,
    }
     # Datei öffnen
    with open(output_path, "w", encoding="utf-8") as f:
        # Werte speichern
        json.dump(werte, f, indent=2, ensure_ascii=False)

    return werte