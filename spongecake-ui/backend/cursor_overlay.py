#!/usr/bin/env python3
"""
cursor_overlay.py

A demo overlay that hides the system cursor (within this app)
and draws a custom cursor image that tracks the mouse.
It also dynamically draws text next to the cursor with a rounded
background that resizes to fit its content and animates dots on the text.

In addition, the script runs a TCP text update server in a background
thread which listens for incoming text updates on a specified port.
Any text received will update the base text for the animation.

Requirements:
  • macOS
  • PyObjC (install via: pip install pyobjc)

Usage:
  • Place a PNG image named "custom-cursor.png" in the same directory 
    (32x32 recommended) or the code will generate a red circle.
  • Run: python3 cursor_overlay.py
  • To update the overlay text while running, send a TCP connection to localhost:9999,
    write your custom text, then close the connection.
  • To stop, close the overlay window or interrupt the process (Ctrl+C).
"""

import objc
import signal
import sys
import socket
import threading
import time

from Cocoa import (
    NSApplication,
    NSWindow,
    NSBackingStoreBuffered,
    NSColor,
    NSImage,
    NSView,
    NSTimer,
    NSCursor,
)
from AppKit import (
    NSScreen,
    NSStatusWindowLevel,
    NSEvent,
    NSRectFill,
    NSFont,
    NSBezierPath,
)
from Foundation import NSMakeRect, NSPoint, NSObject, NSNotificationCenter, NSString, NSAttributedString
from PyObjCTools import AppHelper  # For better signal integration

try:
    from Foundation import NSFontAttributeName, NSForegroundColorAttributeName
except ImportError:
    NSFontAttributeName = "NSFont"
    NSForegroundColorAttributeName = "NSForegroundColor"


class CursorOverlayView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(CursorOverlayView, self).initWithFrame_(frame)
        if self is None:
            return None

        # Try loading a custom cursor image from file.
        self.customImage = NSImage.alloc().initWithContentsOfFile_("custom-cursor.png")
        if self.customImage is None:
            # No image file found; create a red circle programmatically.
            size = (32, 32)
            self.customImage = NSImage.alloc().initWithSize_(size)
            self.customImage.lockFocus()
            NSColor.redColor().setFill()
            circleRect = NSMakeRect(0, 0, size[0], size[1])
            path = NSBezierPath.bezierPathWithOvalInRect_(circleRect)
            path.fill()
            self.customImage.unlockFocus()

        # Default cursor position.
        self.cursorPos = NSPoint(0, 0)

        # Set up animation variables:
        # baseText is the message without dots.
        self.baseText = "Thinking"
        # dotIndex cycles from 0 to 2 (which will yield 1 to 3 dots).
        self.dotIndex = 0
        # lastUpdate is the timestamp of the last animation update.
        self.lastUpdate = time.time()
        # overlayText is initialized to baseText with one dot.
        self.overlayText = self.baseText + "."
        return self

    def tick_(self, timer):
        """Update the mouse position and animate the overlay text dots."""
        self.cursorPos = NSEvent.mouseLocation()
        curTime = time.time()
        # Update the animated dots every 0.5 seconds.
        if curTime - self.lastUpdate >= 0.5:
            self.dotIndex = (self.dotIndex + 1) % 3  # Cycle: 0,1,2
            # If a text update comes in from the socket, it will update self.baseText.
            self.overlayText = self.baseText + "." * (self.dotIndex + 1)
            self.lastUpdate = curTime
        self.setNeedsDisplay_(True)
    
    def hideCursorTimer_(self, timer):
        """Periodically force-hide the system cursor."""
        NSCursor.hide()
    
    def drawRect_(self, rect):
        """
        Clear the view, then draw the custom cursor image and render overlay text 
        with a rounded background.
        """
        # Clear the view.
        NSColor.clearColor().setFill()
        NSRectFill(rect)

        # Draw the custom cursor image (32x32 centered at the cursor position).
        x = self.cursorPos.x - 16
        y = self.cursorPos.y - 16
        imageRect = NSMakeRect(x, y, 32, 32)
        self.customImage.drawInRect_(imageRect)

        # Draw overlay text if available.
        if hasattr(self, "overlayText") and self.overlayText:
            textAttributes = {
                NSFontAttributeName: NSFont.systemFontOfSize_(14),
                # Custom text color: hex #87610085 (red=135, green=97, blue=0, alpha≈133/255)
                NSForegroundColorAttributeName: NSColor.colorWithCalibratedRed_green_blue_alpha_(
                    135/255.0, 97/255.0, 0.0, 133/255.0
                )
            }
            attrText = NSAttributedString.alloc().initWithString_attributes_(self.overlayText, textAttributes)
            textSize = attrText.size()
            padding = 4  # Padding around the text.
            # Position the background rectangle to the right of the cursor image.
            bgX = imageRect.origin.x + imageRect.size.width + 5  # 5px gap.
            bgY = imageRect.origin.y + (imageRect.size.height - textSize.height) / 2 - padding
            bgWidth = textSize.width + 2 * padding
            bgHeight = textSize.height + 2 * padding
            bgRect = NSMakeRect(bgX, bgY, bgWidth, bgHeight)
            # Custom background color: hex #FFF8E7AB → (red=248, green=231, blue=171, alpha=1.0)
            backgroundColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, 0.5)
            # Create a rounded rectangle path with a corner radius of 5.
            roundedPath = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bgRect, 5, 5)
            backgroundColor.setFill()
            roundedPath.fill()
            # Draw the attributed text inside the rounded rectangle.
            textPoint = (bgX + padding, bgY + padding)
            attrText.drawAtPoint_(textPoint)


