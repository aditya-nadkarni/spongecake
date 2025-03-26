# data_entry_example.py
import logging
from time import sleep
from dotenv import load_dotenv
from spongecake import Desktop, AgentStatus
import subprocess

# Configure logging - most logs in the SDK are INFO level logs
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

load_dotenv()

result = [None]

# -------------------------
# Handlers for desktop agent statuses
# -------------------------

def complete_handler(data):
        """COMPLETE -- Handle successful task data (just print out success message in this case)"""
        print("\n✅ Task completed successfully!")
        result[0] = data
    
def needs_input_handler(messages):
    """NEEDS_INPUT -- Get input from the user, and pass it back to `action`"""
    for msg in messages:
        if hasattr(msg, "content"):
            text_parts = [part.text for part in msg.content if hasattr(part, "text")]
            print(f"\n💬 Agent asks: {' '.join(text_parts)}")

    user_says = input("Enter your response (or 'exit'/'quit'): ").strip()
    if user_says.lower() in ("exit", "quit"):
        print("Exiting as per user request.")
        result[0] = None  # Just return None when user exits
        return None  # Return None to indicate no further action
    return user_says  # Return the user input to continue

def needs_safety_check_handler(safety_checks, pending_call):
    """NEEDS_SAFETY_CHECK -- Have the user acknowledge the safety checks, and pass it back to `action`"""
    print("\n")
    for check in safety_checks:
        if hasattr(check, "message"):
            print(f"☢️  Pending Safety Check: {check.message}")

    print("🔔 Please acknowledge the safety check(s) in order to proceed with the computer call.")
    ack = input("Type 'ack' to confirm, or 'exit'/'quit': ").strip().lower()
    if ack in ("exit", "quit"):
        print("Exiting as per user request.")
        result[0] = None  # Just return None when user exits
        return False  # Don't proceed
    if ack == "ack":
        print("Acknowledged. Proceeding with the computer call...")
        return True  # Proceed with the call
    return False  # Don't proceed by default
    
def error_handler(error_message):
    """ERROR -- Handle errors (just print it out in this case)"""
    print(f"😱 ERROR: {error_message}")
    result[0] = None  # Just return None on error


# -------------------------
# Main
# -------------------------

def main():
    # Start up an isolated desktop. Edit desktop name, and docker_image if needed
    desktop = Desktop(name="newdesktop")
    container = desktop.start()
    print("🍰 spongecake container started:", container)
    print("...\n")

    # Open VNC connection to see the desktop, password is 'secret' (only works on mac)
    try:
        print('Attempting to open VNC connection to view Mac desktop, password is "secret"...')
        subprocess.run(["open", f"vnc://localhost:{desktop.vnc_port}"], check=True)
    except Exception as e:
        print(f"❌ Failed to open VNC connection: {e}")

    
    try:
        print(
            "\n👾 Performing desktop action... see output_image.png to see screenshots "
            "OR connect to the VNC server to view actions in real time"
        )

        
        user_prompt = f"""
            # AGENT INSTRUCTIONS #
            Go to https://www.cbp.gov/sites/default/files/assets/documents/2023-Nov/CBP%20Form%207501.pdf

            # DATA FIELDS #
            For filer code, enter '12345'
            For entry type, enter '01'
            For summary date, enter '3/21/2025'
            For port code, enter '23'
            For mode of transport, enter 'Vessel'
            For ultimate consignee name, enter 'Desport Apparel' 

            # INTERACTION INSTRUCTIONS # 
            YOU SHOULD ONLY NEED TO SCROLL DOWN OR CLICK OR TYPE. NEVER DO ANYTHING ELSE

            # STOPPING CONDITION # 
            You are STRICTLY ONLY done until you have entered in all of the data fields from above 

        """

        auto_mode = False
        # If auto_mode is enabled, use the ignore_safety_and_input flag
        if auto_mode:
            status, data = desktop.action(input_text=user_prompt, ignore_safety_and_input=True)
            # In auto mode, we should get a COMPLETE or ERROR status directly
            if status == AgentStatus.ERROR:
                print(f"❌ error in auto mode: {data}")
            result[0] = data
        else:
            # ACTION: Start the action chain with the initial command and all handlers
            status, data = desktop.action(
                input_text=user_prompt,
                complete_handler=complete_handler,
                needs_input_handler=needs_input_handler,
                needs_safety_check_handler=needs_safety_check_handler,
                error_handler=error_handler
            )

        # Show final results
        final_result = result[0]
        if final_result is None:
            print("\n⛔️ Task was interrupted or encountered an error\n")
        elif hasattr(final_result, "output_text"):
            print(f"📩 Result: {final_result.output_text}\n")
        else:
            print("Done.\n")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        print("\nExiting gracefully...")

    # Clean up the container. Optionally, leave the container running and connect to it again when needed. 
    # print("Stopping and removing container...")
    # desktop.stop()
    print("🍰")


if __name__ == "__main__":
    main()
