import json
import math
import os
import uuid
import pandas as pd
import numpy as np
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session, Response
from insight_analysis import summarize_csv_insights as summary
from ai_chart_planner import generate_chart_plan
from analysis.correlation_engine import compute_correlations
from ai.query_agent import ask_question
from reporting.report_generator import generate_report, report_to_html
from llm_client import AVAILABLE_MODELS
from dataset_intelligence import build_dataset_profile
from feature_importance import compute_feature_importance
from chart_recommender import recommend_charts
from column_classifier import classify_columns
from target_detector import detect_target_columns
from insight_engine import discover_insights

CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


def save_cache(data, session_id):
    path = os.path.join(CACHE_DIR, f"{session_id}.json")
    with open(path, "w") as f:
        json.dump(data, f, default=str)


def load_cache(session_id):
    path = os.path.join(CACHE_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def convert_numpy(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj


def clean_for_json(obj):
    """
    Recursively convert a chart-data structure into a JSON-safe form:
      - numpy scalar types (bool_, int64, float64 …) → native Python equivalents
      - float NaN / Infinity → None   (bare NaN is invalid JSON)
      - dict / list handled recursively
    """
    # numpy scalars first (covers bool_, int8-64, float16-64, etc.)
    if isinstance(obj, np.generic):
        val = obj.item()          # converts to native Python int/float/bool/str
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
        return val
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (bool, int)):   # plain Python bool/int are fine
        return obj
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean_for_json(v) for v in obj]
    return obj

from main import (
    basic_overview,
    missing_overview,
    column_types,
    healthy,
    simple_stats,
    detect_outliers,
    overall_dataset_health,
    column_risk_scores,
    primary_risk_column,
    generate_chart_data
)

app = Flask(__name__)
app.secret_key = "insight-forge-secret"


@app.route("/")
def home():
    return render_template("home.html", available_models=AVAILABLE_MODELS)


@app.route("/analyze", methods=["POST"])
def analyze():

    # 0. Read API key and model from form
    api_key = request.form.get("api_key", "").strip()
    model_name = request.form.get("model_name", "gemini-2.5-flash").strip()

    if not api_key:
        flash("Please enter your API key before generating analysis.", "error")
        return redirect(url_for("home"))

    # 1. File validation
    if "datafile" not in request.files:
        flash("No file uploaded. Please upload a CSV or XLSX file.", "error")
        return redirect(url_for("home"))

    file = request.files["datafile"]

    if file.filename == "":
        flash("No file selected. Please upload a CSV or XLSX file.", "error")
        return redirect(url_for("home"))

    filename = file.filename.lower()

    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        flash("Only CSV and XLSX files are allowed.", "error")
        return redirect(url_for("home"))

    # 2. Read file safely
    try:
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(file)
            except UnicodeDecodeError:
                file.seek(0)
                df = pd.read_csv(file, encoding="latin1")
        else:
            df = pd.read_excel(file)
            df.columns = df.columns.astype(str)

    except Exception:
        flash("Failed to read file. Please upload a valid CSV or XLSX file.", "error")
        return redirect(url_for("home"))

    # 3. Core Analysis
    # 📉 Sampling for large datasets (e.g. 200k rows) to prevent timeouts and session size issues
    if len(df) > 50000:
        df_sample = df.sample(n=50000, random_state=42)
    else:
        df_sample = df

    overview = basic_overview(df)
    missing = missing_overview(df)
    types = column_types(df)
    health = healthy(df)
    stats = simple_stats(df)
    outliers = detect_outliers(df)

    # 4. Overall Health Score
    score = overall_dataset_health(
        overview,
        missing,
        health,
        outliers
    )

    # 5. Data Trust Level
    if score >= 85:
        trust_level = "High"
    elif score >= 65:
        trust_level = "Moderate"
    else:
        trust_level = "Low"

    # 6. Primary Risk Detection
    risk_scores = column_risk_scores(
        df,
        missing["missing_percentage_per_column"],
        outliers,
        health
    )

    primary_col, primary_score = primary_risk_column(risk_scores)

    # 7. Chart Data for Graphical View
    charts = generate_chart_data(df_sample)

    # Dataset intelligence profile
    dataset_profile = build_dataset_profile(df_sample)
    column_classes = classify_columns(df_sample)
    targets = detect_target_columns(df_sample, column_classes)

    # 8. Final Insights Dictionary
    final_insights = {
        "basic_overview": overview,
        "missing_overview": missing,
        "column_types": types,
        "health_checks": health,
        "simple_stats": stats,
        "outliers": outliers,
        "overall_health_score": score,
        "data_trust_level": trust_level,
        "primary_risk_column": primary_col,
        "primary_risk_score": primary_score,
        "charts": charts,
        "dataset_profile": dataset_profile,
        "column_classifications": column_classes,
        "targets": targets
    }

    # 9. AI Executive Summary
    # 🔧 Clean numpy values before sending to AI
    clean_insights = convert_numpy(final_insights)

    data_summary = summary(clean_insights, api_key=api_key, model_name=model_name, dataset_profile=dataset_profile)
    clean_insights["summary"] = data_summary

    # 10. Correlation Discovery
    correlation_data = compute_correlations(df_sample)
    correlation_data = convert_numpy(correlation_data)
    clean_insights["correlations"] = correlation_data

    # 11. AI Chart Plan (classifies dataset + decides which charts to render)
    ai_plan = generate_chart_plan(clean_insights, api_key=api_key, model_name=model_name, dataset_profile=dataset_profile)

    # Feature importance + recommendations
    importance = compute_feature_importance(df_sample, dataset_profile, column_classes)
    recommended = recommend_charts(dataset_profile, df_sample, importance, correlation_data, column_classes)
    strategic = discover_insights(df_sample, correlation_data, importance, column_classes)

    # 12. Store insights + credentials in server-side cache to bypass cookie limits
    session_id = str(uuid.uuid4())
    session["session_id"] = session_id
    
    cache_data = {
        "clean_insights": clean_insights,
        "dataset_profile": dataset_profile,
        "top_features": importance,
        "column_classifications": column_classes,
        "api_key": api_key,
        "model_name": model_name,
        "total_rows": len(df),
        "primary_risk_column": primary_col,
        "primary_risk_score": primary_score
    }
    save_cache(cache_data, session_id)

    safe_charts = clean_for_json(charts)
    return render_template(
        "dashboard.html",
        insights=clean_insights,
        charts_json=json.dumps(safe_charts),
        ai_dataset_type=ai_plan.get("dataset_type", "Unknown"),
        ai_dataset_summary=ai_plan.get("dataset_summary", ""),
        ai_charts_json=json.dumps(ai_plan.get("charts", [])),
        correlation_json=json.dumps(correlation_data),
        drivers_json=json.dumps(importance.get("top_features", [])),
        target_column=importance.get("target_column"),
        recommended_charts_json=json.dumps(recommended),
        strategic_insights_json=json.dumps(strategic)
    )


