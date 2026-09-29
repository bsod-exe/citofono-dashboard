import datetime
from PIL import Image, ImageDraw, ImageFont
import calendar as cal_mod

# --- FUNZIONI DI SUPPORTO RICOSTRUITE ---

def font(weight, size):
    """Tenta di caricare un font standard di sistema (Ubuntu), altrimenti usa il default."""
    try:
        base_font = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
        if weight == 'bold':
            return ImageFont.truetype(f"{base_font}-Bold.ttf", size)
        else:
            return ImageFont.truetype(f"{base_font}.ttf", size)
    except IOError:
        return ImageFont.load_default()

def rounded_glass_card(bg, box, radius=24):
    """Disegna una card con angoli arrotondati ed effetto vetro."""
    overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(box, radius=radius, fill=(255, 255, 255, 20), outline=(255, 255, 255, 50), width=1)
    bg.alpha_composite(overlay)

def generate_icon(color):
    """Genera un'icona segnaposto colorata per evitare crash se mancano i file."""
    def builder(size):
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([0, 0, size-1, size-1], fill=color)
        return img
    return builder

# Mappa icone fittizie (puoi rimettere le tue PNG in futuro)
ICON_MAP = {
    'cloudy': generate_icon((150, 160, 170, 255)), # Grigio
    'sunny': generate_icon((255, 210, 80, 255)),   # Giallo
    'rain': generate_icon((80, 130, 220, 255))     # Blu
}

# --- FINE FUNZIONI DI SUPPORTO ---


