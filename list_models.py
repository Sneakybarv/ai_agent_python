import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# List available models
models = client.models.list()

print("Available models for this account:")
for m in models:
    print("-", m.name)
    