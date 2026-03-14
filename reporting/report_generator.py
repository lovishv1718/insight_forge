"""
Auto Business Report Generator for Insight Forge.

Generates a structured 5-section business intelligence report
using existing analysis metrics + selected LLM for narrative generation.
"""
import json
import datetime
import llm_client


def generate_report(clean_insights: dict, api_key: str = "", model_name: str = "gemini-2.5-flash", dataset_profile: dict | None = None, top_features: list | None = None) -> dict:
    """
    Generate a structured 5-section business intelligence report.

    Args:
        clean_insights: the full insights dict from the analysis pipeline
        api_key: user's API key
        model_name: selected model identifier

    Returns:
        dict with:
          - title: report title
          - generated_at: timestamp
          - sections: list of {id, title, icon, content (HTML)}
    """
    # Build reduced payload
    reduced = {}
    for key in ("basic_overview", "column_types", "missing_overview",
                "simple_stats", "outliers", "overall_health_score",
                "data_trust_level", "primary_risk_column", "primary_risk_score",
                "health_checks", "correlations"):
        if key in clean_insights:
            reduced[key] = clean_insights[key]
    if dataset_profile:
        reduced["dataset_profile"] = dataset_profile
    if top_features:
        reduced["top_features"] = top_features

    json_string = json.dumps(reduced, indent=2)

    prompt = f"""You are a senior business intelligence consultant generating a formal analytics report for a C-level audience.

Based on the dataset metadata below, generate a comprehensive report with EXACTLY 5 sections.

DATASET METADATA:
{json_string}

REPORT SECTIONS (generate ALL 5):

1. **Executive Summary** — 3-4 sentences. High-level overview of what this dataset represents, its scale, and its primary business value. Sound authoritative.

2. **Key Metrics** — Present 5-8 critical metrics in a bullet-point format. Each metric should have a label and value. Examples: Total Records, Columns, Health Score, Missing Data Rate, Outlier Exposure, Primary Risk Column, etc. Use the actual numbers from the metadata.

3. **Important Insights** — 4-6 bullet points describing the most significant findings from the data. Focus on patterns, anomalies, distribution characteristics, and correlation signals. Each insight should explain WHY it matters for business decisions.

4. **Data Quality Assessment** — Evaluate data quality across 4 dimensions: Completeness (missing data), Consistency (type mismatches), Reliability (outlier presence), and Usability (overall health score). Rate each as Good/Fair/Poor with 1-sentence justification.

5. **Recommended Actions** — 4-6 specific, actionable recommendations the team should implement before using this data for analysis or modeling. Be concrete (e.g., "Impute missing CustomerID values using lookup tables" not "Fix missing data").

RESPONSE FORMAT — Return ONLY valid JSON, no markdown, no code fences:
{{
  "title": "Business Intelligence Report: [Dataset Name/Theme]",
  "sections": [
    {{
      "id": "executive-summary",
      "title": "Executive Summary",
      "icon": "file-text",
      "content": "<p>Your HTML content here. Use <strong>, <ul>, <li>, <br/> for formatting.</p>"
    }},
    {{
      "id": "key-metrics",
      "title": "Key Metrics",
      "icon": "bar-chart-2",
      "content": "<ul><li><strong>Total Records:</strong> 541,909</li>...</ul>"
    }},
    {{
      "id": "important-insights",
      "title": "Important Insights",
      "icon": "lightbulb",
      "content": "<ul><li>...</li></ul>"
    }},
    {{
      "id": "quality-assessment",
      "title": "Data Quality Assessment",
      "icon": "shield-check",
      "content": "<ul><li><strong>Completeness:</strong> Good — ...</li>...</ul>"
    }},
    {{
      "id": "recommended-actions",
      "title": "Recommended Actions",
      "icon": "target",
      "content": "<ol><li>...</li></ol>"
    }}
  ]
}}

IMPORTANT: Content must be valid HTML (not markdown). Use <strong>, <em>, <ul>, <ol>, <li>, <p>, <br/> tags.
Respond with ONLY the JSON object.
"""

    try:
        raw_text = llm_client.generate(prompt, api_key, model_name, json_mode=True)

        if not raw_text:
            return _fallback_report(clean_insights)

        cleaned = raw_text.strip()
        
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].startswith("```"): lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace + 1]

        result = json.loads(cleaned)

        if not isinstance(result, dict) or "sections" not in result:
            return _fallback_report(clean_insights)

        report = {
            "title": str(result.get("title", "Business Intelligence Report")),
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sections": []
        }

        for section in result.get("sections", []):
            if isinstance(section, dict):
                report["sections"].append({
                    "id": str(section.get("id", "")),
                    "title": str(section.get("title", "")),
                    "icon": str(section.get("icon", "file-text")),
                    "content": str(section.get("content", ""))
                })

        if len(report["sections"]) == 0:
            return _fallback_report(clean_insights)

        return report

    except Exception as e:
        print(f"[report_generator] Error: {e}")
        return _fallback_report(clean_insights)


