#!/usr/bin/env python3
"""
API Server for Spongecake

This lightweight web server runs inside the Docker container and exposes
desktop actions (click, scroll, type, etc.) through a REST API.
"""

import os
import sys
import json
import base64
import logging
import subprocess
from typing import Optional, Dict, Any, List, Union

# Set up FastAPI
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("spongecake-api")

# Initialize FastAPI app
app = FastAPI(
    title="Spongecake API",
    description="API for controlling the virtual desktop in the Spongecake container",
    version="0.1.0"
)

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request models
class ClickRequest(BaseModel):
    x: int
    y: int
    button: str = "left"

class ScrollRequest(BaseModel):
    x: int
    y: int
    scroll_x: int = 0
    scroll_y: int = 0

class KeypressRequest(BaseModel):
    keys: List[str]

class TypeRequest(BaseModel):
    text: str

class WaitRequest(BaseModel):
    seconds: float = 2.0

class ActionRequest(BaseModel):
    type: str
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[str] = None
    scroll_x: Optional[int] = None
    scroll_y: Optional[int] = None
    keys: Optional[List[str]] = None
    text: Optional[str] = None
    seconds: Optional[float] = None
    url: Optional[str] = None

# Helper functions to execute desktop actions
def execute_command(command: List[str]) -> str:
    """Execute a shell command and return its output."""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Command execution failed: {e.stderr}")

def click(x: int, y: int, button: str = "left") -> Dict[str, Any]:
    """Execute a click at the specified coordinates.
    
    Move the mouse to (x, y) and click the specified button.
    button can be 'left', 'middle', or 'right'.
    """
    logger.info(f"Clicking at ({x}, {y}) with {button} button")
    
    # Match the button mapping from Desktop class
    button_map = {
        "left": 1,
        "middle": 2,
        "wheel": 2,
        "right": 3
    }
    button_num = button_map.get(button.lower(), 1)
    
    logger.info(f"Action: click at ({x}, {y}) with button '{button}' -> mapped to {button_num}")
    command = ["xdotool", "mousemove", str(x), str(y), "click", str(button_num)]
    execute_command(command)
    
    return {"status": "success", "action": "click", "x": x, "y": y, "button": button}

def scroll(x: int, y: int, scroll_x: int = 0, scroll_y: int = 0) -> Dict[str, Any]:
    """Execute a scroll at the specified coordinates.
    
    Move to (x, y) and scroll horizontally (scroll_x) or vertically (scroll_y).
    Negative scroll_y -> scroll up, positive -> scroll down.
    Negative scroll_x -> scroll left, positive -> scroll right (button 6 or 7).
    """
    logger.info(f"Scrolling at ({x}, {y}) with delta (scroll_x={scroll_x}, scroll_y={scroll_y})")
    
    # First move to the position
    execute_command(["xdotool", "mousemove", str(x), str(y)])
    
    # Vertical scroll (button 4 = up, button 5 = down)
    if scroll_y != 0:
        button = "4" if scroll_y < 0 else "5"
        # Use a fixed number of clicks (3) as in the Desktop class
        for _ in range(3):
            execute_command(["xdotool", "click", button])
    
    # Horizontal scroll (button 6 = left, button 7 = right)
    if scroll_x != 0:
        button = "6" if scroll_x < 0 else "7"
        # Use a fixed number of clicks (3) as in the Desktop class
        for _ in range(3):
            execute_command(["xdotool", "click", button])
    
    return {
        "status": "success", 
        "action": "scroll", 
        "x": x, 
        "y": y, 
        "scroll_x": scroll_x, 
        "scroll_y": scroll_y
    }

def keypress(keys: List[str]) -> Dict[str, Any]:
    """Execute keypress(es).
    
    Press (and possibly hold) keys in sequence. Allows pressing
    Ctrl/Shift down, pressing other keys, then releasing them.
    Example: keys=["CTRL","F"] -> Ctrl+F
    """
    logger.info(f"Pressing keys: {keys}")
    
    ctrl_pressed = False
    shift_pressed = False
    
    for k in keys:
        # Handle special modifiers
        if k.upper() == 'CTRL':
            logger.info("    => holding down CTRL")
            execute_command(["xdotool", "keydown", "ctrl"])
            ctrl_pressed = True
        elif k.upper() == 'SHIFT':
            logger.info("    => holding down SHIFT")
            execute_command(["xdotool", "keydown", "shift"])
            shift_pressed = True
        # Check special keys
        elif k.lower() == "enter":
            execute_command(["xdotool", "key", "Return"])
        elif k.lower() == "space":
            execute_command(["xdotool", "key", "space"])
        else:
            # For normal alphabetic or punctuation
            lower_k = k.lower()  # xdotool keys are typically lowercase
            execute_command(["xdotool", "key", lower_k])

    # Release modifiers
    if ctrl_pressed:
        logger.info("    => releasing CTRL")
        execute_command(["xdotool", "keyup", "ctrl"])
    if shift_pressed:
        logger.info("    => releasing SHIFT")
        execute_command(["xdotool", "keyup", "shift"])
    
    return {"status": "success", "action": "keypress", "keys": keys}

