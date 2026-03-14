import pandas as pd

KEYWORDS = ["risk","score","rating","class","status","segment","tier","outcome"]

def detect_target_columns(df: pd.DataFrame, column_types: dict) -> dict:
    ids = set(column_types.get("id_columns", []))
    temporals = set(column_types.get("temporal_columns", []))
    numeric_cols = [c for c in column_types.get("numeric_columns", []) if c not in ids and c not in temporals]
    categorical_cols = [c for c in column_types.get("categorical_columns", []) if c not in ids and c not in temporals]

    classification_targets = []
    regression_targets = []

    for c in df.columns.astype(str):
        if c in ids or c in temporals:
            continue
        lc = c.lower()
        if any(k in lc for k in KEYWORDS):
            if pd.api.types.is_numeric_dtype(df[c]):
                regression_targets.append(c)
            else:
                classification_targets.append(c)

    if not classification_targets:
        for c in categorical_cols:
            u = df[c].nunique(dropna=True)
            if 2 <= u <= 50:
                classification_targets.append(c)
                break

    if not regression_targets:
        n_rows = len(df)
        for c in numeric_cols:
            uniq_ratio = (df[c].nunique(dropna=True) / n_rows) if n_rows > 0 else 0.0
            if 0.1 <= uniq_ratio <= 0.8:
                regression_targets.append(c)
                break
        if not regression_targets and numeric_cols:
            regression_targets.append(numeric_cols[-1])

    return {
        "classification_targets": classification_targets,
        "regression_targets": regression_targets
    }
