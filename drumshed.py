import streamlit as st
import os
import base64

# Initialize session state variables
if "is_running" not in st.session_state:
    st.session_state['is_running'] = False

# Load sound files
sound_folder = "./sounds"
sound_files = [f for f in os.listdir(sound_folder) if f.endswith(('.wav', '.mp3', '.ogg'))]
selected_sound = st.selectbox("Select a sound", sound_files)
sound_path = os.path.join(sound_folder, selected_sound)

with open(sound_path, "rb") as f:
    sound_bytes = f.read()
sound_base64 = base64.b64encode(sound_bytes).decode()

# Tempo and feel controls
st.slider("Tempo (BPM)", 40, 200, 120, key="tempo")
feel_option = st.selectbox("Feel", ["1/4", "1/8", "Triplet", "1/16"], index=0)
feel_map = {
    "1/4": lambda bpm: 60.0 / bpm,
    "1/8": lambda bpm: 60.0 / (bpm * 2),
    "Triplet": lambda bpm: 60.0 / (bpm * 3),
    "1/16": lambda bpm: 60.0 / (bpm * 4)
}
interval = feel_map[feel_option](st.session_state["tempo"])

# Toggle button
if st.button("Play / Stop"):
    st.session_state['is_running'] = not st.session_state['is_running']

st.write(f"Interval: {interval:.2f} seconds.")

# JavaScript for controlling sound looping
js_code = f"""
<script>
var sound = new Audio("data:audio/wav;base64,{sound_base64}");
var intervalMs = {interval * 1000}; // milliseconds
var timer = null;

function startSound() {{
    if (!timer) {{
        sound.currentTime = 0;
        sound.play();
        timer = setInterval(() => {{
            sound.currentTime = 0;
            sound.play();
        }}, intervalMs);
    }}
}}

function stopSound() {{
    if (timer) {{
        clearInterval(timer);
        timer = null;
        sound.pause();
        sound.currentTime = 0;
    }}
}}

if ({str(st.session_state['is_running']).lower()}) {{
    startSound();
}} else {{
    stopSound();
}}
</script>
"""

# Embed the JavaScript
st.components.v1.html(js_code)