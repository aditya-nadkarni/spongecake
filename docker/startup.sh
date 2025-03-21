#!/usr/bin/env bash

# Start a virtual X server on display :99
Xvfb :99 -screen 0 1280x720x24 &
export DISPLAY=:99

# Start Xfce4 session
startxfce4 &

# Give Xfce a moment to start up
sleep 2

# Re-apply the wallpaper in case it didn't stick during build
xfconf-query \
  -c xfce4-desktop \
  -p /backdrop/screen0/monitorscreen/workspace0/last-image \
  -s /usr/share/backgrounds/spongecake-background.png \
|| true

# Start x11vnc server (password-protected)
x11vnc -display :99 -N -forever -shared -rfbauth /home/myuser/.vncpass -rfbport 5900 &

# Start Firefox with Marionette
firefox-esr -marionette &

# Start socat for port forwarding
socat TCP-LISTEN:3838,fork TCP:127.0.0.1:2828 &

# Keep the container alive (log tailing, etc.)
tail -f /dev/null
