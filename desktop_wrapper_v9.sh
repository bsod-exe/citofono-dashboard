#!/bin/sh
LOCK=/var/dashboard_wrapper.lock

if [ -f "$LOCK" ]; then
    OLDPID=$(cat "$LOCK" 2>/dev/null)
    if [ -n "$OLDPID" ] && kill -0 "$OLDPID" 2>/dev/null; then
        exit 0
    fi
fi
echo $$ > "$LOCK"

# 1. Inizializza l'hardware video con il binario originale
pkill -f desktop_orig 2>/dev/null
/var/desktop_orig "$@" &
sleep 3
pkill -f desktop_orig 2>/dev/null
sleep 1

# 2. Avvia il nostro demone anti-tearing in C
pkill -f sstar_fb_daemon 2>/dev/null
/var/sstar_fb_daemon &

# 3. Loop di download silenzioso
FRAME_URL="https://raw.githubusercontent.com/bsod-exe/citofono-dashboard/dashboard-output/frame.bin"
TMP=/var/dashboard_frame.tmp
DEST=/var/new_frame.bin

while true; do
    if [ ! -f "$LOCK" ] || [ "$(cat "$LOCK" 2>/dev/null)" != "$$" ]; then
        exit 0
    fi
    
    # Scarica il frame singolo e innesca il demone
    wget -q -O "$TMP" "$FRAME_URL" && mv "$TMP" "$DEST"
    
    sleep 60
done
