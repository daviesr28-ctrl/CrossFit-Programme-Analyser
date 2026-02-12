import streamlit as st
import pandas as pd
import re
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect('programming_history.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS wods 
             (date TEXT, name TEXT, scheme TEXT, priority TEXT, modality TEXT, movements TEXT, reps INTEGER)''')
conn.commit()

# --- FULL L2 MOVEMENT LIBRARY ---
# These are pulled directly from your L2 Worksheet 
L2_MOVEMENTS = {
    "Gymnastics": [
        "Air Squat", "Box Jump", "Burpee", "Dip", "GHD", "Handstand", "Muscle-Up", 
        "Pull-Up", "Push-Up", "Sit-Up", "Toes-to-Bar", "T2B", "Knees-to-Elbows", 
        "Hip Extension", "Back Extension", "C2B", "Chest-to-Bar"
    ],
    "Weightlifting": [
        "Back Squat", "Clean", "Deadlift", "Front Squat", "Kettlebell Swing", 
        "Overhead Squat", "OHS", "Press", "Push Jerk", "Push Press", 
        "Sumo Deadlift High Pull", "SDHP", "Snatch", "Thruster", "Wall Ball"
    ],
    "Monostructural": [
        "Double-Under", "DU", "Row", "Run", "Bike", "SkiErg", "Swim", "Shuttle Run"
    ]
}

def analyze_wod(text):
    found_moves = []
    modalities = []
    
    for cat, moves in L2_MOVEMENTS.items():
        for move in moves:
            if re.search(r'\b' + re.escape(move.lower()) + r'\b', text.lower()):
                found_moves.append(move)
                if cat[0] not in modalities: modalities.append(cat[0])
    
    # Priority Logic (Task vs Time) 
    priority = "Time" if "amrap" in text.lower() or "minutes" in text.lower() else "Task"
    
    # Scheme Logic 
    unique_count = len(set(found_moves))
    if unique_count == 1: scheme = "Single"
    elif unique_count == 2: scheme = "Couplet"
    elif unique_count == 3: scheme = "Triplet"
    else: scheme = "Chipper"
    
    # Rep Volume 
    numbers = re.findall(r'\b\d+\b', text)
    total_reps = sum(int(n) for n in numbers if 5 < int(n) < 500)
    
    return scheme, priority, "+".join(modalities), ", ".join(set(found_moves)), total_reps

# --- UI INTERFACE ---
st.set_page_config(page_title="L2 Programming Log", layout="wide")
st.title("📋 CrossFit L2 Programming Analysis & Log")

# Input Section
with st.expander("➕ Add New Workout", expanded=True):
    wod_name = st.text_input("Workout Name (e.g., 'Monday Metcon')")
    raw_text = st.text_area("Paste Workout Details:", height=150)
    if st.button("Analyze and Save to Log"):
        if raw_text:
            scheme, priority, modality, moves, reps = analyze_wod(raw_text)
            c.execute("INSERT INTO wods VALUES (?, ?, ?, ?, ?, ?, ?)", 
                      (datetime.now().strftime("%Y-%m-%d"), wod_name, scheme, priority, modality, moves, reps))
            conn.commit()
            st.success("Workout Added!")
            st.rerun()

# --- THE PROGRAMMING TABLE ---
st.header("📚 Your Programming Log")
# This allows you to look back at all previous workouts in a table format
history_df = pd.read_sql_query("SELECT * FROM wods ORDER BY date DESC", conn)

if not history_df.empty:
    # Rename columns for the display table to match your sheet 
    display_df = history_df.rename(columns={
        "date": "Date",
        "name": "Workout Description",
        "scheme": "Scheme",
        "priority": "Priority",
        "modality": "Modality (G/W/M)",
        "movements": "Movements Detected",
        "reps": "Total Reps"
    })
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("No workouts saved yet. Add your first workout above!")
