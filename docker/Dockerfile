FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    # X11 / VNC
    xvfb x11vnc xauth x11-xserver-utils \
    x11-apps sudo software-properties-common \
    # Basic GUI automation
    xdotool \
    # Python & pip
    python3 python3-pip \
    # xfce4 desktop environment and goodies
    xfce4 xfce4-goodies \
    # D-Bus session launcher
    dbus-x11 \
    # Misc utilities
    curl wget git nano xterm \
    # Screenshot utilities
    imagemagick \
    socat \
    # Remove unneeded dependencies and clean up
    && apt-get remove -y light-locker xfce4-screensaver xfce4-power-manager || true \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install firefox
RUN add-apt-repository ppa:mozillateam/ppa  && apt-get update  && apt-get install -y --no-install-recommends firefox-esr  && update-alternatives --set x-www-browser /usr/bin/firefox-esr  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install/upgrade pip
RUN pip3 install --upgrade pip

USER root
RUN echo 'pref("ui.caretBlinkTime", 0);' > /usr/lib/firefox-esr/defaults/pref/local-settings.js

# Create non-root user and set that as the working directory
RUN useradd -ms /bin/bash myuser && echo "myuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER myuser
WORKDIR /home/myuser

# Create a default Firefox profile with Marionette settings
RUN mkdir -p /home/myuser/.mozilla/firefox && \
    echo 'user_pref("marionette.accept_remote_connections", true);' >> /home/myuser/.mozilla/firefox/user.js && \
    echo 'user_pref("marionette.port", 2828);' >> /home/myuser/.mozilla/firefox/user.js && \
    echo 'user_pref("marionette.host", "127.0.0.1");' >> /home/myuser/.mozilla/firefox/user.js

# Set VNC password to ("secret")
RUN x11vnc -storepasswd secret /home/myuser/.vncpass

# Expose the VNC, Firefox Marionette, and socat ports
EXPOSE 5900
EXPOSE 2828
EXPOSE 3838

CMD Xvfb :99 -screen 0 1280x720x24 & \
    export DISPLAY=:99 && \
    startxfce4 & \
    x11vnc -display :99 -N -forever -shared -rfbauth /home/myuser/.vncpass -rfbport 5900 & \
    firefox-esr -marionette & \
    socat TCP-LISTEN:3838,fork TCP:127.0.0.1:2828 & \
    tail -f /dev/null
