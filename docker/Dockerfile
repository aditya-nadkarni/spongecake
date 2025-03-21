FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------
# Install dependencies
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# Install Firefox
# ---------------------------------------------------------
RUN add-apt-repository ppa:mozillateam/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends firefox-esr \
    && update-alternatives --set x-www-browser /usr/bin/firefox-esr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV MOZ_MARIONETTE=1

# ---------------------------------------------------------
# Install/upgrade pip
# ---------------------------------------------------------
RUN pip3 install --upgrade pip

# ---------------------------------------------------------
# Firefox custom preference
# ---------------------------------------------------------
USER root
RUN echo 'pref("ui.caretBlinkTime", 0);' > /usr/lib/firefox-esr/defaults/pref/local-settings.js

# ---------------------------------------------------------
# Create non-root user
# ---------------------------------------------------------
RUN useradd -ms /bin/bash myuser && echo "myuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER myuser
WORKDIR /home/myuser

# Create a default Firefox profile with Marionette settings
RUN mkdir -p /home/myuser/.mozilla/firefox && \
    echo 'user_pref("marionette.accept_remote_connections", true);' >> /home/myuser/.mozilla/firefox/user.js && \
    echo 'user_pref("marionette.port", 2828);' >> /home/myuser/.mozilla/firefox/user.js && \
    echo 'user_pref("marionette.host", "127.0.0.1");' >> /home/myuser/.mozilla/firefox/user.js

# ---------------------------------------------------------
# Set VNC password
# ---------------------------------------------------------
RUN sudo x11vnc -storepasswd secret /home/myuser/.vncpass && \
    sudo chown myuser:myuser /home/myuser/.vncpass

# ---------------------------------------------------------
# Copy wallpaper into container
# ---------------------------------------------------------
COPY spongecake-background.png /usr/share/backgrounds/spongecake-background.png

# ---------------------------------------------------------
# xfconf-query at build time
# ---------------------------------------------------------
RUN xfconf-query \
    -c xfce4-desktop \
    -p /backdrop/screen0/monitorscreen/workspace0/last-image \
    -s /usr/share/backgrounds/spongecake-background.png \
 || true

# ---------------------------------------------------------
# Copy and enable startup script as root user
# ---------------------------------------------------------
USER root
COPY startup.sh /home/myuser/startup.sh
RUN chmod +x /home/myuser/startup.sh
USER myuser
WORKDIR /home/myuser

# ---------------------------------------------------------
# Expose VNC port
# ---------------------------------------------------------
EXPOSE 5900
EXPOSE 2828
EXPOSE 3838

# ---------------------------------------------------------
# Default command: run our startup script
# ---------------------------------------------------------
CMD ["/home/myuser/startup.sh"]
