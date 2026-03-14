import pandas as pd
import numpy as np
from target_detector import detect_target_columns

def compute_feature_importance(df: pd.DataFrame, dataset_profile: dict | None = None, column_types: dict | None = None) -> dict:
    try:
        from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    except Exception:
        return {"target_column": None, "top_features": []}

    if column_types is None:
        # Fallback: simple classification of columns
        numeric_cols = df.select_dtypes(include=["number"]).columns.astype(str).tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.astype(str).tolist()
        column_types = {
            "id_columns": [],
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "text_columns": [],
            "temporal_columns": []
        }

    targets = detect_target_columns(df, column_types)
    target = None
    mode = None

    if targets.get("classification_targets"):
        target = targets["classification_targets"][0]
        mode = "classification"
    elif targets.get("regression_targets"):
        target = targets["regression_targets"][0]
        mode = "regression"

    if not target:
        return {"target_column": None, "top_features": []}

    y = df[target]
    ids = set(column_types.get("id_columns", []))
    temporals = set(column_types.get("temporal_columns", []))
    X = df.drop(columns=[target])
    X = X.select_dtypes(include=["number"])
    X = X[[c for c in X.columns if c not in ids and c not in temporals]]

    if X.shape[1] == 0 or y.isnull().all():
        return {"target_column": target, "top_features": []}

    # Align indices and drop NA rows uniformly
    data = pd.concat([X, y], axis=1).dropna()
    X_clean = data[X.columns]
    y_clean = data[target]

    try:
        if mode == "regression":
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_clean.values, y_clean.values)
        else:
            y_codes = pd.Categorical(y_clean).codes
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_clean.values, y_codes)
        imps = model.feature_importances_
        pairs = list(zip(X_clean.columns.tolist(), imps))
        pairs.sort(key=lambda x: x[1], reverse=True)
        top = [{"feature": f, "importance": float(v)} for f, v in pairs[:5]]
        return {"target_column": target, "top_features": top}
    except Exception:
        return {"target_column": target, "top_features": []}
