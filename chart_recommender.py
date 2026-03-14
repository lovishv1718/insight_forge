import pandas as pd
import numpy as np

def recommend_charts(dataset_profile: dict, df: pd.DataFrame, importance: dict, correlations: dict | None = None, column_types: dict | None = None) -> list:
    recs = []
    ids = set(column_types.get("id_columns", []) if column_types else [])
    text_cols = set(column_types.get("text_columns", []) if column_types else [])

    def high_unique(c):
        n = len(df)
        return (df[c].nunique(dropna=True) / n) > 0.9 if n > 0 else False

    def usable(cols):
        return [c for c in cols if c not in ids and c not in text_cols and not high_unique(c)]

    num_cols = usable(column_types.get("numeric_columns", []) if column_types else dataset_profile.get("numeric_columns", []))
    cat_cols = usable(column_types.get("categorical_columns", []) if column_types else dataset_profile.get("categorical_columns", []))
    tmp_cols = usable(column_types.get("temporal_columns", []) if column_types else [])

    # Feature importance bar
    top = importance.get("top_features", []) if importance else []
    if top:
        labels = [t["feature"] for t in top if t["feature"] in num_cols]
        data = [t["importance"] for t in top if t["feature"] in num_cols]
        if labels:
            recs.append({
                "chart_type": "bar",
                "title": "Feature Importance",
                "labels": labels,
                "data": data
            })

    # Top correlations bar (abs r)
    if correlations and correlations.get("strong_correlations"):
        pairs = [p for p in correlations["strong_correlations"] if p["feature_a"] in num_cols and p["feature_b"] in num_cols][:10]
        labels = [f"{p['feature_a']}↔{p['feature_b']}" for p in pairs]
        data = [abs(p["correlation"]) for p in pairs]
        if labels:
            recs.append({
                "chart_type": "bar",
                "title": "Top Correlations",
                "labels": labels,
                "data": data
            })

    # Numeric vs Numeric -> Drop scatter recommendation as Graphical View already has an advanced one.

    # Categorical vs Numeric → bar of mean value by category
    if cat_cols and num_cols:
        c = cat_cols[0]
        n = num_cols[0]
        grouped = df[[c, n]].dropna().groupby(c)[n].mean().sort_values(ascending=False).head(8)
        if not grouped.empty:
            recs.append({
                "chart_type": "bar",
                "title": f"Mean {n} by {c}",
                "labels": grouped.index.astype(str).tolist(),
                "data": grouped.values.tolist()
            })

    # Categorical distribution → pie
    for c in cat_cols[:2]:
        vc = df[c].value_counts(dropna=True).head(6)
        if not vc.empty:
            recs.append({
                "chart_type": "pie",
                "title": f"Distribution: {c}",
                "labels": vc.index.astype(str).tolist(),
                "data": vc.values.tolist()
            })

    # Temporal columns → line chart of sum of a numeric column over time
    if tmp_cols and num_cols:
        t = tmp_cols[0]
        n = num_cols[0]
        try:
            ts = df[[t, n]].dropna()
            if not pd.api.types.is_datetime64_any_dtype(ts[t]):
                ts[t] = pd.to_datetime(ts[t], errors="coerce")
                ts = ts.dropna()
            series = ts.groupby(pd.Grouper(key=t, freq="D"))[n].sum().head(60)
            if not series.empty:
                recs.append({
                    "chart_type": "line",
                    "title": f"{n} over time",
                    "labels": [str(i.date()) for i in series.index],
                    "data": series.values.tolist()
                })
        except Exception:
            pass

    return recs