def _fallback_report(clean_insights: dict) -> dict:
    """Generate a basic report from raw metrics when LLM is unavailable."""
    overview = clean_insights.get("basic_overview", {})
    health = clean_insights.get("overall_health_score", "N/A")
    trust = clean_insights.get("data_trust_level", "N/A")
    missing = clean_insights.get("missing_overview", {})
    risk_col = clean_insights.get("primary_risk_column", "N/A")
    risk_score = clean_insights.get("primary_risk_score", "N/A")

    return {
        "title": "Business Intelligence Report",
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sections": [
            {
                "id": "executive-summary",
                "title": "Executive Summary",
                "icon": "file-text",
                "content": f"<p>This dataset contains <strong>{overview.get('rows', 'N/A')}</strong> records across <strong>{overview.get('columns', 'N/A')}</strong> columns. The overall health score is <strong>{health}%</strong> with a data trust level of <strong>{trust}</strong>.</p>"
            },
            {
                "id": "key-metrics",
                "title": "Key Metrics",
                "icon": "bar-chart-2",
                "content": f"<ul><li><strong>Total Records:</strong> {overview.get('rows', 'N/A')}</li><li><strong>Total Columns:</strong> {overview.get('columns', 'N/A')}</li><li><strong>Health Score:</strong> {health}%</li><li><strong>Trust Level:</strong> {trust}</li><li><strong>Missing Data:</strong> {missing.get('missing_percentage', 'N/A')}%</li><li><strong>Primary Risk:</strong> {risk_col} ({risk_score})</li></ul>"
            },
            {
                "id": "important-insights",
                "title": "Important Insights",
                "icon": "lightbulb",
                "content": "<p><em>AI narrative generation is temporarily unavailable. Please retry later for detailed insights.</em></p>"
            },
            {
                "id": "quality-assessment",
                "title": "Data Quality Assessment",
                "icon": "shield-check",
                "content": f"<p>Overall health score: <strong>{health}%</strong>. Trust level: <strong>{trust}</strong>.</p>"
            },
            {
                "id": "recommended-actions",
                "title": "Recommended Actions",
                "icon": "target",
                "content": "<p><em>AI recommendations are temporarily unavailable. Please retry later.</em></p>"
            }
        ]
    }


def report_to_html(report: dict) -> str:
    """Convert a report dict to a standalone HTML page for PDF generation."""
    sections_html = ""
    for section in report.get("sections", []):
        sections_html += f"""
        <div style="margin-bottom: 32px; page-break-inside: avoid;">
            <h2 style="color: #2dd4bf; font-size: 20px; font-weight: 800; margin-bottom: 12px; border-bottom: 2px solid #1e293b; padding-bottom: 8px;">
                {section.get('title', '')}
            </h2>
            <div style="color: #cbd5e1; font-size: 14px; line-height: 1.8;">
                {section.get('content', '')}
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report.get('title', 'Report')}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            background: #020617;
            color: #f1f5f9;
            max-width: 800px;
            margin: 0 auto;
            padding: 48px 32px;
        }}
        h1 {{
            font-size: 28px;
            font-weight: 900;
            color: #ffffff;
            margin-bottom: 8px;
        }}
        .meta {{
            color: #64748b;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 40px;
        }}
        strong {{ color: #2dd4bf; }}
        ul, ol {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; }}
    </style>
</head>
<body>
    <h1>{report.get('title', 'Business Intelligence Report')}</h1>
    <p class="meta">Generated: {report.get('generated_at', '')} &bull; Insight Forge Analytics</p>
    {sections_html}
</body>
</html>"""
