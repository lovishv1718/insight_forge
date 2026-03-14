import pandas as pd
import numpy as np
import math
import os
from pprint import pprint


# 1 st part
def basic_overview(df, file_size_mb=None):
    insights = {}

    insights["rows"] = df.shape[0]
    insights["columns"] = df.shape[1]

    if file_size_mb is not None:
        insights["file_size"] = f"{file_size_mb:.4f} MB"

    return insights


# 2nd part
def missing_overview(df):
    insights = {}

    total_missing = df.isnull().sum().sum()
    total_cells = df.shape[0] * df.shape[1]

    insights["total_missing"] = int(total_missing)
    insights["missing_percentage"] = round((total_missing / total_cells) * 100, 2)

    missing_count_per_column = (
        df.isnull()
          .sum()
          .sort_values(ascending=False)
    )

    insights["missing_count_per_column"] = missing_count_per_column.to_dict()

    insights["missing_percentage_per_column"] = (
        (missing_count_per_column / len(df)) * 100
    ).round(2).to_dict()

    return insights

    
# 3rd part   
def column_types(df):
    insights={
        "numeric":{
            "count":0,
            "columns":[]
        },
        
        "categorical":{
            "count":0,
            "columns":[]
        },
        
        "datetime":{
            "count":0,
            "columns":[]
        },
        
        "boolean":{
            "count":0,
            "columns":[]
        }
        
    }
    demo=df.select_dtypes(include=['number'])
    if demo.shape[1]!=0:
        insights["numeric"]["count"]=demo.shape[1]
        insights["numeric"]["columns"]=demo.columns.tolist()
        
    demo2=df.select_dtypes(include=['object'])
    if demo2.shape[1]!=0:
        insights["categorical"]["count"]=demo2.shape[1]
        insights["categorical"]["columns"]=demo2.columns.tolist()
        
    demo3=df.select_dtypes(include=['datetime64'])
    if demo3.shape[1]!=0:
        insights["datetime"]["count"]=demo3.shape[1]
        insights["datetime"]["columns"]=demo3.columns.tolist()
        
    demo4=df.select_dtypes(include=['boolean'])
    if demo4.shape[1]!=0:
        insights["boolean"]["count"]=demo4.shape[1]
        insights["boolean"]["columns"]=demo4.columns.tolist()
        
    return insights
        
# 4th part
def healthy(df):
    insights = {
        "single_value_columns": [],
        "high_cardinality_columns": [],
        "numeric_as_text_columns": [],
        "imbalanced_columns": []
    }

    total_rows = len(df)

    # 1. Single value columns
    for col in df.columns:
        if df[col].nunique(dropna=True) == 1:
            insights["single_value_columns"].append(col)

    # 2. High cardinality
    for col in df.columns:
        unique_ratio = df[col].nunique(dropna=True) / total_rows
        if unique_ratio > 0.8:
            insights["high_cardinality_columns"].append(col)

    # 3. Numeric stored as text
    for col in df.select_dtypes(include=["object"]).columns:
        non_null_count = df[col].notna().sum()
        if non_null_count == 0:
            continue

        converted = pd.to_numeric(df[col], errors="coerce")
        converted_count = converted.notna().sum()

        success_ratio = converted_count / non_null_count

        if success_ratio >= 0.8:
            insights["numeric_as_text_columns"].append(col)

    # 4. Imbalanced columns (NEW)
    for col in df.columns:
        value_counts = df[col].value_counts(normalize=True, dropna=True)

        if len(value_counts) > 1:
            if value_counts.iloc[0] > 0.95:
                insights["imbalanced_columns"].append(col)

    return insights


# 5th part
def simple_stats(df):
    my_dict = {}

    numeric_data = df.select_dtypes(include=['number']).columns.tolist()
    categorical_data = df.select_dtypes(include=['object']).columns.tolist()

    my_dict["numeric_data"] = {}
    my_dict["categorical_data"] = {}

    for col in numeric_data:
        my_dict["numeric_data"][col] = {
            "mean": df[col].mean().item(),
            "median": df[col].median().item(),
            "min": df[col].min().item(),
            "max": df[col].max().item()
        }

    for col in categorical_data:
        counts = df[col].value_counts(dropna=True).head(5)
        percentages = df[col].value_counts(normalize=True, dropna=True).head(5) * 100
        
        top_values = {}
        for val in counts.index:
            top_values[str(val)] = {
                "count": counts[val].item(),
                "percentage": round(percentages[val].item(), 1)
            }
            
        mode_val = df[col].mode()
        my_dict["categorical_data"][col] = {
            "unique_values": df[col].nunique(dropna=True),
            "most_frequent": mode_val.iloc[0] if not mode_val.empty else None,
            "top_values": top_values
        }

    return my_dict

