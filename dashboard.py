import datetime
import math
import urllib.request
import json
from PIL import Image, ImageDraw, ImageFont
import calendar as cal_mod

# --- FUNZIONI DI SUPPORTO E STILE ---

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

# --- NUOVE ICONE VETTORIALI METEO ---

def icon_sunny(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    c = size / 2
    r = size * 0.22
    draw.ellipse([c-r, c-r, c+r, c+r], fill=(255, 195, 0, 255))
    for i in range(8):
        angle = i * math.pi / 4
        x1 = c + math.cos(angle) * (r * 1.4)
        y1 = c + math.sin(angle) * (r * 1.4)
        x2 = c + math.cos(angle) * (r * 1.9)
        y2 = c + math.sin(angle) * (r * 1.9)
        draw.line([(x1, y1), (x2, y2)], fill=(255, 195, 0, 255), width=max(2, int(size*0.06)))
    return img

def icon_cloudy(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    color = (215, 225, 235, 255)
    draw.rounded_rectangle([size*0.15, size*0.45, size*0.85, size*0.75], radius=size*0.15, fill=color)
    draw.ellipse([size*0.2, size*0.25, size*0.55, size*0.6], fill=color)
    draw.ellipse([size*0.4, size*0.15, size*0.8, size*0.55], fill=color)
    return img

def icon_rain(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    rain_color = (100, 170, 255, 255)
    for dx, dy in [(0.3, 0.65), (0.5, 0.65), (0.7, 0.65)]:
        x1, y1 = size*dx, size*dy
        x2, y2 = size*(dx - 0.1), size*(dy + 0.25)
        draw.line([(x1, y1), (x2, y2)], fill=rain_color, width=max(2, int(size*0.04)))
    cloud_color = (160, 175, 190, 255)
    draw.rounded_rectangle([size*0.15, size*0.35, size*0.85, size*0.65], radius=size*0.15, fill=cloud_color)
    draw.ellipse([size*0.2, size*0.15, size*0.55, size*0.5], fill=cloud_color)
    draw.ellipse([size*0.4, size*0.05, size*0.8, size*0.45], fill=cloud_color)
    return img

ICON_MAP = {
    'sunny': icon_sunny,
    'cloudy': icon_cloudy,
    'rain': icon_rain
}

# --- MOTORE METEO REALE (OPEN-METEO) ---

def get_real_weather():
    """Scarica il meteo reale di Patti (ME) da Open-Meteo."""
    # Coordinate di Patti (Messina)
    lat, lon = "38.14", "14.97"
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&hourly=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Europe%2FRome"
    
    # Dati fittizi in caso di mancanza di connessione internet di GitHub
    weather = {
        'location': 'Patti (ME)',
        'current_temp': 22, 'current_label': 'In aggiornamento...', 'current_icon': 'cloudy',
        'today_min': 15, 'today_max': 25,
        'hourly': [['Adesso', 22, 'cloudy'], ['---', 0, 'cloudy'], ['---', 0, 'cloudy'], ['---', 0, 'cloudy'], ['---', 0, 'cloudy']],
        'daily': [['Oggi', 15, 25, 'cloudy'], ['---', 0, 0, 'cloudy'], ['---', 0, 0, 'cloudy'], ['---', 0, 0, 'cloudy'], ['---', 0, 0, 'cloudy']]
    }

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())

        # Converte i codici numerici internazionali (WMO) nelle nostre icone
        def get_icon(code):
            if code <= 1: return 'sunny'
            elif code <= 3: return 'cloudy'
            elif code in [45, 48]: return 'cloudy' # nebbia
            else: return 'rain' # pioggia o temporali

        def get_label(code):
            if code == 0: return 'Sereno'
            elif code in [1, 2]: return 'Parz. nuvoloso'
            elif code == 3: return 'Nuvoloso'
            elif code in [45, 48]: return 'Nebbia'
            elif 51 <= code <= 69: return 'Pioggia'
            elif 71 <= code <= 79: return 'Neve'
            elif code >= 95: return 'Temporale'
            return 'Instabile'

        # Meteo Attuale
        weather['current_temp'] = round(data['current']['temperature_2m'])
        weather['current_icon'] = get_icon(data['current']['weather_code'])
        weather['current_label'] = get_label(data['current']['weather_code'])
        weather['today_min'] = round(data['daily']['temperature_2m_min'][0])
        weather['today_max'] = round(data['daily']['temperature_2m_max'][0])

        # Previsioni orarie (Adesso + prossime 4 fasce saltando di 3 ore in 3 ore)
        now_hour = datetime.datetime.now().hour
        hourly = [['Adesso', weather['current_temp'], weather['current_icon']]]
        for i in range(1, 5):
            idx = now_hour + (i * 3)
            if idx < len(data['hourly']['time']):
                time_str = data['hourly']['time'][idx][11:16] # Es. "15:00"
                temp = round(data['hourly']['temperature_2m'][idx])
                icon = get_icon(data['hourly']['weather_code'][idx])
                hourly.append([time_str, temp, icon])
        weather['hourly'] = hourly

        # Previsioni per i prossimi giorni
        giorni_sett = ['Lun','Mar','Mer','Gio','Ven','Sab','Dom']
        daily = []
        for i in range(5):
            date_str = data['daily']['time'][i] # Es "2023-10-25"
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            label = 'Oggi' if i == 0 else giorni_sett[dt.weekday()]
            tmin = round(data['daily']['temperature_2m_min'][i])
            tmax = round(data['daily']['temperature_2m_max'][i])
            icon = get_icon(data['daily']['weather_code'][i])
            daily.append([label, tmin, tmax, icon])
        weather['daily'] = daily

    except Exception as e:
        print("Errore scaricamento meteo:", e)

    return weather


# --- COSTRUZIONE DELLA DASHBOARD ---

def build():
    # Dimensioni schermo citofono
    W, H = 1024, 600
    pad = 32

    # Immagine di base scura
    bg = Image.new('RGBA', (W, H), (20, 24, 28, 255))
    draw = ImageDraw.Draw(bg)

    # Scarica i dati reali da Open-Meteo!
    weather = get_real_weather()

    # --- Top: data + location (NIENTE OROLOGIO) ---
    now = datetime.datetime.now()
    giorni = ['Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato','Domenica']
    mesi = ['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio',
            'agosto','settembre','ottobre','novembre','dicembre']
    date_str = f'{giorni[now.weekday()]} {now.day} {mesi[now.month-1]} {now.year}'

    draw.text((pad, 30), date_str, font=font('bold', 28), fill=(255, 255, 255, 255))
    draw.text((pad, 70), weather['location'], font=font('medium', 20), fill=(255, 205, 90, 255))

    # --- Top right: meteo corrente ---
    icon_fn = ICON_MAP[weather['current_icon']]
    icon = icon_fn(80)
    bg.alpha_composite(icon, (548, 18))
    draw.text((650, 24), f"{weather['current_temp']}°", font=font('bold', 46), fill=(255, 255, 255, 255))
    draw.text((650, 78), weather['current_label'], font=font('regular', 18), fill=(225, 235, 225, 255))
    draw.text((650, 104), f"Min {weather['today_min']}°    Max {weather['today_max']}°", font=font('regular', 15), fill=(190, 205, 190, 255))

    # Linea divisoria
    draw.line([(pad, 122), (W - pad, 122)], fill=(255, 255, 255, 60), width=1)

    # --- Calendar card (in basso a sinistra) ---
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

    # Pallini eventi d'esempio
    example_events = [d for d in [28, 30] if d <= days_in_month]
    for d in example_events:
        col = (d - 1 + first_weekday) % 7
        r = (d - 1 + first_weekday) // 7
        x = start_x + col*col_w + 9
        y = grid_y0 + r*row_h + 22
        draw.ellipse([x-3, y-3, x+3, y+3], fill=(90, 180, 110, 255))

    # --- Weather cards (colonna destra) ---
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
