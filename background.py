from PIL import Image, ImageDraw, ImageFilter
import math, random

W, H = 1024, 600

def radial_gradient(light, dark, cx_f=0.42, cy_f=0.45):
    base = Image.new('RGB', (W, H), dark)
    px = base.load()
    cx, cy = W * cx_f, H * cy_f
    max_dist = math.hypot(max(cx, W - cx), max(cy, H - cy))
    for y in range(H):
        for x in range(0, W, 2):
            dist = min(1, math.hypot(x - cx, y - cy) / max_dist)
            r = int(light[0] + (dark[0] - light[0]) * dist)
            g = int(light[1] + (dark[1] - light[1]) * dist)
            b = int(light[2] + (dark[2] - light[2]) * dist)
            px[x, y] = (r, g, b)
            if x + 1 < W:
                px[x + 1, y] = (r, g, b)
    return base

def wave_ribbon(draw, pts_top, pts_bottom, fill):
    # pts_top and pts_bottom define a ribbon shape (smooth via many points)
    draw.polygon(pts_top + pts_bottom[::-1], fill=fill)

def smooth_curve(p0, p1, p2, p3, steps=40):
    # Catmull-Rom-ish via simple quadratic bezier chain for a flowing line
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0]
        y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1]
        pts.append((x, y))
    return pts

def make_background():
    light = (108, 196, 118)
    dark = (16, 48, 30)
    base = radial_gradient(light, dark).convert('RGBA')

    waves = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(waves)

    darker = (8, 34, 22)
    lighter = (150, 225, 150)

    # Top-left flowing ribbon (dark, semi-transparent), like reference top-left wave
    top1 = smooth_curve((-30, -30), (180, -20), (140, 90), (260, 60))
    bot1 = smooth_curve((-30, 90), (100, 140), (230, 150), (320, 40))
    wave_ribbon(wd, top1, bot1, darker + (130,))

    top2 = smooth_curve((-30, 40), (120, 30), (90, 130), (200, 100))
    bot2 = smooth_curve((-30, 130), (60, 180), (170, 190), (240, 110))
    wave_ribbon(wd, top2, bot2, lighter + (55,))

    # Bottom-right flowing ribbon
    top3 = smooth_curve((W + 30, H + 30), (W - 200, H + 10), (W - 150, H - 100), (W - 280, H - 70))
    bot3 = smooth_curve((W + 30, H - 90), (W - 100, H - 150), (W - 240, H - 160), (W - 340, H - 40))
    wave_ribbon(wd, top3, bot3, darker + (130,))

    top4 = smooth_curve((W + 30, H - 40), (W - 130, H - 30), (W - 100, H - 130), (W - 210, H - 100))
    bot4 = smooth_curve((W + 30, H - 130), (W - 60, H - 180), (W - 180, H - 190), (W - 250, H - 110))
    wave_ribbon(wd, top4, bot4, lighter + (50,))

    waves = waves.filter(ImageFilter.GaussianBlur(2))

    base.alpha_composite(waves)

    # subtle grain
    grain = Image.new('L', (W, H))
    gpx = grain.load()
    random.seed(42)
    for y in range(H):
        for x in range(W):
            gpx[x, y] = random.randint(118, 138)
    grain = grain.convert('RGBA')
    grain.putalpha(10)
    base.alpha_composite(grain)

    return base.convert('RGB')

if __name__ == '__main__':
    bg = make_background()
    bg.save('background_preview.png')
    print('saved')
