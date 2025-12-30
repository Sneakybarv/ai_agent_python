import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from .tools import (
    get_or_create_user_profile, 
    format_user_context,
    get_carb_budget_remaining,
    suggest_low_gi_foods,
    get_diabetes_tips,
    get_average_glucose
)

load_dotenv()

# Initialize LLM with error handling
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        api_key=api_key
    )
except Exception as e:
    print(f"✗ Error initializing LLM: {e}")
    raise


def run_agent():
    """Run the main AI health assistant agent."""
    try:
        # Load or create user profile
        user_profile = get_or_create_user_profile()
        user_context = format_user_context(user_profile)
        
        # Extract diabetes type for personalized tips
        diabetes_type_name = list(user_profile.diabetes_type.keys())[0]
        diabetes_tips = "\n".join([f"  • {tip}" for tip in get_diabetes_tips(diabetes_type_name)])
        
        # Enhanced system prompt with comprehensive health guidance
        system_prompt = f"""You are a knowledgeable and compassionate AI health and nutrition assistant specializing in diabetes management.

{user_context}

DIABETES MANAGEMENT TIPS FOR {diabetes_type_name}:
{diabetes_tips}

LOW GLYCEMIC INDEX FOODS TO SUGGEST:
{', '.join(suggest_low_gi_foods())}

WHEN RESPONDING:
- Always personalize advice based on their diabetes type and profile
- Provide evidence-based nutrition recommendations
- Help with carb counting and meal planning
- Be supportive and encouraging
- Remind them to consult healthcare providers for medical decisions
- Ask clarifying questions when needed"""

        # Store conversation history
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        
        print("=" * 60)
        print("🏥 Gemini AI Health Assistant")
        print("=" * 60)
        print(f"Welcome, {user_profile.user_id}!")
        print(f"Daily carb budget: {user_profile.carb_budget}g")
        carb_remaining = get_carb_budget_remaining(user_profile)
        print(f"Carbs remaining today: {carb_remaining}g")
        print("\nType 'exit' to quit | 'profile' to view profile | 'tips' for health tips")
        print("=" * 60 + "\n")

        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() == "exit":
                    print("\n✓ Goodbye! Stay healthy!\n")
                    break
                
                if user_input.lower() == "profile":
                    print(user_context)
                    continue
                
                if user_input.lower() == "tips":
                    print("\n📋 Health Tips for your diabetes type:")
                    for tip in get_diabetes_tips(diabetes_type_name):
                        print(f"  • {tip}")
                    print()
                    continue
                
                # Add user message to history
                messages.append(HumanMessage(content=user_input))
                
                # Get response from LLM with error handling
                response = llm.invoke(messages)
                response_text = response.content
                
                # Add assistant response to history
                messages.append(response)
                
                print(f"\nAssistant: {response_text}\n")
                
            except KeyboardInterrupt:
                print("\n\n✓ Session ended by user")
                break
            except Exception as e:
                print(f"\n⚠️ Error processing message: {e}")
                print("Please try again or type 'exit' to quit.\n")
    
    except Exception as e:
        print(f"✗ Fatal error in agent: {e}")
        raise