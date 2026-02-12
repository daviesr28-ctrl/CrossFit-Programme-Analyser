import streamlit as st
import pandas as pd
import re
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect('programming_history.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS wods 
             (date TEXT, descriptor TEXT, modality TEXT, load TEXT, time_domain TEXT, 
              reps_category TEXT, scheme TEXT, priority TEXT, movements TEXT, raw_wod TEXT)''')
conn.commit()

# --- MOVEMENT LIBRARY (From L2 Sheet) ---
L2_MOVEMENTS = {
    "Gymnastics": ["Air Squat", "Box Jump", "Burpee", "Dip", "GHD", "Handstand", "Muscle-Up", "Pull-Up", "Push-Up", "Sit-Up", "Toes-to-Bar", "T2B", "Knees-to-Elbows", "Hip Extension", "Back Extension"],
    "Weightlifting": ["Back Squat", "Clean", "Deadlift", "Front Squat", "Kettlebell Swing", "Overhead Squat", "OHS", "Press", "Push Jerk", "Push Press", "Sumo Deadlift High Pull", "SDHP", "Snatch", "Thruster", "Wall Ball"],
    "Monostructural": ["Double-Under", "DU", "Row", "Run", "Bike", "SkiErg", "Swim", "Shuttle Run"]
}

def analyze_wod(text):
    found_moves = []
    modalities = set()
    
    # 1. Check for weight indicators (Forces 'W' modality)
    has_weight = re.search(r'\b\d+\s*(kg|lb|lbs|kilos)\b', text.lower())
    if has_weight:
        modalities.add("W")
    
    # 2. Check movements and assign modalities
    for cat, moves in L2_MOVEMENTS.items():
        category_detected = False
        for move in moves:
            if re.search(r'\b' + re.escape(move.lower()) + r'\b', text.lower()):
                found_moves.append(move)
                category_detected = True
        
        if category_detected:
            modalities.add(cat[0]) # Adds G, W, or M

    # 3. Scheme Analysis (Single, Couplet, Triplet, Chipper)
    unique_moves = list(set(found_moves))
    count = len(unique_moves)
    if count == 1: scheme = "Single"
    elif count == 2: scheme = "Couplet"
    elif count == 3: scheme = "Triplet"
    else: scheme = "Chipper"
    
    # 4. Priority (Task vs Time)
    priority = "Time" if "amrap" in text.lower() else "Task"
    
    # 5. Rep Volume Buckets (From L2 Sheet)
    numbers = re.findall(r'\b\d+\b', text)
    total_reps = sum(int(n) for n in numbers if 5 < int(n) < 500)
    if total_reps < 50: reps_cat = "Low (<50)"
    elif total_reps <= 200: reps_cat = "Medium (50-200)"
    else: reps_cat = "High (>200)"
    
    return "+".join(sorted(list(modalities))), scheme, priority, ", ".join(unique_moves), reps_cat

st.set_page_config(page_title="L2 Programming Analyzer", layout="wide")
st.title("🏋️‍♂️ CrossFit L2 Programming Analysis Dashboard")

# 1. INPUT SECTION
with st.container(border=True):
    st.subheader("Add New Workout")
    col1, col2 = st.columns(2)
    with col1:
        wod_desc = st.text_input("Workout Descriptor", placeholder="e.g. WOD 1")
        time_domain = st.selectbox("Time Domain", ["< 5 min", "5-10 min", "11-20 min", "> 20 min"])
        load_type = st.selectbox("Load Type", ["Bodyweight", "Light", "Medium", "Heavy"])
    with col2:
        raw_text = st.text_area("Paste Workout Details:", height=130, placeholder="Example: 21-15-9 Thrusters 40kg and Pull-ups")

    if st.button("Analyze & Save"):
        if raw_text and wod_desc:
            mod, sch, pri, moves, rep_cat = analyze_wod(raw_text)
            c.execute("INSERT INTO wods VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                      (datetime.now().strftime("%Y-%m-%d %H:%M"), wod_desc, mod, load_type, time_domain, rep_cat, sch, pri, moves, raw_text))
            conn.commit()
            st.success(f"Saved {wod_desc}!")
            st.rerun()

# 2. LOG TABLE
st.divider()
st.header("📋 Programming Analysis Log")
history_df = pd.read_sql_query("SELECT * FROM wods ORDER BY date DESC", conn)

if not history_df.empty:
    display_df = history_df.rename(columns={
        "descriptor": "WOD",
        "modality": "Modality (G/W/M)",
        "load": "Load",
        "time_domain": "Time Domain",
        "reps_category": "Volume",
        "scheme": "Scheme",
        "priority": "Priority",
        "movements": "Movements",
        "raw_wod": "Full Text"
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download History (CSV)", data=csv, file_name="cf_l2_log.csv", mime="text/csv")
else:
    st.info("No workouts logged yet.")
