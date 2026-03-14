import json
import main
import ai_chart_planner
import pandas as pd

try:
    print("Loading dataset...")
    df = pd.read_csv('big_student_dataset.csv')
    df_sample = df.dropna(subset=df.columns[df.isnull().sum() < len(df)*0.5]).sample(n=min(len(df), 2000), random_state=42)
    
    print("Generating profiles...")
    dataset_profile = main.generate_dataset_profile(df)
    
    clean_insights = {
        "basic_overview": main.basic_overview(df),
        "column_types": main.column_types(df),
        "missing_overview": main.missing_overview(df),
        "health_checks": main.healthy(df),
        "simple_stats": main.simple_stats(df_sample),
        "outliers": main.detect_outliers(df_sample),
        "dataset_profile": dataset_profile
    }
    
    clean_insights["overall_health_score"] = main.overall_dataset_health(
        clean_insights["basic_overview"], 
        clean_insights["missing_overview"], 
        clean_insights["health_checks"], 
        clean_insights["outliers"]
    )
    
    # We must mock api_key. Since user has a valid one, I will use a placeholder 
    # but the API call will fail if I don't provide a real one.
    # We'll just run it and see if the LLM client throws.
    # WAIT! Since I don't have the user's API key, I CANNOT run Gemini. 
    # Only the user can run Gemini.
    print("Test script ready. Waiting for user's trigger.")
except Exception as e:
    import traceback
    traceback.print_exc()
