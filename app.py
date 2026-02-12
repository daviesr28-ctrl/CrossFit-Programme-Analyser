import streamlit as st
import pandas as pd
import re
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect('programming_history.db', check_same_thread=False)
c = conn.cursor()
# Updated table to match every column from the L2 Worksheet 
c.execute('''CREATE TABLE IF NOT EXISTS wods 
             (date TEXT, descriptor TEXT, modality TEXT, load TEXT, time_domain TEXT, 
              reps_category TEXT, scheme TEXT, priority TEXT, movements TEXT)''')
conn.commit()

# --- FULL L2 MOVEMENT LIBRARY  ---
L2_MOVEMENTS = {
    "Gymnastics": ["Air Squat", "Box Jump", "Burpee", "Dip", "GHD", "Handstand", "Muscle-Up", "Pull-Up", "Push-Up", "Sit-Up", "Toes-to-Bar", "T2B", "Knees-to-Elbows", "Hip Extension", "Back Extension"],
    "Weightlifting": ["Back Squat", "Clean", "Deadlift", "Front Squat", "Kettlebell Swing", "Overhead Squat", "Press", "Push Jerk", "Push Press", "Sumo Deadlift High Pull", "SDHP", "Snatch", "Thruster", "Wall Ball"],
    "Monostructural": ["Double-Under", "DU", "Row", "Run", "Bike", "SkiErg", "Swim", "Shuttle Run"]
}

def analyze_wod(text):
    found_moves = []
    modalities = []
    for cat, moves in L2_MOVEMENTS.items():
        for move in moves:
            if re.search(r'\b' + re.escape(move.lower()) + r'\b', text.lower()):
                found_moves.append(move)
                if cat[0] not in modalities: modalities.append(cat[0])
    
    # Priority 
    priority = "Time" if "amrap" in text.lower() else "Task"
    
    # Scheme 
    unique_count = len(set(found_moves))
    if unique_count == 1: scheme = "Single"
    elif unique_count == 2: scheme = "Couplet"
    elif unique_count == 3: scheme = "Triplet"
    else: scheme = "Chipper"
    
    # Repetition Buckets 
    numbers = re.findall(r'\b\d+\b', text)
    total_reps = sum(int(n) for n in numbers if 5 < int(n) < 500)
    if total_reps < 50: reps_cat = "Low (<50)"
    elif total_reps <= 200: reps_cat = "Medium (50-200)"
    else: reps_cat = "High (>200)"
    
    return "+".join(modalities), scheme, priority, ", ".join(set(found_moves)), reps_cat

st.set_page_config(page_title="L2 Programming Analyzer", layout="wide")
st.title("🏋️‍♂️ CrossFit L2 Programming Analysis Dashboard")

# 1. INPUT SECTION
with st.container(border=True):
    st.subheader("Add New Workout")
    col1, col2 = st.columns(2)
    with col1:
        wod_desc = st.text_input("Workout Descriptor (e.g., WOD 1)", placeholder="Monday Morning Metcon")
        time_domain = st.selectbox("Time Domain ", ["< 5 min", "5-10 min", "11-20 min", "> 20 min"])
        load_type = st.selectbox("Load ", ["Bodyweight", "Light", "Medium", "Heavy"])
    with col2:
        raw_text = st.text_area("Paste Workout Details (Text Box):", height=130, placeholder="21-15-9 Thrusters and Pull-ups...")

    if st.button("Analyze & Save to Worksheet Log"):
        if raw_text and wod_desc:
            mod, sch, pri, moves, rep_cat = analyze_wod(raw_text)
            c.execute("INSERT INTO wods VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                      (datetime.now().strftime("%Y-%m-%d"), wod_desc, mod, load_type, time_domain, rep_cat, sch, pri, moves))
            conn.commit()
            st.success(f"Saved {wod_desc} to your history!")
            st.rerun()

# 2. THE DIGITAL WORKSHEET TABLE 
st.divider()
st.header("📋 Completed Programming Worksheet")
history_df = pd.read_sql_query("SELECT * FROM wods ORDER BY date DESC", conn)

if not history_df.empty:
    # Rename columns to match your PDF exactly 
    display_df = history_df.rename(columns={
        "descriptor": "Workout Descriptor",
        "modality": "Modality (G/W/M)",
        "load": "Load",
        "time_domain": "Time",
        "reps_category": "Total Repetitions",
        "scheme": "Scheme",
        "priority": "Priority",
        "movements": "Movements"
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Download Button to prevent data loss
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Analysis History (CSV)", data=csv, file_name="crossfit_l2_analysis.csv", mime="text/csv")
else:
    st.info("Your log is empty. Enter a workout above to start your analysis.")
