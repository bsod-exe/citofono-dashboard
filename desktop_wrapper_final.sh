#!/bin/sh
LOCK=/var/dashboard_wrapper.lock

if [ -f "$LOCK" ]; then
    OLDPID=$(cat "$LOCK" 2>/dev/null)
    if [ -n "$OLDPID" ] && kill -0 "$OLDPID" 2>/dev/null; then
        exit 0
    fi
fi
echo $$ > "$LOCK"

# 1. Inizializzazione pulita
pkill -f desktop_orig 2>/dev/null
/var/desktop_orig "$@" &
sleep 3
pkill -f desktop_orig 2>/dev/null
sleep 1

# 2. Reset del pan (allineamento iniziale)
echo "0,0" > /sys/class/graphics/fb0/pan 2>/dev/null

# 3. Impostazioni
FRAME_URL="https://raw.githubusercontent.com/bsod-exe/citofono-dashboard/dashboard-output/frame_x3.bin"
LOCAL=/var/dashboard_frame.bin
TMP=/var/dashboard_frame.tmp
OLD_MD5=""

# 4. Loop Intelligente (Zero lampeggiamenti)
while true; do
    if [ ! -f "$LOCK" ] || [ "$(cat "$LOCK" 2>/dev/null)" != "$$" ]; then
        exit 0
    fi

    # Scarica il frame da 7.3MB in background
    if wget -q -O "$TMP" "$FRAME_URL"; then
        SIZE=$(wc -c < "$TMP" 2>/dev/null)
        if [ "$SIZE" = "7372800" ]; then
            
            # Controlla se l'immagine è davvero cambiata da GitHub
            NEW_MD5=$(md5sum "$TMP")
            if [ "$NEW_MD5" != "$OLD_MD5" ]; then
                
                # Applica l'immagine allo schermo solo se ci sono novità (ogni 15 min)
                mv "$TMP" "$LOCAL"
                dd if="$LOCAL" of=/dev/fb0 bs=1M 2>/dev/null
                OLD_MD5="$NEW_MD5"
            fi
        fi
    fi
    
    sleep 60
done
