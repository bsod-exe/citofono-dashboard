from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
from background import make_background
from icons import make_sun, make_sun_cloud, make_cloud_only, make_rain_cloud, make_snow_cloud
from weather import get_weather_safe
import datetime

ICON_MAP = {
    'sun': make_sun,
    'sun_cloud': make_sun_cloud,
    'cloud': make_cloud_only,
    'rain': make_rain_cloud,
    'snow': make_snow_cloud,
}

W, H = 1024, 600

FONT_DIR_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts') + '/'
FONT_DIR_SYSTEM = '/usr/share/fonts/truetype/google-fonts/'

def font(weight, size):
    files = {
        'light': 'Poppins-Light.ttf',
        'regular': 'Poppins-Regular.ttf',
        'medium': 'Poppins-Medium.ttf',
        'bold': 'Poppins-Bold.ttf',
    }
    fname = files[weight]
    local_path = FONT_DIR_LOCAL + fname
    if os.path.exists(local_path):
        return ImageFont.truetype(local_path, size)
    return ImageFont.truetype(FONT_DIR_SYSTEM + fname, size)

def rounded_glass_card(base, box, radius=22, fill=(255,255,255,235)):
    overlay = Image.new('RGBA', base.size, (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle(box, radius=radius, fill=fill)
    base.alpha_composite(overlay)

def build():
    weather, is_live = get_weather_safe()

    bg = make_background().convert('RGBA')
    draw = ImageDraw.Draw(bg)

    pad = 38

    # --- Top: clock + date + location (left) ---
    now = datetime.datetime.now()
    giorni = ['Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato','Domenica']
    mesi = ['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio',
            'agosto','settembre','ottobre','novembre','dicembre']
    time_str = now.strftime('%H:%M')
    date_str = f'{giorni[now.weekday()]} {now.day} {mesi[now.month-1]} {now.year}'

    draw.text((pad, 24), time_str, font=font('bold', 62), fill=(255,255,255,255))
    draw.text((pad, 95), date_str, font=font('regular', 20), fill=(225,235,225,255))
    draw.text((pad, 125), weather['location'], font=font('medium', 20), fill=(255,205,90,255))

    # --- Top right: current weather ---
    icon_fn = ICON_MAP[weather['current_icon']]
    icon = icon_fn(90)
    bg.alpha_composite(icon, (548, 18))
    draw.text((650, 24), f"{weather['current_temp']}°", font=font('bold', 46), fill=(255,255,255,255))
    draw.text((650, 78), weather['current_label'], font=font('regular', 18), fill=(225,235,225,255))
    draw.text((650, 104), f"Min {weather['today_min']}°   Max {weather['today_max']}°", font=font('regular', 15), fill=(190,205,190,255))

    # divider
    draw.line([(pad, 172), (W - pad, 172)], fill=(255,255,255,60), width=1)

    # --- Calendar card (bottom left) ---
    cal_box = [pad, 196, 494, 578]
    rounded_glass_card(bg, cal_box, radius=24)
    draw = ImageDraw.Draw(bg)

    import calendar as cal_mod
    mesi_cap = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio',
                'Agosto','Settembre','Ottobre','Novembre','Dicembre']
    month_label = f'{mesi_cap[now.month-1]} {now.year}'

    cx0, cy0 = cal_box[0] + 24, cal_box[1] + 24
    draw.text((cx0, cy0), month_label, font=font('bold', 22), fill=(40,50,40,255))

    days = ['L','M','M','G','V','S','D']
    col_w = (494 - 24*2 - 38) / 7
    start_x = cx0
    header_y = cy0 + 46
    for i, d in enumerate(days):
        col = (start_x + i*col_w, header_y)
        color = (200,60,60,255) if i == 6 else (110,120,110,255)
        draw.text(col, d, font=font('medium', 15), fill=color)

    first_weekday, days_in_month = cal_mod.monthrange(now.year, now.month)  # Mon=0
    today = now.day

    row_h = 42
    grid_y0 = header_y + 32
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
            tcolor = (200,60,60,255) if is_sunday and not is_today else (55,65,55,255)
            if is_today:
                circ_r = 15
                ccx, ccy = x + 10, y + 8
                draw.ellipse([ccx-circ_r, ccy-circ_r, ccx+circ_r, ccy+circ_r], fill=(60,120,235,255))
                draw.text((ccx, ccy), txt, font=font('bold', 15), fill=(255,255,255,255), anchor='mm')
            else:
                draw.text((x, y), txt, font=font('regular', 15), fill=tcolor)
            day_num += 1
        row += 1
        if day_num > days_in_month:
            break

    # event dots (placeholder finché non colleghiamo un calendario reale)
    example_events = [d for d in [28, 30] if d <= days_in_month]
    for d in example_events:
        col = (d - 1 + first_weekday) % 7
        r = (d - 1 + first_weekday) // 7
        x = start_x + col*col_w + 9
        y = grid_y0 + r*row_h + 24
        draw.ellipse([x-3, y-3, x+3, y+3], fill=(90,180,110,255))

    # --- Weather cards (right column) ---
    right_x0 = 514
    right_w = W - pad - right_x0

    # hourly card
    hourly_box = [right_x0, 196, right_x0 + right_w, 340]
    rounded_glass_card(bg, hourly_box, radius=24)
    draw = ImageDraw.Draw(bg)
    draw.text((right_x0+22, 214), 'Previsioni orarie', font=font('bold', 19), fill=(40,50,40,255))

    hours = weather['hourly']
    slot_w = (right_w - 44) / max(len(hours), 1)
    hy = 254
    for i, (label, temp, kind) in enumerate(hours):
        cx = right_x0 + 22 + i*slot_w
        if i == 0:
            chip_box = [cx-8, hy-8, cx+slot_w-14, hy+72]
            ov = Image.new('RGBA', bg.size, (0,0,0,0))
            ImageDraw.Draw(ov).rounded_rectangle(chip_box, radius=16, fill=(90,150,230,40))
            bg.alpha_composite(ov)
            draw = ImageDraw.Draw(bg)
        draw.text((cx, hy), label, font=font('medium', 14), fill=(70,80,70,255))
        ic = ICON_MAP[kind](36)
        bg.alpha_composite(ic, (int(cx), hy+22))
        draw = ImageDraw.Draw(bg)
        draw.text((cx, hy+60), f'{temp}°', font=font('medium', 15), fill=(40,50,40,255))

    # 5-day card
    days_box = [right_x0, 356, right_x0 + right_w, 578]
    rounded_glass_card(bg, days_box, radius=24)
    draw = ImageDraw.Draw(bg)
    draw.text((right_x0+22, 374), 'Previsioni prossimi giorni', font=font('bold', 19), fill=(40,50,40,255))

    forecast = weather['daily']
    fy = 416
    row_h2 = 30
    for i, (label, lo, hi, kind) in enumerate(forecast):
        y = fy + i*row_h2
        weight = 'bold' if label == 'Oggi' else 'medium'
        draw.text((right_x0+22, y), label, font=font(weight, 15), fill=(40,50,40,255))
        ic = ICON_MAP[kind](26)
        bg.alpha_composite(ic, (right_x0+95, y-5))
        draw.text((right_x0+215, y), f'{lo}°', font=font('regular', 14), fill=(110,120,110,255))
        draw.text((right_x0+265, y), f'{hi}°', font=font('bold', 15), fill=(40,50,40,255))
        draw = ImageDraw.Draw(bg)

    return bg.convert('RGB')

if __name__ == '__main__':
    img = build()
    img.save('dashboard_preview.jpg', quality=92)
    print('saved')
