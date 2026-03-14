"""
Natural Language Data Question Agent for Insight Forge.

Accepts user questions about the uploaded dataset and uses the
selected LLM to generate answers + optional chart data.
"""
import json
import llm_client


def ask_question(question: str, clean_insights: dict, api_key: str = "", model_name: str = "gemini-2.5-flash", dataset_profile: dict | None = None, columns: list | None = None, basic_stats: dict | None = None, column_classifications: dict | None = None, correlations: dict | None = None, total_rows: int | None = None, primary_risk_column: str | None = None, primary_risk_score: float | None = None, top_features: dict | None = None) -> dict:
    """
    Answer a natural language question about the dataset.

    Args:
        question: the user's question string
        clean_insights: the full insights dict from the analysis pipeline
        api_key: user's API key
        model_name: selected model identifier

    Returns:
        dict with:
          - answer: string with the AI-generated answer
          - chart: optional chart dict {type, title, labels, data} or None
    """
    if not question or not question.strip():
        return {"answer": "Please enter a question about your dataset.", "chart": None}

    # Build a reduced payload to stay within token limits
    reduced = {}
    for key in ("basic_overview", "column_types", "missing_overview",
                "simple_stats", "outliers", "overall_health_score",
                "data_trust_level", "primary_risk_column", "correlations"):
        if key in clean_insights:
            reduced[key] = clean_insights[key]
    
    if dataset_profile:
        reduced["dataset_profile"] = dataset_profile
    if column_classifications:
        reduced["column_classifications"] = column_classifications
    if basic_stats:
        reduced["basic_stats"] = basic_stats
    if correlations:
        reduced["top_correlations"] = correlations.get("strong_correlations", [])
    
    # Add new contextual intelligence fields
    if total_rows:
        reduced["total_rows_in_original_file"] = total_rows
    if primary_risk_column:
        reduced["primary_risk_column"] = primary_risk_column
    if primary_risk_score:
        reduced["primary_risk_score"] = primary_risk_score
    if top_features:
        reduced["top_features_importance"] = top_features.get("top_features", [])

    json_string = json.dumps(reduced, indent=2)

    prompt = f"""You are a senior data analyst answering questions based on structured dataset context. Do NOT invent values. Use the provided profile, column classifications, statistics, and correlations. You have access to metadata only, not raw rows.

Dataset Profile:
{json.dumps(reduced.get("dataset_profile", {}), indent=2)}

Total Rows in Original Dataset:
{reduced.get("total_rows_in_original_file", "Unknown")}

Column Types:
{json.dumps(reduced.get("column_classifications", {}), indent=2)}

Statistics:
{json.dumps(reduced.get("basic_stats", {}), indent=2)}

Top Correlations:
{json.dumps(reduced.get("top_correlations", []), indent=2)}

Key Drivers / Feature Importance:
{json.dumps(reduced.get("top_features_importance", []), indent=2)}

Primary Risk Column:
{reduced.get("primary_risk_column", "None")} (Score: {reduced.get("primary_risk_score", 0)})

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer the question specifically and concisely using the metadata provided.
2. If the metadata contains enough information to answer, give a data-backed response.
3. If the metadata doesn't contain enough info, clearly say "Based on the available metadata, I cannot determine..." and suggest what additional analysis would be needed.
4. If you can derive a useful visualization from your answer, include a "chart" object.
5. Keep your answer to 2-4 sentences maximum.

RESPONSE FORMAT — Return ONLY valid JSON, no markdown, no code fences:
{{
  "answer": "Your concise answer here...",
  "chart": null
}}

OR if a chart is useful:
{{
  "answer": "Your concise answer here...",
  "chart": {{
    "type": "bar",
    "title": "Chart Title",
    "labels": ["A", "B", "C"],
    "data": [10, 20, 30]
  }}
}}

Chart type must be one of: "bar", "pie", "doughnut", "line", "radar", "polarArea".
Respond with ONLY the JSON object.
"""

    try:
        raw_text = llm_client.generate(prompt, api_key, model_name, json_mode=True)

        if not raw_text:
            return {
                "answer": "The AI service is temporarily unavailable. Please try again in a moment.",
                "chart": None
            }

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

        result = json.loads(cleaned)

        # Validate
        answer = str(result.get("answer", "No answer generated."))
        chart = result.get("chart", None)

        if chart is not None:
            valid_types = {"bar", "pie", "doughnut", "line", "radar", "polarArea"}
            if (not isinstance(chart, dict)
                    or chart.get("type") not in valid_types
                    or not isinstance(chart.get("labels"), list)
                    or not isinstance(chart.get("data"), list)
                    or len(chart["labels"]) == 0
                    or len(chart["data"]) == 0):
                chart = None
            else:
                min_len = min(len(chart["labels"]), len(chart["data"]))
                chart["labels"] = [str(l) for l in chart["labels"][:min_len]]
                chart["data"] = [float(d) if d is not None else 0.0 for d in chart["data"][:min_len]]
                chart["title"] = str(chart.get("title", "Chart"))
                chart["type"] = str(chart["type"])

        return {"answer": answer, "chart": chart}

    except json.JSONDecodeError:
        # If LLM returned non-JSON, use raw text as the answer
        if raw_text:
            return {"answer": raw_text[:500], "chart": None}
        return {"answer": "Could not parse the AI response. Please rephrase your question.", "chart": None}
    except Exception as e:
        print(f"[query_agent] Error: {e}")
        return {
            "answer": f"An error occurred while processing your question. Please try again.",
            "chart": None
        }
