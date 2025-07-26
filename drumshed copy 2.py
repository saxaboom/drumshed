import streamlit as st
import threading
import time
import os
from datetime import datetime
import json
import pandas as pd
import numpy as np
import soundfile as sf
import io

DATA_FILE = "data.json"

# --- Data handling ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {"practice_log": [], "goals": [], "archives": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str, indent=2)

# --- Generate beep sound once ---
def generate_beep(frequency=1000, duration=0.1, samplerate=44100):
    t = np.linspace(0, duration, int(samplerate * duration), False)
    tone = np.sin(frequency * t * 2 * np.pi)
    audio = (tone * 32767).astype(np.int16)
    buf = io.BytesIO()
    sf.write(buf, audio, samplerate, format='WAV')
    buf.seek(0)
    return buf.read()

beep_bytes = generate_beep()

# --- Initialize session state ---
if 'beep_data' not in st.session_state:
    st.session_state['beep_data'] = None
if 'stop_event' not in st.session_state:
    st.session_state['stop_event'] = threading.Event()
if 'is_running' not in st.session_state:
    st.session_state['is_running'] = False

# --- Metronome thread ---
def metronome_loop(stop_event, interval):
    while not stop_event.is_set():
        # Update shared beep data for main thread to play
        st.session_state['beep_data'] = beep_bytes
        time.sleep(interval)

# --- UI Controls for Metronome ---
if 'thread' not in st.session_state:
    st.session_state['thread'] = None

def start_stop():
    if not st.session_state['is_running']:
        # Start the background thread
        st.session_state['stop_event'].clear()
        interval = 60 / st.session_state['tempo']
        st.session_state['thread'] = threading.Thread(target=metronome_loop, args=(st.session_state['stop_event'], interval), daemon=True)
        st.session_state['thread'].start()
        st.session_state['is_running'] = True
    else:
        # Stop the background thread
        st.session_state['stop_event'].set()
        st.session_state['is_running'] = False

st.title("🎶 The Woodshed 🎶")
st.subheader("Metronome Settings & Controls")

# --- Select sound ---
sounds_folder = "./sounds"
sound_files = [f for f in os.listdir(sounds_folder) if os.path.isfile(os.path.join(sounds_folder, f))]
selected_sound = st.selectbox("Select Click Sound", sound_files)
sound_path = os.path.join(sounds_folder, selected_sound)

def load_sound(path):
    data, sr = sf.read(path, dtype='float32')
    return data, sr
sound_array, sr = load_sound(sound_path)

col1, col2 = st.columns([2, 1])
with col1:
    st.session_state['tempo'] = st.slider("Tempo (BPM)", 40, 200, 120)
with col2:
    st.session_state['feel'] = st.selectbox("Feel", ["1/4", "1/8", "Triplet", "1/16"])

st.button("Start" if not st.session_state['is_running'] else "Stop", on_click=start_stop)

# --- Display current beat indicator ---
indicator_placeholder = st.empty()

# --- Play beep in browser if available ---
if st.session_state['beep_data'] is not None:
    st.audio(st.session_state['beep_data'], format='audio/wav')
    st.session_state['beep_data'] = None

# --- Practice Material ---
st.header("Practice Material")
with st.expander("Browse Practice PDFs & Images", expanded=False):
    folder = "images"
    if os.path.exists(folder):
        subfolders = [sf for sf in os.listdir(folder) if os.path.isdir(os.path.join(folder, sf))]
        selected_subfolder = st.selectbox("Select Practice Folder", subfolders)
        subfolder_path = os.path.join(folder, selected_subfolder)
        files = [f for f in os.listdir(subfolder_path) if os.path.isfile(os.path.join(subfolder_path, f))]
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
                        index=["New", "In-the-works", "Dormant", "Demo-Ready", "Live-Ready", "Studio-Ready", "Forked"].index(row['Status']),
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
