import json
import llm_client


def summarize_csv_insights(insights_data, api_key="", model_name="gemini-2.5-flash", dataset_profile=None):
    """
    Reads insights data and generates a summary using the selected LLM.
    """
    try:
        # Converting JSON to a string so the model can read the raw data
        json_string = json.dumps({"insights": insights_data, "dataset_profile": dataset_profile or {}}, indent=2)
        
        prompt = f"""
        You are a Senior Data Consultant. Your goal is to scope a dataset for a team of Data Scientists and Business Analysts. 

Below is a JSON object containing statistical insights. Provide a high-end, executive-level report formatted in Markdown. 

Your report MUST be structured with the following headers to ensure the dashboard renders correctly:

### Executive Summary: [Dataset Name/Theme]
Provide a sophisticated 2-3 sentence overview. Don't say "The data has X rows." Instead, say "The dataset presents a robust volume of [X] records, indicating a high-frequency transactional pattern centered around [Region/Category]."

### Key Findings & Anomalies
Identify 3-4 specific high-level insights. 
- Use [Critical], [Warning], or [Observation] tags in the text.
- Focus on data quality risks (e.g., negative prices, skewed distributions, or high null counts in key ID columns).
- Explain WHY these matter for the upcoming analysis.

### Preliminary Trends & Observations
Describe the mathematical "story" of the data based on simple stats. Mention correlations or distribution patterns that an analyst should keep an eye on.

### Actionable Recommendations
Provide 3-5 specific steps the team should take BEFORE starting their deep analysis (e.g., "Implement a cleaning pipeline for the 'InvoiceDate' column to fix 12% inconsistency" or "Perform outlier capping on the 'UnitPrice' feature").

Tone: Professional, authoritative, and strategic. Avoid "AI-speak" like "I hope this helps." Go straight to the insights.
        
        Data Insights:
        {json_string}
        """

        response_text = llm_client.generate(prompt, api_key, model_name)
        
        if not response_text or len(response_text.strip()) < 10:
            return _generate_fallback_summary(insights_data, dataset_profile)
            
        return response_text

    except Exception as e:
        print(f"[insight_analysis] Error generating summary: {e}")
        return _generate_fallback_summary(insights_data, dataset_profile)


def _generate_fallback_summary(insights, profile):
    """Generates a high-quality metadata-based fallback summary when AI fails."""
    profile = profile or {}
    dtype = profile.get("dataset_type", "General Dataset")
    domain = profile.get("domain", "Unknown Domain")
    metrics = profile.get("key_metrics", {})
    rows = metrics.get("rows", 0)
    cols = metrics.get("columns", 0)
    missing = metrics.get("avg_missing_pct", 0)
    outliers = metrics.get("avg_outlier_pct", 0)
    health = insights.get("overall_health_score", 0)
    trust = insights.get("data_trust_level", "Moderate")
    risk_col = insights.get("primary_risk_column", "None")

    return f"""
### Executive Summary: {dtype} Analysis
The dataset presents a structured volume of {rows:,} records across {cols} distinct features, indicating a {domain}-focused data pattern. With an overall health score of **{health}/100**, the data is currently categorized as having **{trust} Trust Level** for strategic decision-making.

### Key Findings & Anomalies
- **[Critical] Data Integrity:** The dataset contains an average missing value rate of {missing}%, which may impact the precision of predictive models if not addressed via imputation.
- **[Warning] Outlier Presence:** Approximately {outliers}% of numeric values are flagged as statistical outliers, with **{risk_col}** identified as the primary risk feature requiring capping or transformation.
- **[Observation] Structural Profile:** The primary entities detected suggest a focus on {", ".join(profile.get("primary_entities", ["General Entities"]))}, providing a solid foundation for segmented analysis.

### Preliminary Trends & Observations
The mathematical profile suggests a high-cardinality distribution in categorical features, while numeric columns show moderate variance. Initial health checks indicate that the dataset is ready for basic scoping, though deep statistical modeling will require the cleaning steps outlined below.

### Actionable Recommendations
- **Standardize Null Values:** Implement a dedicated cleaning pipeline to handle the {missing}% missingness in key identifier columns.
- **Outlier Management:** Perform robust scaling or percentile-based capping on the **{risk_col}** feature to stabilize downstream variance.
- **Entity Validation:** Verify the consistency of {profile.get("primary_entities", ["primary"])[0]} records against source systems to ensure 100% referential integrity.
"""
