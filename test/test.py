# test_script.py
from time import sleep
from dotenv import load_dotenv
from spongecake import Desktop
from spongecake.agent import AgentStatus
load_dotenv()

def handle_action(desktop, action_input, auto_mode=False):
    """
    Standalone function to handle the agent action loop. This function demonstrates how to use
    the new state-based API from outside the SDK.
    
    Args:
        desktop: A Desktop instance
        action_input: The initial command to send to the agent
        auto_mode: If True, automatically handle safety checks and input requests without user interaction
        
    Returns:
        The final result of the action
    """
    print(
        "Performing desktop action... see output_image.png to see screenshots "
        "OR connect to the VNC server to view actions in real time"
    )

    # Start the action chain with the initial command
        # If auto_mode is enabled, use the ignore_safety_and_input flag
    if auto_mode:
        print("Running in auto mode - safety checks and input requests will be handled automatically")
        status, data = desktop.action(input_text=action_input, ignore_safety_and_input=True)
        # In auto mode, we should get a COMPLETE or ERROR status directly
        if status == AgentStatus.ERROR:
            print(f"Error in auto mode: {data}")
        return data

    # Start the action chain with the initial command in interactive mode
    status, data = desktop.action(input_text=action_input)

    while True:
        # Handle different statuses
        if status == AgentStatus.NEEDS_INPUT:
            # Agent needs more input
            messages = data
            for msg in messages:
                if hasattr(msg, "content"):
                    text_parts = [part.text for part in msg.content if hasattr(part, "text")]
                    print(f"Agent asks: {' '.join(text_parts)}")

            user_says = input("Enter your response (or 'exit'/'quit'): ").strip().lower()
            if user_says in ("exit", "quit"):
                print("Exiting as per user request.")
                return desktop.get_agent().current_response

            # Call action again with the user input
            status, data = desktop.action(input_text=user_says)
            continue

        elif status == AgentStatus.NEEDS_SAFETY_CHECK:
            # Safety checks need acknowledgment
            safety_checks = data["safety_checks"]
            for check in safety_checks:
                if hasattr(check, "message"):
                    print(f"Pending Safety Check: {check.message}")

            print("Please acknowledge the safety check(s) in order to proceed with the computer call.")
            ack = input("Type 'ack' to confirm, or 'exit'/'quit': ").strip().lower()
            if ack in ("exit", "quit"):
                print("Exiting as per user request.")
                return desktop.get_agent().current_response
            if ack == "ack":
                print("Acknowledged. Proceeding with the computer call...")
                # Call action again with acknowledged safety checks
                status, data = desktop.action(acknowledged_safety_checks=True)
                continue

        elif status == AgentStatus.ERROR:
            # An error occurred
            print(f"Error: {data}")
            return desktop.get_agent().current_response

        # If we get here, the action is complete
        return data

def main():
    # Start up an isolated desktop. Edit desktop name, and docker_image if needed
    desktop = Desktop(name="newdesktop")
    container = desktop.start()
    print("🍰 spongecake container started:", container)

    # Example usage
    print('What would you like your agent to do? Below are some examples or write your own:')
    print('> Find me flights from San Francisco to Tokyo')
    print('> Fill out the form at https://bit.ly/3RiWH76, CBP\'s website')
    print('> Go to Youtube.com and search for a video titled "Python Tutorial"')
    print('\n>prompt: ', end="")
    user_prompt = input("").strip()
    
    # Check if auto mode is requested
    auto_mode = False
    if user_prompt.lower().startswith("auto:"):
        auto_mode = True
        user_prompt = user_prompt[5:].strip()
        print("Auto mode enabled - will handle all interactions automatically")
    
    try:
        # Use the standalone handle_action function with auto_mode flag
        result = handle_action(desktop, user_prompt, auto_mode)
        if result:
            if hasattr(result, "output_text"):
                print(f"\n<*> Result: {result.output_text}\n")
            else:
                print(f"\n<*> Task completed successfully\n")
    except Exception as e:
        print(f"❌An error occurred: {e}")
        print("\nExiting gracefully...")

    # Clean up the container. Optionally, leave the container running and connect to it again when needed. 
    print("Stopping and removing container...")
    desktop.stop()


if __name__ == "__main__":
    main()
