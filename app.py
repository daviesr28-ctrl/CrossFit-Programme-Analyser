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
    "Weightlifting": ["Back Squat", "Clean", "Deadlift", "Front Squat", "Kettlebell Swing", "Overhead Squat", "Press", "Push Jerk", "Push Press", "Sumo Deadlift High Pull", "SDHP", "Snatch", "Thruster", "Wall Ball"],
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
        for move in moves:
            if re.search(r'\b' + re.escape(move.lower()) + r'\b', text.lower()):
                found_moves.append(move)
                modalities.add(cat[0]) # Adds G, W, or M
    
    # 3. If no weight is found but movements are detected, ensure G is there for bodyweight
    if not has_weight and "Gymnastics" in [c for c in L2_MOVEMENTS if any(m in found_moves for m in L2_MOVEMENTS
