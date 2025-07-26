import streamlit as st
import os
from datetime import datetime
import pandas as pd
import threading
import time
import json
import numpy as np
import soundfile as sf
import io

DATA_FILE = "data.json"

# --- Data Handling ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {"practice_log": [], "goals": [], "archives": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str, indent=2)

# Generate a short beep sound once
def generate_beep(frequency=1000, duration=0.1, samplerate=44100):
    t = np.linspace(0, duration, int(samplerate * duration), False)
    tone = np.sin(frequency * t * 2 * np.pi)
    audio = (tone * 32767).astype(np.int16)
    buf = io.BytesIO()
    sf.write(buf, audio, samplerate, format='WAV')
    buf.seek(0)
    return buf

beep_buffer = generate_beep()

# Load data at start
data = load_data()

# --- Helper Functions ---
def list_files_in_folder(folder_path):
    return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

# --- Metronome logic ---
metronome_running = False
metronome_thread = None

def get_timing(feel, tempo):
    if feel == "1/4":
        interval = 60 / tempo
        pattern = ["main"]
    elif feel == "1/8":
        interval = 60 / (tempo * 2)
        pattern = ["main", "tap"]
    elif feel == "Triplet":
        interval = 60 / (tempo * 3)
        pattern = ["main", "tap", "tap"]
    elif feel == "1/16":
        interval = 60 / (tempo * 4)
        pattern = ["main", "tap", "tap", "tap"]
    else:
        interval = 60 / tempo
        pattern = ["main"]
    return interval, pattern

# --- Main ---
st.title("🎶 The Woodshed 🎶")

# --- Controls ---
st.subheader("Metronome Settings & Controls")
sounds_folder = "./sounds"
sound_files = list_files_in_folder(sounds_folder)

# Select sound
selected_sound = st.selectbox("Select Click Sound", sound_files)
sound_path = os.path.join(sounds_folder, selected_sound)

# Load selected sound
def load_sound(sound_path):
    data, sr = sf.read(sound_path, dtype='float32')
    return data, sr
sound_array, sr = load_sound(sound_path)

col1, col2 = st.columns([2, 1])
with col1:
    tempo = st.slider("Tempo (BPM)", 40, 200, 120)
with col2:
    feel = st.selectbox("Feel", ["1/4", "1/8", "Triplet", "1/16"])

# Placeholder for the audio player
audio_placeholder = st.empty()

# Start/Stop button
if 'metronome_state' not in st.session_state:
    st.session_state['metronome_state'] = False

def start_stop():
    if not st.session_state['metronome_state']:
        st.session_state['metronome_state'] = True
        threading.Thread(target=metronome_loop, args=(tempo, feel), daemon=True).start()
    else:
        st.session_state['metronome_state'] = False

def metronome_loop(tempo, feel):
    global metronome_running
    interval, pattern = get_timing(feel, tempo)
    while st.session_state['metronome_state']:
        # Play beep sound
        # Update st.audio
        audio_placeholder.audio(beep_buffer.read(), format='audio/wav', start_time=0)
        time.sleep(interval)

st.button("Start" if not st.session_state['metronome_state'] else "Stop", on_click=start_stop)

# --- Practice Material ---
st.header("Practice Material")
with st.expander("Browse Practice PDFs & Images", expanded=False):
    folder = "images"
    if os.path.exists(folder):
        subfolders = [sf for sf in os.listdir(folder) if os.path.isdir(os.path.join(folder, sf))]
        selected_subfolder = st.selectbox("Select Practice Folder", subfolders)
        subfolder_path = os.path.join(folder, selected_subfolder)
        files = list_files_in_folder(subfolder_path)
        if files:
            selected_file = st.selectbox("Select File", files)
            file_path = os.path.join(subfolder_path, selected_file)
            if selected_file.endswith('.pdf'):
                st.write("PDF viewing is limited in Streamlit. Download below:")
                st.markdown(f"[Download {selected_file}](/{file_path})")
            elif selected_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                st.image(file_path, use_container_width=True)
            else:
                st.write("File type not supported for preview.")
        else:
            st.write("No files in this folder.")
    else:
        st.write("Images folder not found.")

# --- Practice Log / Diary ---
st.header("Practice Log / Diary")
with st.expander("Add Practice Log Entry", expanded=False):
    diary = st.text_area("Notes on today's session")
    if st.button("Save Notes"):
        data = load_data()
        data["practice_log"].append({
            "timestamp": str(datetime.now()),
            "entry": diary
        })
        save_data(data)
        st.success("Notes saved!")

