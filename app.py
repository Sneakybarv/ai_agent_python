
# if u wanna run the ui put this into ur terminal: streamlit run app.py

import os
import json
import re
from datetime import date

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from agent.tools import (
    load_user_profile,
    save_user_profile,
    UserProfile,
    DIABETES_TYPES,
    GENERAL_GOALS,
    # meals
    log_meal,
    get_today_totals,
    budget_status,
    get_meal_log_path,
)

from pathlib import Path
env_path = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=env_path, override=True)

st.set_page_config(page_title="Diabetes Nutrition Tracker", page_icon="🍽️", layout="wide")

def extract_json(text: str) -> dict:
    """Extract the first JSON object from model output."""
    if not text or not str(text).strip():
        raise ValueError("Empty model output.")
    text = str(text).strip()

    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return json.loads(m.group(1))

    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))

    return json.loads(text)


@st.cache_resource
def get_llm():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY. Put it in a .env file next to main.py / app.py.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        api_key=api_key,
    )


def estimate_macros_from_text(llm, desc: str) -> dict:
    prompt = f"""
You are a nutrition estimator.

Food: {desc}

Return ONLY valid JSON (no markdown, no commentary), exactly in this shape:
{{
  "item_name": "string",
  "nutrients": {{
    "carbs_g": number,
    "calories_kcal": number,
    "protein_g": number,
    "fat_g": number
  }}
}}
"""
    resp = llm.invoke([HumanMessage(content=prompt)])
    data = extract_json(resp.content)

    nutrients = data.get("nutrients", {}) or {}
    for k in ["carbs_g", "calories_kcal", "protein_g", "fat_g"]:
        try:
            nutrients[k] = float(nutrients.get(k, 0) or 0)
        except Exception:
            nutrients[k] = 0.0

    return {
        "item_name": data.get("item_name") or desc or "unknown",
        "nutrients": nutrients,
    }


def load_meals_df(user_id: str) -> pd.DataFrame:
    """Load all meals for this user from meal_log.json into a dataframe."""
    path = get_meal_log_path()
    if not os.path.exists(path):
        return pd.DataFrame(columns=["ts", "item_name", "source", "carbs_g", "calories_kcal", "protein_g", "fat_g"])

    try:
        with open(path, "r") as f:
            entries = json.load(f)
    except Exception:
        return pd.DataFrame(columns=["ts", "item_name", "source", "carbs_g", "calories_kcal", "protein_g", "fat_g"])

    rows = []
    for e in entries:
        if e.get("user_id") != user_id:
            continue
        n = e.get("nutrients", {}) or {}
        rows.append(
            {
                "ts": e.get("ts", ""),
                "item_name": e.get("item_name", ""),
                "source": e.get("source", "text"),
                "carbs_g": float(n.get("carbs_g", 0) or 0),
                "calories_kcal": float(n.get("calories_kcal", 0) or 0),
                "protein_g": float(n.get("protein_g", 0) or 0),
                "fat_g": float(n.get("fat_g", 0) or 0),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("ts", ascending=False)
    return df


def df_today_only(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    today = date.today().isoformat()
    return df[df["ts"].astype(str).str.startswith(today)]


# ui
st.title("🍽️ Diabetes Nutrition Tracker")
st.caption("Log meals + see daily carb budget progress (Gemini estimates).")

if "profile" not in st.session_state:
    st.session_state.profile = load_user_profile()

profile = st.session_state.profile

if profile is None:
    st.header("👤 Create your profile")

    with st.form("profile_form"):
        user_id = st.text_input("User ID", placeholder="e.g., rehan").strip()

        diabetes_type = st.selectbox("Diabetes type", list(DIABETES_TYPES.keys()), index=list(DIABETES_TYPES.keys()).index("None"))
        goals = st.multiselect("Goals", GENERAL_GOALS, default=["Weight loss"])

        carb_budget = st.number_input("Daily carb budget (grams)", min_value=0.0, value=28.0, step=1.0)

        submitted = st.form_submit_button("Save profile")

    if submitted:
        if not user_id:
            st.warning("Please enter a user ID.")
            st.stop()

        new_profile = UserProfile(
            user_id=user_id,
            diabetes_type={diabetes_type: {}},
            general_goals=goals,
            carb_budget=float(carb_budget),
        )

        save_user_profile(new_profile)
        st.session_state.profile = new_profile
        st.success("Profile saved! Reloading…")
        st.rerun()

    st.stop()

with st.sidebar:
    st.header("Profile")
    st.write(f"**User:** {profile.user_id}")
    st.write(f"**Carb budget:** {profile.carb_budget} g/day")
    st.write(f"**Goals:** {', '.join(profile.general_goals) if profile.general_goals else '—'}")
    st.divider()
    st.write("**Meal log file:**")
    st.code(get_meal_log_path())

llm = get_llm()

totals = get_today_totals(profile.user_id)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Carbs (g) today", f"{totals['carbs_g']:.1f}")
c2.metric("Calories today", f"{totals['calories_kcal']:.0f}")
c3.metric("Protein (g) today", f"{totals['protein_g']:.1f}")
c4.metric("Fat (g) today", f"{totals['fat_g']:.1f}")
st.info(budget_status(profile.carb_budget, totals))

st.divider()

st.subheader("Log a meal")
with st.form("log_form", clear_on_submit=True):
    food_text = st.text_input("Describe what you ate", placeholder="e.g., 1 banana, medium")
    submitted = st.form_submit_button("Estimate + Log")

if submitted:
    if not food_text.strip():
        st.warning("Type a food description first.")
    else:
        with st.spinner("Estimating macros..."):
            try:
                result = estimate_macros_from_text(llm, food_text.strip())
                log_meal(profile.user_id, result["item_name"], result["nutrients"], source="text")
                st.success(f"Logged: {result['item_name']}")
                st.json(result)
                st.rerun()
            except Exception as e:
                st.error(f"Could not log meal: {e}")

st.divider()

st.subheader("Meal history")
df_all = load_meals_df(profile.user_id)
df_today = df_today_only(df_all)

tab1, tab2 = st.tabs(["Today", "All time"])
with tab1:
    st.dataframe(df_today, use_container_width=True, hide_index=True)
with tab2:
    st.dataframe(df_all, use_container_width=True, hide_index=True)
