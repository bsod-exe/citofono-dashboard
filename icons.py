from PIL import Image, ImageDraw, ImageFilter

def glass_card(draw_target, box, radius=20, fill=(255,255,255,235), outline=(255,255,255,120)):
    """Draw a rounded glass-like card onto an RGBA image."""
    draw_target.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=1)

def _blurred_ellipse(size, fill, blur):
    img = Image.new('RGBA', size, (0,0,0,0))
    d = ImageDraw.Draw(img)
    d.ellipse([size[0]*0.1, size[1]*0.15, size[0]*0.9, size[1]*0.85], fill=fill)
    return img.filter(ImageFilter.GaussianBlur(blur))

def make_sun(sz=64):
    img = Image.new('RGBA', (sz, sz), (0,0,0,0))
    d = ImageDraw.Draw(img)
    cx, cy, r = sz/2, sz/2, sz*0.28
    # glow
    glow = _blurred_ellipse((sz, sz), (255, 200, 60, 120), sz*0.12)
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(255, 196, 60, 255))
    return img

def make_cloud_glass(sz=96, tint=(255,255,255)):
    """Glassmorphism style cloud: semi-transparent, blurred body, thin bright rim, small highlight."""
    W = H = sz
    base = Image.new('RGBA', (W, H), (0,0,0,0))

    # cloud silhouette mask made of overlapping ellipses
    mask = Image.new('L', (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([W*0.10, H*0.40, W*0.55, H*0.85], fill=255)
    md.ellipse([W*0.35, H*0.25, W*0.80, H*0.75], fill=255)
    md.ellipse([W*0.55, H*0.42, W*0.95, H*0.85], fill=255)
    md.ellipse([W*0.20, H*0.55, W*0.85, H*0.90], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))

    glass = Image.new('RGBA', (W, H), tint + (110,))
    base.paste(glass, (0,0), mask)

    # rim light: slightly eroded mask outline
    rim = Image.new('L', (W, H), 0)
    rd = ImageDraw.Draw(rim)
    rd.ellipse([W*0.10, H*0.40, W*0.55, H*0.85], outline=255, width=3)
    rd.ellipse([W*0.35, H*0.25, W*0.80, H*0.75], outline=255, width=3)
    rd.ellipse([W*0.55, H*0.42, W*0.95, H*0.85], outline=255, width=3)
    rim = rim.filter(ImageFilter.GaussianBlur(1))
    rim_layer = Image.new('RGBA', (W, H), (255,255,255,160))
    base.paste(rim_layer, (0,0), rim)

    # soft highlight top-left
    hl = Image.new('L', (W, H), 0)
    hd = ImageDraw.Draw(hl)
    hd.ellipse([W*0.18, H*0.22, W*0.5, H*0.45], fill=140)
    hl = hl.filter(ImageFilter.GaussianBlur(6))
    hl_layer = Image.new('RGBA', (W, H), (255,255,255,255))
    base.paste(hl_layer, (0,0), hl)

    return base

def make_sun_cloud(sz=96):
    img = Image.new('RGBA', (sz, sz), (0,0,0,0))
    sun = make_sun(int(sz*0.7))
    img.alpha_composite(sun, (int(sz*0.18), 0))
    cloud = make_cloud_glass(sz)
    img.alpha_composite(cloud, (0, int(sz*0.18)))
    return img

def make_cloud_only(sz=96):
    return make_cloud_glass(sz)

def make_rain_cloud(sz=96):
    img = make_cloud_glass(sz)
    d = ImageDraw.Draw(img)
    drop_color = (110, 170, 240, 230)
    for i in range(4):
        x = sz*0.28 + i*sz*0.14
        y0 = sz*0.72
        d.line([(x, y0), (x - sz*0.05, y0 + sz*0.18)], fill=drop_color, width=3)
    return img

def make_snow_cloud(sz=96):
    img = make_cloud_glass(sz)
    d = ImageDraw.Draw(img)
    flake_color = (255, 255, 255, 235)
    r = sz * 0.022
    for i in range(4):
        x = sz*0.28 + i*sz*0.14
        y = sz*0.80
        d.ellipse([x-r, y-r, x+r, y+r], fill=flake_color)
    return img

if __name__ == '__main__':
    icons = Image.new('RGBA', (500, 120), (30,60,40,255))
    icons.alpha_composite(make_sun(96), (0,0))
    icons.alpha_composite(make_sun_cloud(96), (100,0))
    icons.alpha_composite(make_cloud_only(96), (200,0))
    icons.alpha_composite(make_rain_cloud(96), (300,0))
    icons.save('icons_preview.png')
    print('ok')
