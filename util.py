import os
import json
import requests

def _call_google_search_api(query: str, num_results: int = 5) -> dict:
    """
    Perform a Google Custom Search and return structured results.
    Requires:
      - GOOGLE_API_KEY (from https://console.cloud.google.com/apis/credentials)
      - GOOGLE_CSE_ID (Custom Search Engine ID)
    """
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        raise ValueError("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID in environment variables")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": min(num_results, 10),  # Google allows up to 10 results per request
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "title": item.get("title"),
            "url": item.get("link"),
            "snippet": item.get("snippet"),
        })

    return {
        "query": query,
        "results": results,
    }


def _call_tavily_search_api(query: str, num_results: int = 5) -> dict:
    """
    Free web search using Tavily API.
    """
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    if not TAVILY_API_KEY:
        raise ValueError("Missing TAVILY_API_KEY in environment variables")

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "num_results": num_results,
        "include_answer": True,
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()

    # Format response
    return {
        "query": query,
        "summary": data.get("answer"),
        "results": [
            {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content")}
            for r in data.get("results", [])
        ],
    }