def build():
    # Dimensioni schermo citofono
    W, H = 1024, 600
    pad = 32

    # Immagine di base scura
    bg = Image.new('RGBA', (W, H), (20, 24, 28, 255))
    draw = ImageDraw.Draw(bg)

    # Dati Meteo di base
    weather = {
        'location': 'Roma',
        'current_temp': 22,
        'current_label': 'Parzialmente nuvoloso',
        'current_icon': 'cloudy',
        'today_min': 14,
        'today_max': 24,
        'hourly': [
            ['Adesso', 22, 'cloudy'],
            ['12:00', 23, 'sunny'],
            ['15:00', 24, 'sunny'],
            ['18:00', 21, 'cloudy'],
            ['21:00', 18, 'rain']
        ],
        'daily': [
            ['Oggi', 14, 24, 'cloudy'],
            ['Mer', 13, 22, 'sunny'],
            ['Gio', 12, 20, 'rain'],
            ['Ven', 15, 25, 'sunny'],
            ['Sab', 16, 26, 'sunny']
        ]
    }

    # --- Top: date + location ---
    now = datetime.datetime.now()
    giorni = ['Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato','Domenica']
    mesi = ['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio',
            'agosto','settembre','ottobre','novembre','dicembre']
    date_str = f'{giorni[now.weekday()]} {now.day} {mesi[now.month-1]} {now.year}'

    draw.text((pad, 30), date_str, font=font('bold', 28), fill=(255, 255, 255, 255))
    draw.text((pad, 70), weather['location'], font=font('medium', 20), fill=(255, 205, 90, 255))

    # --- Top right: current weather ---
    icon_fn = ICON_MAP[weather['current_icon']]
    icon = icon_fn(80)
    bg.alpha_composite(icon, (548, 18))
    draw.text((650, 24), f"{weather['current_temp']}°", font=font('bold', 46), fill=(255, 255, 255, 255))
    draw.text((650, 78), weather['current_label'], font=font('regular', 18), fill=(225, 235, 225, 255))
    draw.text((650, 104), f"Min {weather['today_min']}°    Max {weather['today_max']}°", font=font('regular', 15), fill=(190, 205, 190, 255))

    # Divider
    draw.line([(pad, 122), (W - pad, 122)], fill=(255, 255, 255, 60), width=1)

    # --- Calendar card ---
    cal_box = [pad, 142, 494, 578]
    rounded_glass_card(bg, cal_box, radius=24)
    draw = ImageDraw.Draw(bg)

    mesi_cap = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio',
                'Agosto','Settembre','Ottobre','Novembre','Dicembre']
    month_label = f'{mesi_cap[now.month-1]} {now.year}'

    cx0, cy0 = cal_box[0] + 24, cal_box[1] + 20
    draw.text((cx0, cy0), month_label, font=font('bold', 22), fill=(240, 245, 240, 255))

    days = ['L','M','M','G','V','S','D']
    col_w = (494 - 24*2 - 38) / 7
    start_x = cx0
    header_y = cy0 + 42
    for i, d in enumerate(days):
        col = (start_x + i*col_w, header_y)
        color = (240, 80, 80, 255) if i == 6 else (160, 170, 160, 255)
        draw.text(col, d, font=font('medium', 15), fill=color)

    first_weekday, days_in_month = cal_mod.monthrange(now.year, now.month)
    today = now.day

    row_h = 40
    grid_y0 = header_y + 28
    day_num = 1
    row = 0
    started = False
    for r in range(6):
        y = grid_y0 + r*row_h
        for c in range(7):
            if row == 0 and c < first_weekday and not started:
                continue
            if day_num > days_in_month:
                break
            started = True
            x = start_x + c*col_w
            is_sunday = (c == 6)
            is_today = (day_num == today)
            txt = str(day_num)
            tcolor = (240, 80, 80, 255) if is_sunday and not is_today else (220, 230, 220, 255)
            if is_today:
                circ_r = 14
                ccx, ccy = x + 10, y + 8
                draw.ellipse([ccx-circ_r, ccy-circ_r, ccx+circ_r, ccy+circ_r], fill=(60, 120, 235, 255))
                draw.text((ccx, ccy), txt, font=font('bold', 15), fill=(255, 255, 255, 255), anchor='mm')
            else:
                draw.text((x, y), txt, font=font('regular', 15), fill=tcolor)
            day_num += 1
        row += 1
        if day_num > days_in_month:
            break

    # Event dots (giorni 28 e 30 d'esempio)
    example_events = [d for d in [28, 30] if d <= days_in_month]
    for d in example_events:
        col = (d - 1 + first_weekday) % 7
        r = (d - 1 + first_weekday) // 7
        x = start_x + col*col_w + 9
        y = grid_y0 + r*row_h + 22
        draw.ellipse([x-3, y-3, x+3, y+3], fill=(90, 180, 110, 255))

    # --- Weather cards ---
    right_x0 = 514
    right_w = W - pad - right_x0

    # Hourly card
    hourly_box = [right_x0, 142, right_x0 + right_w, 282]
    rounded_glass_card(bg, hourly_box, radius=24)
    draw = ImageDraw.Draw(bg)
    draw.text((right_x0+22, 156), 'Previsioni orarie', font=font('bold', 19), fill=(240, 245, 240, 255))

    hours = weather['hourly']
    slot_w = (right_w - 44) / max(len(hours), 1)
    hy = 192
    for i, (label, temp, kind) in enumerate(hours):
        cx = right_x0 + 22 + i*slot_w
        if i == 0:
            chip_box = [cx-8, hy-8, cx+slot_w-14, hy+68]
            ov = Image.new('RGBA', bg.size, (0,0,0,0))
            ImageDraw.Draw(ov).rounded_rectangle(chip_box, radius=16, fill=(90, 150, 230, 40))
            bg.alpha_composite(ov)
            draw = ImageDraw.Draw(bg)
        draw.text((cx, hy), label, font=font('medium', 14), fill=(200, 210, 200, 255))
        ic = ICON_MAP[kind](34)
        bg.alpha_composite(ic, (int(cx), hy+20))
        draw = ImageDraw.Draw(bg)
        draw.text((cx, hy+56), f'{temp}°', font=font('medium', 15), fill=(240, 245, 240, 255))

    # 5-day card
    days_box = [right_x0, 298, right_x0 + right_w, 578]
    rounded_glass_card(bg, days_box, radius=24)
    draw = ImageDraw.Draw(bg)
    draw.text((right_x0+22, 314), 'Previsioni prossimi giorni', font=font('bold', 19), fill=(240, 245, 240, 255))

    forecast = weather['daily']
    fy = 352
    row_h2 = 30
    for i, (label, lo, hi, kind) in enumerate(forecast):
        y = fy + i*row_h2
        weight = 'bold' if label == 'Oggi' else 'medium'
        draw.text((right_x0+22, y), label, font=font(weight, 15), fill=(240, 245, 240, 255))
        ic = ICON_MAP[kind](26)
        bg.alpha_composite(ic, (right_x0+95, y-5))
        draw.text((right_x0+215, y), f'{lo}°', font=font('regular', 14), fill=(180, 190, 180, 255))
        draw.text((right_x0+265, y), f'{hi}°', font=font('bold', 15), fill=(240, 245, 240, 255))
        draw = ImageDraw.Draw(bg)

    return bg.convert('RGB')
