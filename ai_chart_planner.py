import json
import time
import llm_client


def generate_chart_plan(clean_insights: dict, api_key: str = "", model_name: str = "gemini-2.5-flash", dataset_profile: dict | None = None) -> dict:
    """
    Two-phase AI chart planner:
      Phase 1 — Classify the dataset (Sales, ML, HR, Financial, etc.)
      Phase 2 — Generate 8-12 analyst-curated charts like a senior Power BI analyst

    Returns a dict:
    {
        "dataset_type": "E-Commerce / Retail Sales",
        "dataset_summary": "This dataset captures ...",
        "charts": [
            {
                "type": "bar",
                "title": "Revenue Concentration by Geography",
                "subtitle": "Top 10 countries by total invoice value",
                "labels": [...],
                "data": [...],
                "insight": "UK dominates with 82% of total transactions...",
                "kpi": {"label": "Total Revenue", "value": "£1.2M"}  // optional
            },
            ...
        ]
    }
    Returns a fallback dict on any failure.
    """
    # Step 1 — Build enriched but token-safe payload
    reduced = {}
    for key in ("basic_overview", "column_types", "missing_overview",
                "simple_stats", "outliers", "overall_health_score",
                "data_trust_level", "primary_risk_column", "health_checks"):
        if key in clean_insights:
            reduced[key] = clean_insights[key]
    if dataset_profile:
        reduced["dataset_profile"] = dataset_profile

    json_string = json.dumps(reduced, indent=2)

    # Step 2 — Construct the two-phase prompt
    prompt = f"""You are a SENIOR BUSINESS & PRODUCT ANALYST with 5+ years of Power BI experience. You are given a JSON summary of a dataset. Your job has two phases:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — DATASET CLASSIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Analyze the column names, data types, value ranges, statistical patterns, and domain signals to classify this dataset into ONE of these categories (or create a more specific one):
- E-Commerce / Retail Sales
- Student Performance / Education
- HR / Employee Analytics
- Financial Transactions / Banking
- Healthcare / Clinical
- IoT / Sensor Data
- Marketing / Campaign Analytics
- Supply Chain / Logistics
- Real Estate / Property
- Social Media / User Engagement
- Machine Learning Feature Dataset
- Survey / Feedback Data
- (or any other specific domain you identify)

Provide:
- "dataset_type": a short, specific label (max 5 words)
- "dataset_summary": 2-3 sentences describing what this dataset represents from a BUSINESS perspective. Explain what questions this data can answer, who would use it, and what decisions it supports. Do NOT describe the technical structure — describe the BUSINESS story.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — ANALYST-CURATED DASHBOARD CHARTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Now, think like a senior Power BI analyst presenting this data to C-level executives. Design 8 to 12 charts that TELL THE STORY of this dataset. Each chart should answer a specific business question.

For each chart, provide:
- "type": one of "bar", "pie", "doughnut", "line", "radar", "polarArea"
- "title": a professional, business-oriented title
- "subtitle": a 1-line methodology note
- "labels": array of string labels (max 12 items)
- "data": array of numeric values matching labels
- "insight": a 1-sentence BUSINESS insight explaining what this chart reveals and WHY it matters
- "kpi": (OPTIONAL, include for 2-4 charts max) an object with "label" and "value" showing a headline metric

CRITICAL RULES:
1. Generate EXACTLY 8 to 12 charts. Maximize diversity.
2. Use VARIETY — do not repeat the same chart type more than 3 times.
3. Each chart must answer a DIFFERENT business question about the data.
4. All data values must come directly or be derived from the JSON metadata below.
5. Labels and data arrays must have the SAME length.
6. Never include charts with empty labels or data arrays.
7. Titles should sound like they're on a Power BI executive dashboard.
8. The insight text should explain the "so what?" — why does this matter for business decisions?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return ONLY a valid JSON object. No markdown, no explanations, no code fences. Just the raw JSON:

{{
  "dataset_type": "E-Commerce / Retail Sales",
  "dataset_summary": "This dataset captures UK-based online retail transactions...",
  "charts": [
    {{
      "type": "doughnut",
      "title": "Transaction Volume by Geography",
      "subtitle": "Percentage share of orders across top markets",
      "labels": ["UK", "Germany", "France"],
      "data": [82, 10, 8],
      "insight": "UK dominates with 82% of transactions, indicating high geographic concentration risk.",
      "kpi": {{"label": "Primary Market", "value": "UK (82%)"}}
    }}
  ]
}}

Dataset Metadata:
{json_string}

Respond with ONLY the JSON object, nothing else.
"""

    # Step 3 — Call LLM via unified client
    try:
        raw_text = llm_client.generate(prompt, api_key, model_name, json_mode=True)

        if not raw_text:
            print("[ai_chart_planner] LLM returned no response")
            return _fallback_from_metadata(reduced)

        cleaned = raw_text.strip()
        
        # Strip potential markdown fences if the model ignored json_mode
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].startswith("```"): lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace + 1]

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as je:
            print(f"[ai_chart_planner] JSON parse failed: {je}")
            print(f"[ai_chart_planner] Raw text (first 500 chars): {raw_text[:500]}")
            return _fallback_from_metadata(reduced)

        # Validate top-level structure
        if not isinstance(result, dict):
            return _fallback_from_metadata(reduced)

        dataset_type = str(result.get("dataset_type", "Unknown Dataset"))
        dataset_summary = str(result.get("dataset_summary", ""))
        raw_charts = result.get("charts", [])

        if not isinstance(raw_charts, list):
            return _fallback_from_metadata(reduced)

        # Validate and clean each chart
        valid_types = {"bar", "pie", "doughnut", "line", "radar", "polarArea"}
        cleaned = []
        for i, chart in enumerate(raw_charts):
            if not isinstance(chart, dict):
                with open('app_debug.log', 'a') as f: f.write(f"[ai_chart_planner] Chart {i} rejected: Not a dict\n")
                continue
            if chart.get("type") not in valid_types:
                with open('app_debug.log', 'a') as f: f.write(f"[ai_chart_planner] Chart {i} rejected: Invalid type {chart.get('type')}\n")
                continue
            if not isinstance(chart.get("labels"), list) or not isinstance(chart.get("data"), list):
                with open('app_debug.log', 'a') as f: f.write(f"[ai_chart_planner] Chart {i} rejected: Missing labels or data list\n")
                continue
            
            # Ensure equal length BEFORE checking for empty arrays
            min_len = min(len(chart["labels"]), len(chart["data"]))
            if min_len == 0:
                with open('app_debug.log', 'a') as f: f.write(f"[ai_chart_planner] Chart {i} rejected: Empty labels/data after min_len calculation\n")
                continue  # Skip if no data points after equalization
                
            chart["labels"] = [str(l) for l in chart["labels"][:min_len]]
            chart["data"] = [(float(d) if d is not None else 0.0) for d in chart["data"][:min_len]]
            
            # Additional validation to ensure we have valid data after processing
            if len(chart["labels"]) == 0 or len(chart["data"]) == 0:
                with open('app_debug.log', 'a') as f: f.write(f"[ai_chart_planner] Chart {i} rejected: Zero length labels/data\n")
                continue
                
            chart["title"] = str(chart.get("title", "Chart"))
            chart["subtitle"] = str(chart.get("subtitle", ""))
            chart["insight"] = str(chart.get("insight", ""))
            # Validate optional kpi field
            if "kpi" in chart:
                kpi = chart["kpi"]
                if isinstance(kpi, dict) and "label" in kpi and "value" in kpi:
                    chart["kpi"] = {"label": str(kpi["label"]), "value": str(kpi["value"])}
                else:
                    del chart["kpi"]
            cleaned.append(chart)

        # Final validation to ensure no empty charts are returned
        final_charts = []
        for i, chart in enumerate(cleaned):
            if (chart and 
                chart.get("type") and 
                isinstance(chart.get("labels"), list) and 
                isinstance(chart.get("data"), list) and
                len(chart["labels"]) > 0 and 
                len(chart["data"]) > 0):
                final_charts.append(chart)
            else:
                 with open('app_debug.log', 'a') as f: f.write(f"[ai_chart_planner] Cleaned chart {i} rejected in final validation\n")

        with open('app_debug.log', 'a') as f: f.write(f"[ai_chart_planner] Returning {len(final_charts)} charts.\n")
        
        if len(final_charts) == 0:
            with open('app_debug.log', 'a') as f: f.write(f"[ai_chart_planner] No valid charts remained, triggering fallback\n")
            return _fallback_from_metadata(reduced)

        return {
            "dataset_type": dataset_type,
            "dataset_summary": dataset_summary,
            "charts": final_charts
        }

    except Exception as e:
        import traceback
        with open('app_debug.log', 'a') as f:
            f.write(f"[ai_chart_planner] Error generating chart plan: {e}\n{traceback.format_exc()}\n")
        print(f"[ai_chart_planner] Error generating chart plan: {e}")
        return _fallback_from_metadata(reduced)


