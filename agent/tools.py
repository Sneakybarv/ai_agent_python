import json
import os
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from datetime import datetime


DIABETES_TYPES = {
    "T1": {},
    "T2": {},
    "Prediabetes": {},
    "None": {}
}

GENERAL_GOALS = [
    "Avoid spikes",
    "Weight loss",
    "Improve A1C",
    "Energy management"
]

USER_DATA_FILE = "user_profile.json"
MEAL_LOG_FILE = "meal_log.json"
BLOOD_SUGAR_LOG_FILE = "blood_sugar_log.json"

# Common foods with carb counts (grams per serving)
COMMON_FOODS = {
    "apple": {"carbs": 25, "portion": "1 medium"},
    "banana": {"carbs": 27, "portion": "1 medium"},
    "bread": {"carbs": 15, "portion": "1 slice"},
    "rice": {"carbs": 45, "portion": "1 cup cooked"},
    "potato": {"carbs": 37, "portion": "1 medium baked"},
    "broccoli": {"carbs": 7, "portion": "1 cup"},
    "chicken": {"carbs": 0, "portion": "100g"},
    "egg": {"carbs": 1, "portion": "1 large"},
    "milk": {"carbs": 12, "portion": "1 cup"},
    "yogurt": {"carbs": 20, "portion": "1 cup"},
    "oats": {"carbs": 54, "portion": "1 cup cooked"},
    "pasta": {"carbs": 43, "portion": "1 cup cooked"},
}


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
    try:
        if not profile.user_id or not profile.user_id.strip():
            raise ValueError("User ID cannot be empty")
        if profile.carb_budget <= 0:
            raise ValueError("Carb budget must be positive")
        
        file_path = get_user_profile_path()
        with open(file_path, 'w') as f:
            json.dump(asdict(profile), f, indent=2)
        print(f"✓ User profile saved successfully")
    except (ValueError, IOError, OSError) as e:
        print(f"✗ Error saving user profile: {e}")
        raise


def load_user_profile() -> Optional[UserProfile]:
    """Load user profile from JSON file. Returns None if file doesn't exist."""
    try:
        file_path = get_user_profile_path()
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        return UserProfile(**data)
    except (json.JSONDecodeError, KeyError, IOError, OSError) as e:
        print(f"✗ Error loading user profile: {e}")
        return None


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


# ====== Carb Counting Tools ======
def get_food_carbs(food_name: str) -> Optional[Dict[str, Any]]:
    """Look up carbs for a common food. Returns None if food not found."""
    food_key = food_name.lower().strip()
    if food_key in COMMON_FOODS:
        return COMMON_FOODS[food_key]
    return None


def calculate_meal_carbs(foods: List[Dict[str, float]]) -> float:
    """Calculate total carbs for a meal.
    
    Args:
        foods: List of dicts with 'name' and 'servings' keys
    
    Returns:
        Total carbs in the meal
    """
    total_carbs = 0.0
    for food in foods:
        if 'name' in food and 'servings' in food:
            food_info = get_food_carbs(str(food['name']))
            if food_info:
                total_carbs += food_info['carbs'] * food['servings']
    return round(total_carbs, 1)


# ====== Meal Logging Tools ======
@dataclass
class MealEntry:
    timestamp: str
    meal_type: str  # breakfast, lunch, dinner, snack
    foods: List[str]
    total_carbs: float
    notes: str = ""


def log_meal(meal: MealEntry) -> bool:
    """Log a meal to the meal history."""
    try:
        file_path = os.path.join(os.path.dirname(__file__), MEAL_LOG_FILE)
        meals = []
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                meals = json.load(f)
        
        meals.append(asdict(meal))
        
        with open(file_path, 'w') as f:
            json.dump(meals, f, indent=2)
        
        return True
    except (IOError, OSError, ValueError) as e:
        print(f"✗ Error logging meal: {e}")
        return False


