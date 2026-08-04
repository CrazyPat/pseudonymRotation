import numpy as np
import pandas as pd


def minmax(series: pd.Series) -> pd.Series:
    """Standartisiert Wertebereich zwischen 0 und 1.0"""
    # Alle Werte in float.
    s = series.astype(float)
    # Kleinster und größter Wert.
    min_v, max_v = s.min(), s.max()
    # Normalsieriungsformel wird angewandt + Divisionsschutz durch 0.
    return pd.Series(np.ones(len(s)), index=s.index) if min_v == max_v else (s - min_v) / (max_v - min_v)



def find_knee_point(
    df: pd.DataFrame,
    util_col: str = "Utility_Score",
    priv_col: str = "Privacy_Score_Avg",
) -> pd.DataFrame:
    """
    Bestimmt das Optimum also Kneepoint zwischen Nutzen und Privacy.
    """
    # Copy erstellen
    out = df.copy()

    # Normalisierung auf 0 bis 1
    # Utility
    x = (out[util_col] - out[util_col].min()) / (
        out[util_col].max() - out[util_col].min()
    )
    # Privacy
    y = (out[priv_col] - out[priv_col].min()) / (
        out[priv_col].max() - out[priv_col].min()
    )

    # Alle dinaten des Indexes
    n = len(out)
    # Initialisiert Array. Alles zuerst True
    pareto = np.ones(n, dtype=bool)
    # Kombinationsvergleich.
    for i in range(n):
        for j in range(n):
            # Selbstvergleich skipp
            if i == j:
                continue
            # dominiert punkt j den punkt i
            if (
                (x.iloc[j] >= x.iloc[i])
                and (y.iloc[j] >= y.iloc[i])
                and ((x.iloc[j] > x.iloc[i]) or (y.iloc[j] > y.iloc[i]))
            ):  # Falls nur ein Punkt j gefunden wird der i dominiert dann pareto nicht optimal also break
                pareto[i] = False
                break
    # Filtert beide Koordinaten auf die Pareto-Optimalen Werte.
    x_p = x[pareto]
    y_p = y[pareto]

    # A = maximale Utitlity.
    idx_a = x_p.idxmax()
    # B = maximale Privacy.
    idx_b = y_p.idxmax()
    
    # Zwei Punkte werden definiert. Die Gerade dadurch ist die Sekante.
    x1, y1 = x_p.loc[idx_a], y_p.loc[idx_a]
    x2, y2 = x_p.loc[idx_b], y_p.loc[idx_b]

    # Abstand oberhalb der Sekante.
    # Geradengleichung auswerten für jeden Punkt also den Abstand zur Sekante.
    nom = (y2 - y1) * x_p - (x2 - x1) * y_p + x2 * y1 - y2 * x1
    # Werte < 0 werde auf 0.0 gesetzt.
    nom = np.maximum(0.0, nom)
    # Euklidischer Abstand zwischen A und B um geometrischen Abstand zu normieren.
    den = np.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
    # Neue Spalte True or False
    out["Pareto_Member"] = pareto
    # Neue Distanz-Spalte zur Gerade nur init. --> Damit landen alle False unten.
    out["Chord_Distance"] = -1.0
    # Überschreibt in der Spalte die distance aber nur dort wo True ist.
    out.loc[pareto, "Chord_Distance"] = nom / (den + 1e-9)
    # Sortiert absteigend nach Distanz damit der Kniepunkt an Index 0 steht.
    return out.sort_values(by="Chord_Distance", ascending=False).reset_index(
        drop=True
    )


def add_plateau(df: pd.DataFrame, eps: float = 0.005) -> pd.DataFrame:
    """
    Markiert Konfigurationen als Plateau_Member, wenn sie maximal eps schlechter sind als die Pareto-Front.
    """
    # Alle Pareto-Punkte als Referenz extrahieren
    pareto_points = df[df["Pareto_Member"] == True]
    in_plateau = []

    # Prüfung der Epsilon-Dominanz für jede config.
    for _, row in df.iterrows():
        # Echte Pareto-Mitglieder sind immer automatisch im Plateau
        if row["Pareto_Member"]:
            # Hinzufügen.
            in_plateau.append(True)
            continue
        # Utility-Score der aktullen conf.
        u = row["Utility_Score"]
        # Privacy-Score der aktullen conf.
        p = row["Privacy_Score_Avg"]

        # Punkt entfernen nur wenn ein Pareto-Punkt existiert der in beiden BESSER ist als eps.
        more_than_eps = (
            (pareto_points["Utility_Score"] - u > eps) &
            (pareto_points["Privacy_Score_Avg"] - p > eps)
        ).any()
        # Werte hinzufügen, die nicht mehr als eps schlechter sind als Pareto-Front.
        in_plateau.append(not more_than_eps)
    # Neue Spalte hinzufügen.
    df["Plateau_Member"] = in_plateau
    return df


def add_scores(
    df: pd.DataFrame, eps: float = 0.005) -> pd.DataFrame:
    """
    Berechnet die kombinierten Privacy- und Utility-Scores.
    """
    # Kopie.
    out = df.copy()

    # Utility-Score aus normalisierten trackern pro segment.
    util_gain = minmax(out["Avg_Utility_ThirdParty"])
    # Reset-Kosten: Wie oft musste resettet werden und damit das System arbeiten.
    reset_cost = minmax(out["Total_Resets"])
    # Utility-Score.
    out["Utility_Score"] = 0.5 * util_gain + 0.5 * (1.0 - reset_cost)

    # Verkettungsrisiko normalisieren.
    linkability_risk = minmax(out["Mean_Cosine_Prev_Pseudonym"])
    # Alle Spalten, welche NN_Accuracy_k am Anfang haben damit alle in der Config angegebene Angriffsbereiche z. B. k1, k10 usw.
    acc_columns = [
        col for col in out.columns if col.startswith("kNN_Accuracy_k")
    ]
    privacy_cols = []
    for acc_col in acc_columns:
        # Erkennt welcher Suffix verwendet wurde z. B. 1 oder 10.
        k_suffix = acc_col.replace("kNN_Accuracy", "")
        # Normalisiert die Trefferquote
        acc_risk = minmax(out[acc_col])

        # Privacy-Score Berechnung --> invertieren damit es ein Schutzwert ist --> Generiert Spalte.
        out[f"Privacy_Score{k_suffix}"] = 0.5 * (1.0 - acc_risk) + 0.5 * (
            1.0 - linkability_risk
        )
        # Anfügen an Liste für späteren durchlauf für Durchschnitt
        privacy_cols.append(f"Privacy_Score{k_suffix}")

    # Berechnet den Durchschnittlichen Privacy-Score über alle k-Spalten
    if privacy_cols:
        out["Privacy_Score_Avg"] = out[privacy_cols].mean(axis=1)
    # Fallback
    else:
        out["Privacy_Score_Avg"] = 0.0
    # Kneepoint berechnen und zurückgeben mit dem durchschnittlichen Privacy-Score
    df_knee = find_knee_point(
        out, util_col="Utility_Score", priv_col="Privacy_Score_Avg"
    )
    # Plateau-Flag hinzufügen und zurückgeben
    return add_plateau(df_knee, eps=eps)