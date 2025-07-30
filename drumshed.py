import streamlit as st
import os
import re
from datetime import datetime
import json
import pandas as pd
# import numpy as np
# import soundfile as sf
# import io

# --- Constants ---
DATA_FILE = "data.json"
SOUNDS_FOLDER = "./sounds"

# Initialize session state variables
if "is_running" not in st.session_state:
    st.session_state['is_running'] = False

# --- Load Data File For Practice Notes etc.. ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {"practice_log": [], "goals": [], "archives": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str, indent=2)


# Load sound file as base64
import base64

# --- UI: Title and Settings ---
# st.title("🎶Drumshed🎶")
# only logo full page
st.image("images/logo.jpeg", use_container_width=True)

st.subheader("Metronome")
# --- Select Sound ---
sound_folder = "./sounds"
sound_files = [f for f in os.listdir(sound_folder) if f.endswith(('.wav', '.mp3', '.ogg'))]
selected_sound = st.selectbox("Click Sounds", sound_files)
sound_path = os.path.join(sound_folder, selected_sound)

with open(sound_path, "rb") as f:
    sound_bytes = f.read()
sound_base64 = base64.b64encode(sound_bytes).decode()

# --- Sliders and Select Boxes
col1, col2 = st.columns([3,1])
with col1:
    st.slider("Tempo", 40, 200, 120, key="tempo")
with col2:
    feel_option = st.selectbox("Feel", ["1/4", "1/8", "Triplet", "1/16"], index=0, )
    feel_map = {
        "1/4": lambda bpm: 60.0 / bpm,
        "1/8": lambda bpm: 60.0 / (bpm * 2),
        "Triplet": lambda bpm: 60.0 / (bpm * 3),
        "1/16": lambda bpm: 60.0 / (bpm * 4)
    }
# --- calculated time interval ---
interval = feel_map[feel_option](st.session_state["tempo"])
# st.write(f"Interval: {interval:.2f} seconds.")

if st.button("Start / Stop", use_container_width=True):
        st.session_state['is_running'] = not st.session_state['is_running']


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

## rendering javascript down here 
# JavaScript for playing sound
js_code = f"""
<script>
var sound = new Audio("data:audio/wav;base64,{sound_base64}");
var interval = {interval * 1000}; // milliseconds
var timer;

function startMetronome() {{
    if (!timer) {{
        sound.currentTime = 0;
        sound.play();
        timer = setInterval(() => {{
            sound.currentTime = 0;
            sound.play();
        }}, interval);
    }}
}}

function stopMetronome() {{
    clearInterval(timer);
    timer = null;
}}

if ({str(st.session_state['is_running']).lower()}) {{
    startMetronome();
}} else {{
    stopMetronome();
}}
</script>
"""

# Render the JavaScript
st.components.v1.html(js_code)