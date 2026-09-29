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

# 3. Impostazioni (ORA USA IL FILE SINGOLO)
FRAME_URL="https://raw.githubusercontent.com/bsod-exe/citofono-dashboard/dashboard-output/frame.bin"
LOCAL=/var/dashboard_frame.bin
TMP=/var/dashboard_frame.tmp
OLD_MD5=""

# 4. Loop Intelligente (1 aggiornamento ogni 15 min)
while true; do
    if [ ! -f "$LOCK" ] || [ "$(cat "$LOCK" 2>/dev/null)" != "$$" ]; then
        exit 0
    fi

    # Bypassa la cache di GitHub con un timestamp
    if wget -q -O "$TMP" "${FRAME_URL}?t=$(date +%s)"; then
        SIZE=$(wc -c < "$TMP" 2>/dev/null)
        
        # Dimensione esatta del file singolo (1024x600x4)
        if [ "$SIZE" = "2457600" ]; then
            
            NEW_MD5=$(md5sum "$TMP")
            if [ "$NEW_MD5" != "$OLD_MD5" ]; then
                
                mv "$TMP" "$LOCAL"
                dd if="$LOCAL" of=/dev/fb0 bs=1M 2>/dev/null
                OLD_MD5="$NEW_MD5"
            fi
        fi
    fi
    
    sleep 60
done
