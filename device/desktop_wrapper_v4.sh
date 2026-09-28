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
SINGLE=/var/dashboard_frame_single.bin
TMP=/var/dashboard_frame.tmp
LOG=/var/dashboard_wrapper.log
PANFILE=/sys/class/graphics/fb0/pan

echo "$(date) - avvio wrapper v4 PID $$" >> "$LOG"

pkill -f desktop_orig 2>/dev/null
/var/desktop_orig "$@" &
sleep 3
pkill -f desktop_orig 2>/dev/null
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
            head -c 2457600 "$LOCAL" > "$SINGLE"

            CURPAN=$(cat "$PANFILE" 2>/dev/null)
            if [ "$CURPAN" = "0,0" ]; then
                # scrivi nella pagina nascosta (600), poi mostrala
                dd if="$SINGLE" of=/dev/fb0 bs=2457600 seek=1 2>/dev/null
                echo "0,600" > "$PANFILE"
                # ora la pagina 0 e' nascosta: aggiorna anche quella,
                # cosi' resta valida se il sistema resetta il pan da solo
                dd if="$SINGLE" of=/dev/fb0 bs=2457600 seek=0 2>/dev/null
            else
                dd if="$SINGLE" of=/dev/fb0 bs=2457600 seek=0 2>/dev/null
                echo "0,0" > "$PANFILE"
                dd if="$SINGLE" of=/dev/fb0 bs=2457600 seek=1 2>/dev/null
            fi
        else
            echo "$(date) - download incompleto o corrotto ($SIZE byte), salto questo giro" >> "$LOG"
            rm -f "$TMP"
        fi
    else
        echo "$(date) - wget fallito, riprovo al prossimo giro" >> "$LOG"
    fi
    sleep 5
done