def get_meal_history(days: int = 7) -> List[MealEntry]:
    """Get meal history for the last N days."""
    try:
        file_path = os.path.join(os.path.dirname(__file__), MEAL_LOG_FILE)
        
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r') as f:
            meals = json.load(f)
        
        return [MealEntry(**m) for m in meals[-days*3:]]  # Approximate 3 meals/day
    except (json.JSONDecodeError, IOError, OSError, TypeError) as e:
        print(f"✗ Error retrieving meal history: {e}")
        return []


def get_daily_carbs_total(target_date: Optional[str] = None) -> float:
    """Calculate total carbs consumed on a specific date (default: today)."""
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    
    meals = get_meal_history(days=30)
    total = 0.0
    
    for meal in meals:
        if meal.timestamp.startswith(target_date):
            total += meal.total_carbs
    
    return round(total, 1)


# ====== Blood Sugar Logging Tools ======
@dataclass
class BloodSugarEntry:
    timestamp: str
    glucose_level: float  # mg/dL
    meal_type: Optional[str] = None
    notes: str = ""


def log_blood_sugar(entry: BloodSugarEntry) -> bool:
    """Log blood sugar reading."""
    try:
        if entry.glucose_level <= 0:
            raise ValueError("Glucose level must be positive")
        
        file_path = os.path.join(os.path.dirname(__file__), BLOOD_SUGAR_LOG_FILE)
        readings = []
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                readings = json.load(f)
        
        readings.append(asdict(entry))
        
        with open(file_path, 'w') as f:
            json.dump(readings, f, indent=2)
        
        return True
    except (IOError, OSError, ValueError) as e:
        print(f"✗ Error logging blood sugar: {e}")
        return False


def get_blood_sugar_history(days: int = 30) -> List[BloodSugarEntry]:
    """Get blood sugar readings for the last N days."""
    try:
        file_path = os.path.join(os.path.dirname(__file__), BLOOD_SUGAR_LOG_FILE)
        
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r') as f:
            readings = json.load(f)
        
        return [BloodSugarEntry(**r) for r in readings[-(days*4):]]  # Approximate 4 readings/day
    except (json.JSONDecodeError, IOError, OSError, TypeError) as e:
        print(f"✗ Error retrieving blood sugar history: {e}")
        return []


def get_average_glucose(days: int = 30) -> Optional[float]:
    """Calculate average glucose level for the last N days."""
    readings = get_blood_sugar_history(days=days)
    
    if not readings:
        return None
    
    average = sum(r.glucose_level for r in readings) / len(readings)
    return round(average, 1)


# ====== Recommendation Tools ======
def get_carb_budget_remaining(profile: UserProfile) -> float:
    """Calculate remaining carb budget for today."""
    daily_total = get_daily_carbs_total()
    remaining = profile.carb_budget - daily_total
    return max(0, round(remaining, 1))


def suggest_low_gi_foods() -> List[str]:
    """Suggest low glycemic index foods."""
    return [
        "Leafy greens (spinach, kale)",
        "Broccoli and cauliflower",
        "Berries (blueberries, strawberries)",
        "Nuts and seeds",
        "Greek yogurt",
        "Lentils and beans",
        "Whole grain oats",
        "Sweet potatoes"
    ]


def get_diabetes_tips(diabetes_type: str) -> List[str]:
    """Get diabetes-specific health tips."""
    tips = {
        "T1": [
            "Monitor insulin timing carefully",
            "Count carbs accurately for dosing",
            "Check for hypoglycemia symptoms",
            "Stay hydrated throughout the day",
            "Regular blood sugar monitoring",
            "Carry fast-acting carbs with you"
        ],
        "T2": [
            "Focus on portion control",
            "Increase physical activity gradually",
            "Monitor medication timing",
            "Limit processed foods",
            "Track weight regularly",
            "Manage stress levels"
        ],
        "Prediabetes": [
            "Make lifestyle changes early",
            "Aim for 150+ minutes weekly exercise",
            "Reduce refined carbohydrates",
            "Lose 5-10% of body weight if overweight",
            "Monitor blood sugar regularly",
            "Consider preventive screening"
        ]
    }
    return tips.get(diabetes_type, ["Consult your healthcare provider for personalized advice"])





