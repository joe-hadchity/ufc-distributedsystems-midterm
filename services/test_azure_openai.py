import requests
import os

# Azure OpenAI configuration
endpoint = "https://demoopenai2025.openai.azure.com/"
deployment = "o4-mini"
api_key = "sk-your-real-key-here"

url = f"{endpoint}openai/deployments/{deployment}/chat/completions?api-version=2024-12-01-preview"
headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

# Fixed: temperature must be 1 (default) for o4-mini
data = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one short sentence."}
    ],
    "temperature": 1
}

try:
    r = requests.post(url, headers=headers, json=data, timeout=30)
    r.raise_for_status()
    print("✅ Connection successful!")
    print("Response:\n", r.json()["choices"][0]["message"]["content"])
except Exception as e:
    print("❌ Connection failed:", e)
    if 'r' in locals():
        print("Status code:", r.status_code, "\nResponse:", r.text)
