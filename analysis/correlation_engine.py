"""
Correlation Discovery Engine for Insight Forge.

Computes pairwise correlations between numeric columns and returns
the strongest relationships (|r| > 0.5) in a structured format.
"""
import pandas as pd
import numpy as np


def compute_correlations(df, threshold=0.5, max_pairs=12):
    """
    Compute pairwise Pearson correlations for all numeric columns.

    Args:
        df: pandas DataFrame
        threshold: minimum |correlation| to include (default 0.5)
        max_pairs: maximum number of correlation pairs to return

    Returns:
        dict with:
          - strong_correlations: list of {feature_a, feature_b, correlation, strength}
          - matrix_summary: {total_numeric_cols, total_pairs_checked, strong_count}
    """
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    result = {
        "strong_correlations": [],
        "matrix_summary": {
            "total_numeric_cols": len(numeric_cols),
            "total_pairs_checked": 0,
            "strong_count": 0,
        },
    }

    if len(numeric_cols) < 2:
        return result

    # Compute full correlation matrix
    corr_matrix = df[numeric_cols].corr(method="pearson")

    # Extract unique pairs (upper triangle, no self-correlation)
    pairs = []
    n = len(numeric_cols)
    total_pairs = 0

    for i in range(n):
        for j in range(i + 1, n):
            total_pairs += 1
            r = corr_matrix.iloc[i, j]

            # Skip NaN correlations
            if pd.isna(r):
                continue

            r_val = round(float(r), 4)

            if abs(r_val) >= threshold:
                # Classify strength
                abs_r = abs(r_val)
                if abs_r >= 0.8:
                    strength = "Very Strong"
                elif abs_r >= 0.6:
                    strength = "Strong"
                else:
                    strength = "Moderate"

                direction = "Positive" if r_val > 0 else "Negative"

                pairs.append({
                    "feature_a": numeric_cols[i],
                    "feature_b": numeric_cols[j],
                    "correlation": r_val,
                    "abs_correlation": abs_r,
                    "strength": strength,
                    "direction": direction,
                })

    # Sort by absolute correlation descending, take top N
    pairs.sort(key=lambda p: p["abs_correlation"], reverse=True)
    top_pairs = pairs[:max_pairs]

    # Remove the helper field before returning
    for p in top_pairs:
        del p["abs_correlation"]

    result["strong_correlations"] = top_pairs
    result["matrix_summary"]["total_pairs_checked"] = total_pairs
    result["matrix_summary"]["strong_count"] = len(top_pairs)

    return result
