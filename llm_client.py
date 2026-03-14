"""
Unified LLM Client for Insight Forge.

Provides a single `generate()` function that routes to the correct
provider (Google Gemini or OpenAI) based on the model name.
Includes retry logic with exponential backoff.
"""
import time

# ── Supported Models ────────────────────────────────────────────────────────
# Only models capable of structured JSON generation / long reports

AVAILABLE_MODELS = {
    "gemini": {
        "provider": "Google Gemini",
        "models": [
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "desc": "Fastest, best value"},
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "desc": "Most capable"},
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "desc": "Fast & efficient"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "desc": "1M context window"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "desc": "Light & fast"},
        ]
    },
    "openai": {
        "provider": "OpenAI",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "desc": "Flagship multimodal"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "desc": "Fast & affordable"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "desc": "128K context"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "desc": "Legacy fast model"},
        ]
    }
}


def get_provider(model_name: str) -> str:
    """Detect provider from model name."""
    if model_name.startswith("gemini"):
        return "gemini"
    elif model_name.startswith("gpt"):
        return "openai"
    else:
        return "unknown"


def generate(prompt: str, api_key: str, model_name: str, max_retries: int = 3, json_mode: bool = False) -> str:
    """
    Generate text using the specified model and provider.

    Args:
        prompt: the text prompt
        api_key: user's API key
        model_name: model identifier (e.g. 'gemini-2.5-flash', 'gpt-4o')
        max_retries: number of retries on transient errors
        json_mode: enforce JSON output mode

    Returns:
        The raw text response from the LLM.

    Raises:
        Exception if all retries fail.
    """
    provider = get_provider(model_name)

    if provider == "gemini":
        return _call_gemini(prompt, api_key, model_name, max_retries, json_mode)
    elif provider == "openai":
        return _call_openai(prompt, api_key, model_name, max_retries, json_mode)
    else:
        raise ValueError(f"Unsupported model: {model_name}")


def _call_gemini(prompt: str, api_key: str, model_name: str, max_retries: int, json_mode: bool = False) -> str:
    """Call Google Gemini API."""
    from google import genai
    import re

    client = genai.Client(api_key=api_key)

    for attempt in range(max_retries):
        try:
            config = genai.types.GenerateContentConfig(response_mime_type="application/json") if json_mode else None
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )

            # Extract text — handle candidates/parts structure
            raw_text = ""
            try:
                # Try the simple .text accessor first
                if hasattr(response, 'text') and response.text:
                    raw_text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        raw_text += part.text
            except Exception:
                pass

            # Strip <think>...</think> blocks from thinking models
            if raw_text:
                raw_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()

            if not raw_text:
                print(f"[llm_client] Gemini returned empty response on attempt {attempt+1}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1))
                    continue
                return ""

            return raw_text

        except Exception as e:
            err_str = str(e)
            # Handle 429 RESOURCE_EXHAUSTED specifically
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                if attempt < max_retries - 1:
                    wait = (2 ** (attempt + 1)) + 2  # Add jitter
                    print(f"[llm_client] Rate limit hit ({err_str[:50]}...), retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                else:
                    print(f"[llm_client] Rate limit exhausted after {max_retries} attempts.")
                    return "" # Return empty string to trigger fallback instead of crashing
            
            if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"[llm_client] Gemini error ({err_str[:80]}), retrying in {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            
            print(f"[llm_client] Non-retriable error: {err_str}")
            return "" # Return empty string on other errors to trigger fallback

    return ""


def _call_openai(prompt: str, api_key: str, model_name: str, max_retries: int, json_mode: bool = False) -> str:
    """Call OpenAI API."""
    try:
        from openai import OpenAI
    except ImportError:
        print("[llm_client] OpenAI package not installed.")
        return ""

    client = OpenAI(api_key=api_key)

    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a senior data analyst. Return only the requested format."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            if json_mode:
                if model_name in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]:
                    kwargs["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            err_str = str(e)
            if ("503" in err_str or "429" in err_str or "overloaded" in err_str.lower()) and attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"[llm_client] OpenAI error, retrying in {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                print(f"[llm_client] OpenAI non-retriable error: {err_str}")
                return ""
    return ""
