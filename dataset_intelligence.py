import math
import pandas as pd
import numpy as np

def _domain_guess(columns):
    s = " ".join([c.lower() for c in columns])
    if any(k in s for k in ["order", "invoice", "price", "customer", "product", "sale"]):
        return "E-Commerce"
    if any(k in s for k in ["student", "grade", "score", "exam", "class"]):
        return "Education"
    if any(k in s for k in ["employee", "salary", "department", "hr"]):
        return "HR"
    if any(k in s for k in ["transaction", "amount", "balance", "account", "bank"]):
        return "Financial"
    if any(k in s for k in ["patient", "diagnosis", "medical", "clinic", "health"]):
        return "Healthcare"
    return "General"

def _dataset_type_guess(df):
    cols = df.columns.astype(str).tolist()
    dom = _domain_guess(cols)
    if dom == "E-Commerce":
        return "Retail Transactions"
    if dom == "Education":
        return "Student Performance"
    if dom == "HR":
        return "Employee Analytics"
    if dom == "Financial":
        return "Banking Transactions"
    if dom == "Healthcare":
        return "Clinical Records"
    return "Structured Dataset"

def _primary_entities(columns):
    ents = []
    for c in columns:
        lc = c.lower()
        if any(k in lc for k in ["id", "uuid", "key"]):
            ents.append(c)
        if any(k in lc for k in ["customer", "client", "user", "student", "employee", "account", "product", "item"]):
            ents.append(c)
    return list(dict.fromkeys(ents))

def _potential_targets(df):
    cols = df.columns.astype(str).tolist()
    candidates = []
    for c in cols:
        lc = c.lower()
        if any(k in lc for k in ["target", "label", "outcome", "result", "score", "grade", "churn", "price", "amount"]):
            candidates.append(c)
    if candidates:
        return candidates
    if len(cols) > 0:
        return [cols[-1]]
    return []

def _key_metrics(df):
    rows = int(df.shape[0])
    cols = int(df.shape[1])
    miss_pct = float(df.isnull().mean().mul(100).mean()) if rows > 0 else 0.0
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    outlier_avg = 0.0
    if num_cols:
        vals = []
        for c in num_cols:
            s = df[c].dropna()
            if len(s) == 0:
                continue
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            if iqr <= 0:
                continue
            n_out = len(s[(s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)])
            vals.append(100.0 * n_out / len(s))
        outlier_avg = float(np.mean(vals)) if vals else 0.0
    return {
        "rows": rows,
        "columns": cols,
        "avg_missing_pct": round(miss_pct, 2),
        "avg_outlier_pct": round(outlier_avg, 2)
    }

def _summary(df, domain, dtype, metrics):
    return f"{dtype} in {domain}. {metrics['rows']} records across {metrics['columns']} columns. Missing {metrics['avg_missing_pct']}%, outlier {metrics['avg_outlier_pct']}%."

def build_dataset_profile(df: pd.DataFrame) -> dict:
    cols = df.columns.astype(str).tolist()
    domain = _domain_guess(cols)
    dtype = _dataset_type_guess(df)
    ents = _primary_entities(cols)
    metrics = _key_metrics(df)
    num_cols = df.select_dtypes(include=["number"]).columns.astype(str).tolist()
    cat_cols = df.select_dtypes(include=["object"]).columns.astype(str).tolist()
    targets = _potential_targets(df)
    return {
        "dataset_type": dtype,
        "domain": domain,
        "primary_entities": ents,
        "key_metrics": metrics,
        "numeric_columns": num_cols,
        "categorical_columns": cat_cols,
        "potential_targets": targets,
        "summary": _summary(df, domain, dtype, metrics)
    }
