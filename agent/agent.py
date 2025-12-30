import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def run_agent():
    print("Gemini AI Agent (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=user_input
            )
            print("Agent:", response.text)

        except Exception as e:
            print("⚠️ Error:", e)
            
            
            
            