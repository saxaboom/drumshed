import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Auto Theme Detection", layout="wide")

st.title("Auto Detect System Theme")

# JavaScript for detecting system theme
html_code = """
<script>
(function() {
    const theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'Dark' : 'Light';
    // Send message to Streamlit
    const message = {type: 'theme', theme: theme};
    window.parent.postMessage(message, '*');
})();
</script>
"""

# Display the HTML with JS
components.html(html_code, height=0)

# Use a hidden element or a workaround to get the theme
# Since direct communication isn't straightforward, we can use a workaround:
# Re-render the page and set the theme based on JavaScript detection

# Instead, we can suggest the user to refresh or set the theme manually if detection isn't perfect.

# For demonstration, let's just provide a button to simulate setting the theme
if "system_theme" not in st.session_state:
    # Default fallback
    st.session_state["system_theme"] = "Light"

# Button to refresh detection (simulate re-detect)
if st.button("Re-detect System Theme"):
    # The detection script runs again on refresh or re-render
    st.rerun()

# Show current theme
st.write(f"Detected system theme: {st.session_state['system_theme']}")

# Apply background based on detected theme
def set_bg_color(color):
    st.markdown(
        f"""
        <style>
        .reportview-container {{
            background-color: {color};
            color: {"white" if color != "#FFFFFF" else "black"};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Since real-time detection isn't straightforward without a custom component,
# you might need users to refresh after first load to apply the correct theme.

# For simplicity, let's let user select manually:
theme = st.selectbox("Select Theme", ["Light", "Dark"])

if theme == "Light":
    set_bg_color("#FFFFFF")
else:
    set_bg_color("#222222")