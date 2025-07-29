import streamlit as st
import threading
import time
import os
import re
from datetime import datetime
import json
import pandas as pd
import numpy as np
import soundfile as sf
import io

# --- Constants ---
DATA_FILE = "data.json"
SOUNDS_FOLDER = "./sounds"

# --- Initialize Session State Variables ---
# These should be initialized once at startup
for key, default in [
    ('is_running', False),
    ('stop_metronome', False),
    ('current_beat', 0),
    ('audio_trigger', False),
    ('should_rerun', False),
    ('tempo', 120),
    ('feel', "1/4"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- Load Data ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {"practice_log": [], "goals": [], "archives": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str, indent=2)

# --- Generate Beep Sound ---
def generate_beep():
    t = np.linspace(0, 0.1, int(44100 * 0.1), False)
    tone = np.sin(1000 * t * 2 * np.pi)
    audio = (tone * 32767).astype(np.int16)
    buf = io.BytesIO()
    sf.write(buf, audio, 44100, format='WAV')
    buf.seek(0)
    return buf.read()

beep_bytes = generate_beep()

# --- Load Selected Sound ---
def load_sound(path):
    data, sr = sf.read(path, dtype='float32')
    return data, sr

# --- UI: Title and Settings ---
# st.title("🎶Drumshed🎶")

# only logo full page
st.image("images/logo.jpeg", use_container_width=True)
st.subheader("Metronome")

# --- Select Sound ---
sounds_files = [f for f in os.listdir(SOUNDS_FOLDER) if os.path.isfile(os.path.join(SOUNDS_FOLDER, f))]
selected_sound = st.selectbox("Select Click Sound", sounds_files)
sound_path = os.path.join(SOUNDS_FOLDER, selected_sound)
sound_array, sr = load_sound(sound_path)

# --- Sliders and Selectboxes ---
col1, col2 = st.columns([2, 1])
with col1:
    st.session_state['tempo'] = st.slider("Tempo (BPM)", 40, 200, st.session_state['tempo'])
with col2:
    st.session_state['feel'] = st.selectbox("Feel", ["1/4", "1/8", "Triplet", "1/16"], index=["1/4", "1/8", "Triplet", "1/16"].index(st.session_state['feel']))

# --- Start/Stop Button ---
def start_stop():
    if not st.session_state['is_running']:
        st.session_state['is_running'] = True
        st.session_state['stop_metronome'] = False
        st.session_state['current_beat'] = 0
        st.session_state['audio_trigger'] = False
        start_metronome(st.session_state['tempo'])
        st.rerun()
    else:
        st.session_state['stop_metronome'] = True
        st.session_state['is_running'] = False
        st.rerun()

st.button("Start" if not st.session_state['is_running'] else "Stop", on_click=start_stop)

# --- Background Metronome Thread ---
def start_metronome(tempo):
    def metronome():
        interval = 60.0 / tempo
        while not st.session_state['stop_metronome']:
            # Signal main app to play sound
            st.session_state['audio_trigger'] = True
            st.session_state['current_beat'] += 1
            # Set rerun flag
            st.session_state['should_rerun'] = True
            time.sleep(interval)
    t = threading.Thread(target=metronome, daemon=True)
    st.session_state['metronome_thread'] = t
    t.start()

# --- Check if rerun is needed ---
if st.session_state.get('should_rerun', False):
    st.session_state['should_rerun'] = False
    st.rerun()

# --- Play beep when triggered ---
if st.session_state.get('audio_trigger', False):
    st.audio(beep_bytes, format='audio/wav')
    st.session_state['audio_trigger'] = False

# --- Display current beat ---
st.write(f"Current Beat: {st.session_state.get('current_beat', 0)}")


import os
import re
import streamlit as st

# --- Practice Material Section ---
st.subheader("Practice Files")
with st.expander("View Files", expanded=False):
    folder = "images"
    if os.path.exists(folder):
        # Get subfolders
        subfolders = [sf for sf in os.listdir(folder) if os.path.isdir(os.path.join(folder, sf))]
        
        # Function to extract the prefix for sorting subfolders
        def get_prefix(folder_name):
            match = re.match(r'^([A-Za-z0-9]+)', folder_name)
            return match.group(1) if match else folder_name

        # Sort subfolders based on prefix
        subfolders_sorted = sorted(subfolders, key=get_prefix)

        if subfolders_sorted:
            # Prepare display names without the prefix for subfolders
            subfolder_display_map = {}
            subfolder_display_names = []

            for sf in subfolders_sorted:
                # Remove prefix and underscore
                name_without_prefix = re.sub(r'^[A-Za-z0-9]+_', '', sf)
                subfolder_display_names.append(name_without_prefix)
                subfolder_display_map[name_without_prefix] = sf

            selected_subfolder_display = st.selectbox("Select Folder", subfolder_display_names)
            selected_subfolder = subfolder_display_map[selected_subfolder_display]
            subfolder_path = os.path.join(folder, selected_subfolder)

            # List files in selected subfolder
            files = [f for f in os.listdir(subfolder_path) if os.path.isfile(os.path.join(subfolder_path, f))]

            if files:
                # Sort files based on prefix
                def get_file_prefix(filename):
                    match = re.match(r'^([A-Za-z0-9]+)', filename)
                    return match.group(1) if match else filename

                files_sorted = sorted(files, key=get_file_prefix)

                # Create display names for files (remove prefix and extension)
                file_display_map = {}
                file_display_names = []

                for f in files_sorted:
                    name_without_prefix = re.sub(r'^[^_]*_', '', f)
                    name_without_ext = re.sub(r'\.[^.]+$', '', name_without_prefix)
                    file_display_names.append(name_without_ext)
                    file_display_map[name_without_ext] = f

                selected_file_display = st.selectbox("Select File", file_display_names)
                selected_file = file_display_map[selected_file_display]
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
            st.write("No subfolders found.")
    else:
        st.write("Images folder not found.")

        

# --- Practice Log / Diary ---
st.subheader("Practice Log")
with st.expander("Add Notes", expanded=False):
    diary = st.text_area("Notes on today's session")
    if st.button("Save Notes"):
        data = load_data()
        data["practice_log"].append({
            "timestamp": str(datetime.now()),
            "entry": diary
        })
        save_data(data)

with st.expander("View Notes", expanded=True):
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
st.subheader("Goals & Progress")
data = load_data()
goals_df = pd.DataFrame(data.get("goals", []))
if not goals_df.empty:
    goals_df['Target Date'] = pd.to_datetime(goals_df['Target Date'], errors='coerce')
    goals_df = goals_df.sort_values(by='Target Date')
archives_df = pd.DataFrame(data.get("archives", []))

# --- Add a Goal ---
with st.expander("Add Goal", expanded=False):
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
            st.rerun()

# --- View Goals ---
with st.expander("View Goals", expanded=True):
    data = load_data()
    goals_df = pd.DataFrame(data.get("goals", []))
    if not goals_df.empty:
        goals_df['Target Date'] = pd.to_datetime(goals_df['Target Date'], errors='coerce')
        goals_df = goals_df.sort_values(by='Target Date')
        for idx, row in goals_df.iterrows():
            status_icons = {
                "New": "🟣",
                "In-the-works": "🟡🟠🟠",
                "Dormant": "🟤",
                "Demo-Ready": "🟡🟡🟠🟠🟠🟢",
                "Live-Ready": "🟡🟡🟠🟠🟠🟢🟢🟢",
                "Studio-Ready": "🟡🟡🟠🟠🟠🟢🟢🟢🟢🔴🔴",
                # "Studio-Ready": "🟣🟣🟣🟣", #🔴🔴
                "Forked": "🔴"
            }
            icon = status_icons.get(row['Status'], "⚪")
            title = f"{icon}  -  **{row['Goal']}** - by - {row['Target Date'].date()} - currently: **{row['Status']}**"
            # title = f"**{row['Goal']}** - {row['Target Date'].date()} - **{row['Status']}** - {icon}"
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
with st.expander("Done Pile", expanded=False):
    data = load_data()
    archives_df = pd.DataFrame(data.get("archives", []))
    if not archives_df.empty:
        for idx, row in archives_df.iterrows():
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