import requests
import json
import traceback

try:
    url = 'http://127.0.0.1:5000/analyze'
    files = {'datafile': open('big_student_dataset.csv', 'rb')}
    data = {'model_name': 'gemini-2.5-flash', 'api_key': ''}

    print("Sending request...")
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    
    # We are expecting HTML back, let's see if the ai_charts_json is actually carrying a fallback.
    html_content = response.text
    
    # Extract the payload to see what AI generated
    import re
    match = re.search(r'id="ai-charts-json-data"[^>]*>(.*?)</script>', html_content, re.DOTALL)
    if match:
        json_data = match.group(1).strip()
        print("Successfully found AI Charts JSON in HTML.")
        try:
            charts = json.loads(json_data)
            print(f"Number of AI Charts generated: {len(charts)}")
            if len(charts) > 0:
                print(f"Initial Chart Title: {charts[0].get('title', 'Unknown')}")
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error extracting from HTML: {e}")
            print(f"Raw Snippet (first 500 chars): {json_data[:500]}")
    else:
        print("Could not find ai-charts-json-data block in the returned HTML.")
        
except Exception as e:
    print(f"Fatal error:")
    traceback.print_exc()
