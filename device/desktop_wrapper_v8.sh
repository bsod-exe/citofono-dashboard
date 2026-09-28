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

echo "$(date) - avvio wrapper v8 PID $$" >> "$LOG"

pkill -f desktop_orig 2>/dev/null
/var/desktop_orig "$@" &
sleep 3
pkill -f desktop_orig 2>/dev/null
sleep 1

CURPAGE=0

while true; do
    if [ ! -f "$LOCK" ] || [ "$(cat "$LOCK" 2>/dev/null)" != "$$" ]; then
        echo "$(date) - lock perso o rimosso, esco" >> "$LOG"
        exit 0
    fi

    # Diagnostica: legge il pan REALE prima di scrivere, senza aprire /dev/fb0
    # (cat su un file sysfs non ha lo stesso side-effect del dd su /dev/fb0)
    REALPAN_BEFORE=$(cat "$PANFILE" 2>/dev/null)
    echo "$(date) - ciclo inizio: CURPAGE=$CURPAGE REALPAN_BEFORE=$REALPAN_BEFORE" >> "$LOG"

    if wget -q -O "$TMP" "$FRAME_URL"; then
        SIZE=$(wc -c < "$TMP" 2>/dev/null)
        if [ "$SIZE" = "7372800" ]; then
            mv "$TMP" "$LOCAL"
            head -c 2457600 "$LOCAL" > "$SINGLE"

            if [ "$CURPAGE" = "0" ]; then
                dd if="$SINGLE" of=/dev/fb0 bs=2457600 seek=1 2>/dev/null
                echo "0,600" > "$PANFILE"
                CURPAGE=1
            else
                dd if="$SINGLE" of=/dev/fb0 bs=2457600 seek=0 2>/dev/null
                echo "0,0" > "$PANFILE"
                CURPAGE=0
            fi

            REALPAN_AFTER=$(cat "$PANFILE" 2>/dev/null)
            echo "$(date) - ciclo fine: CURPAGE=$CURPAGE REALPAN_AFTER=$REALPAN_AFTER" >> "$LOG"
        else
            echo "$(date) - download incompleto o corrotto ($SIZE byte), salto questo giro" >> "$LOG"
            rm -f "$TMP"
        fi
    else
        echo "$(date) - wget fallito, riprovo al prossimo giro" >> "$LOG"
    fi
    sleep 5
done
