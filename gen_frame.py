#!/usr/bin/env python3
"""
Entry point usato da GitHub Actions (e utilizzabile anche a mano sul PC)
per generare il file raw da scrivere nel framebuffer del videocitofono.

Uso:
    python3 gen_frame.py [output_dir]

Genera:
    <output_dir>/frame.bin      singolo frame BGRA 1024x600 (2.457.600 byte)
    <output_dir>/frame_x3.bin   stesso frame ripetuto 3 volte (7.372.800 byte)
                                 necessario per la tripla bufferizzazione del
                                 framebuffer del device (vedi HANDOFF.md §5)
                                 
"""
from PIL import Image
import sys
import os
from dashboard import build

def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out_dir, exist_ok=True)

    img = build().convert('RGBA')
    raw = img.tobytes('raw', 'BGRA')

    single_path = os.path.join(out_dir, 'frame.bin')
    triple_path = os.path.join(out_dir, 'frame_x3.bin')

    with open(single_path, 'wb') as f:
        f.write(raw)
    with open(triple_path, 'wb') as f:
        f.write(raw * 3)

    print(f'Scritto {single_path} ({len(raw)} byte)')
    print(f'Scritto {triple_path} ({len(raw)*3} byte)')


img = img.resize((1024, 600))

# 2. Converti in RGBA per assicurarti di avere 4 canali
img = img.convert("RGBA")

# 3. Separa i canali per riordinarli
r, g, b, a = img.split()

# 4. Forza l'opacità al 100% per oscurare la telecamera o altri layer di fabbrica
a = a.point(lambda i: 255)

# 5. Ricomponi l'immagine nel formato BGRA richiesto da Sigmastar
img_bgra = Image.merge("RGBA", (b, g, r, a))

# 6. Estrai i byte PURI (senza intestazioni file)
raw_bytes = img_bgra.tobytes()

# 7. Salva sia il file singolo che quello triplo per lo script finale
import os
os.makedirs("build_output", exist_ok=True)

with open("build_output/frame.bin", "wb") as f:
    f.write(raw_bytes)

with open("build_output/frame_x3.bin", "wb") as f:
    f.write(raw_bytes * 3)

if __name__ == '__main__':
    main()
