import streamlit as st
import os
from datetime import datetime
import pandas as pd
import threading
import time
import json
import sounddevice as sd
import soundfile as sf

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

# Load data at start
data = load_data()

# --- Helper Functions ---
def list_files_in_folder(folder_path):
    return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

def load_sound(sound_path):
    return sf.read(sound_path, dtype='float32')

def apply_volume(data, volume):
    return data * volume

def play_sound(data, samplerate):
    sd.play(data, samplerate)
    sd.wait()

def get_timing_and_volumes(feel, tempo):
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

def get_volumes_for_pattern(pattern):
    return [1.0 if p == "main" else 0.6 for p in pattern]

def run_metronome(tempo, feel, sound_file_path, stop_event, beat_flag, main_sound):
    data, samplerate = load_sound(sound_file_path)
    interval, pattern = get_timing_and_volumes(feel, tempo)
    volumes = get_volumes_for_pattern(pattern)
    while not stop_event.is_set():
        for vol in volumes:
            if stop_event.is_set():
                break
            sound_data = apply_volume(main_sound, vol)
            threading.Thread(target=play_sound, args=(sound_data, samplerate), daemon=True).start()
            time.sleep(interval)

# --- Main ---
st.title("🎶 The Woodshed 🎶")

# --- Always visible controls ---
st.subheader("Metronome Settings & Controls")
sounds_folder = "./sounds"
sound_files = list_files_in_folder(sounds_folder)

if 'stop_event' not in st.session_state:
    from threading import Event
    st.session_state['stop_event'] = threading.Event()
if 'beat_flag' not in st.session_state:
    st.session_state['beat_flag'] = {'beat': False}
if 'metronome_thread' not in st.session_state:
    st.session_state['metronome_thread'] = None
if 'is_running' not in st.session_state:
    st.session_state['is_running'] = False

selected_sound = st.selectbox("Select Click Sound", sound_files)
sound_path = os.path.join(sounds_folder, selected_sound)
main_sound, sr = load_sound(sound_path)

col1, col2 = st.columns([2, 1])
with col1:
    tempo = st.slider("Tempo (BPM)", 40, 200, 120)
with col2:
    feel = st.selectbox("Feel", ["1/4", "1/8", "Triplet", "1/16"])

def toggle_metronome():
    if not st.session_state['is_running']:
        st.session_state['stop_event'].clear()
        new_params = dict(st.query_params)
        new_params['metronome'] = "running"
        st.query_params = new_params
        thread = threading.Thread(target=run_metronome, args=(
            tempo, feel, sound_path, st.session_state['stop_event'], st.session_state['beat_flag'], main_sound
        ), daemon=True)
        thread.start()
        st.session_state['metronome_thread'] = thread
        st.session_state['is_running'] = True
    else:
        new_params = dict(st.query_params)
        new_params['metronome'] = "stopped"
        st.query_params = new_params
        st.session_state['stop_event'].set()
        st.session_state['metronome_thread'] = None
        st.session_state['is_running'] = False

if st.button("Start" if not st.session_state['is_running'] else "Stop"):
    toggle_metronome()

# Visual Indicator
indicator_placeholder = st.empty()
time.sleep(0.1)
current_state = st.query_params.get("metronome", ["stopped"])[0]
if current_state == "running" and st.session_state['is_running']:
    if st.session_state['beat_flag'].get('beat', False):
        indicator_placeholder.markdown("🔴")
    else:
        indicator_placeholder.markdown("")
else:
    indicator_placeholder.markdown("")

st.write(f"**Current:** {feel} feel at {tempo} BPM.")

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
# Add entry form inside expander
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

# View practice log entries
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
archives = pd.DataFrame(data.get("archives", []))

# --- Add a Goal form inside an expander ---
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

# --- Active Goals with Update & Archive ---
with st.expander("View Goals", expanded=True):
    data = load_data()
    goals = pd.DataFrame(data.get("goals", []))
    if not goals.empty:
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
            title = f"{icon} {row['Goal']} - {row['Status']} - {row['Target Date']}"
            with st.expander(title, expanded=False):
                # Show Details
                st.write(f"**Details:** {row['Details']}")
                # Update Status
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
                # Action dropdown for archive/delete
                with col2:
                    action = st.selectbox(
                        "Action",
                        ["Keep", "Success", "Delete"],
                        index=0,
                        key=f"action_{idx}"
                    )
                    if action == "Success":
                        # Move to archives
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
st.header("Archived Goals")
if not archives.empty:
    for idx, row in archives.iterrows():
        title = f"✅ {row['Goal']} - {row['Status']} - {row['Target Date']}"
        with st.expander(title, expanded=False):
            st.write(f"**Details:** {row['Details']}")
            if st.button(f"Delete from Archive", key=f"del_archive_{idx}"):
                # Remove from archives
                data["archives"].pop(idx)
                save_data(data)
                st.success(f"Archived goal '{row['Goal']}' permanently deleted.")
                st.rerun()
else:
    st.write("No archived goals.")
    
