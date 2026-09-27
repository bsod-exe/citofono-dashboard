#!/bin/sh
LOCK=/var/dashboard_wrapper.lock

if [ -f "$LOCK" ]; then
    OLDPID=$(cat "$LOCK" 2>/dev/null)
    if [ -n "$OLDPID" ] && kill -0 "$OLDPID" 2>/dev/null; then
        exit 0
    fi
fi
echo $$ > "$LOCK"

FRAME_URL="https://raw.githubusercontent.com/bsod-exe/citofono-dashboard/dashboard-output/frame_x3.bin"
LOCAL=/var/dashboard_frame.bin
TMP=/var/dashboard_frame.tmp
LOG=/var/dashboard_wrapper.log

echo "$(date) - avvio wrapper PID $$" >> "$LOG"

/var/desktop_orig "$@" &
ORIG_PID=$!
sleep 3
kill "$ORIG_PID" 2>/dev/null
sleep 1

while true; do
    if [ ! -f "$LOCK" ] || [ "$(cat "$LOCK" 2>/dev/null)" != "$$" ]; then
        echo "$(date) - lock perso o rimosso, esco" >> "$LOG"
        exit 0
    fi
    if wget -q -O "$TMP" "$FRAME_URL"; then
        SIZE=$(wc -c < "$TMP" 2>/dev/null)
        if [ "$SIZE" = "7372800" ]; then
            mv "$TMP" "$LOCAL"
            dd if="$LOCAL" of=/dev/fb0 bs=1M 2>/dev/null
        else
            echo "$(date) - download incompleto o corrotto ($SIZE byte), salto questo giro" >> "$LOG"
            rm -f "$TMP"
        fi
    else
        echo "$(date) - wget fallito, riprovo al prossimo giro" >> "$LOG"
    fi
    sleep 60
done
