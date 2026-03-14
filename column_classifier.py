import pandas as pd

def classify_columns(df: pd.DataFrame) -> dict:
    cols = df.columns.astype(str).tolist()
    n_rows = len(df)
    id_cols = []
    temporal = []
    categorical = []
    numeric = []
    text = []

    for c in cols:
        s = df[c]
        lc = c.lower()
        uniq_ratio = (s.nunique(dropna=True) / n_rows) if n_rows > 0 else 0.0

        is_datetime = pd.api.types.is_datetime64_any_dtype(s)
        name_temporal = any(k in lc for k in ["date", "time", "timestamp"])

        if "id" in lc or uniq_ratio > 0.9:
            id_cols.append(c)
            continue

        if is_datetime or name_temporal:
            temporal.append(c)
            continue

        if pd.api.types.is_numeric_dtype(s):
            numeric.append(c)
            continue

        if pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s) or pd.api.types.is_categorical_dtype(s):
            # categorical if low unique
            if s.nunique(dropna=True) < 50:
                categorical.append(c)
            else:
                # long text heuristic: average length > 30 or high uniqueness
                avg_len = 0.0
                try:
                    avg_len = s.dropna().astype(str).str.len().mean() or 0.0
                except Exception:
                    avg_len = 0.0
                if avg_len > 30 or uniq_ratio > 0.9:
                    text.append(c)
                else:
                    categorical.append(c)
            continue

    return {
        "id_columns": id_cols,
        "numeric_columns": numeric,
        "categorical_columns": categorical,
        "text_columns": text,
        "temporal_columns": temporal
    }
