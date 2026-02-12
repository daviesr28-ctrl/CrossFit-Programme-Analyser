{\rtf1\ansi\ansicpg1252\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
import re\
import sqlite3\
from datetime import datetime\
\
# --- DATABASE SETUP ---\
conn = sqlite3.connect('programming_history.db', check_same_thread=False)\
c = conn.cursor()\
c.execute('''CREATE TABLE IF NOT EXISTS wods \
             (date TEXT, scheme TEXT, movements TEXT, intensity TEXT, volume_total INTEGER)''')\
conn.commit()\
\
# --- MOVEMENT LIBRARY ---\
MOVEMENTS = \{\
    "Gymnastics": ["Air Squat", "Box Jump", "Burpee", "Chest-to-Bar Pull-Up", "C2B", "Pull-Up", "BMU", "RMU", "HSPU", "T2B", "Wall Walk"],\
    "Weightlifting": ["Thruster", "Clean and Jerk", "Snatch", "Deadlift", "Back Squat", "Front Squat", "OHS", "STOH", "Wall Ball", "DB Snatch"],\
    "Monostructural": ["Double-Under", "DU", "Row", "Run", "Bike", "SkiErg", "Shuttle Run"]\
\}\
\
# --- LOGIC FUNCTIONS ---\
def analyze_wod(text):\
    found = []\
    for cat, moves in MOVEMENTS.items():\
        for move in moves:\
            if re.search(r'\\b' + re.escape(move.lower()) + r'\\b', text.lower()):\
                found.append(move)\
    \
    # Rep Volume Logic \
    numbers = re.findall(r'\\b\\d+\\b', text)\
    total_reps = sum(int(n) for n in numbers if 5 < int(n) < 500)\
    \
    # Scheme Logic \
    unique_count = len(set(found))\
    if unique_count == 1: scheme = "Single"\
    elif unique_count == 2: scheme = "Couplet"\
    elif unique_count == 3: scheme = "Triplet"\
    else: scheme = "Chipper"\
    \
    return scheme, ", ".join(set(found)), total_reps\
\
# --- UI INTERFACE ---\
st.set_page_config(page_title="CrossFit L2 Data Center", layout="wide")\
st.title("\uc0\u55357 \u56523  Gym Programming History & Analysis")\
\
# Sidebar for History\
st.sidebar.header("History Log")\
history_df = pd.read_sql_query("SELECT * FROM wods", conn)\
st.sidebar.dataframe(history_df)\
\
if st.sidebar.button("Clear History"):\
    c.execute("DELETE FROM wods")\
    conn.commit()\
    st.rerun()\
\
# Main Input\
raw_text = st.text_area("Enter Today's Workout:", height=150)\
\
if st.button("Analyze & Save Workout"):\
    scheme, moves, reps = analyze_wod(raw_text)\
    \
    # Determine Intensity based on Weightlifting presence\
    intensity = "High" if "kg" in raw_text.lower() or "lb" in raw_text.lower() else "Medium/Low"\
    \
    # Save to Database\
    c.execute("INSERT INTO wods VALUES (?, ?, ?, ?, ?)", \
              (datetime.now().strftime("%Y-%m-%d"), scheme, moves, intensity, reps))\
    conn.commit()\
    st.success("Workout saved to history!")\
\
# --- TRENDS DASHBOARD ---\
if not history_df.empty:\
    st.divider()\
    st.header("\uc0\u55357 \u56520  Programming Balance (Trends)")\
    \
    col1, col2 = st.columns(2)\
    \
    with col1:\
        st.subheader("Scheme Distribution")\
        # Shows if you program too many Couplets vs Triplets \
        scheme_counts = history_df['scheme'].value_counts()\
        st.bar_chart(scheme_counts)\
        \
    with col2:\
        st.subheader("Volume Over Time")\
        # Tracks the 'Total Repetitions' column from your L2 worksheet \
        st.line_chart(history_df.set_index('date')['volume_total'])}
