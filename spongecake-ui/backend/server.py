import logging
import subprocess
import os
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

def kill_process_on_port(port):
    """
    A quick hacky way to free up 'port' on macOS/Linux by killing
    any processes listening on that port.
    NOTE: This won't work on Windows without a different command.
    """
    try:
        # lsof -t -i :PORT returns the PIDs. xargs kill -9 kills them forcibly.
        os.system(f"lsof -t -i tcp:{port} | xargs kill -9 2> /dev/null")
        logging.info(f"Killed any process using TCP port {port}")
    except Exception as e:
        logging.warning(f"Failed to kill process on port {port}: {e}")

def start_novnc_server(
    novnc_path="/Users/terrell/Coding Projects/spongecake/spongecake-ui/noVNC-1.6.0",
    port="6080",
    vnc_host="localhost",
    vnc_port="5900"
):
    """
    Launch websockify with noVNC as a background process.
    """
    # First kill anything listening on 6080 to avoid "Address already in use"
    kill_process_on_port(port)

    cmd = [
        "python", "-m", "websockify",
        "--web", novnc_path,
        str(port),
        f"{vnc_host}:{vnc_port}"
    ]
    process = subprocess.Popen(cmd)
    logging.info(f"NoVNC process started on port {port} (PID={process.pid})")
    return process

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
    desktop = Desktop(name="computer_use_agent")
    container = desktop.start()
    logs.append(f"🍰 Container started: {container}")

    # 2) Start noVNC
    novnc_process = start_novnc_server(
        novnc_path="/Users/terrell/Coding Projects/spongecake/spongecake-ui/noVNC-1.6.0",
        port="6080",
        vnc_host="localhost",
        vnc_port=str(desktop.vnc_port)
    )

    logs.append(f"Started noVNC server on http://localhost:6080/vnc.html with vnc_port {desktop.vnc_port}")
    return logs

def run_agent_action(user_prompt, auto_mode=False):
    """
    Actually run the agent logic in the Spongecake Desktop.
    Returns a list of log messages.
    """
    logs = []
    # Ensure container is running
    logs = start_container_if_needed(logs)

    logs.append("\n👾 Performing desktop action...")

    formatted_prompt = f"""
    {user_prompt} 
    If a user mentioned going to a website, always start by trying to go directly to the URL or using Bing instead of going to Google first.
    """

    agent_response = None

    # Run the agent in auto or interactive mode
    try:
        if auto_mode:
            status, data = desktop.action(input_text=formatted_prompt, ignore_safety_and_input=True)
        else:
            status, data = desktop.action(input_text=formatted_prompt, ignore_safety_and_input=False)

        if status == AgentStatus.ERROR:
            logs.append(f"❌ Error in agent action: {data}")
            agent_response = None
        else:
            logs.append(f"✅ Agent status: {status}")
            agent_response = str(data[0].content[0].text)
    except Exception as exc:
        error_msg = f"❌ Exception while running action: {exc}"
        logs.append(error_msg)
        logging.error(error_msg, exc_info=True)  # <-- This logs full traceback

    logs.append("Done.\n")
    return {
        "logs": logs,
        "agent_response": agent_response
    }

@app.route("/api/start-container", methods=["POST"])
def api_start_container():
    """
    POST /api/start-container
    Ensures the container + noVNC is running.
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
    messages = data.get("messages", "")
    auto_mode = data.get("auto_mode", False)
    result = run_agent_action(messages, auto_mode)
    return jsonify(result)

if __name__ == "__main__":
    # Run Flask on port 5000 by default
    app.run(host="0.0.0.0", port=5000, debug=True)
