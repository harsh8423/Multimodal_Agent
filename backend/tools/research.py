import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

################################ PERPLEXITY SEARCH #################################

def search_with_perplexity_sonar(
    search_description: str,
    user_prompt: str,
    model: str = "sonar-pro",
    api_key: str = None
):
    """
    Perform web search + answer synthesis using Perplexity's Sonar Pro model.

    Parameters:
        search_description (str): instruction / context to guide the search (system message)
        user_prompt (str): the actual user query
        model (str): which model to use; default "sonar-pro"
        api_key (str): your Perplexity API key (optional, will use env var if not provided)

    Returns:
        dict: parsed response, including answer, citations, search_results etc.
    """
    if api_key is None:
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("Perplexity API key not provided and PERPLEXITY_API_KEY environment variable not set")

    url = "https://api.perplexity.ai/chat/completions"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    messages = []
    # system message with the description
    if search_description:
        messages.append({"role": "system", "content": search_description})
    # user message
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": model,
        "messages": messages,
    }


    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

    resp_json = response.json()

    # You might get fields like "search_results", "citations", etc.
    # Let's parse and return them.
    result = {
        "answer": resp_json.get("choices", [])[0].get("message", {}).get("content") if resp_json.get("choices") else None,
        "search_results": resp_json.get("search_results"),
        "citations": resp_json.get("citations"),
        "raw_response": resp_json
    }

    return result


########################################### GROUNDING WITH GOOGLE SEARCH #######################################


import requests

def gemini_google_search(search_description: str, model: str = "gemini-2.5-pro", api_key: str = None):
    """
    Perform grounded search using Gemini 2.5 Pro with Google Search tool enabled.

    Parameters:
        search_description (str): The query or description to send
        model (str): Model to use (default: gemini-2.5-pro)
        api_key (str): Your Google API key (optional, will use env var if not provided)

    Returns:
        dict: Parsed response including grounded answer
    """
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not provided and GEMINI_API_KEY environment variable not set")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": search_description}
                ]
            }
        ],
        "tools": [
            {"google_search": {}}
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
 
    if response.status_code != 200:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

    data = response.json()

    # Extract main text response (if present)
    text_response = None
    try:
        text_response = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        text_response = None

    return {
        "answer": text_response,
        "raw_response": data
    }