def detect_outliers(df):
    insights = {}
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    for col in numeric_columns:

        series = df[col].dropna()

        if len(series) == 0:
            insights[col] = 0
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = series[(series < lower) | (series > upper)]

        percentage = (len(outliers) / len(series)) * 100

        insights[col] = round(percentage, 2)

    return insights

def missing_penalty_columnwise(missing_pct_per_col):

    total_penalty = 0

    for col, pct in missing_pct_per_col.items():

        ratio = pct / 100
        penalty = 12 * (ratio ** 1.3)

        if pct > 20:
            penalty += 3

        total_penalty += penalty

    return total_penalty


def overall_dataset_health(overview, missing, health_checks, outliers):

    total_columns = overview["columns"]

    # Column-wise missing penalty
    missing_penalty = missing_penalty_columnwise(
        missing["missing_percentage_per_column"]
    )

    # Ratios
    single_ratio = len(health_checks["single_value_columns"]) / total_columns
    type_ratio = len(health_checks["numeric_as_text_columns"]) / total_columns
    card_ratio = len(health_checks["high_cardinality_columns"]) / total_columns
    imbalance_ratio = len(health_checks.get("imbalanced_columns", [])) / total_columns

    # Average outlier %
    if len(outliers) > 0:
        avg_outlier = sum(outliers.values()) / len(outliers)
    else:
        avg_outlier = 0

    outlier_ratio = avg_outlier / 100

    # Penalties
    single_penalty = 25 * (single_ratio ** 1.2)
    type_penalty = 20 * (type_ratio ** 1.3)
    card_penalty = 10 * (card_ratio ** 1.1)
    imbalance_penalty = 8 * (imbalance_ratio ** 1.1)
    outlier_penalty = 15 * (outlier_ratio ** 1.2)

    total_penalty = (
        missing_penalty +
        single_penalty +
        type_penalty +
        card_penalty +
        imbalance_penalty +
        outlier_penalty
    )

    health = 100 - total_penalty

    return round(max(min(health, 100), 0), 2)

def column_risk_scores(df, missing_pct_per_col, outliers, health_checks):

    risks = {}

    for col in df.columns:

        risk = 0

        # Missing risk
        pct_missing = missing_pct_per_col.get(col, 0)
        ratio = pct_missing / 100
        risk += 50 * (ratio ** 1.3)

        # Outlier risk
        if col in outliers:
            out_ratio = outliers[col] / 100
            risk += 25 * (out_ratio ** 1.2)

        # Numeric as text
        if col in health_checks["numeric_as_text_columns"]:
            risk += 15

        # Single value
        if col in health_checks["single_value_columns"]:
            risk += 30

        risks[col] = round(risk, 2)

    return risks


def primary_risk_column(risk_dict):

    if not risk_dict:
        return None, 0

    col = max(risk_dict, key=risk_dict.get)
    return col, risk_dict[col]


# ── Intelligence insight generators ──────────────────────────────────────────

def _missing_insight(missing_pct_series):
    if missing_pct_series.empty or missing_pct_series.sum() == 0:
        return "No missing values detected across all columns. Dataset is complete."
    worst_col = missing_pct_series.index[0]
    worst_val = float(missing_pct_series.iloc[0])
    if worst_val <= 5:
        return f"{worst_col} has the highest missing rate at {worst_val}%, which is within acceptable range."
    elif worst_val <= 20:
        return f"{worst_col} shows moderate missing data ({worst_val}%). Consider imputation strategies."
    else:
        return f"Critical: {worst_col} is {worst_val}% missing. This column may need removal or advanced imputation."


def _outlier_insight(labels, iqr_data):
    if not labels:
        return "No numeric columns available."
    max_val = max(iqr_data) if iqr_data else 0
    if max_val < 2:
        return "Low outlier presence detected across numeric features."
    max_idx = iqr_data.index(max_val)
    max_col = labels[max_idx]
    if max_val <= 10:
        return f"{max_col} shows moderate outlier exposure at {max_val}%. Review for data entry errors."
    else:
        return f"{max_col} has high outlier exposure ({max_val}%). Investigate this feature before modeling."


