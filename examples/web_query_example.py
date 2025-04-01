# example.py
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

    # Tool Calls
    def get_wikipedia_elements(searchText):
        '''Grabs the entire text content of a Wikipedia page - omits any section headers'''
        logging.info("    [TOOL CALL]: Grabbing relevant context from page...")
        content = desktop.get_page_html(query=f"""
            let container = document.querySelector('#bodyContent');
            if (!container) {{
                return null;
            }}

            // Select all <p>, <section>, and <h1>-<h6> tags within #bodyContent
            let elements = container.querySelectorAll('p, section, h1, h2, h3, h4, h5, h6');

            // Filter by whether the element's text contains the search string
            let matchingElements = Array.from(elements).filter((el) => {{
                // You can adjust includes() to be case-insensitive if needed
                // by converting both to a single case
                return el.textContent.includes("{searchText}");
            }});

            // Return the combined outerHTML of the matching elements
            return matchingElements.map((el) => el.outerHTML).join('\\n');
        """)
        return content
    
    # Create tool call definitions
    custom_tools = [
        {
            "type": "function",
            "name": "get_wikipedia_elements",
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

    # Call the desktop agent
    question = "When was GPT-4.5 released?"
    print(f"\n --> 🙋‍♀️ Question: {question}")
    status, data = desktop.action(
        input_text=f"Go to the Wikipedia page for OpenAI, and answer the question: {question}.\nOnce you are on the Wikipedia page, DO NOT scroll on the Wikipedia page or use Ctrl+F to search.",
        complete_handler=complete_handler,
        needs_input_handler=needs_input_handler,
        needs_safety_check_handler=needs_safety_check_handler,
        error_handler=error_handler,
        # Add tools
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

    # Clean up the container. Optionally, leave the container running and connect to it again when needed. 
    # print("Stopping and removing container...")
    # desktop.stop()
    print("🍰")


if __name__ == "__main__":
    main()
