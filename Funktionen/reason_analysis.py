"""
Fasst Abschlussgründe und Domain-Kennzahlen jeder Sweep-Konfiguration zusammen.
"""

import pandas as pd
from pathlib import Path


def summarize_segments(df, slots, domains, events, days):
    """Berechnet Abschlussgründe und Domain-Kennzahlen für eine Konfiguration."""
    df = df.copy()
    # dauer der segmente in tagen
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    df['duration_days'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 86400.0
    rot = df[df['trigger'] == 'rotation_threshold']
    #kennzahlen berechnen
    n_segs = len(df)
    p50 = rot['duration_days'].median()
    # trigger verteilung
    df['trigger_detail'] = df['trigger_detail'].fillna(df['trigger'])
    df.loc[df['trigger'] == 'expired', 'trigger_detail'] = 'expired'
    triggers = df['trigger_detail'].value_counts(normalize=True).to_dict()
    # overshoot nur für echte rotationen
    avg_overshoot = rot['overshoot'].mean() if not rot.empty else 0.0
    max_overshoot = rot['overshoot'].max() if not rot.empty else 0.0
    # domains pro pseudonym
    single = df['unique_domains'] == 1
    fill = df['unique_domains'] / domains
    used_slots = df.groupby('user_id')['slot_id'].nunique() / slots
    # ausgabe
    return {
        "Slots": slots,
        "Max_Domains": domains,
        "Max_Events": events,
        "Max_Days": days,
        "Segments": n_segs,
        "Median_Age_Days": round(p50, 3),
        "Avg_Overshoot": round(avg_overshoot, 2),
        "Max_Overshoot": round(max_overshoot, 2),
        "Avg_Domains_Per_Segment": round(df['unique_domains'].mean(), 3),
        "Domain_Limit_Fill_Pct": round(fill.mean() * 100, 3),
        "Used_Slots_Pct": round(used_slots.mean() * 100, 3),
        "Single_Domain_Segments_Pct": round(single.mean() * 100, 3),
        "Single_Domain_Visits_Pct": round(df.loc[single, 'page_visits'].sum() / df['page_visits'].sum() * 100, 3),
        "Trigger_Distribution": triggers
    }


def reason_analysis(sweep_dir="../Data/ergebnisse/raw_sweeps", output_file="../Data/ergebnisse/sweep_trigger_analyse.csv"):
    """Fasst Abschlussgründe und Domain-Kennzahlen für jede Sweep-Konfiguration zusammen."""
    sweep_dir = Path(sweep_dir)
    summary_results = []
    # für sweep mit *segments
    for seg_file in sorted(sweep_dir.glob("*_segments.csv")):
        filename_clean = seg_file.stem.replace("_segments", "")
        parts = filename_clean.split("_")
        if len(parts) != 4:
            continue
        slots, domains, events, days = map(int, parts)
        df = pd.read_csv(seg_file)
        if df.empty:
            continue
        summary_results.append(summarize_segments(df, slots, domains, events, days))

    # nichts überschreiben, wenn keine segment-dateien da sind
    if not summary_results:
        print(f"Keine Segment-Dateien in {sweep_dir}, {output_file} bleibt unverändert.")
        return
    # in df
    df_summary = pd.DataFrame(summary_results)
    # speichern
    df_summary.to_csv(output_file, index=False)
    print(f"Gespeichert unter: {output_file}")


# main
if __name__ == "__main__":
    reason_analysis()
