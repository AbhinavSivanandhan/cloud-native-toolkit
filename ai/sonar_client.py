# File: ai/sonar_client.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Loads .env from project root

SONAR_API_KEY = os.getenv("SONAR_API_KEY")
SONAR_ENDPOINT = "https://api.perplexity.ai/chat/completions"
SONAR_MODEL = "sonar-pro"

def ask_sonar(prompt, system_prompt="You are a concise, trusted cloud governance assistant."):
    if not SONAR_API_KEY:
        raise EnvironmentError("Missing SONAR_API_KEY in environment variables")

    headers = {
        "Authorization": f"Bearer {SONAR_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "model": SONAR_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post(SONAR_ENDPOINT, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"[Sonar API Error] {str(e)}"