with st.expander("View Practice Log Entries", expanded=True):
    data = load_data()
    logs = data.get("practice_log", [])
    for idx, entry in reversed(list(enumerate(logs))):
        with st.expander(f"Entry {idx+1} - {entry['timestamp']}", expanded=False):
            st.write(entry['entry'])
            if st.button(f"Delete Entry {idx+1}", key=f"del_log_{idx}"):
                logs.pop(idx)
                data["practice_log"] = logs
                save_data(data)
                st.rerun()

# --- Goals & Progress ---
st.header("Goals & Progress")
data = load_data()
goals = pd.DataFrame(data.get("goals", []))
if not goals.empty:
    goals['Target Date'] = pd.to_datetime(goals['Target Date'], errors='coerce')
    goals = goals.sort_values(by='Target Date')
archives = pd.DataFrame(data.get("archives", []))

# --- Add a Goal ---
with st.expander("Add a Goal", expanded=False):
    with st.form("add_goal_form"):
        goal_text = st.text_input("Goal")
        target_date = st.date_input("Target Date")
        goal_details = st.text_input("Details")
        submitted = st.form_submit_button("Add Goal")
        if submitted:
            new_goal = {
                "Goal": goal_text,
                "Target Date": str(target_date),
                "Details": goal_details,
                "Status": "New",
                "Start Date": str(datetime.now().date())
            }
            data["goals"].append(new_goal)
            save_data(data)
            st.success("Goal added!")

# --- View Goals ---
with st.expander("View Goals", expanded=True):
    data = load_data()
    goals = pd.DataFrame(data.get("goals", []))
    if not goals.empty:
        goals['Target Date'] = pd.to_datetime(goals['Target Date'], errors='coerce')
        goals = goals.sort_values(by='Target Date')
        for idx, row in goals.iterrows():
            status_icons = {
                "New": "🟢",
                "In-the-works": "🟡",
                "Dormant": "🟤",
                "Demo-Ready": "🔵",
                "Live-Ready": "🟠",
                "Studio-Ready": "🟣",
                "Forked": "🟢"
            }
            icon = status_icons.get(row['Status'], "⚪")
            title = f"**{row['Goal']}** - {row['Target Date'].date()} - **{row['Status']}** - {icon}"
            with st.expander(title, expanded=False):
                st.write(f"**Details:** {row['Details']}")
                col1, col2 = st.columns(2)
                with col1:
                    new_status = st.selectbox(
                        "Update Status",
                        ["New", "In-the-works", "Dormant", "Demo-Ready", "Live-Ready", "Studio-Ready", "Forked"],
                        index=["New", "In-the-works", "Dormant", "Demo-Ready", "Live-Ready", "Studio-Ready", 
"Forked"].index(row['Status']),
                        key=f"status_{idx}"
                    )
                    if new_status != row['Status']:
                        data["goals"][idx]["Status"] = new_status
                        save_data(data)
                        st.success(f"Status for '{row['Goal']}' updated.")
                        st.rerun()
                with col2:
                    action = st.selectbox(
                        "Action",
                        ["Keep", "Success", "Delete"],
                        index=0,
                        key=f"action_{idx}"
                    )
                    if action == "Success":
                        data["archives"].append({**row, "Status": "Forked"})
                        data["goals"].pop(idx)
                        save_data(data)
                        st.success(f"Goal '{row['Goal']}' archived.")
                        st.rerun()
                    elif action == "Delete":
                        data["goals"].pop(idx)
                        save_data(data)
                        st.success(f"Goal '{row['Goal']}' deleted.")
                        st.rerun()
    else:
        st.write("No goals set yet.")

# --- Archived Goals ---
with st.expander("Archived Goals", expanded=False):
    if not archives.empty:
        for idx, row in archives.iterrows():
            title = f"✅ {row['Goal']} - {row['Status']} - {row['Target Date']}"
            with st.expander(title, expanded=False):
                st.write(f"**Details:** {row['Details']}")
                if st.button(f"Delete from Archive", key=f"del_archive_{idx}"):
                    data["archives"].pop(idx)
                    save_data(data)
                    st.success(f"Archived goal '{row['Goal']}' permanently deleted.")
                    st.rerun()
    else:
        st.write("No archived goals.")

