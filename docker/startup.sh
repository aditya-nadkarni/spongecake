#!/usr/bin/env bash

# 1) Clean up any stale X lock files and sockets.
rm -f /tmp/.X*-lock
rm -f /tmp/.X11-unix/X*

# 2) Start a virtual X server on display :99 with extra flags (-ac, -nolisten tcp).
Xvfb :99 -screen 0 1280x720x24 -ac -nolisten tcp &
export DISPLAY=:99

# Give Xvfb a moment to come up.
sleep 2

# 3) Start Xfce4 session
startxfce4 &

# Give Xfce a moment to start up
sleep 2

# Re-apply the wallpaper in case it didn't stick during build
xfconf-query -c xfce4-desktop \
  -p /backdrop/screen0/monitorscreen/workspace0/last-image \
  -s /usr/share/backgrounds/spongecake-background.png \
  --create -t string || true

# Start x11vnc server (password-protected)
x11vnc -display :99 -N -forever -shared -rfbauth /home/myuser/.vncpass -rfbport 5900 &

# Start Marionette server for Firefox
export MOZ_MARIONETTE=1
socat TCP-LISTEN:2829,fork TCP:localhost:2828 &

# Start the Spongecake API server
python3 /app/api_server.py &

# Start Firefox with Marionette
firefox-esr -marionette &

# Start socat for port forwarding
socat TCP-LISTEN:3838,fork TCP:127.0.0.1:2828 &

# Keep the container alive (log tailing, etc.)
tail -f /dev/null
