import json
import os
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any


DIABETES_TYPES = {
    "T1": {},
    "T2": {},
    "Prediabetes": {},
    "None": {}
}

GENERAL_GOALS = [
    "Avoid spikes",
    "Weight loss"
]

USER_DATA_FILE = "user_profile.json"


@dataclass
class UserProfile:
    user_id: str
    diabetes_type: Dict[str, Any]
    general_goals: List[str]
    carb_budget: float


def get_user_profile_path() -> str:
    """Get the path to the user profile JSON file."""
    return os.path.join(os.path.dirname(__file__), USER_DATA_FILE)


def save_user_profile(profile: UserProfile) -> None:
    """Save user profile to JSON file."""
    file_path = get_user_profile_path()
    with open(file_path, 'w') as f:
        json.dump(asdict(profile), f, indent=2)
    print(f"User profile saved to {file_path}")


def load_user_profile() -> Optional[UserProfile]:
    """Load user profile from JSON file. Returns None if file doesn't exist."""
    file_path = get_user_profile_path()
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    return UserProfile(**data)


def create_user_profile() -> UserProfile:
    """Create a new user profile by prompting the user for information."""
    print("\n=== Setting up your profile ===\n")
    
    user_id = input("Enter your user ID: ").strip()
    
    print(f"\nDiabetes types: {', '.join(DIABETES_TYPES.keys())}")
    diabetes_type_name = input("Select your diabetes type: ").strip()
    
    # Validate diabetes type
    if diabetes_type_name not in DIABETES_TYPES:
        print(f"Invalid diabetes type. Using 'None'")
        diabetes_type_name = "None"
    
    # Collect diabetes-specific information
    print(f"\n=== Enter information for {diabetes_type_name} ===")
    diabetes_info = {}
    
    if diabetes_type_name == "T1":
        diabetes_info["insulin_type"] = input("Insulin type (e.g., Humalog, Lantus): ").strip()
        diabetes_info["daily_injections"] = input("Number of daily injections: ").strip()
        diabetes_info["a1c"] = input("Current A1C level (optional): ").strip() or None
    
    elif diabetes_type_name == "T2":
        diabetes_info["medication"] = input("Current medication (e.g., Metformin, Januvia): ").strip()
        diabetes_info["a1c"] = input("Current A1C level (optional): ").strip() or None
        diabetes_info["comorbidities"] = input("Any comorbidities (optional): ").strip() or None
    
    elif diabetes_type_name == "Prediabetes":
        diabetes_info["fasting_glucose"] = input("Fasting glucose level (optional): ").strip() or None
        diabetes_info["a1c"] = input("A1C level (optional): ").strip() or None
        diabetes_info["risk_factors"] = input("Risk factors (optional): ").strip() or None
    
    # Initialize diabetes_type as a dictionary with the selected type and info
    diabetes_type = {diabetes_type_name: diabetes_info}
    
    print(f"\nAvailable goals: {', '.join(GENERAL_GOALS)}")
    goals_input = input("Select your goals (comma-separated): ").strip()
    general_goals = [g.strip() for g in goals_input.split(",")]
    
    carb_budget = float(input("Enter your daily carb budget (grams): ").strip())
    
    profile = UserProfile(
        user_id=user_id,
        diabetes_type=diabetes_type,
        general_goals=general_goals,
        carb_budget=carb_budget
    )
    
    save_user_profile(profile)
    return profile


def get_or_create_user_profile() -> UserProfile:
    """Load existing profile or create a new one."""
    profile = load_user_profile()
    if profile:
        print(f"Welcome back, {profile.user_id}!")
        return profile
    else:
        print("No existing profile found.")
        return create_user_profile()


def format_user_context(profile: UserProfile) -> str:
    """Format user profile as context string for the AI."""
    # Extract diabetes type name from dictionary
    diabetes_type_name = list(profile.diabetes_type.keys())[0] if profile.diabetes_type else "Unknown"
    diabetes_info = profile.diabetes_type.get(diabetes_type_name, {})
    
    # Build context string
    context = f"""
User Profile Information:
- User ID: {profile.user_id}
- Diabetes Type: {diabetes_type_name}
- Health Goals: {', '.join(profile.general_goals)}
- Daily Carb Budget: {profile.carb_budget}g
"""
    
    # Add diabetes-specific information if available
    if diabetes_info:
        context += f"- Diabetes Type Details: {json.dumps(diabetes_info, indent=2)}\n"
    
    context += "\nPlease refer to this information when providing advice and recommendations."
    
    return context