class AppObserver(NSObject):
    def applicationDidBecomeActive_(self, notification):
        NSCursor.hide()
        print("Application activated: default cursor hidden.")


def cleanup_and_exit(signum, frame):
    """Cleanup: unhide the cursor and exit cleanly."""
    from AppKit import NSCursor
    for _ in range(10):
        NSCursor.unhide()
    print("Cleanup complete. Exiting.")
    sys.exit(0)


def text_update_server(view, host="127.0.0.1", port=9999):
    """
    A simple TCP server that listens for text data and updates the overlay text.
    When new text is received, it updates view.baseText so that the animated text 
    uses the new value.
    This function runs in a background thread.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow quick reuse of the address.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Text update server listening on {}:{}".format(host, port))
    
    while True:
        try:
            client_sock, addr = server_socket.accept()
            data = client_sock.recv(1024)
            if data:
                new_text = data.decode("utf-8").strip()
                # Update the base text. The animated dots will be added automatically.
                view.baseText = new_text
                print("Updated base overlay text:", new_text)
            client_sock.close()
        except Exception as e:
            print("Error in text update server:", e)
            break


def main():
    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)

    app = NSApplication.sharedApplication()
    NSCursor.hide()

    screenFrame = NSScreen.mainScreen().frame()
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        screenFrame,
        0,  # Borderless.
        NSBackingStoreBuffered,
        False
    )
    window.setLevel_(NSStatusWindowLevel)
    window.setBackgroundColor_(NSColor.clearColor())
    window.setOpaque_(False)
    window.setIgnoresMouseEvents_(True)

    contentView = CursorOverlayView.alloc().initWithFrame_(screenFrame)
    window.setContentView_(contentView)
    window.makeKeyAndOrderFront_(None)

    # Spawn a background thread for the text update server.
    update_thread = threading.Thread(target=text_update_server, args=(contentView,), daemon=True)
    update_thread.start()

    NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        0.016, contentView, b"tick:", None, True
    )
    NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        0.1, contentView, b"hideCursorTimer:", None, True
    )

    observer = AppObserver.alloc().init()
    NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
        observer,
        b"applicationDidBecomeActive:",
        "NSApplicationDidBecomeActiveNotification",
        None
    )

    AppHelper.runConsoleEventLoop()


if __name__ == '__main__':
    main()