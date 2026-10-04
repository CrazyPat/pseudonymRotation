"""
Berechnet Kennzahlen des bereinigten Clickstream-Datensatzes und speichert sie als JSON.
Die Werte dienen als Grundlage für die Kennzahlen in Kapitel 4.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def describe_series(s: pd.Series) -> dict:
    """Liefert Verteilungskennzahlen für eine numerische Series."""
    return {
        "mean": float(s.mean()),
        "std": float(s.std()),
        "min": float(s.min()),
        "p10": float(s.quantile(0.10)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.median()),
        "p75": float(s.quantile(0.75)),
        "p90": float(s.quantile(0.90)),
        "p95": float(s.quantile(0.95)),
        "p99": float(s.quantile(0.99)),
        "max": float(s.max()),
    }

def gini(s: pd.Series) -> float:
    """Gini-Koeffizient einer Verteilung."""
    values = np.sort(s.values.astype(float))
    n = len(values)
    if n == 0 or values.sum() == 0:
        return 0.0
    cum = np.cumsum(values)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)


def max_same_domain_streak(domains: pd.Series) -> int:
    """Längste Serie direkt aufeinanderfolgender Aufrufe derselben Domain."""
    same_as_prev = (domains == domains.shift()).astype(int)
    streak = same_as_prev.groupby((same_as_prev != same_as_prev.shift()).cumsum()).cumsum()
    return int(streak.max()) + 1 if len(streak) else 1


def dataset_check(input_file: str, output_file: str) -> None:
    df = pd.read_csv(input_file)
    df["used_at"] = pd.to_datetime(df["used_at"])
    df_sorted = df.sort_values(["panelist_id", "used_at"])

    domains_per_user = df.groupby("panelist_id")["domain"].nunique()
    events_per_user = df.groupby("panelist_id").size()
    events_per_domain = df.groupby("domain").size()

    stats = {}

    # basis
    stats["basis"] = {
        "n_nutzer": int(df["panelist_id"].nunique()),
        "n_events_gesamt": int(len(df)),
        "n_einzigartige_domains_gesamt": int(df["domain"].nunique()),
        "zeitraum_start": str(df["used_at"].min()),
        "zeitraum_ende": str(df["used_at"].max()),
        "zeitraum_tage": int((df["used_at"].max() - df["used_at"].min()).days),
    }

    # domains und events pro nutzer
    stats["domains_pro_nutzer"] = describe_series(domains_per_user)
    stats["events_pro_nutzer"] = describe_series(events_per_user)

    # events pro domain und wie stark sich die aufrufe auf wenige domains konzentrieren
    stats["events_pro_domain"] = describe_series(events_per_domain)
    stats["events_pro_domain"]["gini"] = gini(events_per_domain)

    # top 20 domains
    top_domains = events_per_domain.sort_values(ascending=False).head(20)
    stats["top_20_domains"] = {str(domain): int(count) for domain, count in top_domains.items()}

    # pausen zwischen zwei aufrufen eines nutzers in stunden
    gaps_hours = df_sorted.groupby("panelist_id")["used_at"].diff().dt.total_seconds().dropna() / 3600.0
    stats["pause_zwischen_events_stunden"] = describe_series(gaps_hours)

    # längste serie auf derselben domain pro nutzer (für den rotation-lock)
    streaks = df_sorted.groupby("panelist_id")["domain"].apply(max_same_domain_streak)
    stats["max_same_domain_streak_pro_nutzer"] = describe_series(streaks)

    # aufrufe pro kalendertag
    events_per_day = df.groupby(df["used_at"].dt.date).size()
    stats["events_pro_kalendertag"] = describe_series(pd.Series(events_per_day.values))

    # nutzer mit wenig aktivität
    stats["nutzer_mit_wenig_aktivitaet"] = {
        "anzahl_nutzer_unter_10_domains": int((domains_per_user < 10).sum()),
        "anzahl_nutzer_unter_50_events": int((events_per_user < 50).sum()),
        "anteil_nutzer_unter_10_domains": float((domains_per_user < 10).mean()),
        "anteil_nutzer_unter_50_events": float((events_per_user < 50).mean()),
    }

    # speichern
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"Kennzahlen gespeichert unter: {output_file}")
    print(json.dumps(stats["basis"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    dataset_check(
        input_file="Data/datensatz/browsing_clean.csv",
        output_file="Data/ergebnisse/dataset_stats.json",
    )