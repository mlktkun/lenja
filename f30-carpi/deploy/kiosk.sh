#!/bin/sh
# Startet die Oberfläche im Vollbild (Wayland-Kiosk mit cage + Chromium).
# Als Autostart des Benutzers carpi einrichten, z. B. per systemd-User-Unit
# oder getty-Autologin + Aufruf in ~/.profile.
set -eu

# Warten, bis das Backend antwortet
until curl -sf http://127.0.0.1:8080/api/status >/dev/null; do sleep 1; done

exec cage -- chromium \
  --kiosk --noerrdialogs --disable-infobars --no-first-run \
  --disable-session-crashed-bubble --overscroll-history-navigation=0 \
  --check-for-update-interval=31536000 \
  http://127.0.0.1:8080/