def type_text(text: str) -> Dict[str, Any]:
    """Type text."""
    logger.info(f"Typing text: {text}")
    
    # Use --clearmodifiers to clear any stuck modifier keys
    execute_command(["xdotool", "type", "--clearmodifiers", text])
    
    return {"status": "success", "action": "type", "text": text}

def wait(seconds: float = 2.0) -> Dict[str, Any]:
    """Wait for the specified number of seconds."""
    logger.info(f"Waiting for {seconds} seconds")
    
    import time
    time.sleep(seconds)
    
    return {"status": "success", "action": "wait", "seconds": seconds}

def goto(url: str) -> Dict[str, Any]:
    """Open Firefox and navigate to the specified URL.
    
    Args:
        url: The URL to navigate to (e.g., "https://example.com")
    """
    logger.info(f"Navigating to URL: {url}")
    
    # Use firefox-esr with new-tab option and run in background
    execute_command(["bash", "-c", f"export DISPLAY=:99 && firefox-esr -new-tab {url} &"])
    
    return {"status": "success", "action": "goto", "url": url}

def take_screenshot() -> Dict[str, Any]:
    """Take a screenshot and return it as base64.
    
    Takes a screenshot of the current desktop.
    Returns the base64-encoded PNG screenshot as a string.
    """
    logger.info("Taking screenshot")
    
    try:
        # Use ImageMagick's import command to capture the screen
        # The command captures the root window and outputs PNG data to stdout
        # Then we pipe it to base64 to encode it
        result = execute_command([
            "bash", "-c", 
            "export DISPLAY=:99 && import -window root png:- | base64 -w 0"
        ])
        
        # The result is already base64-encoded
        base64_data = result.strip()
        
        return {
            "status": "success", 
            "action": "screenshot", 
            "screenshot": base64_data
        }
    except Exception as e:
        logger.error(f"Screenshot failed: {str(e)}")
        return {
            "status": "error",
            "action": "screenshot",
            "error": str(e)
        }

# API endpoints
@app.get("/")
async def root():
    """Root endpoint that returns basic information about the API."""
    return {
        "name": "Spongecake API",
        "version": "0.1.0",
        "description": "API for controlling the virtual desktop in the Spongecake container"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/click")
async def api_click(request: ClickRequest):
    """Click at the specified coordinates."""
    return click(request.x, request.y, request.button)

@app.post("/scroll")
async def api_scroll(request: ScrollRequest):
    """Scroll at the specified coordinates."""
    return scroll(request.x, request.y, request.scroll_x, request.scroll_y)

@app.post("/keypress")
async def api_keypress(request: KeypressRequest):
    """Execute keypress(es)."""
    return keypress(request.keys)

@app.post("/type")
async def api_type(request: TypeRequest):
    """Type text."""
    return type_text(request.text)

@app.post("/wait")
async def api_wait(request: WaitRequest):
    """Wait for the specified number of seconds."""
    return wait(request.seconds)

@app.get("/screenshot")
async def api_screenshot():
    """Take a screenshot and return it as base64."""
    return take_screenshot()

@app.post("/action")
async def api_action(action: ActionRequest):
    """Execute an action based on its type."""
    action_type = action.type
    
    if action_type == "click":
        if action.x is None or action.y is None:
            raise HTTPException(status_code=400, detail="Click action requires x and y coordinates")
        return click(action.x, action.y, action.button or "left")
    
    elif action_type == "scroll":
        if action.x is None or action.y is None:
            raise HTTPException(status_code=400, detail="Scroll action requires x and y coordinates")
        return scroll(action.x, action.y, action.scroll_x or 0, action.scroll_y or 0)
    
    elif action_type == "keypress":
        if not action.keys:
            raise HTTPException(status_code=400, detail="Keypress action requires keys")
        return keypress(action.keys)
    
    elif action_type == "type":
        if action.text is None:
            raise HTTPException(status_code=400, detail="Type action requires text")
        return type_text(action.text)
    
    elif action_type == "wait":
        return wait(action.seconds or 2.0)
    
    elif action_type == "screenshot":
        return take_screenshot()
        
    elif action_type == "goto":
        if action.url is None:
            raise HTTPException(status_code=400, detail="Goto action requires a URL")
        return goto(action.url)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")

if __name__ == "__main__":
    # Run the server
    port = int(os.environ.get("API_PORT", 8000))
    host = os.environ.get("API_HOST", "0.0.0.0")
    
    logger.info(f"Starting Spongecake API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
