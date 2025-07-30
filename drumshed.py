import streamlit as st
import os
import time

# Initialize session state variables
if "is_running" not in st.session_state:
    st.session_state['is_running'] = False

# Load sound file as base64
import base64

sound_folder = "./sounds"
sound_files = [f for f in os.listdir(sound_folder) if f.endswith(('.wav', '.mp3', '.ogg'))]
selected_sound = st.selectbox("Select a sound", sound_files)
sound_path = os.path.join(sound_folder, selected_sound)

with open(sound_path, "rb") as f:
    sound_bytes = f.read()
sound_base64 = base64.b64encode(sound_bytes).decode()

# Slider and feel
st.slider("Tempo (BPM)", 40, 200, 120, key="tempo")
feel_option = st.selectbox("Feel", ["1/4", "1/8", "Triplet", "1/16"], index=0)
feel_map = {
    "1/4": lambda bpm: 60.0 / bpm,
    "1/8": lambda bpm: 60.0 / (bpm * 2),
    "Triplet": lambda bpm: 60.0 / (bpm * 3),
    "1/16": lambda bpm: 60.0 / (bpm * 4)
}
interval = feel_map[feel_option](st.session_state["tempo"])

# Start/Stop button
if st.button("Start / Stop"):
    st.session_state['is_running'] = not st.session_state['is_running']

st.write(f"Interval: {interval:.2f} seconds.")

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