def _hist_insight(col, skewness):
    if abs(skewness) < 0.5:
        return f"{col} appears approximately normally distributed (skewness: {round(skewness, 2)})."
    elif skewness > 1:
        return f"{col} shows right-skewed distribution (skewness: {round(skewness, 2)}). Log scale applied."
    elif skewness < -1:
        return f"{col} shows left-skewed distribution (skewness: {round(skewness, 2)}). Outliers may pull the tail."
    elif skewness > 0.5:
        return f"{col} is slightly right-skewed (skewness: {round(skewness, 2)})."
    else:
        return f"{col} is slightly left-skewed (skewness: {round(skewness, 2)})."


def _cat_insight(col, n_unique, top5, total):
    top_val   = str(top5.index[0]) if not top5.empty else "N/A"
    top_count = int(top5.iloc[0]) if not top5.empty else 0
    top_pct   = round(top_count / total * 100, 1) if total > 0 else 0
    if n_unique > 50:
        return f"{col} is a high-cardinality feature ({n_unique} categories). Top value '{top_val}' at {top_pct}%."
    elif top_pct > 80:
        return f"{col} is heavily dominated by '{top_val}' ({top_pct}%), indicating class imbalance."
    else:
        return f"{col} has {n_unique} unique categories. '{top_val}' is the most frequent at {top_pct}%."


def _scatter_insight(x_col, y_col, pearson_r):
    if pearson_r is None:
        return f"Correlation between {x_col} and {y_col} could not be computed."
    r_abs = abs(pearson_r)
    direction = "positive" if pearson_r > 0 else "negative"
    if r_abs >= 0.8:
        strength = "strong"
    elif r_abs >= 0.5:
        strength = "moderate"
    elif r_abs >= 0.3:
        strength = "weak"
    else:
        strength = "negligible"
    return f"{x_col} and {y_col} show a {strength} {direction} correlation (r = {pearson_r})."


