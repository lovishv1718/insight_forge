import json
import os
import sys

# add path
sys.path.append('c:/Users/MSI/OneDrive/Desktop/insight_forge_traeai')

from ai_chart_planner import generate_chart_plan

def test_cache():
    cache_dir = 'c:/Users/MSI/OneDrive/Desktop/insight_forge_traeai/cache'
    files = sorted(os.listdir(cache_dir), key=lambda x: os.path.getmtime(os.path.join(cache_dir, x)), reverse=True)
    if not files:
        print("No cache files")
        return

    latest = os.path.join(cache_dir, files[0])
    print(f"Loading {latest}...")
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)

    insights = data.get('clean_insights', {})
    params = {
        'clean_insights': insights,
        'api_key': data.get('api_key', ''),
        'model_name': data.get('model_name', 'gemini-2.5-flash'),
        'dataset_profile': data.get('dataset_profile')
    }

    print(f"Calling generate_chart_plan with model {params['model_name']}...")
    result = generate_chart_plan(**params)
    print("FINISHED")
    print(json.dumps(result, indent=2)[:500])

if __name__ == '__main__':
    test_cache()
