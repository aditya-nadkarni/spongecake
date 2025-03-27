# server.py
import logging
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from spongecake import Desktop, AgentStatus
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
load_dotenv()

app = Flask(__name__)
CORS(app)

# We'll keep a global reference to the Desktop() object
desktop = None

########################################
# 1) HELPER: Start noVNC
########################################
def start_novnc_server(novnc_path="/Users/terrell/Coding Projects/spongecake/spongecake-ui/noVNC-1.6.0", port="6080", vnc_host="localhost", vnc_port="5900"):
    """
    Launch websockify with noVNC as a background process.
    Example:
        cmd = [
            "python", "-m", "websockify",
            "--web", "/path/to/noVNC",
            "6080",
            "localhost:5900"
        ]
    """
    cmd = [
        "python", "-m", "websockify",
        "--web", novnc_path,
        port,
        f"{vnc_host}:{vnc_port}"
    ]
    process = subprocess.Popen(cmd)
    return process

########################################
# 2) HELPER: Start container if needed
########################################
def start_container_if_needed(logs=None):
    """
    Creates a Desktop() object if we don't already have one.
    Starts the container + noVNC server.
    """
    global desktop
    if logs is None:
        logs = []

    if desktop is not None:
        logs.append("Container already started.")
        return logs

    # 1) Start the Spongecake Desktop container
    desktop = Desktop(name="dinner_reservation")
    container = desktop.start()
    logs.append(f"🍰 Container started: {container}")

    # 2) Start noVNC
    novnc_process = start_novnc_server(
        novnc_path="/Users/terrell/Coding Projects/spongecake/spongecake-ui/noVNC-1.6.0",
        port="6080",
        vnc_host="localhost",
        vnc_port=str(desktop.vnc_port)
    )
    logs.append("Started noVNC server on http://localhost:6080/vnc.html")

    return logs

########################################
# 3) HELPER: Run the agent action
########################################
def run_agent_action(user_prompt, auto_mode=True):
    """
    Actually run the agent logic in the Spongecake Desktop.
    Returns a list of log messages.
    """
    logs = []
    # Ensure container is running
    logs = start_container_if_needed(logs)

    # Attempt to open macOS VNC in case user wants to see it
    try:
        logs.append('Attempting to open VNC connection (password is "secret")...')
        subprocess.run(["open", f"vnc://localhost:{desktop.vnc_port}"], check=True)
    except Exception as e:
        logs.append(f"❌ Failed to open VNC connection: {e}")

    logs.append("\n👾 Performing desktop action...")

    formatted_prompt = f"""
    # AGENT GOAL #
    {user_prompt}

    # STOPPING CONDITION # 
    You are only done once you have booked the reservation.
    """

    # Run the agent in auto or interactive mode
    try:
        if auto_mode:
            status, data = desktop.action(input_text=formatted_prompt, ignore_safety_and_input=True)
        else:
            # For simplicity, we’ll also do ignore_safety_and_input if you're not handling manual input
            # If you truly need interactive prompts, see the original dinner_res_refactored approach
            status, data = desktop.action(input_text=formatted_prompt, ignore_safety_and_input=False)

        if status == AgentStatus.ERROR:
            logs.append(f"❌ Error in agent action: {data}")
        else:
            logs.append(f"✅ Agent status: {status}")
            logs.append(f"Agent data: {data}")
    except Exception as exc:
        logs.append(f"❌ Exception while running action: {exc}")

    logs.append("Done.\n")
    return logs

########################################
# 4) FLASK ROUTES
########################################
@app.route("/api/start-container", methods=["POST"])
def api_start_container():
    """
    POST /api/start-container
    Simply ensures the container + noVNC is running.
    """
    logs = start_container_if_needed()
    return jsonify({"logs": logs})

@app.route("/api/run-agent", methods=["POST"])
def api_run_agent():
    """
    POST /api/run-agent
    JSON body: { "userPrompt": "...", "autoMode": true/false }
    """
    data = request.get_json()
    user_prompt = data.get("userPrompt", "")
    auto_mode = data.get("autoMode", True)

    logs = run_agent_action(user_prompt, auto_mode)
    return jsonify({"logs": logs})

########################################
# 5) MAIN ENTRY
########################################
if __name__ == "__main__":
    # Run Flask on port 5000 by default
    app.run(host="0.0.0.0", port=5000, debug=True)
