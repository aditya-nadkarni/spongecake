# dinner_res_refactored.py
import logging
from time import sleep
from dotenv import load_dotenv
from spongecake import Desktop, AgentStatus
import subprocess
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

load_dotenv()

def start_novnc_server(novnc_path="/path/to/noVNC", port="6080", vnc_host="localhost", vnc_port="5900"):
    """
    Launch websockify with noVNC as a background process.
    """
    cmd = [
        "python", "-m", "websockify",
        "--web", novnc_path,
        port,
        f"{vnc_host}:{vnc_port}"
    ]
    # Start the process without blocking the main thread.
    process = subprocess.Popen(cmd)
    return process

def complete_handler(data, log):
    """Handle a successful task completion."""
    log.append("✅ Task completed successfully!")
    return data

def needs_input_handler(messages, log, input_callback):
    """Handle a request for user input using a callback to obtain the input."""
    for msg in messages:
        if hasattr(msg, "content"):
            text_parts = [part.text for part in msg.content if hasattr(part, "text")]
            log.append(f"💬 Agent asks: {' '.join(text_parts)}")
    # Use the provided callback to get the response
    user_says = input_callback()
    if user_says.lower() in ("exit", "quit"):
        log.append("Exiting as per user request.")
        return None
    return user_says

def needs_safety_check_handler(safety_checks, pending_call, log, input_callback):
    """Handle safety checks by logging messages and obtaining acknowledgment via a callback."""
    for check in safety_checks:
        if hasattr(check, "message"):
            log.append(f"☢️  Pending Safety Check: {check.message}")
    log.append("🔔 Please acknowledge the safety check(s) to proceed with the computer call.")
    ack = input_callback()
    if ack.lower() in ("exit", "quit"):
        log.append("Exiting as per user request.")
        return False
    if ack.lower() == "ack":
        log.append("Acknowledged. Proceeding with the computer call...")
        return True
    return False

def error_handler(error_message, log):
    """Handle errors by logging them."""
    log.append(f"😱 ERROR: {error_message}")
    return None

def run_agent_action(user_prompt, auto_mode=True, input_callback=None):
    """
    Run the desktop agent action.
    
    Parameters:
      user_prompt (str): The command or instruction for the agent.
      auto_mode (bool): If True, bypass safety and input prompts.
      input_callback (callable): A function that returns user input when called. 
                                 Required if auto_mode is False.
    
    Returns:
      tuple: (final_result, log) where final_result is the outcome from the agent action,
             and log is a list of strings representing progress messages.
    """
    log = []
    result = [None]


    try:
        # Start the desktop container
        desktop = Desktop(name="dinner_reservation")
        container = desktop.start()
        log.append(f"🍰 spongecake container started: {container}")

        # Attempt to open the VNC viewer
        try:
            log.append('Attempting to open VNC connection to view Mac desktop, password is "secret"...')
            subprocess.run(["open", f"vnc://localhost:{desktop.vnc_port}"], check=True)
        except Exception as e:
            log.append(f"❌ Failed to open VNC connection: {e}")
        
        novnc_process = start_novnc_server(novnc_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "spongecake-ui", "noVNC-1.6.0"), port="6080", vnc_host="localhost", vnc_port=str(desktop.vnc_port))
        log.append("Started noVNC server on http://localhost:6080/vnc.html")

        log.append("\n👾 Performing desktop action...")

        # Prepare the agent prompt
        formatted_prompt = f"""
    # AGENT GOAL #
    Book a reservation for Serafina Restaurant in San Francisco

    # STEP-BY-STEP INSTRUCTIONS #

    Go to https://www.opentable.com/s?dateTime=2025-03-28T19%3A00%3A00&covers=2&latitude=37.7829745&longitude=-122.4182459&term=serafina%20san%20francisco&shouldUseLatLongSearch=true&originCorrelationId=6aa09c09-669a-4a13-970f-1aa8bd3f070c&corrid=c3ef7403-d781-45cb-b75d-5b2e569aa6cb&intentModifiedTerm=serafina&metroId=4&originalTerm=serafina%20san%20francisco&pinnedRid=1108642&queryUnderstandingType=location&sortBy=web_conversion
    Book at the earliest being 7:30pm and only on Friday.

    # INTERACTION INSTRUCTIONS # 
    YOU SHOULD ONLY NEED TO SCROLL DOWN OR CLICK. NEVER DO ANYTHING ELSE.
    WHEN YOU SCROLL DOWN, YOU SHOULD ALWAYS DO IT AT STRICTLY MOST ONCE ON A GIVEN PAGE.

    # ROADBLOCKS #
    If you encounter a CAPTCHA, you should ALWAYS ask the user to provide the CAPTCHA solution 
    or take over manually (via your VNC viewer).

    # STOPPING CONDITION # 
    You are only done once you have booked the reservation. NEVER ASK ME QUESTIONS.
    """
        # Execute the agent action
        if auto_mode:
            status, data = desktop.action(input_text=formatted_prompt, ignore_safety_and_input=True)
            if status == AgentStatus.ERROR:
                log.append(f"❌ Error in auto mode: {data}")
            result[0] = data
        else:
            if input_callback is None:
                raise ValueError("input_callback must be provided in interactive mode.")
            status, data = desktop.action(
                input_text=formatted_prompt,
                complete_handler=lambda data: complete_handler(data, log),
                needs_input_handler=lambda messages: needs_input_handler(messages, log, input_callback),
                needs_safety_check_handler=lambda safety_checks, pending_call: needs_safety_check_handler(safety_checks, pending_call, log, input_callback),
                error_handler=lambda error_message: error_handler(error_message, log)
            )
            result[0] = data

        # Log the final outcome
        final_result = result[0]
        if final_result is None:
            log.append("\n⛔️ Task was interrupted or encountered an error\n")
        elif hasattr(final_result, "output_text"):
            log.append(f"📩 Result: {final_result.output_text}\n")
        else:
            log.append("Done.\n")
    except Exception as e:
        log.append(f"❌ An error occurred: {e}")
        log.append("\nExiting gracefully...")

    # Optionally, stop the container if needed:
    # desktop.stop()
    log.append("🍰")
    return result[0], log

if __name__ == "__main__":
    # Example usage in auto mode
    final_result, log_messages = run_agent_action("Dummy prompt", auto_mode=True)
    for msg in log_messages:
        print(msg)
