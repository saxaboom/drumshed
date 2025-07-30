import streamlit as st
import os
import base64

# Initialize session state
if "is_running" not in st.session_state:
    st.session_state['is_running'] = False

# Load sound files
sound_folder = "./sounds"
sound_files = [f for f in os.listdir(sound_folder) if f.endswith(('.wav', '.mp3', '.ogg'))]
selected_sound = st.selectbox("Select a sound (short click recommended)", sound_files)
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

# Toggle Play/Stop
if st.button("Play / Stop"):
    st.session_state['is_running'] = not st.session_state['is_running']

st.write(f"Interval: {interval:.2f} seconds.")

# JavaScript code for precise one-shot clicks
js_code = f"""
<script>
// Initialize AudioContext
const ctx = new (window.AudioContext || window.webkitAudioContext)();

// Decode the sound buffer once
const soundDataUrl = "data:audio/wav;base64,{sound_base64}";
let buffer = null;

// Load and decode the sound
fetch(soundDataUrl)
  .then(res => res.arrayBuffer())
  .then(arrayBuffer => ctx.decodeAudioData(arrayBuffer))
  .then(decodedBuffer => {{
    buffer = decodedBuffer;
    if ({str(st.session_state['is_running']).lower()}) {{
      startMetronome();
    }}
  }});

// Variables for scheduling
let scheduleId = null;
const intervalSeconds = {interval};
let isPlaying = false;

// Function to play a single click
function playClick() {{
  if (!buffer) return;
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.connect(ctx.destination);
  source.start();
}}

// Function to start scheduling clicks
function startMetronome() {{
  if (scheduleId || !buffer) return;
  if (ctx.state === 'suspended') {{
    ctx.resume().then(() => scheduleNext());
  }} else {{
    scheduleNext();
  }}
}}

// Schedule the next click
function scheduleNext() {{
  if (!{str(st.session_state['is_running']).lower()}) return;
  // Play click immediately
  playClick();
  // Schedule next click
  scheduleId = setTimeout(() => {{
    scheduleNext();
  }}, intervalSeconds * 1000);
}}

// Function to stop scheduling
function stopMetronome() {{
  clearTimeout(scheduleId);
  scheduleId = null;
}}

// React to toggle state
if ({str(st.session_state['is_running']).lower()}) {{
  startMetronome();
}} else {{
  stopMetronome();
}}
</script>
"""

# Render the HTML/JS
st.components.v1.html(js_code, height=0, width=0)