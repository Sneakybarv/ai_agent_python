import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from .tools import get_or_create_user_profile, format_user_context

load_dotenv()


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    api_key=os.getenv("GEMINI_API_KEY")
)


def run_agent():
    # Load or create user profile
    user_profile = get_or_create_user_profile()
    user_context = format_user_context(user_profile)
    
    # Create system prompt with user context
    system_prompt = f"""You are a helpful AI health and nutrition assistant.

{user_context}

Use this information to provide personalized recommendations. Be conversational and helpful."""

    # Store conversation history
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    
    print("Gemini AI Agent (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        try:
            # Add user message to history
            messages.append(HumanMessage(content=user_input))
            
            # Get response from LLM
            response = llm.invoke(messages)
            response_text = response.content
            
            # Add assistant response to history
            messages.append(response)
            
            print("Agent:", response_text)
        except Exception as e:
            print("⚠️ Error:", e)