# ── Feature 2: Natural Language Data Questions ──────────────────────────────

@app.route("/ask", methods=["POST"])
def ask():
    """Handle natural language questions about the dataset."""
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"answer": "No dataset loaded. Please upload a file first.", "chart": None})

    cache_data = load_cache(session_id)
    if not cache_data:
        return jsonify({"answer": "Session data expired or not found. Please re-upload.", "chart": None})

    stored_insights = cache_data.get("clean_insights", {})
    api_key = cache_data.get("api_key", "")
    model_name = cache_data.get("model_name", "gemini-2.5-flash")
    dataset_profile = cache_data.get("dataset_profile")
    column_classes = cache_data.get("column_classifications")

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"answer": "Please enter a question.", "chart": None})

    result = ask_question(
        question,
        stored_insights,
        api_key=api_key,
        model_name=model_name,
        dataset_profile=dataset_profile,
        basic_stats=stored_insights.get("simple_stats"),
        column_classifications=column_classes,
        correlations=stored_insights.get("correlations"),
        total_rows=cache_data.get("total_rows"),
        primary_risk_column=cache_data.get("primary_risk_column"),
        primary_risk_score=cache_data.get("primary_risk_score"),
        top_features=cache_data.get("top_features")
    )
    return jsonify(result)


# ── Feature 3: Auto Business Report Generator ──────────────────────────────

@app.route("/report", methods=["POST"])
def report():
    """Generate a structured business report."""
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"error": "No dataset loaded. Please upload a file first."})

    cache_data = load_cache(session_id)
    if not cache_data:
        return jsonify({"error": "Session data expired or not found. Please re-upload."})

    stored_insights = cache_data.get("clean_insights", {})
    api_key = cache_data.get("api_key", "")
    model_name = cache_data.get("model_name", "gemini-2.5-flash")
    dataset_profile = cache_data.get("dataset_profile")
    top_features = cache_data.get("top_features")

    report_data = generate_report(
        stored_insights, 
        api_key=api_key, 
        model_name=model_name, 
        dataset_profile=dataset_profile, 
        top_features=top_features.get("top_features") if isinstance(top_features, dict) else None
    )
    return jsonify(report_data)


@app.route("/report/download", methods=["POST"])
def report_download():
    """Download the business report as an HTML file."""
    session_id = session.get("session_id")
    if not session_id:
        return "No dataset loaded.", 400

    cache_data = load_cache(session_id)
    if not cache_data:
        return "Session data expired.", 400

    stored_insights = cache_data.get("clean_insights", {})
    api_key = cache_data.get("api_key", "")
    model_name = cache_data.get("model_name", "gemini-2.5-flash")
    dataset_profile = cache_data.get("dataset_profile")
    top_features = cache_data.get("top_features")

    report_data = generate_report(
        stored_insights, 
        api_key=api_key, 
        model_name=model_name,
        dataset_profile=dataset_profile,
        top_features=top_features.get("top_features") if isinstance(top_features, dict) else None
    )
    html_content = report_to_html(report_data)

    return Response(
        html_content,
        mimetype="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=insight_forge_report.html"
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
