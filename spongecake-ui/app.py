import streamlit as st
import sys, os
import subprocess

# 1) Kill the overlay
HIDE_OVERLAY_CSS = """
<style>
/* Hide the semi-transparent overlay and spinner container. */
.blocker,
[data-testid="stModal"],
.overlay,
.stApp > [data-testid="stToolbar"] + div [data-testid="stBlock"],
.stApp > [data-testid="stToolbar"] + div [role="progressbar"] {
  display: none !important;
}

/* Force widgets back to enabled state. */
[data-testid="stAppViewContainer"] [disabled],
[data-testid="stAppViewContainer"] .stDisabled {
  pointer-events: auto !important;
  opacity: 1 !important;
  cursor: pointer !important;
}
</style>
"""

# 2) Add some JS that forcibly removes the 'disabled' attribute from any elements
FORCE_ENABLE_JS = """
<script>
document.addEventListener('DOMContentLoaded', function() {
  // This runs once the DOM is loaded
  const enableElements = () => {
    document.querySelectorAll('[disabled]').forEach(el => {
      el.removeAttribute('disabled');
    });
  };
  enableElements();

  // Optionally keep trying every second, just in case Streamlit re-adds 'disabled':
  setInterval(enableElements, 1000);
});
</script>
"""

st.set_page_config(page_title="Desktop Agent UI", layout="wide")
st.markdown(HIDE_OVERLAY_CSS, unsafe_allow_html=True)
st.markdown(FORCE_ENABLE_JS, unsafe_allow_html=True)




sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from examples.dinner_res import run_agent_action, start_novnc_server
from spongecake import Desktop

# Title up top
st.title("Desktop Agent UI")

########################################
# Set up columns for side-by-side layout
########################################
left_col, right_col = st.columns([1, 2], gap="large")


#
# LEFT COLUMN: Input prompts, buttons, logs
#
with left_col:
    # Session state variables to track steps
    if "container_started" not in st.session_state:
        st.session_state["container_started"] = False
    if "vnc_shown" not in st.session_state:
        st.session_state["vnc_shown"] = False
    if "agent_done" not in st.session_state:
        st.session_state["agent_done"] = False

    # User prompt and auto-mode checkbox
    user_prompt = st.text_input("Enter your prompt:")
    auto_mode = st.checkbox("Auto mode", value=True)

    # Define a simple input callback for interactive mode
    def input_callback():
        return st.text_input("Agent needs additional input:")

    # ------------------------
    # STEP 1: Start container & noVNC
    # ------------------------
    if not st.session_state["container_started"]:
        if st.button("Start Desktop + noVNC"):
            # 1) Start the Spongecake desktop container
            st.session_state["desktop"] = Desktop(name="dinner_reservation")
            container = st.session_state["desktop"].start()
            st.write(f"🍰 Container started: {container}")

            # 2) Launch noVNC in the background
            novnc_process = start_novnc_server(
                novnc_path="/Users/terrell/Coding Projects/spongecake/spongecake-ui/noVNC-1.6.0",
                port="6080",
                vnc_host="localhost",
                vnc_port=str(st.session_state["desktop"].vnc_port),
            )
            st.write("Started noVNC server on http://localhost:6080/vnc.html")

            st.session_state["container_started"] = True
    else:
        st.success("Container + noVNC are started!")

    # ------------------------
    # STEP 2: Show VNC Viewer
    # ------------------------
    if st.session_state["container_started"] and not st.session_state["vnc_shown"]:
        # Provide a button to reveal the VNC viewer
        if st.button("Open VNC Viewer"):
            st.session_state["vnc_shown"] = True

    # Optional “Manual Refresh” button
    if st.session_state["vnc_shown"]:
        if st.button("Manual Refresh"):
            st.experimental_rerun()

    # ------------------------
    # STEP 3: Run the Agent
    # ------------------------
    if st.session_state["vnc_shown"] and not st.session_state["agent_done"]:
        # Let the user click a button to run the agent
        if st.button("Run Agent Action"):
            st.write("## Agent Log")
            st.write(f"Starting agent with prompt: {user_prompt}")

            if "desktop" not in st.session_state:
                st.error("Desktop not started. Please start the container first.")
            else:
                # Actually run the agent
                if auto_mode:
                    st.write("Auto mode enabled. Bypassing safety checks...")
                    result, log = run_agent_action(user_prompt, auto_mode=True)
                else:
                    st.write("Interactive mode: awaiting user input...")
                    result, log = run_agent_action(
                        user_prompt, auto_mode=False, input_callback=input_callback
                    )

                # Display the log
                for msg in log:
                    st.write(msg)

                # Display final result
                st.write("### Final Result")
                st.write(result)

                st.session_state["agent_done"] = True

    elif st.session_state["agent_done"]:
        st.success("The agent has finished its task!")

#
# RIGHT COLUMN: Display the VNC iframe if shown
#
with right_col:
    if st.session_state.get("vnc_shown", False):
        st.subheader("VNC Viewer")

        # If you want to always show the default port from the Desktop object:
        default_vnc_url = (
            "http://localhost:6080/vnc.html?"
            f"host=localhost&port={st.session_state['desktop'].vnc_port}&password=secret"
            "&toolbar=0&autoconnect=true"
        )
        vnc_url = st.text_input("noVNC URL:", default_vnc_url, key="vnc_url")
        
        # Just show the iframe, no auto-refresh
        st.components.v1.html(
            f"""
            <iframe id="vnc_frame" src="{vnc_url}"
                    width="1024" height="768" frameborder="0"></iframe>
            """,
            height=768,
            width=1024,
        )
    else:
        st.info("VNC Viewer not opened yet. Click 'Open VNC Viewer' on the left.")
