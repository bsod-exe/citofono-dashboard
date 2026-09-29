#!/bin/sh
LOCK=/var/dashboard_wrapper.lock

if [ -f "$LOCK" ]; then
    OLDPID=$(cat "$LOCK" 2>/dev/null)
    if [ -n "$OLDPID" ] && kill -0 "$OLDPID" 2>/dev/null; then
        exit 0
    fi
fi
echo $$ > "$LOCK"

# --- FASE 1: CONFIGURAZIONE AUTOMATICA RETE (ALL'AVVIO) ---
if ! ifconfig wlan0 | grep -q "inet addr"; then
    mkdir -p /var/run/wpa_supplicant
    if [ ! -f /var/wpa.conf ]; then
        printf 'ctrl_interface=/var/run/wpa_supplicant\nnetwork={\n    ssid="IcaroFibra_FTTH_44AA 2GHz"\n    psk="854123698745"\n}\n' > /var/wpa.conf
    fi
    ifconfig wlan0 up
    pkill wpa_supplicant
    /dnake/bin/wpa_supplicant -B -i wlan0 -D nl80211 -c /var/wpa.conf
    sleep 4
    ifconfig wlan0 192.168.1.41 netmask 255.255.255.0 up
    route del default gw 192.168.1.1 dev eth0 2>/dev/null
    route add default gw 192.168.1.1 dev wlan0
fi

# --- FASE 2: INIZIALIZZAZIONE HARDWARE VIDEO ---
pkill -f desktop_orig 2>/dev/null
if [ ! -f /var/desktop_orig ]; then
    cp /dnake/bin/desktop /var/desktop_orig
    chmod +x /var/desktop_orig
fi

/var/desktop_orig "$@" &
sleep 3
pkill -f desktop_orig 2>/dev/null
sleep 1

echo "0,0" > /sys/class/graphics/fb0/pan 2>/dev/null

# --- FASE 3: LOOP DI AGGIORNAMENTO (OGNI 1 MINUTO) ---
FRAME_URL="https://raw.githubusercontent.com/bsod-exe/citofono-dashboard/dashboard-output/frame.bin"
LOCAL=/var/dashboard_frame.bin
TMP=/var/dashboard_frame.tmp

while true; do
    if [ ! -f "$LOCK" ] || [ "$(cat "$LOCK" 2>/dev/null)" != "$$" ]; then
        exit 0
    fi

    # Scarica il frame forzando il bypass della cache con il timestamp attuale
    if wget -q -O "$TMP" "${FRAME_URL}?t=$(date +%s)"; then
        SIZE=$(wc -c < "$TMP" 2>/dev/null)
        
        # Verifica che il file sia integro (2.457.600 byte)
        if [ "$SIZE" = "2457600" ]; then
            mv "$TMP" "$LOCAL"
            dd if="$LOCAL" of=/dev/fb0 bs=1M 2>/dev/null
        fi
    fi
    
    # Aggiornamento puntuale ogni 60 secondi
    sleep 60
done