# 9th part — Chart Data Generator (Production-Grade Edition)
def generate_chart_data(df):
    """
    Generates structured, JSON-safe chart data for Chart.js rendering.
    Includes: FD binning, skewness/log-scale, Pearson r, regression line,
    IQR+Z-score dual outlier, smart sampling, intelligence insights, complexity index.
    """
    charts = {}
    n_rows = len(df)

    numeric_cols     = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    datetime_cols    = df.select_dtypes(include=['datetime64']).columns.tolist()
    bool_cols        = df.select_dtypes(include=['bool']).columns.tolist()

    # ── IQR outlier % helper ─────────────────────────────────────────────────
    def _outlier_pct(series):
        s = series.dropna()
        if len(s) == 0:
            return 0.0
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        n_out = len(s[(s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)])
        return round(n_out / len(s) * 100, 2)

    # ── Z-score outlier % helper ─────────────────────────────────────────────
    def _zscore_outlier_pct(series):
        s = series.dropna()
        if len(s) < 3:
            return 0.0
        mean, std = s.mean(), s.std()
        if std == 0:
            return 0.0
        z = (s - mean).abs() / std
        return round((z > 3).sum() / len(s) * 100, 2)

    # ── 1. ID-Like Column Detection ──────────────────────────────────────────
    id_like_cols = set()
    for col in numeric_cols:
        if n_rows > 0 and df[col].nunique() / n_rows > 0.95:
            id_like_cols.add(col)
    cat_id_like = set()
    for col in categorical_cols:
        if n_rows > 0 and df[col].nunique() / n_rows > 0.90:
            cat_id_like.add(col)

    analytic_numeric      = [c for c in numeric_cols if c not in id_like_cols]
    analytic_categorical  = [c for c in categorical_cols if c not in cat_id_like]

    # ── 2. Column Type Breakdown (Doughnut) ──────────────────────────────────
    charts["type_breakdown"] = {
        "labels": ["Numeric", "Categorical", "Datetime", "Boolean"],
        "data":   [len(numeric_cols), len(analytic_categorical),
                   len(datetime_cols), len(bool_cols)],
        "column_names": {
            "Numeric":     numeric_cols,
            "Categorical": analytic_categorical,
            "Datetime":    datetime_cols,
            "Boolean":     bool_cols,
        }
    }

    # ── 3. Missing Data per Column (sorted descending) ───────────────────────
    missing_pct = df.isnull().mean().mul(100).round(2).sort_values(ascending=False)

    def _missing_color(v):
        if v <= 5:
            return 'rgba(52,211,153,0.75)'
        elif v <= 20:
            return 'rgba(250,204,21,0.80)'
        else:
            return 'rgba(239,68,68,0.80)'

    charts["missing_bar"] = {
        "labels":  missing_pct.index.tolist(),
        "data":    missing_pct.values.tolist(),
        "colors":  [_missing_color(v) for v in missing_pct.values],
        "insight": _missing_insight(missing_pct)
    }

    # ── 4. Outlier % per Numeric Column (IQR + Z-score) ────────────────────
    outlier_labels, iqr_data, zscore_data = [], [], []
    for col in numeric_cols:
        pct_iqr = _outlier_pct(df[col])
        pct_z   = _zscore_outlier_pct(df[col])
        label   = f"{col} [ID]" if col in id_like_cols else col
        outlier_labels.append(label)
        iqr_data.append(pct_iqr)
        zscore_data.append(pct_z)

    low_outlier = (len(iqr_data) > 0 and max(iqr_data, default=0) < 2)
    charts["outlier_bar"] = {
        "labels":           outlier_labels,
        "data":             iqr_data,
        "zscore_data":      zscore_data,
        "low_outlier_flag": low_outlier,
        "insight":          ("Low outlier presence detected across numeric features."
                             if low_outlier
                             else _outlier_insight(outlier_labels, iqr_data))
    }

    # ── 5. Risk-Based Numeric Ranking (FD bins) — Top-4 Histograms ─────────
    charts["histograms"] = []
    if analytic_numeric:
        raw_missing = {c: df[c].isnull().mean() * 100 for c in analytic_numeric}
        raw_outlier = {c: _outlier_pct(df[c]) for c in analytic_numeric}
        raw_var     = {}
        for c in analytic_numeric:
            s = df[c].dropna()
            raw_var[c] = float(s.var()) if len(s) > 1 else 0.0

        max_var  = max(raw_var.values()) if raw_var else 1.0
        norm_var = {c: (raw_var[c] / max_var) if max_var > 0 else 0.0
                    for c in analytic_numeric}

        priority = {
            c: (0.4 * raw_outlier[c] / 100
                + 0.3 * raw_missing[c] / 100
                + 0.3 * norm_var[c])
            for c in analytic_numeric
        }

        ranked_numeric = sorted(analytic_numeric, key=lambda c: priority[c], reverse=True)
        for col in ranked_numeric[:4]:
            series = df[col].dropna()
            if len(series) < 2:
                continue
            try:
                skewness = float(series.skew())
                use_log  = abs(skewness) > 1 and series.min() > 0

                # Freedman-Diaconis bin sizing
                q75, q25 = np.percentile(series, [75, 25])
                iqr_val  = q75 - q25
                if iqr_val > 0:
                    bin_width = 2 * iqr_val / (len(series) ** (1.0 / 3.0))
                    data_range = series.max() - series.min()
                    n_bins = int(np.ceil(data_range / bin_width)) if bin_width > 0 else 10
                else:
                    n_bins = 10
                n_bins = max(2, min(n_bins, 50))

                if use_log:
                    log_series = np.log1p(series)
                    counts, bin_edges = np.histogram(log_series, bins=n_bins)
                    bin_labels = [f"log({round(float(b), 2)})" for b in bin_edges[:-1]]
                else:
                    counts, bin_edges = np.histogram(series, bins=n_bins)
                    bin_labels = [f"{round(float(b), 2)}" for b in bin_edges[:-1]]

                charts["histograms"].append({
                    "column":   col,
                    "labels":   bin_labels,
                    "data":     counts.tolist(),
                    "skewness": round(skewness, 3),
                    "use_log":  use_log,
                    "insight":  _hist_insight(col, skewness)
                })
            except Exception:
                continue

    # ── 6. Entropy-Based Categorical Ranking — Top-3 Columns ────────────────
    charts["top5_bars"] = []
    if analytic_categorical:
        def _entropy(col):
            vc = df[col].value_counts(normalize=True, dropna=True)
            if vc.empty:
                return 0.0
            return -sum(p * math.log2(p) for p in vc if p > 0)

        ranked_cat = sorted(analytic_categorical, key=_entropy, reverse=True)
        for col in ranked_cat[:3]:
            total = int(df[col].notna().sum())
            top5  = df[col].value_counts(dropna=True).head(5)
            if top5.empty:
                continue
            n_unique = int(df[col].nunique(dropna=True))
            charts["top5_bars"].append({
                "column":           col,
                "labels":           top5.index.astype(str).tolist(),
                "data":             top5.values.tolist(),
                "percentages":      [round(v / total * 100, 1) if total > 0 else 0
                                     for v in top5.values],
                "high_cardinality": n_unique > 50,
                "unique_count":     n_unique,
                "insight":          _cat_insight(col, n_unique, top5, total)
            })

    # ── 7. Correlation-Based Scatter Plot with Regression Line ───────────────
    charts["scatter"] = None
    if len(analytic_numeric) >= 2:
        try:
            variances = {c: float(df[c].dropna().var()) for c in analytic_numeric}
            top2      = sorted(variances, key=variances.get, reverse=True)[:2]
            x_col, y_col = top2[0], top2[1]

            pair_df = df[[x_col, y_col]].dropna()

            # Check if we have any data points after dropping NaN
            if len(pair_df) == 0:
                # No valid data points, skip scatter plot
                charts["scatter"] = None
                return charts

            sampled_note = None
            if len(pair_df) > 50_000:
                pair_df = pair_df.sample(n=1000, random_state=42)
                sampled_note = "Visualization generated using sampled data for performance."

            pearson_r = None
            if len(pair_df) >= 2:
                try:
                    corr = pair_df[x_col].corr(pair_df[y_col])
                    pearson_r = round(float(corr), 4) if not math.isnan(corr) else None
                except Exception:
                    pearson_r = None

            regression_points = None
            if pearson_r is not None and len(pair_df) >= 2:
                try:
                    x_vals = pair_df[x_col].values.astype(float)
                    y_vals = pair_df[y_col].values.astype(float)
                    x_mean, y_mean = x_vals.mean(), y_vals.mean()
                    slope_num = np.sum((x_vals - x_mean) * (y_vals - y_mean))
                    slope_den = np.sum((x_vals - x_mean) ** 2)
                    if slope_den != 0:
                        slope     = slope_num / slope_den
                        intercept = y_mean - slope * x_mean
                        x_min, x_max = float(x_vals.min()), float(x_vals.max())
                        regression_points = [
                            {"x": x_min, "y": round(slope * x_min + intercept, 4)},
                            {"x": x_max, "y": round(slope * x_max + intercept, 4)}
                        ]
                except Exception:
                    regression_points = None

            charts["scatter"] = {
                "x_label":      x_col,
                "y_label":      y_col,
                "points":       [{"x": float(r[x_col]), "y": float(r[y_col])}
                                 for _, r in pair_df.iterrows()],
                "pearson_r":    pearson_r,
                "regression":   regression_points,
                "sampled_note": sampled_note,
                "insight":      _scatter_insight(x_col, y_col, pearson_r)
            }
        except Exception:
            if len(analytic_numeric) >= 2:
                x_col, y_col = analytic_numeric[0], analytic_numeric[1]
                sample = df[[x_col, y_col]].dropna().head(200)
                
                # Check if we have any valid data points
                if len(sample) == 0:
                    charts["scatter"] = None
                else:
                    charts["scatter"] = {
                        "x_label":      x_col,
                        "y_label":      y_col,
                        "points":       [{"x": float(r[x_col]), "y": float(r[y_col])}
                                         for _, r in sample.iterrows()],
                        "pearson_r":    None,
                        "regression":   None,
                        "sampled_note": None,
                        "insight":      f"{x_col} and {y_col} relationship could not be computed."
                    }

    # ── 8. Data Complexity Index ─────────────────────────────────────────────
    num_count   = len(numeric_cols)
    avg_missing = (float(np.mean(df.isnull().mean().mul(100).values))
                   if n_rows > 0 else 0.0)
    avg_outlier = float(np.mean(iqr_data)) if iqr_data else 0.0
    complexity_score = round(
        0.3 * num_count + 0.4 * avg_missing + 0.3 * avg_outlier, 2
    )
    if complexity_score <= 20:
        complexity_label = "Simple"
    elif complexity_score <= 50:
        complexity_label = "Moderate"
    else:
        complexity_label = "Complex"

    charts["complexity"] = {
        "score": complexity_score,
        "label": complexity_label
    }

    return charts
