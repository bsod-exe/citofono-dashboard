#!/bin/sh
# ==========================================================================
# Wrapper che sostituisce /dnake/bin/desktop
#
# IMPORTANTE: questo script presuppone che il VERO binario originale sia
# stato rinominato in /dnake/bin/desktop_orig (non cancellato!) - vedi
# la guida "Fase 2" per i dettagli del repack.
#
# Perche' lanciamo comunque il binario originale per qualche secondo:
# i nostri test manuali riusciti finora hanno sempre "ucciso" un desktop
# gia' avviato (quindi con l'hardware video/layer gia' inizializzato dalle
# librerie Sigmastar MI). Non abbiamo mai verificato che scrivere su
# /dev/fb0 funzioni su un boot "a freddo" senza che desktop sia MAI partito.
# Per sicurezza, lo lanciamo brevemente e poi lo fermiamo: cosi' restiamo
# nelle condizioni gia' validate.
# ==========================================================================

FRAME_URL="https://raw.githubusercontent.com/bsod-exe/citofono-dashboard/dashboard-output/frame_x3.bin"
LOCAL=/var/dashboard_frame.bin
TMP=/var/dashboard_frame.tmp
LOG=/var/dashboard_wrapper.log

echo "$(date) - avvio wrapper" >> "$LOG"

# 1. Inizializza l'hardware video con il binario originale, poi fermalo
/dnake/bin/desktop_orig "$@" &
ORIG_PID=$!
sleep 3
kill "$ORIG_PID" 2>/dev/null
sleep 1

# 2. Loop infinito: scarica l'ultimo frame e scrivilo sul framebuffer
while true; do
    if wget -q -O "$TMP" "$FRAME_URL"; then
        # dimensione attesa: 1024*600*4*3 = 7372800 byte
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
