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
    desktop = Desktop(name="web_query_example_desktop")
    container = desktop.start()

    # Open VNC connection to see the desktop, password is 'secret' (only works on mac)
    try:
        print('Attempting to open VNC connection to view Mac desktop, password is "secret"...')
        subprocess.run(["open", f"vnc://localhost:{desktop.vnc_port}"], check=True)
    except Exception as e:
        print(f"❌ Failed to open VNC connection: {e}")

    # Function definition
    def get_wikipedia_elements(searchText):
        '''Grabs the entire text content of a Wikipedia page - omits any section headers'''
        logging.info("    [TOOL CALL]: Grabbing relevant context from page...")

        # Use the built-in get_page_html function to grab the elements we want to return to the agent
        # Note: Its entirely possible to provide the full page as context, but the agent often gets lost in the mix - The more specific the query the better
        content = desktop.get_page_html(query=f"""
            let container = document.querySelector('#bodyContent');
            if (!container) {{
                return null;
            }}
            let elements = container.querySelectorAll('p, section, h1, h2, h3, h4, h5, h6');
            let matchingElements = Array.from(elements).filter((el) => {{
                return el.textContent.includes("{searchText}");
            }});
            return matchingElements.map((el) => el.outerHTML).join('\\n');
        """)
        return content
    
    # Create tool call definitions
    custom_tools = [
        {
            "type": "function",
            "name": "get_wikipedia_elements",
            # For the purposes of this example, we will instruct the agent to always use this function
            "description": "ALWAYS use this function to grab elements of a wikipedia page that contain a certain search term to answer questions, allowing you to extract relevant information WITHOUT scrolling.\n **IMPORTANT**: ONLY use this function when you are on a Wikipedia page",
            "parameters": {
                "type": "object",
                "properties": {
                    "searchText": {
                        "type": "string",
                        "description": "Search query to find elements on the Wikipedia containing the string"
                    }
                },
                "required": ["searchText"]
            }
        }
    ]

    # Create a function map to allow the desktop agent to call the appropriate function
    function_map = {
        "get_wikipedia_elements": get_wikipedia_elements
    }

    try:
        # Call the desktop agent
        question = "When was GPT-4.5 released?"
        print(f"\n --> 🙋‍♀️ Question: {question}")
        status, data = desktop.action(
            input_text=f"Go directly to the Wikipedia page for OpenAI (do not use Google), and answer the question: {question}.\nOnce you are on the OpenAI Wikipedia page, DO NOT scroll on the Wikipedia page.", # We'll explicitly instruc the agent not to scroll. Although this is for the purposes of this example, the agent is generally pretty bad at scrolling..
            complete_handler=complete_handler,
            needs_input_handler=needs_input_handler,
            needs_safety_check_handler=needs_safety_check_handler,
            error_handler=error_handler,
            # Add tools and function map
            tools=custom_tools,
        function_map=function_map,
        )
    
        # Show final results
        final_result = result[0]
        if final_result is None:
            print("\n⛔️ Task was interrupted or encountered an error\n")
        elif hasattr(final_result, "output_text"):
            print(f"📩 Answer: {final_result.output_text}\n")
        else:
            print("Done.\n")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        print("\nExiting gracefully...")

    # Clean up the container. Optionally, leave the container running and connect to it again when needed. 
    print("Stopping and removing container...")
    desktop.stop()
    print("🍰")


if __name__ == "__main__":
    main()
