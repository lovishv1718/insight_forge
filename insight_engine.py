import pandas as pd
import numpy as np

def discover_insights(df: pd.DataFrame, correlations: dict, feature_importance: dict, column_types: dict) -> list:
    tops = []
    imp_map = {t["feature"]: t["importance"] for t in (feature_importance.get("top_features") or [])}
    corr_pairs = correlations.get("strong_correlations") or []
    for p in corr_pairs:
        a, b, r = p["feature_a"], p["feature_b"], float(p["correlation"])
        strength = abs(r)
        imp_weight = max(imp_map.get(a, 0.0), imp_map.get(b, 0.0))
        anomaly_weight = 1.0
        desc = f"{a} correlates {'positively' if r>0 else 'negatively'} with {b} (r={r})."
        score = strength * (0.6 + 0.4 * imp_weight) * anomaly_weight
        tops.append({"title": f"Relationship: {a} ↔ {b}", "description": desc, "score": round(score, 4)})

    cat_cols = column_types.get("categorical_columns", [])[:2]
    for c in cat_cols:
        vc = df[c].value_counts(normalize=True, dropna=True).head(1)
        if not vc.empty:
            topv = vc.index[0]
            pct = float(vc.values[0]) * 100
            tops.append({
                "title": f"Dominant Category: {c}",
                "description": f"Category '{topv}' dominates {round(pct,1)}% of {c}.",
                "score": round(pct/100 * 0.5, 4)
            })

    tops.sort(key=lambda x: x["score"], reverse=True)
    return tops[:5]
