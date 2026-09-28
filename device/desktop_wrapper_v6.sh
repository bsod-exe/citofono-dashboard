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

echo "$(date) - avvio wrapper v6 PID $$" >> "$LOG"

pkill -f desktop_orig 2>/dev/null
/var/desktop_orig "$@" &
sleep 3
pkill -f desktop_orig 2>/dev/null
sleep 1

# Assicurati che il pan resti sempre a 0,0 (il sistema lo forza comunque,
# quindi seguiamo la corrente invece di combatterla)
echo "0,0" > /sys/class/graphics/fb0/pan 2>/dev/null

# Loop di scrittura rapida sulla pagina 0, per minimizzare la finestra
# di conflitto col refresh periodico del compositore hardware
(
    while true; do
        if [ -f "$LOCAL" ]; then
            dd if="$LOCAL" of=/dev/fb0 bs=1M 2>/dev/null
        fi
        sleep 2
    done
) &
WRITER_PID=$!

# Loop di download, separato e più lento
while true; do
    if [ ! -f "$LOCK" ] || [ "$(cat "$LOCK" 2>/dev/null)" != "$$" ]; then
        echo "$(date) - lock perso o rimosso, esco" >> "$LOG"
        kill "$WRITER_PID" 2>/dev/null
        exit 0
    fi
    if wget -q -O "$TMP" "$FRAME_URL"; then
        SIZE=$(wc -c < "$TMP" 2>/dev/null)
        if [ "$SIZE" = "7372800" ]; then
            mv "$TMP" "$LOCAL"
        else
            echo "$(date) - download incompleto o corrotto ($SIZE byte), salto questo giro" >> "$LOG"
            rm -f "$TMP"
        fi
    else
        echo "$(date) - wget fallito, riprovo al prossimo giro" >> "$LOG"
    fi
    sleep 60
done