def _fallback_from_metadata(meta: dict) -> dict:
    charts = []
    outs = meta.get("outliers", {}) or {}
    overall = float(meta.get("overall_health_score", 0) or 0)
    missing_pct = float(meta.get("missing_overview", {}).get("missing_percentage", 0) or 0)
    stats = meta.get("simple_stats", {}) or {}
    num_stats = stats.get("numeric_data", {}) or {}
    cat_stats = stats.get("categorical_data", {}) or {}
    health = meta.get("health_checks", {}) or {}
    total_cols = int(meta.get("basic_overview", {}).get("columns", 0) or 0)

    # 1) Polar Area — Executive Quality Mix (distinct from Graphical View)
    try:
        avg_outlier = 0.0
        if isinstance(outs, dict) and outs:
            vals = [float(v or 0) for v in outs.values()]
            avg_outlier = float(sum(vals) / len(vals)) if vals else 0.0
        charts.append({
            "type": "polarArea",
            "title": "Executive Quality Mix",
            "subtitle": "Missing vs Outlier vs Health",
            "labels": ["Missing %", "Avg Outlier %", "Health Score"],
            "data": [missing_pct, avg_outlier, overall],
            "insight": "Macro quality snapshot for leadership decisions."
        })
    except Exception:
        pass

    # 2) Radar — Risk Signals Distribution (counts across integrity flags)
    try:
        sv = len(health.get("single_value_columns", []) or [])
        nt = len(health.get("numeric_as_text_columns", []) or [])
        hc = len(health.get("high_cardinality_columns", []) or [])
        im = len(health.get("imbalanced_columns", []) or [])
        charts.append({
            "type": "radar",
            "title": "Risk Signals Distribution",
            "subtitle": "Integrity flags across schema",
            "labels": ["Single Value", "Numeric as Text", "High Cardinality", "Imbalanced"],
            "data": [float(sv), float(nt), float(hc), float(im)],
            "insight": "Signal intensity profile guiding remediation focus."
        })
    except Exception:
        pass

    # 3) Doughnut — Integrity Impact (flagged vs clean columns)
    try:
        sv_cols = set(health.get("single_value_columns", []) or [])
        nt_cols = set(health.get("numeric_as_text_columns", []) or [])
        hc_cols = set(health.get("high_cardinality_columns", []) or [])
        im_cols = set(health.get("imbalanced_columns", []) or [])
        flagged_union = sv_cols | nt_cols | hc_cols | im_cols
        flagged = len(flagged_union)
        clean = max(total_cols - flagged, 0)
        charts.append({
            "type": "doughnut",
            "title": "Integrity Impact",
            "subtitle": "Flagged vs clean columns",
            "labels": ["Flagged", "Clean"],
            "data": [float(flagged), float(clean)],
            "insight": "Overall integrity footprint across the dataset."
        })
    except Exception:
        pass

    # 4) Bar — Composite Risk Ranking (top features by combined risk)
    try:
        miss_per_col = meta.get("missing_overview", {}).get("missing_percentage_per_column", {}) or {}
        composite = []
        for c in set(list(miss_per_col.keys()) + list(outs.keys())):
            m = float(miss_per_col.get(c, 0) or 0)
            o = float(outs.get(c, 0) or 0)
            score = 0.6 * m + 0.4 * o
            composite.append((c, score))
        composite.sort(key=lambda x: x[1], reverse=True)
        top = composite[:10]
        if top:
            charts.append({
                "type": "bar",
                "title": "Top Integrity Risks",
                "subtitle": "Composite score (0.6×Missing + 0.4×Outlier)",
                "labels": [str(k) for k, _ in top],
                "data": [float(v) for _, v in top],
                "insight": "Prioritized cleanup sequence to stabilize downstream analysis."
            })
    except Exception:
        pass

    # 5) Line — Skewness Proxy (|mean − median| across numeric features)
    try:
        diffs = []
        for col, s in (num_stats.items() if isinstance(num_stats, dict) else []):
            try:
                mean_v = float(s.get("mean", 0))
                med_v = float(s.get("median", 0))
                diffs.append((col, abs(mean_v - med_v)))
            except Exception:
                continue
        diffs.sort(key=lambda x: x[1], reverse=True)
        topd = diffs[:10]
        if topd:
            charts.append({
                "type": "line",
                "title": "Skewness Proxy",
                "subtitle": "Absolute difference between mean and median",
                "labels": [str(k) for k, _ in topd],
                "data": [float(v) for _, v in topd],
                "insight": "Skew-prone features that can distort modeling."
            })
    except Exception:
        pass

    # 6) Pie — Category Complexity Concentration (unique value buckets)
    try:
        buckets = {"Low (≤5)": 0, "Medium (6–20)": 0, "High (>20)": 0}
        for col, s in (cat_stats.items() if isinstance(cat_stats, dict) else []):
            try:
                u = int(s.get("unique_values", 0) or 0)
                if u <= 5: buckets["Low (≤5)"] += 1
                elif u <= 20: buckets["Medium (6–20)"] += 1
                else: buckets["High (>20)"] += 1
            except Exception:
                continue
        labels = list(buckets.keys())
        data = [float(buckets[k]) for k in labels]
        if sum(data) > 0:
            charts.append({
                "type": "pie",
                "title": "Category Complexity Concentration",
                "subtitle": "Unique value buckets",
                "labels": labels,
                "data": data,
                "insight": "Complex categories affect grouping efficiency."
            })
    except Exception:
        pass

    # 7) Bar — Coverage vs Reliability (2 KPI bars)
    try:
        coverage = max(0.0, 100.0 - missing_pct)
        charts.append({
            "type": "bar",
            "title": "Coverage vs Reliability",
            "subtitle": "Non-missing coverage vs health score",
            "labels": ["Coverage", "Health"],
            "data": [coverage, overall],
            "insight": "High coverage with low health indicates structural issues."
        })
    except Exception:
        pass

    # 8) Pie — Outlier Severity Mix (bins of outlier %)
    try:
        bins = {"≤2%": 0, "2–10%": 0, "10–20%": 0, ">20%": 0}
        for v in (outs.values() if isinstance(outs, dict) else []):
            try:
                val = float(v or 0)
                if val <= 2: bins["≤2%"] += 1
                elif val <= 10: bins["2–10%"] += 1
                elif val <= 20: bins["10–20%"] += 1
                else: bins[">20%"] += 1
            except Exception:
                continue
        labels = list(bins.keys())
        data = [float(bins[k]) for k in labels]
        if sum(data) > 0:
            charts.append({
                "type": "pie",
                "title": "Outlier Severity Mix",
                "subtitle": "Distribution across severity buckets",
                "labels": labels,
                "data": data,
                "insight": "Severity profile informs cap/trimming strategies."
            })
    except Exception:
        pass

    # Final validation to ensure no empty charts
    validated_charts = []
    for chart in charts:
        if (chart and 
            chart.get("type") and 
            isinstance(chart.get("labels"), list) and 
            isinstance(chart.get("data"), list) and
            len(chart["labels"]) > 0 and 
            len(chart["data"]) > 0):
            validated_charts.append(chart)
    
    return {
        "dataset_type": "Fallback Analytics",
        "dataset_summary": "AI service unavailable — distinct executive charts derived from metadata.",
        "charts": validated_charts
    }
