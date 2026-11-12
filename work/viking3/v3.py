import json, math, os, random, sys, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H, FPS, DUR = 1920, 1080, 30, 30.0
NF = int(DUR * FPS)
D = os.path.dirname(os.path.abspath(__file__))
V2 = '/workspace/work/viking2/'

def hexc(h, a=255):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(t): t = clamp(t); return t * t * (3 - 2 * t)
def eio(t): t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def back(t):
    t = clamp(t); c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

def fnt(path, sz, var=None, axes=None):
    f = ImageFont.truetype(path, sz)
    if var: f.set_variation_by_name(var)
    if axes: f.set_variation_by_axes(axes)
    return f
FRED = V2 + 'Fredoka.ttf'; NUN = V2 + 'Nunito.ttf'

INK = hexc('#121216')
WHITE = (255, 255, 255, 255)

# ======================================================= painting helpers
def vgrad(w, h, stops):
    col = Image.new('RGB', (1, 256)); px = col.load()
    for y in range(256):
        t = y / 255
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]; p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = (t - p0) / max(1e-6, p1 - p0); a, b = hexc(c0), hexc(c1)
                px[0, y] = tuple(int(lerp(a[j], b[j], k)) for j in range(3)); break
    return col.resize((w, h), Image.BILINEAR).convert('RGBA')

def glow(w, h, cx, cy, rx, ry, color, alpha):
    m = Image.new('L', (w // 4, h // 4), 0); d = ImageDraw.Draw(m)
    n = 30
    for i in range(n):
        k = 1 - i / n
        d.ellipse([(cx - rx * k) / 4, (cy - ry * k) / 4, (cx + rx * k) / 4, (cy + ry * k) / 4], fill=int(alpha * (i / n) ** 1.8))
    m = m.filter(ImageFilter.GaussianBlur(max(rx, ry) / 40)).resize((w, h), Image.BILINEAR)
    lay = Image.new('RGBA', (w, h), hexc(color)); lay.putalpha(m); return lay

def fastblur(img, r):
    if r < 0.6: return img
    if r < 3: return img.filter(ImageFilter.GaussianBlur(r))
    w, h = img.size
    sm = img.resize((max(1, w // 2), max(1, h // 2)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(r / 2))
    return sm.resize((w, h), Image.BILINEAR)

def shade_side(layer, mask, strength=80, side=1, color=(10, 10, 30)):
    w, h = layer.size
    g = Image.new('L', (w, h), 0); d = ImageDraw.Draw(g)
    if side > 0: d.rectangle([w * 0.6, 0, w, h], fill=strength)
    else: d.rectangle([0, 0, w * 0.4, h], fill=strength)
    g = g.filter(ImageFilter.GaussianBlur(w * 0.06))
    g = ImageChops.multiply(g, mask)
    dk = Image.new('RGBA', (w, h), color + (255,)); dk.putalpha(g)
    return Image.alpha_composite(layer, dk)

def shape_layer(size, draw_fn, color, shade=0, side=1):
    m = Image.new('L', size, 0); draw_fn(ImageDraw.Draw(m))
    lay = Image.new('RGBA', size, hexc(color)); lay.putalpha(m)
    if shade: lay = shade_side(lay, m, shade, side)
    return lay

# ======================================================= characters
# Units: R = head radius (px, in sprite). Sprite anchor: feet center bottom.
def draw_face(d, cx, cy, R, expr, blink, look):
    lx, ly = look
    er = 0.26 * R
    for s in (-1, 1):
        ex, ey = cx + s * 0.265 * R, cy - 0.02 * R
        if blink:
            d.line([ex - er * 0.9, ey + 0.04 * R, ex + er * 0.9, ey + 0.04 * R], fill=WHITE, width=max(2, int(0.06 * R)))
        else:
            d.ellipse([ex - er, ey - er * 1.05, ex + er, ey + er * 1.05], fill=WHITE)
            pr = 0.16 * R
            px, py = ex + lx * 0.07 * R, ey + ly * 0.06 * R + 0.02 * R
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=INK)
            d.ellipse([px - pr * 0.1, py - pr * 0.75, px + pr * 0.45, py - pr * 0.2], fill=WHITE)
        bw = max(2, int(0.055 * R))
        by = ey - er - 0.17 * R
        if expr in ('worried', 'scared'):
            inner = -0.07 * R; outer = 0.04 * R
            d.line([ex - s * 0.17 * R, by + outer, ex + s * 0.15 * R, by + inner], fill=WHITE, width=bw)
        elif expr in ('angry', 'smirk'):
            inner = (0.08 if expr == 'angry' else 0.04) * R; outer = -0.05 * R
            d.line([ex - s * 0.17 * R, by + outer, ex + s * 0.15 * R, by + inner], fill=WHITE, width=bw)
        else:
            d.arc([ex - 0.17 * R, by - 0.03 * R, ex + 0.17 * R, by + 0.13 * R], 205, 335, fill=WHITE, width=bw)
    my = cy + 0.43 * R; mw = max(2, int(0.05 * R))
    if expr == 'happy':
        d.arc([cx - 0.13 * R, my - 0.14 * R, cx + 0.13 * R, my + 0.06 * R], 15, 165, fill=WHITE, width=mw)
    elif expr in ('worried', 'scared'):
        d.ellipse([cx - 0.055 * R, my - 0.05 * R, cx + 0.055 * R, my + 0.08 * R], fill=WHITE)
    elif expr == 'angry':
        d.line([cx - 0.1 * R, my + 0.03 * R, cx + 0.1 * R, my - 0.005 * R], fill=WHITE, width=mw)
    else:
        d.arc([cx - 0.09 * R, my - 0.09 * R, cx + 0.09 * R, my + 0.03 * R], 25, 155, fill=WHITE, width=mw)

def head(img, cx, cy, R, rim):
    w, h = img.size
    d = ImageDraw.Draw(img)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=INK)
    a = Image.new('L', (w, h), 0); ImageDraw.Draw(a).ellipse([cx - R, cy - R, cx + R, cy + R], fill=255)
    b = Image.new('L', (w, h), 0); ImageDraw.Draw(b).ellipse([cx - R - 0.14 * R, cy - R - 0.06 * R, cx + R - 0.14 * R, cy + R - 0.06 * R], fill=255)
    m = ImageChops.subtract(a, b).filter(ImageFilter.GaussianBlur(max(1, 0.05 * R)))
    m = ImageChops.multiply(m, a)
    lay = Image.new('RGBA', (w, h), hexc(rim)); lay.putalpha(m.point(lambda v: int(v * 0.8)))
    img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    d.arc([cx - 0.78 * R, cy - 0.8 * R, cx + 0.2 * R, cy + 0.2 * R], 200, 245, fill=(255, 255, 255, 70), width=max(2, int(0.06 * R)))

def make_char(kind, R, v, expr='neutral', blink=False, look=(0, 0), pose='down'):
    """v: variant dict. Returns sprite RGBA, anchor bottom-center = feet."""
    SS = 2; R0 = R; R = R * SS
    w, h = int(R * 6.2), int(R * 12.2)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    cx = w / 2; feet = h - 0.15 * R
    hero = kind == 'hero'; jarl = kind == 'jarl'
    leg = (3.3 if hero else 2.7) * R
    bw = (1.98 if hero else 1.8) * R
    bh = (4.9 if hero else 4.5) * R
    if jarl: bw = 2.15 * R; bh = 4.7 * R
    b_bot = feet - leg; b_top = b_bot - bh
    hcy = b_top + 0.15 * R
    lw = max(3, int(0.12 * R))
    legcol = INK if hero else hexc('#2a2420')
    # legs
    for s in (-1, 1):
        x = cx + s * 0.36 * R
        d.line([x, b_bot - 0.3 * R, x, feet - 0.05 * R], fill=legcol, width=lw)
        if not hero:
            for k in range(4):  # leg wraps
                y = b_bot + 0.35 * R + k * 0.45 * R
                d.line([x - 0.11 * R, y, x + 0.11 * R, y + 0.12 * R], fill=hexc('#8f7a62'), width=max(2, int(0.07 * R)))
        d.ellipse([x - 0.17 * R + s * 0.05 * R, feet - 0.14 * R, x + 0.17 * R + s * 0.05 * R, feet + 0.06 * R], fill=INK)
    # cape (jarl) / back hair
    if jarl:
        d.polygon([(cx - 1.0 * R, b_top + 0.6 * R), (cx + 1.0 * R, b_top + 0.6 * R), (cx + 1.6 * R, b_bot + 0.5 * R), (cx - 1.6 * R, b_bot + 0.5 * R)], fill=hexc('#4f3f35'))
    if hero:  # hair halo + bun (behind head)
        hc = hexc(v.get('hair', '#3a2216'))
        d.ellipse([cx - 1.13 * R, hcy - 1.15 * R, cx + 1.13 * R, hcy + 1.0 * R], fill=hc)
        d.ellipse([cx - 0.42 * R, hcy - 1.62 * R, cx + 0.42 * R, hcy - 0.85 * R], fill=hc)
        d.arc([cx - 0.3 * R, hcy - 1.5 * R, cx + 0.3 * R, hcy - 0.95 * R], 200, 300, fill=(255, 255, 255, 60), width=max(2, int(0.05 * R)))
    # body
    coat = v.get('coat', '#E5453A' if hero else '#8B5E3C')
    def body(dd):
        if hero:
            dd.rounded_rectangle([cx - bw / 2, b_top, cx + bw / 2, b_bot], radius=bw * 0.45, fill=255)
            dd.rounded_rectangle([cx - bw / 2 - 0.06 * R, b_top + bh * 0.5, cx + bw / 2 + 0.06 * R, b_bot], radius=bw * 0.3, fill=255)
        else:
            hw = bw / 2; fl = hw + 0.28 * R
            dd.ellipse([cx - hw, b_top, cx + hw, b_top + 2 * hw], fill=255)
            dd.polygon([(cx - hw, b_top + hw), (cx + hw, b_top + hw), (cx + fl, b_bot - 0.12 * R), (cx - fl, b_bot - 0.12 * R)], fill=255)
            dd.rounded_rectangle([cx - fl, b_bot - 0.5 * R, cx + fl, b_bot], radius=0.18 * R, fill=255)
    lay = shape_layer((w, h), body, coat, 85, 1)
    img.alpha_composite(lay); d = ImageDraw.Draw(img)
    if hero:
        dk = v.get('coat_dk', '#B8332B')
        # hood ring around head (drawn after head as collar)
        # pocket
        d.rounded_rectangle([cx - 0.62 * R, b_bot - 1.55 * R, cx + 0.62 * R, b_bot - 0.75 * R], radius=0.2 * R, fill=hexc(dk, 150))
        # cuffs/hands
    else:
        tun2 = v.get('tunic', '#6d4a33')
        # tunic lower layer with stitched hem
        hw = bw / 2; fl = hw + 0.28 * R; mw = hw + 0.28 * R * (bh - 1.6 * R - hw) / (bh - hw)
        d.polygon([(cx - mw, b_bot - 1.6 * R), (cx + mw, b_bot - 1.6 * R), (cx + fl + 0.05 * R, b_bot - 0.12 * R), (cx - fl - 0.05 * R, b_bot - 0.12 * R)], fill=hexc(tun2))
        d.rounded_rectangle([cx - fl - 0.05 * R, b_bot - 0.5 * R, cx + fl + 0.05 * R, b_bot], radius=0.18 * R, fill=hexc(tun2))
        for k in range(7):
            x = cx - fl + 0.3 * R + k * (2 * fl - 0.6 * R) / 6
            d.line([x, b_bot - 0.35 * R, x, b_bot - 0.1 * R], fill=hexc('#d9b26a'), width=max(2, int(0.05 * R)))
        # belt
        d.rectangle([cx - mw - 0.02 * R, b_bot - 1.78 * R, cx + mw + 0.02 * R, b_bot - 1.5 * R], fill=hexc('#2e2119'))
        d.rounded_rectangle([cx - 0.2 * R, b_bot - 1.8 * R, cx + 0.2 * R, b_bot - 1.4 * R], radius=0.06 * R, fill=hexc('#E3B44C'))
        # chest straps
        d.line([cx - bw / 2 + 0.25 * R, b_top + 0.9 * R, cx + bw / 2 - 0.3 * R, b_bot - 1.8 * R], fill=hexc('#3a2a1e'), width=max(3, int(0.14 * R)))
        # fur mantle
        fur = v.get('fur', '#a8957f' if not jarl else '#d9d0c2')
        for k in range(8):
            x = cx - bw / 2 - 0.05 * R + k * (bw + 0.1 * R) / 7
            d.ellipse([x - 0.3 * R, b_top + 0.55 * R, x + 0.3 * R, b_top + 1.15 * R], fill=hexc(fur))
        if jarl:
            for k in range(3):
                d.ellipse([cx - 0.16 * R, b_top + 1.6 * R + k * 0.55 * R, cx + 0.16 * R, b_top + 1.92 * R + k * 0.55 * R], fill=hexc('#E3B44C'))
    # arms / hands
    hr = 0.19 * R
    def hand(x, y): d.ellipse([x - hr, y - hr, x + hr, y + hr], fill=INK)
    sleeve = hexc(coat)
    if pose == 'down':
        hand(cx - bw / 2 + 0.05 * R, b_bot - 0.45 * R); hand(cx + bw / 2 - 0.05 * R, b_bot - 0.45 * R)
    elif pose == 'up':
        for s in (-1, 1):
            d.line([cx + s * bw * 0.4, b_top + 1.2 * R, cx + s * 1.5 * R, b_top - 1.6 * R], fill=sleeve, width=int(0.42 * R))
            hand(cx + s * 1.55 * R, b_top - 1.75 * R)
    elif pose == 'tied':
        hand(cx - 0.2 * R, b_bot - 1.0 * R); hand(cx + 0.2 * R, b_bot - 1.0 * R)
        d.ellipse([cx - 0.45 * R, b_bot - 1.2 * R, cx + 0.45 * R, b_bot - 0.8 * R], outline=hexc('#6aa84f'), width=max(3, int(0.1 * R)))
        d.line([cx + 0.1 * R, b_bot - 0.85 * R, cx + 0.5 * R, b_bot + 1.0 * R], fill=hexc('#6aa84f'), width=max(3, int(0.08 * R)))
    elif pose == 'crossed':
        d.rounded_rectangle([cx - bw / 2 - 0.05 * R, b_top + 1.7 * R, cx + bw / 2 + 0.05 * R, b_top + 2.35 * R], radius=0.3 * R, fill=hexc(v.get('coat', '#8B5E3C')))
        d.rounded_rectangle([cx - bw / 2 - 0.05 * R, b_top + 1.7 * R, cx + bw / 2 + 0.05 * R, b_top + 2.35 * R], radius=0.3 * R, outline=(0, 0, 0, 70), width=max(2, int(0.04 * R)))
        hand(cx - bw / 2 + 0.2 * R, b_top + 2.02 * R); hand(cx + bw / 2 - 0.2 * R, b_top + 2.02 * R)
    elif pose == 'cling':
        hand(cx - bw / 2 + 0.05 * R, b_bot - 0.45 * R)
        d.line([cx + bw * 0.35, b_top + 1.0 * R, cx + 1.4 * R, b_top - 0.6 * R], fill=sleeve, width=int(0.42 * R))
        hand(cx + 1.45 * R, b_top - 0.75 * R)
    # weapon held at side
    wpn = v.get('weapon')
    if wpn == 'axe' and pose in ('down',):
        hx = cx + bw / 2 + 0.05 * R
        d.line([hx, b_top - 1.6 * R, hx, feet - 0.4 * R], fill=hexc('#7a5230'), width=max(3, int(0.13 * R)))
        d.polygon([(hx, b_top - 1.6 * R), (hx + 0.95 * R, b_top - 2.0 * R), (hx + 1.05 * R, b_top - 0.95 * R), (hx, b_top - 1.05 * R)], fill=hexc('#aab3bd'))
        d.polygon([(hx + 0.78 * R, b_top - 1.93 * R), (hx + 1.05 * R, b_top - 2.03 * R), (hx + 1.15 * R, b_top - 0.9 * R), (hx + 0.88 * R, b_top - 0.95 * R)], fill=hexc('#eef2f6'))
        hand(hx, b_bot - 0.45 * R)
    elif wpn == 'spear' and pose == 'down':
        hx = cx + bw / 2 + 0.05 * R
        d.line([hx, b_top - 3.2 * R, hx, feet - 0.2 * R], fill=hexc('#8a6238'), width=max(3, int(0.1 * R)))
        d.polygon([(hx, b_top - 3.9 * R), (hx + 0.2 * R, b_top - 3.2 * R), (hx - 0.2 * R, b_top - 3.2 * R)], fill=hexc('#c9d0d8'))
    # head
    head(img, cx, hcy, R, v.get('rim', '#F2A26A'))
    d = ImageDraw.Draw(img)
    viking = kind in ('viking', 'jarl')
    draw_face(d, cx, hcy + (0.06 * R if viking else 0.04 * R), R, expr, blink, look)
    if hero:
        # hood collar: ring hugging bottom of head
        col = Image.new('L', (w, h), 0); dc = ImageDraw.Draw(col)
        dc.ellipse([cx - 1.12 * R, hcy - 0.35 * R, cx + 1.12 * R, hcy + 1.28 * R], fill=255)
        dc.ellipse([cx - 0.92 * R, hcy - 1.0 * R, cx + 0.92 * R, hcy + 0.98 * R], fill=0)
        dc.rectangle([0, 0, w, hcy + 0.15 * R], fill=0)
        cl = Image.new('RGBA', (w, h), hexc(v.get('coat_dk', '#C93A30'))); cl.putalpha(col)
        img.alpha_composite(cl); d = ImageDraw.Draw(img)
        # drawstrings
        for s in (-1, 1):
            x = cx + s * 0.26 * R
            d.line([x, hcy + 1.05 * R, x + s * 0.02 * R, hcy + 2.25 * R], fill=(255, 255, 255, 235), width=max(2, int(0.06 * R)))
    if viking:
        beard = v.get('beard', '#C4622D'); bdk = v.get('beard_dk', '#9a4a20')
        def bd(dd):
            dd.polygon([(cx - 0.8 * R, hcy + 0.6 * R), (cx + 0.8 * R, hcy + 0.6 * R), (cx + 0.8 * R, hcy + 1.0 * R),
                        (cx + 0.35 * R, hcy + (1.95 if jarl else 1.55) * R), (cx - 0.35 * R, hcy + (1.95 if jarl else 1.55) * R), (cx - 0.8 * R, hcy + 1.0 * R)], fill=255)
        img.alpha_composite(shape_layer((w, h), bd, beard, 70, 1)); d = ImageDraw.Draw(img)
        if jarl:
            for s in (-1, 1):
                x = cx + s * 0.28 * R
                for k in range(3):
                    y = hcy + 2.0 * R + k * 0.3 * R
                    d.ellipse([x - 0.14 * R, y - 0.16 * R, x + 0.14 * R, y + 0.16 * R], fill=hexc(beard))
                d.ellipse([x - 0.09 * R, hcy + 2.85 * R, x + 0.09 * R, hcy + 3.02 * R], fill=hexc('#E3B44C'))
        my = hcy + 0.86 * R
        if expr == 'angry':
            d.rounded_rectangle([cx - 0.2 * R, my - 0.04 * R, cx + 0.2 * R, my + 0.08 * R], radius=0.05 * R, fill=INK)
        elif expr == 'happy':
            d.chord([cx - 0.22 * R, my - 0.12 * R, cx + 0.22 * R, my + 0.16 * R], 0, 180, fill=INK)
        elif expr == 'smirk':
            d.line([cx - 0.22 * R, my + 0.04 * R, cx + 0.1 * R, my + 0.04 * R], fill=INK, width=max(2, int(0.07 * R)))
            d.line([cx + 0.1 * R, my + 0.04 * R, cx + 0.26 * R, my - 0.08 * R], fill=INK, width=max(2, int(0.07 * R)))
        else:
            d.ellipse([cx - 0.11 * R, my - 0.04 * R, cx + 0.11 * R, my + 0.08 * R], fill=INK)
        d.ellipse([cx - 0.5 * R, hcy + 0.52 * R, cx + 0.03 * R, hcy + 0.74 * R], fill=hexc(bdk))
        d.ellipse([cx - 0.03 * R, hcy + 0.52 * R, cx + 0.5 * R, hcy + 0.74 * R], fill=hexc(bdk))
        hel = v.get('helmet', True)
        if hel:
            def hd(dd):
                dd.pieslice([cx - 1.04 * R, hcy - 1.1 * R, cx + 1.04 * R, hcy + 0.1 * R], 180, 360, fill=255)
            img.alpha_composite(shape_layer((w, h), hd, '#9aa4ae', 90, 1)); d = ImageDraw.Draw(img)
            d.rectangle([cx - 1.0 * R, hcy - 0.62 * R, cx + 1.0 * R, hcy - 0.48 * R], fill=hexc('#6b7580'))
            d.rectangle([cx - 0.07 * R, hcy - 1.07 * R, cx + 0.07 * R, hcy - 0.5 * R], fill=hexc('#6b7580'))
            d.arc([cx - 0.8 * R, hcy - 0.95 * R, cx + 0.1 * R, hcy - 0.15 * R], 200, 255, fill=(255, 255, 255, 160), width=max(2, int(0.07 * R)))
            if jarl:
                for s in (-1, 1):
                    d.polygon([(cx + s * 0.85 * R, hcy - 0.55 * R), (cx + s * 1.6 * R, hcy - 1.35 * R), (cx + s * 1.5 * R, hcy - 1.85 * R),
                               (cx + s * 1.28 * R, hcy - 1.25 * R), (cx + s * 0.72 * R, hcy - 0.9 * R)], fill=hexc('#efe6d2'))
        else:  # braided hair band
            hc = hexc(v.get('hair', '#C4622D'))
            d.chord([cx - 1.04 * R, hcy - 1.08 * R, cx + 1.04 * R, hcy + 0.6 * R], 180, 360, fill=hc)
            d.rectangle([cx - 1.02 * R, hcy - 0.32 * R, cx + 1.02 * R, hcy - 0.18 * R], fill=hexc('#E3B44C'))
    # shield in front
    sh = v.get('shield')
    if sh and pose != 'crossed':
        sr = (1.15 if not v.get('shield_up') else 1.1) * R
        sx, sy = cx - 0.55 * R, b_bot - 1.6 * R
        if v.get('shield_up'): sx, sy = cx + 0.1 * R, hcy - 2.3 * R
        img.alpha_composite(shield_img(sr, sh), (int(sx - sr * 1.05), int(sy - sr * 1.05)))
        d = ImageDraw.Draw(img)
        hand(sx + 0.8 * sr, sy + 0.15 * sr)
    if v.get('sweat'):
        x, y = cx - 1.0 * R, hcy - 0.1 * R
        d.polygon([(x, y - 0.32 * R), (x - 0.14 * R, y), (x + 0.14 * R, y)], fill=hexc('#7fcdfc'))
        d.ellipse([x - 0.14 * R, y - 0.14 * R, x + 0.14 * R, y + 0.15 * R], fill=hexc('#7fcdfc'))
        d.ellipse([x - 0.07 * R, y - 0.07 * R, x - 0.01 * R, y + 0.01 * R], fill=(255, 255, 255, 230))
    return img.resize((w // SS, h // SS), Image.LANCZOS)

_shc = {}
def shield_img(sr, sh):
    key = (int(sr), sh)
    if key in _shc: return _shc[key]
    s = int(sr * 2.1); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = s / 2
    d.ellipse([c - sr, c - sr, c + sr, c + sr], fill=hexc('#4f555c'))
    a, b = sh
    for k in range(8):
        d.pieslice([c - sr * 0.9, c - sr * 0.9, c + sr * 0.9, c + sr * 0.9], k * 45, k * 45 + 45, fill=hexc(a if k % 2 == 0 else b))
    for k in range(4):  # plank lines
        x = c - sr * 0.9 + (k + 1) * sr * 1.8 / 5
        d.line([x, c - sr * 0.85, x, c + sr * 0.85], fill=(0, 0, 0, 40), width=max(1, int(sr * 0.03)))
    d.ellipse([c - sr * 0.27, c - sr * 0.27, c + sr * 0.27, c + sr * 0.27], fill=hexc('#c3c9d0'))
    d.ellipse([c - sr * 0.15, c - sr * 0.2, c + sr * 0.05, c - sr * 0.02], fill=(255, 255, 255, 180))
    d.arc([c - sr * 0.8, c - sr * 0.8, c + sr * 0.8, c + sr * 0.8], 195, 250, fill=(255, 255, 255, 120), width=max(2, int(sr * 0.07)))
    m = Image.new('L', (s, s), 0); ImageDraw.Draw(m).rectangle([c, 0, s, s], fill=70)
    m = m.filter(ImageFilter.GaussianBlur(sr * 0.25))
    alpha = im.getchannel('A')
    m = ImageChops.multiply(m, alpha)
    dk = Image.new('RGBA', (s, s), (10, 10, 30, 255)); dk.putalpha(m)
    im = Image.alpha_composite(im, dk)
    _shc[key] = im; return im

# sprite cache: base sizes
_spc = {}
def sprite(kind, v, expr, blink, look, pose, R):
    base = 40 if R <= 40 else (80 if R <= 80 else 150)
    key = (kind, json.dumps(v, sort_keys=True), expr, blink, look, pose, base)
    if key not in _spc:
        _spc[key] = make_char(kind, base, v, expr, blink, look, pose)
    sp = _spc[key]
    k = R / base
    if abs(k - 1) < 0.01: return sp
    return sp.resize((max(1, int(sp.width * k)), max(1, int(sp.height * k))), Image.BILINEAR)

def blink_at(t, seed):
    rnd = random.Random(seed)
    bt = rnd.uniform(0.3, 2.0)
    while bt < 40:
        if 0 <= t - bt < 0.11: return True
        bt += rnd.uniform(1.8, 3.8)
    return False

# ======================================================= world / camera
class Actor:
    def __init__(s, kind, x, z, v=None, expr='neutral', pose='down', look=(0, 0), seed=0, size=1.0, bob=0.0):
        s.kind, s.x, s.z, s.v, s.expr, s.pose, s.look, s.seed, s.size, s.bob = kind, x, z, v or {}, expr, pose, look, seed, size, bob

HEAD_U = 0.13  # head radius in world units (m)

def render_world(frame, actors, cam, t, bg_layers):
    """cam: dict cx, cy(shift), cz, f, horizon, h, focus, ap"""
    cx, cz, f, hor, ch, foc, ap = cam['cx'], cam['cz'], cam['f'], cam['hor'], cam['h'], cam['focus'], cam['ap']
    items = []
    for a in actors:
        dz = a.z - cz
        if dz < 0.25: continue
        s = f / dz
        R = HEAD_U * s * a.size
        if R < 3: continue
        sx = W / 2 + (a.x - cx) * s
        fy = hor + ch * s
        if sx < -R * 6 or sx > W + R * 6: continue
        blur = ap * abs(1 / dz - 1 / foc) * 26
        items.append((dz, a, R, sx, fy, blur))
    items.sort(key=lambda i: -i[0])
    layer = None; lb = None; bbox = None
    def flush():
        nonlocal layer, lb, bbox
        if layer is None: return
        if lb >= 0.8 and bbox:
            x0, y0, x1, y1 = bbox
            pad = int(lb * 3) + 4
            x0, y0 = max(0, x0 - pad), max(0, y0 - pad); x1, y1 = min(W, x1 + pad), min(H, y1 + pad)
            if x1 > x0 and y1 > y0:
                crop = layer.crop((x0, y0, x1, y1))
                crop = fastblur(crop, lb)
                frame.alpha_composite(crop, (x0, y0))
        else:
            frame.alpha_composite(layer)
        layer = None; bbox = None
    for dz, a, R, sx, fy, blur in items:
        bq = round(blur * 2) / 2 if blur < 4 else round(blur)
        if layer is None or bq != lb:
            flush(); layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lb = bq
        expr = a.expr(t) if callable(a.expr) else a.expr
        look = a.look(t) if callable(a.look) else a.look
        pose = a.pose(t) if callable(a.pose) else a.pose
        sp = sprite(a.kind, a.v, expr, blink_at(t, a.seed), look, pose, R)
        bob = a.bob * abs(math.sin(t * 5 + a.seed)) * R * 0.15
        breath = 1 + 0.012 * math.sin(t * 2.2 + a.seed)
        if abs(breath - 1) > 0.004 and R > 30:
            sp = sp.resize((sp.width, int(sp.height * breath)), Image.BILINEAR)
        # shadow
        dsh = ImageDraw.Draw(layer)
        dsh.ellipse([sx - R * 1.1, fy - R * 0.18, sx + R * 1.1, fy + R * 0.18], fill=(40, 20, 20, 70))
        px, py = int(sx - sp.width / 2), int(fy - sp.height - bob)
        paste_safe(layer, sp, px, py)
        bx = (max(0, px), max(0, py), min(W, px + sp.width), min(H, py + sp.height))
        bbox = bx if bbox is None else (min(bbox[0], bx[0]), min(bbox[1], bx[1]), max(bbox[2], bx[2]), max(bbox[3], bx[3]))
    flush()

def paste_safe(dst, src, x, y):
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    if sx0 >= src.width or sy0 >= src.height: return
    dx, dy = max(0, x), max(0, y)
    w = min(src.width - sx0, dst.width - dx); h = min(src.height - sy0, dst.height - dy)
    if w <= 0 or h <= 0: return
    dst.alpha_composite(src, (dx, dy), (sx0, sy0, sx0 + w, sy0 + h))

def cam_bg(bg, zoom, ox=0, oy=0):
    BW, BH = bg.size
    cw, ch = W / zoom, H / zoom
    x0 = (BW - cw) / 2 + ox; y0 = (BH - ch) / 2 + oy
    x0 = clamp(x0, 0, BW - cw); y0 = clamp(y0, 0, BH - ch)
    return bg.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)

# ======================================================= environments
M = 1.25
BW, BH = int(W * M), int(H * M)

def fjord_beach(sky, sea, sand, mtn_cols, sun, hor_frac=0.40, seed=3, snow=True, trees='#5d4a6e'):
    img = vgrad(BW, BH, sky)
    d = ImageDraw.Draw(img)
    hy = BH * hor_frac
    rnd = random.Random(seed)
    if sun: img = Image.alpha_composite(img, glow(BW, BH, BW * sun[0], hy - 10, sun[1] * 1.6, sun[1], sun[2], 255)); d = ImageDraw.Draw(img)
    for li, (col, amp, base) in enumerate(mtn_cols):
        pts = [(-50, hy + 5)]; x = -50
        peaks = []
        while x < BW + 100:
            y = hy - base - rnd.uniform(0, amp); pts.append((x, y)); peaks.append((x, y)); x += rnd.uniform(140, 300)
            pts.append((x, hy - base * 0.4 - rnd.uniform(0, amp * 0.3))); x += rnd.uniform(80, 160)
        pts.append((BW + 100, hy + 5))
        d.polygon(pts, fill=hexc(col))
        if snow and li == 0:
            for (px, py) in peaks:
                d.polygon([(px, py), (px - 55, py + 45), (px - 20, py + 35), (px + 5, py + 50), (px + 30, py + 32), (px + 55, py + 45)], fill=hexc('#efe8f2', 200))
    # pine tree line on far shore
    for x in range(-20, BW + 20, 14):
        hh = rnd.uniform(14, 34)
        d.polygon([(x, hy + 4 - hh), (x - 8, hy + 6), (x + 8, hy + 6)], fill=hexc(trees))
    d.rectangle([0, hy + 3, BW, hy + 9], fill=hexc(trees))
    sea_h = int(BH * 0.16)
    img.paste(vgrad(BW, sea_h, sea), (0, int(hy + 8)))
    d = ImageDraw.Draw(img)
    for i in range(160):  # sparkles
        x = rnd.uniform(0, BW); y = hy + 12 + rnd.uniform(0, sea_h - 10)
        L = rnd.uniform(6, 30)
        d.line([x, y, x + L, y], fill=(255, 255, 255, rnd.randint(60, 150)), width=2)
    sy = int(hy + 8 + sea_h)
    img.paste(vgrad(BW, BH - sy, [(0, sand[0]), (1, sand[1])]), (0, sy))
    d = ImageDraw.Draw(img)
    # foam lines
    for k, (yy, a) in enumerate([(sy - 4, 240), (sy + 18, 120)]):
        d.line([(x, yy + 5 * math.sin(x / 90 + k)) for x in range(0, BW, 10)], fill=(255, 255, 255, a), width=7 - 3 * k)
        for x in range(0, BW, 37):
            d.ellipse([x, yy - 3 + 5 * math.sin(x / 90 + k), x + 6, yy + 3 + 5 * math.sin(x / 90 + k)], fill=(255, 255, 255, a))
    # sand specks / pebbles
    for i in range(120):
        x = rnd.uniform(0, BW); y = rnd.uniform(sy + 40, BH)
        r = rnd.uniform(2, 7) * (y - sy) / (BH - sy) + 1
        d.ellipse([x - r * 2, y - r, x + r * 2, y + r], fill=hexc(sand[1], 90))
    return img, hy

def snow_forest():
    img = vgrad(BW, BH, [(0, '#cfe6ea'), (0.5, '#b4d8d3'), (1, '#86b3a5')])
    d = ImageDraw.Draw(img); rnd = random.Random(9)
    img = Image.alpha_composite(img, glow(BW, BH, BW * 0.55, BH * 0.2, 700, 420, '#fff6dc', 210)); d = ImageDraw.Draw(img)
    for (col, sc, y0, n) in [('#9fc2bd', 0.75, 0.55, 18), ('#6f9f92', 1.0, 0.64, 13), ('#3f6f62', 1.35, 0.76, 9)]:
        for i in range(n):
            x = rnd.uniform(-60, BW + 60)
            if abs(x - BW * 0.5) < 160 * sc: x += 340 * sc * (1 if x > BW * 0.5 else -1)
            hh = rnd.uniform(260, 420) * sc; base = BH * y0 + rnd.uniform(-10, 20)
            d.line([x, base - hh * 0.2, x, base], fill=hexc('#4a3a30'), width=int(10 * sc))
            for k in range(4):
                ww = hh * (0.4 - k * 0.075); top = base - hh * (0.28 + k * 0.2)
                d.polygon([(x, top - hh * 0.26), (x - ww, top + hh * 0.2), (x + ww, top + hh * 0.2)], fill=hexc(col))
                d.polygon([(x, top - hh * 0.26), (x - ww * 0.55, top - hh * 0.03), (x - ww * 0.2, top - hh * 0.07), (x + ww * 0.1, top - hh * 0.02), (x + ww * 0.55, top - hh * 0.04)], fill=hexc('#f4f8f8'))
                d.line([x - ww, top + hh * 0.2, x + ww, top + hh * 0.2], fill=hexc('#f4f8f8'), width=int(6 * sc))
    d.rectangle([0, BH * 0.72, BW, BH], fill=hexc('#eef4f3'))
    d.polygon([(BW * 0.34, BH), (BW * 0.47, BH * 0.72), (BW * 0.53, BH * 0.72), (BW * 0.68, BH)], fill=hexc('#d3e0e0'))
    for i in range(60):
        x = rnd.uniform(0, BW); y = rnd.uniform(BH * 0.74, BH)
        d.ellipse([x - 20, y - 4, x + 20, y + 4], fill=hexc('#dbe7e7'))
    rays = Image.new('L', (BW, BH), 0); dr = ImageDraw.Draw(rays)
    for k in range(6):
        x = BW * (0.18 + k * 0.14)
        dr.polygon([(x, 0), (x + 70, 0), (x - 160, BH), (x - 330, BH)], fill=60)
    rays = rays.filter(ImageFilter.GaussianBlur(50))
    rl = Image.new('RGBA', (BW, BH), hexc('#fff6dc')); rl.putalpha(rays)
    return Image.alpha_composite(img, rl), BH * 0.72

# ======================================================= props
def axe_img(L, ang, glint=0):
    s = 2; n = int(L * 1.5 * s)
    im = Image.new('RGBA', (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = n / 2; Ls = L * s
    d.line([c, c - Ls * 0.5, c, c + Ls * 0.6], fill=hexc('#7a5230'), width=int(Ls * 0.055))
    for k in range(3):
        y = c + Ls * (0.25 + k * 0.08)
        d.line([c - Ls * 0.03, y, c + Ls * 0.03, y + Ls * 0.03], fill=hexc('#3e2a1c'), width=int(Ls * 0.02))
    by = c - Ls * 0.4
    d.polygon([(c, by - Ls * 0.1), (c + Ls * 0.28, by - Ls * 0.24), (c + Ls * 0.34, by + Ls * 0.16), (c, by + Ls * 0.07)], fill=hexc('#a9b2bc'))
    d.polygon([(c + Ls * 0.23, by - Ls * 0.22), (c + Ls * 0.31, by - Ls * 0.26), (c + Ls * 0.38, by + Ls * 0.18), (c + Ls * 0.29, by + Ls * 0.15)], fill=hexc('#f2f5f8'))
    d.rectangle([c - Ls * 0.045, by - Ls * 0.12, c + Ls * 0.045, by + Ls * 0.09], fill=hexc('#5b636c'))
    im = im.rotate(ang, resample=Image.BICUBIC)
    return im.resize((n // s, n // s), Image.LANCZOS)

def star(d, x, y, r, a=255):
    col = (255, 250, 225, a)
    d.polygon([(x, y - r), (x + r * 0.16, y - r * 0.16), (x + r, y), (x + r * 0.16, y + r * 0.16), (x, y + r), (x - r * 0.16, y + r * 0.16), (x - r, y), (x - r * 0.16, y - r * 0.16)], fill=col)
    d.ellipse([x - r * 0.18, y - r * 0.18, x + r * 0.18, y + r * 0.18], fill=(255, 255, 255, a))

def glint(frame, x, y, r, k):
    if k <= 0 or k >= 1: return
    a = math.sin(k * math.pi)
    lay = Image.new('RGBA', (int(r * 4), int(r * 4)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    g = glow(int(r * 4), int(r * 4), r * 2, r * 2, r * 1.6, r * 1.6, '#fff1c0', int(160 * a))
    lay = Image.alpha_composite(lay, g); d = ImageDraw.Draw(lay)
    star(d, r * 2, r * 2, r * a, int(255 * a))
    paste_safe(frame, lay, x - r * 2, y - r * 2)

def boat_img(t, sc=1.0):
    s = 2; w_, h_ = int(560 * s), int(520 * s)
    im = Image.new('RGBA', (w_, h_), (0, 0, 0, 0)); d = ImageDraw.Draw(im); S = s
    d.polygon([(30 * S, 360 * S), (530 * S, 360 * S), (470 * S, 450 * S), (90 * S, 450 * S)], fill=hexc('#7a5234'))
    d.polygon([(30 * S, 360 * S), (530 * S, 360 * S), (520 * S, 378 * S), (40 * S, 378 * S)], fill=hexc('#9c6c45'))
    for k in range(5):
        d.line([(60 * S + k * 95 * S, 392 * S), (95 * S + k * 95 * S, 392 * S)], fill=hexc('#3c281a'), width=10 * S)
    d.rounded_rectangle([300 * S, 280 * S, 450 * S, 362 * S], radius=10 * S, fill=hexc('#d9c09a'))
    for k in range(3):
        x = 330 * S + k * 42 * S; d.ellipse([x - 12 * S, 305 * S, x + 12 * S, 329 * S], fill=hexc('#2a2018'))
    d.line([(210 * S, 30 * S), (210 * S, 362 * S)], fill=hexc('#4a3322'), width=10 * S)
    fl = 14 * math.sin(t * 7)
    d.polygon([(217 * S, 40 * S), (217 * S, 335 * S), ((390 + fl) * S, 335 * S)], fill=hexc('#ecdcbc'))
    d.polygon([(203 * S, 70 * S), (203 * S, 335 * S), ((70 - fl) * S, 335 * S)], fill=hexc('#d6c29d'))
    return im.resize((int(w_ / s * sc), int(h_ / s * sc)), Image.LANCZOS)

def waves(frame, t, col, y0, amp, ph, sp, line='#e9cfa0', la=150):
    d = ImageDraw.Draw(frame)
    pts = [(x, y0 + amp * math.sin(x / 140 + t * sp + ph) + amp * 0.4 * math.sin(x / 61 - t * sp * 1.6)) for x in range(-30, W + 60, 20)]
    d.polygon(pts + [(W + 60, H), (-30, H)], fill=hexc(col))
    d.line(pts, fill=hexc(line, la), width=4)

# ======================================================= UI
NAVY = hexc('#1b2140', 238); GOLD = hexc('#E9BC3F')
def rr_img(w, h, rad, fill, outline=None, ow=0, glow_col=None):
    pad = 40 if glow_col else 4
    img = Image.new('RGBA', ((w + pad * 2) * 2, (h + pad * 2) * 2), (0, 0, 0, 0))
    if glow_col:
        g = Image.new('RGBA', img.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle([pad * 2, pad * 2, (pad + w) * 2, (pad + h) * 2], radius=rad * 2, fill=hexc(glow_col, 170))
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(36)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad * 2, pad * 2, (pad + w) * 2, (pad + h) * 2], radius=rad * 2, fill=fill, outline=outline, width=ow * 2)
    return img.resize((w + pad * 2, h + pad * 2), Image.LANCZOS), pad

def axe_icon(d, x, y, s, col=GOLD):
    d.line([x - 10 * s, y + 11 * s, x + 8 * s, y - 9 * s], fill=col, width=max(2, int(3.2 * s)))
    d.polygon([(x + 2 * s, y - 13 * s), (x + 13 * s, y - 7 * s), (x + 9 * s, y + 1 * s), (x + 4 * s, y - 4 * s)], fill=col)

def counter_img(n):
    img, p = rr_img(196, 60, 18, NAVY, GOLD, 3)
    d = ImageDraw.Draw(img)
    axe_icon(d, p + 38, p + 30, 1.3)
    f = fnt(NUN, 32, b'Black'); t = f'{n} / 100'
    bb = f.getbbox(t); d.text((p + 70, p + 30 - (bb[1] + bb[3]) / 2), t, font=f, fill=WHITE)
    return img

def vote_panel(n):
    w, h = 560, 140
    img, p = rr_img(w, h, 26, NAVY, GOLD, 4)
    d = ImageDraw.Draw(img)
    f = fnt(NUN, 18, b'ExtraBold'); t = 'S H I E L D S   R A I S E D'
    d.text((p + w / 2 - f.getlength(t) / 2, p + 14), t, font=f, fill=hexc('#cfd5ea'))
    axe_icon(d, p + 110, p + 82, 2.2)
    fb = fnt(NUN, 64, b'Black'); fs = fnt(NUN, 48, b'Black')
    num = str(n); nw = fb.getlength(num) + 30
    x0 = p + 215
    d.rounded_rectangle([x0, p + 46, x0 + nw, p + 116], radius=16, fill=WHITE)
    bb = fb.getbbox(num); d.text((x0 + 15, p + 81 - (bb[1] + bb[3]) / 2), num, font=fb, fill=hexc('#1b2140'))
    bb = fs.getbbox('/ 100'); d.text((x0 + nw + 12, p + 81 - (bb[1] + bb[3]) / 2), '/ 100', font=fs, fill=hexc('#9db8ff'))
    for k in range(70):
        x = p + 40 + k * 6.9; d.line([x, p + h - 12, x, p + h - 6], fill=hexc('#55607f'), width=2)
    return img

def title_card(day, sub):
    w, h = 560, 300
    img, p = rr_img(w, h, 28, hexc('#1b1a2a', 240), hexc('#3a3550'), 3, glow_col='#ffb84a')
    d = ImageDraw.Draw(img)
    # snowflake icon
    cx = p + w / 2; cy = p + 62
    for k in range(3):
        a = k * math.pi / 3
        d.line([cx - 18 * math.cos(a), cy - 18 * math.sin(a), cx + 18 * math.cos(a), cy + 18 * math.sin(a)], fill=hexc('#8fd0ff'), width=4)
    fb = fnt(FRED, 120, axes=[700, 100])
    bb = fb.getbbox(day); d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], p + 95 - bb[1] + 4), day, font=fb, fill=WHITE)
    fs = fnt(NUN, 26, b'Black')
    sw = fs.getlength(sub) + 40
    d.rounded_rectangle([cx - sw / 2, p + 230, cx + sw / 2, p + 270], radius=8, fill=GOLD)
    bb = fs.getbbox(sub); d.text((cx - fs.getlength(sub) / 2, p + 250 - (bb[1] + bb[3]) / 2), sub, font=fs, fill=hexc('#1b1a2a'))
    return img

def day_pill(day, sub):
    f1 = fnt(NUN, 26, b'Black'); f2 = fnt(NUN, 18, b'ExtraBold')
    w = int(f1.getlength(day) + f2.getlength(sub) + 110)
    img, p = rr_img(w, 52, 26, NAVY, hexc('#8fa6d6', 150), 2)
    d = ImageDraw.Draw(img)
    cx, cy = p + 32, p + 26
    for k in range(3):
        a = k * math.pi / 3
        d.line([cx - 10 * math.cos(a), cy - 10 * math.sin(a), cx + 10 * math.cos(a), cy + 10 * math.sin(a)], fill=hexc('#8fd0ff'), width=3)
    bb = f1.getbbox(day); d.text((p + 56, cy - (bb[1] + bb[3]) / 2), day, font=f1, fill=WHITE)
    x2 = p + 56 + f1.getlength(day) + 16
    bb = f2.getbbox(sub); d.text((x2, cy - (bb[1] + bb[3]) / 2), sub, font=f2, fill=hexc('#8fd0ff'))
    return img

def lastnight_img():
    f = fnt(NUN, 34, b'Black'); t = 'L A S T   N I G H T'
    w = int(f.getlength(t) + 70)
    img, p = rr_img(w, 66, 12, hexc('#1a140e', 235), hexc('#ffcf7a'), 3, glow_col='#ff9f3a')
    d = ImageDraw.Draw(img); bb = f.getbbox(t)
    d.text((p + 35, p + 33 - (bb[1] + bb[3]) / 2), t, font=f, fill=hexc('#ffe4ad'))
    return img

# ======================================================= captions
WORDS = json.load(open(V2 + 'vo/words.json'))
VO_START = [0.4, 4.55, 8.0, 12.75, 15.9, 20.55, 25.05]
CAP = fnt(FRED, 60, axes=[700, 100])
LBL = fnt(NUN, 22, b'Black')
TRACK = 3

def tracked_w(s):
    return sum(CAP.getlength(ch) for ch in s) + TRACK * (len(s) - 1)

def draw_tracked(d, x, y, s, col):
    for ch in s:
        d.text((x + 3, y + 5), ch, font=CAP, fill=(0, 0, 0, 120), stroke_width=7, stroke_fill=(0, 0, 0, 120))
        x += CAP.getlength(ch) + TRACK
    x0 = x
    return x0

def caption(frame, t):
    d = ImageDraw.Draw(frame)
    for li, line in enumerate(WORDS):
        st = VO_START[li]; ws = line['words']; toks = line['text'].split()
        chunks = []; cur = []
        for i, w_ in enumerate(ws):
            cur.append(i)
            tok = toks[i] if i < len(toks) else w_[2]
            if len(cur) >= 5 or tok.endswith((',', '.', '...')) or i == len(ws) - 1:
                chunks.append(cur); cur = []
        for ci, ch in enumerate(chunks):
            c0 = st + ws[ch[0]][0] - 0.06
            c1 = st + (ws[chunks[ci + 1][0]][0] - 0.06 if ci + 1 < len(chunks) else ws[ch[-1]][1] + 0.4)
            if c0 <= t < c1:
                lt = t - st
                disp = [toks[i] if i < len(toks) else ws[i][2] for i in ch]
                sp = 22
                widths = [tracked_w(s) for s in disp]
                total = sum(widths) + sp * (len(disp) - 1)
                x = W / 2 - total / 2; y = 948
                if line['spk'] == 'J':
                    lab = 'J A R L   B J O R N'
                    lw = LBL.getlength(lab) + 34
                    d.rounded_rectangle([W / 2 - lw / 2, y - 46, W / 2 + lw / 2, y - 10], radius=10, fill=hexc('#1b1a10', 220), outline=GOLD, width=2)
                    bb = LBL.getbbox(lab); d.text((W / 2 - LBL.getlength(lab) / 2, y - 28 - (bb[1] + bb[3]) / 2), lab, font=LBL, fill=GOLD)
                for k, (i, s, wd) in enumerate(zip(ch, disp, widths)):
                    nxt = ws[ch[k + 1]][0] if k + 1 < len(ch) else 99
                    on = ws[i][0] - 0.03 <= lt < nxt
                    col = hexc('#FFC93C') if on else WHITE
                    xx = x
                    for c in s:
                        d.text((xx + 3, y + 5), c, font=CAP, fill=(0, 0, 0, 110), stroke_width=7, stroke_fill=(0, 0, 0, 110))
                        xx += CAP.getlength(c) + TRACK
                    xx = x
                    for c in s:
                        d.text((xx, y), c, font=CAP, fill=col, stroke_width=6, stroke_fill=hexc('#15131a'))
                        xx += CAP.getlength(c) + TRACK
                    x += wd + sp
                return

# ======================================================= post
def make_post():
    vig = Image.new('L', (W // 4, H // 4), 0); d = ImageDraw.Draw(vig)
    n = 40
    for i in range(n):
        k = i / n
        d.ellipse([-W / 4 * 0.25 + k * W / 4 * 0.25, -H / 4 * 0.35 + k * H / 4 * 0.3, W / 4 * 1.25 - k * W / 4 * 0.25, H / 4 * 1.35 - k * H / 4 * 0.3], fill=int(255 * (k ** 0.7)))
    vig = vig.filter(ImageFilter.GaussianBlur(14)).resize((W, H), Image.BILINEAR)
    inv = vig.point(lambda v: int((255 - v) * 0.55))
    dark = Image.new('RGBA', (W, H), (40, 22, 18, 255)); dark.putalpha(inv)
    # film haze edges (light leak) - warm, at left/right edges
    hz = Image.new('L', (W // 4, H // 4), 0); dh = ImageDraw.Draw(hz)
    dh.rectangle([0, 0, 18, H // 4], fill=110); dh.rectangle([W // 4 - 18, 0, W // 4, H // 4], fill=90)
    hz = hz.filter(ImageFilter.GaussianBlur(16)).resize((W, H), Image.BILINEAR)
    haze = Image.new('RGBA', (W, H), (255, 228, 200, 255)); haze.putalpha(hz)
    grains = []
    for i in range(6):
        a = Image.frombytes('L', (W // 2, H // 2), os.urandom(W * H // 4)).resize((W, H), Image.BILINEAR).point(lambda v: v * 12 // 255)
        b = Image.frombytes('L', (W // 2, H // 2), os.urandom(W * H // 4)).resize((W, H), Image.BILINEAR).point(lambda v: v * 12 // 255)
        grains.append((Image.merge('RGB', (a, a, a)), Image.merge('RGB', (b, b, b))))
    return dark, haze, grains

# ======================================================= scenes
def V(**k): return k
COATS = ['#8B5E3C', '#6f4a33', '#7c6a4a', '#5d6b4a', '#7a3b2e', '#4f5f74']
SHIELDS = [('#B23A2E', '#EFE3C8'), ('#2E5E8C', '#E9C24A'), ('#3D7A4A', '#EFE3C8'), ('#7A3B2E', '#E0B34A'), ('#C9962E', '#7a4a22')]
BEARDS = [('#C4622D', '#9a4a20'), ('#8A5A2B', '#6a421f'), ('#D9A441', '#b5842a'), ('#5a3b22', '#3e2816'), ('#b8b2a8', '#8f897f')]
def rand_viking(rnd, shields_up=False, rim='#F2A26A'):
    b = rnd.choice(BEARDS)
    v = V(coat=rnd.choice(COATS), tunic=rnd.choice(['#6d4a33', '#5a4030', '#7a5a3a', '#4a3a2a']), beard=b[0], beard_dk=b[1], rim=rim,
          helmet=rnd.random() < 0.7, hair=rnd.choice(['#C4622D', '#D9A441', '#5a3b22']))
    r = rnd.random()
    if r < 0.6: v['shield'] = rnd.choice(SHIELDS)
    else: v['weapon'] = 'axe'
    if shields_up and 'shield' in v: v['shield_up'] = True
    return v

def crowd(seed, n_rows, per_row, z0, dz, xspan, exclude=None, shields_up=False, rim='#F2A26A', expr_choices=('neutral', 'angry', 'neutral')):
    rnd = random.Random(seed); out = []
    for r in range(n_rows):
        for i in range(per_row):
            z = z0 + r * dz + rnd.uniform(-0.25, 0.25)
            x = lerp(-xspan, xspan, (i + 0.5 * (r % 2)) / max(1, per_row - 1)) + rnd.uniform(-0.25, 0.25)
            if exclude and exclude(x, z): continue
            out.append(Actor('viking', x, z, rand_viking(rnd, shields_up, rim), expr=rnd.choice(expr_choices), seed=rnd.randint(0, 9999), size=rnd.uniform(0.95, 1.05)))
    return out

HERO_V = V(coat='#E5453A', coat_dk='#B8332B', hair='#3a2216', rim='#F6B07A')

def build():
    S = {}
    sunset = dict(sky=[(0, '#c9b6c4'), (0.25, '#f2c2b0'), (0.38, '#f8d2b4'), (0.42, '#efc0b8'), (1, '#e9b9a8')],
                  sea=[(0, '#6f8fae'), (1, '#8fb3c6')], sand=('#e8c6a2', '#d9a985'),
                  mtn_cols=[('#a98aae', 150, 70), ('#8c6f95', 70, 18)], sun=(0.55, 260, '#fff0c8'))
    S['beach'], S['beach_hor'] = fjord_beach(**sunset)
    cool = dict(sky=[(0, '#b9c3d3'), (0.3, '#d8d4d8'), (0.4, '#e7d9cf'), (1, '#d6c6bb')],
                sea=[(0, '#5f7c99'), (1, '#86a3b8')], sand=('#ddc7ad', '#c9ad92'),
                mtn_cols=[('#8a93ab', 170, 80), ('#6c7590', 80, 20)], sun=(0.35, 300, '#fff6e6'))
    S['cool'], S['cool_hor'] = fjord_beach(seed=5, **cool)
    S['forest'], S['forest_hor'] = snow_forest()
    # storm sepia
    st = vgrad(BW, BH, [(0, '#241a12'), (0.5, '#4a3622'), (1, '#2a1f15')])
    d = ImageDraw.Draw(st); rnd = random.Random(5)
    for i in range(18):
        x = rnd.uniform(0, BW); y = rnd.uniform(0, BH * 0.4); r = rnd.uniform(90, 220)
        d.ellipse([x - r * 1.7, y - r * 0.6, x + r * 1.7, y + r * 0.6], fill=hexc(rnd.choice(['#3b2d20', '#4f3c29', '#2f2318'])))
    st = st.filter(ImageFilter.GaussianBlur(18))
    st = Image.alpha_composite(st, glow(BW, BH, BW * 0.62, BH * 0.28, 600, 380, '#c08a48', 140))
    S['storm'] = st
    return S

# shot definitions: each returns frame for local time
def shot_list():
    return [
        ('boot', 0.0, 1.9), ('alone', 1.9, 3.3), ('reveal', 3.3, 4.5), ('trio', 4.5, 5.75), ('axes_up', 5.75, 6.65), ('surround', 6.65, 7.85),
        ('flash', 7.85, 8.75), ('storm', 8.75, 11.25), ('crash', 11.25, 12.55),
        ('jarl', 12.55, 14.25), ('plant', 14.25, 15.85),
        ('wide100', 15.85, 18.1), ('vote', 18.1, 20.5), ('hope', 20.5, 22.45), ('grump', 22.45, 23.75), ('raft', 23.75, 24.95),
        ('day1', 24.95, 26.45), ('march', 26.45, 30.01)]

def run(start, end, out=None, previews=None):
    S = build(); dark, haze, grains = make_post()
    counter = counter_img(0); vpanel = vote_panel(0); tcard = title_card('DAY 1', 'THE FJORD'); dpill = day_pill('DAY 1', 'THE FJORD'); lnight = lastnight_img()
    hero_rim = '#F6B07A'
    # actor sets
    def excl_center(x, z): return abs(x) < 0.9 and z < 6.5
    ring = crowd(11, 3, 9, 4.4, 1.3, 4.6, exclude=lambda x, z: abs(x) < 0.7 and z < 5.2)
    trio = [Actor('viking', -1.15, 3.2, V(coat='#7c6a4a', tunic='#5a4030', beard='#C4622D', beard_dk='#9a4a20', shield=('#B23A2E', '#EFE3C8'), helmet=True, rim='#F6B07A'), expr='angry', seed=21),
            Actor('viking', 0.0, 3.35, V(coat='#4f5f74', tunic='#4a3a2a', beard='#D9A441', beard_dk='#b5842a', weapon='axe', helmet=False, hair='#D9A441', rim='#F6B07A'), expr='neutral', seed=22),
            Actor('viking', 1.15, 3.2, V(coat='#7a3b2e', tunic='#6d4a33', beard='#5a3b22', beard_dk='#3e2816', shield=('#2E5E8C', '#E9C24A'), helmet=True, rim='#F6B07A'), expr='angry', seed=23)]
    trio_bg = crowd(12, 2, 8, 6.0, 1.6, 5.0)
    surround_bg = crowd(13, 2, 7, 2.6, 1.4, 2.6, exclude=lambda x, z: abs(x) < 0.55)
    jarl = Actor('jarl', 0.25, 4.2, V(coat='#7A3B2E', beard='#c2502a', beard_dk='#9c3e1f', helmet=True, rim='#F6B07A'), expr='angry', look=(-0.6, 0), seed=31, size=1.18)
    jarl_flank = crowd(14, 2, 8, 5.3, 1.5, 4.4, exclude=lambda x, z: abs(x - 0.25) < 1.4)
    big = crowd(15, 9, 14, 5.0, 0.75, 6.5, exclude=lambda x, z: abs(x) < 0.4 and z < 5.6)
    vote_row = crowd(16, 1, 7, 4.6, 1, 3.2, exclude=lambda x, z: abs(x) < 0.7, rim='#ffe2c4')
    vote_row2 = crowd(17, 2, 9, 6.4, 1.4, 4.6, rim='#ffe2c4')
    grump_bg = crowd(18, 2, 8, 4.4, 1.3, 3.8, shields_up=True, exclude=lambda x, z: abs(x) < 0.9, rim='#ffe2c4', expr_choices=('happy', 'neutral'))
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    frames = previews if previews else range(start, end)
    SH = shot_list()
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SH if s[1] <= t < s[2])
        lt = t - s0; u = lt / (s1 - s0)
        fr = None
        hor_b = S['beach_hor']
        def beachcam(cx, cz, f, focus, ap, bgz, bgblur, ox=0, oy=0, bg='beach'):
            img = cam_bg(S[bg], bgz, ox, oy)
            if bgblur: img = fastblur(img, bgblur)
            return img, dict(cx=cx, cz=cz, f=f, hor=(S[bg + '_hor'] - (BH - H / bgz) / 2 - oy) * bgz if False else H * 0.40, h=1.45, focus=focus, ap=ap)
        if name == 'boot':
            img = cam_bg(S['beach'], lerp(1.55, 1.62, u), 0, 260)
            fr = fastblur(img, 2.5)
            # foam washing over a yellow boot
            d = ImageDraw.Draw(fr)
            wash = 0.5 + 0.5 * math.sin(lt * 2.4 - 1.2)
            bx, by = W * 0.42, H * 0.66
            boot = Image.new('RGBA', (700, 700), (0, 0, 0, 0)); bd = ImageDraw.Draw(boot)
            bd.rounded_rectangle([200, 120, 380, 520], radius=50, fill=hexc('#F2B33D'))
            bd.rounded_rectangle([200, 400, 560, 540], radius=65, fill=hexc('#F2B33D'))
            bd.rounded_rectangle([190, 520, 575, 568], radius=20, fill=hexc('#3a3a3a'))
            bd.rounded_rectangle([190, 110, 390, 165], radius=24, fill=hexc('#d48f22'))
            bd.arc([225, 170, 345, 470], 185, 250, fill=(255, 255, 255, 150), width=14)
            bd.ellipse([470, 430, 520, 470], fill=(255, 255, 255, 90))
            boot = shade_side(boot, boot.getchannel('A'), 70, 1)
            boot = boot.rotate(68, expand=False, resample=Image.BICUBIC).resize((520, 520), Image.LANCZOS)
            paste_safe(fr, boot, bx - 260, by - 260 + wash * 6)
            # foam sheet
            fy = H * 0.5 + wash * H * 0.26
            foam = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(foam)
            pts = [(x, fy + 18 * math.sin(x / 120 + lt * 2)) for x in range(-20, W + 40, 20)]
            fd.polygon([(-20, 0), (W + 40, 0)] + pts[::-1], fill=(150, 200, 215, 120))
            fd.line(pts, fill=(255, 255, 255, 235), width=14)
            for x in range(0, W, 46):
                y = fy + 18 * math.sin(x / 120 + lt * 2) + 14
                fd.ellipse([x, y, x + 16, y + 9], fill=(255, 255, 255, 200))
            fr.alpha_composite(foam)
        elif name in ('alone', 'reveal'):
            if name == 'alone':
                z = lerp(1.12, 1.0, eio(u)); cz = lerp(-1.2, -0.6, eio(u)); foc = 3.0
            else:
                z = 1.0; cz = lerp(-0.6, -3.6, eio(u)); foc = lerp(3.0, 5.6, eio(u))
            fr = cam_bg(S['beach'], 1.0 + 0.02 * z, 0, -40 if name == 'alone' else -40 + 30 * eio(u))
            fr = fastblur(fr, 1.4 if name == 'alone' else lerp(1.4, 0.5, eio(u)))
            cam = dict(cx=0, cz=cz, f=1500 * z, hor=H * 0.43, h=1.4, focus=foc - cz, ap=1.4)
            acts = [Actor('hero', 0, 3.0, HERO_V | V(sweat=lt > 0.6 or name == 'reveal'), expr='worried', look=(lambda tt: (-1, 0) if 2.4 < tt < 2.95 else (0.4, 0)), seed=1)]
            if name == 'reveal': acts += ring
            cam['focus'] = foc - cz
            render_world(fr, acts, cam, t, None)
        elif name == 'trio':
            fr = fastblur(cam_bg(S['beach'], 1.05 + 0.03 * u, -40 * u, -40), 5 * 0.35)
            cam = dict(cx=lerp(-0.25, 0.25, eio(u)), cz=lerp(0.2, 0.55, eio(u)), f=1500, hor=H * 0.45, h=0.92, focus=lerp(5.5, 2.8, eio(u * 2.5)), ap=1.6)
            render_world(fr, trio_bg + trio, cam, t, None)
            for i, a in enumerate(trio):
                if 'weapon' in a.v or True:
                    pass
            # glints on spear/axe tips
            glint(fr, W * 0.53, H * 0.12, 36, (lt - 0.35) / 0.5)
            glint(fr, W * 0.16, H * 0.25, 28, (lt - 0.7) / 0.5)
        elif name == 'axes_up':
            fr = fastblur(cam_bg(S['beach'], 1.12 + 0.03 * u, 0, -140), 7 * 0.35)
            fr = Image.alpha_composite(fr, glow(W, H, W * 0.55, H * 0.42, 520, 300, '#fff4d8', 230))
            for i in range(7):
                x = W * (0.08 + i * 0.14) + 30 * math.sin(i * 2.1)
                rise = eout((lt - 0.05 * i) / 0.35)
                L = 430 + 60 * math.sin(i * 1.7); yb = H * 0.66 + 50 * math.sin(i * 2.3)
                ax = axe_img(L, (i - 3) * 6 + 5 * math.sin(i))
                paste_safe(fr, ax, x - ax.width / 2, yb - ax.height / 2 + (1 - rise) * 500)
                glint(fr, x + L * 0.25, yb - L * 0.45 + (1 - rise) * 500, 30, (lt - 0.25 - 0.08 * i) / 0.45)
        elif name == 'surround':
            fr = fastblur(cam_bg(S['beach'], 1.2, 0, -80), 8 * 0.35)
            cam = dict(cx=0, cz=lerp(-0.4, -0.2, u), f=1500, hor=H * 0.42, h=0.95, focus=2.4 - lerp(-0.4, -0.2, u), ap=2.2)
            render_world(fr, surround_bg, cam, t, None)
            hero = Actor('hero', 0, 2.4, HERO_V | V(sweat=True), expr='scared', look=(lambda tt: (1, -1) if tt < 7.25 else (-1, -1)), seed=2)
            render_world(fr, [hero], cam, t, None)
            dz = 2.4 - cam['cz']; s = 1500 / dz
            hx, hy = W / 2, H * 0.42 + 0.95 * s
            headY = hy - HEAD_U * s * 8.2
            R = HEAD_U * s
            for i in range(6):
                th = math.radians(-172 + i * 32.8)
                k = eout((lt - 0.04 * i) / 0.32)
                L = 340
                dist = lerp(L * 1.8, R * 3.1 + L * 0.5, k)
                ax = axe_img(L, 90 - math.degrees(th))
                x = hx + math.cos(th) * dist; y = headY + math.sin(th) * dist
                paste_safe(fr, ax, x - ax.width / 2, y - ax.height / 2 + 2 * math.sin(t * 15 + i))
            for (gx, gy, gt) in [(-0.8, -0.9, 0.42), (0.7, -1.0, 0.5), (-0.2, -1.5, 0.6)]:
                glint(fr, hx + gx * R * 1.9, headY + gy * R * 1.6, 46, (lt - gt) / 0.4)
        elif name == 'flash':
            img = Image.new('RGBA', (W, H), hexc('#efe9df'))
            d = ImageDraw.Draw(img)
            b = boat_img(t, 1.4).convert('LA').convert('RGBA')
            b.putalpha(b.getchannel('A').point(lambda v: v // 3))
            paste_safe(img, b, W * 0.5 - b.width / 2, H * 0.48 - b.height / 2)
            for k in range(4):
                d.line([(x, H * 0.75 + k * 30 + 12 * math.sin(x / 80 + k)) for x in range(0, W, 12)], fill=(160, 150, 140, 90), width=3)
            st = cam_bg(S['storm'], 1.0)
            k = ease((lt - 0.45) / 0.45)
            fr = Image.blend(img, st, k)
        elif name in ('storm', 'crash'):
            zz = lerp(1.0, 1.06, ease(u)) if name == 'storm' else lerp(1.15, 1.22, u)
            fr = cam_bg(S['storm'], zz)
            waves(fr, t, '#3c2d1f', H * 0.6, 34, 1.0, 1.6)
            tilt = (9 * math.sin(t * 1.9) - 3) if name == 'storm' else lerp(-6, 24, eout(u * 1.5))
            bob = 18 * math.sin(t * 1.9 + 0.8)
            b = boat_img(t, 1.0)
            herosp = make_char_cached('hero', 26, HERO_V, 'scared', blink_at(t, 3), (0, -1), 'cling')
            b.alpha_composite(herosp, (int(160 - herosp.width / 2), int(362 - herosp.height)))
            b = b.rotate(tilt, resample=Image.BICUBIC, expand=True)
            sc = 1.25 if name == 'storm' else 2.0
            b = b.resize((int(b.width * sc * zz), int(b.height * sc * zz)), Image.BILINEAR)
            cxb = W * 0.5 if name == 'storm' else W * 0.42
            paste_safe(fr, b, cxb - b.width / 2, H * 0.6 + bob - b.height * 0.62)
            if name == 'crash':
                d = ImageDraw.Draw(fr)
                d.polygon([(W * 0.48, H), (W * 0.58, H * 0.68), (W * 0.66, H * 0.62), (W * 0.78, H * 0.74), (W * 0.86, H)], fill=hexc('#1a130d'))
            waves(fr, t, '#2a1f16', H * 0.8, 36, 2.3, 2.1)
            waves(fr, t, '#1d150e', H * 0.93, 26, 4.1, 2.6)
            rain(fr, t)
            for ft in ((0.9, 1.1) if name == 'storm' else (0.15,)):
                if 0 <= lt - ft < 0.12:
                    fr = Image.blend(fr, Image.new('RGBA', (W, H), (255, 236, 205, 255)), 0.6 * (1 - (lt - ft) / 0.12))
            if name == 'crash' and lt < 0.35:
                fr = shake(fr, 14 * (1 - lt / 0.35), t)
            if name == 'storm':
                k = back(lt / 0.35)
                if k > 0.02:
                    lb = lnight.resize((max(1, int(lnight.width * k)), max(1, int(lnight.height * k))), Image.BILINEAR)
                    paste_safe(fr, lb, W / 2 - lb.width / 2, 120 - lb.height / 2)
        elif name in ('jarl', 'plant'):
            if name == 'jarl':
                fr = fastblur(cam_bg(S['beach'], 1.04 + 0.03 * u, 60, -60), 4 * 0.35)
                cam = dict(cx=lerp(0.6, 0.3, eio(u)), cz=lerp(-0.4, 0.3, eio(u)), f=1500, hor=H * 0.42, h=1.35, focus=4.2 - lerp(-0.4, 0.3, eio(u)), ap=1.3)
                render_world(fr, jarl_flank + [jarl, Actor('hero', 2.05, 2.1, HERO_V | V(sweat=True), expr='worried', look=(-1, -0.5), seed=4)], cam, t, None)
            else:
                fr = fastblur(cam_bg(S['beach'], 1.1, 80, -60), 5 * 0.35)
                cam = dict(cx=0.45, cz=lerp(1.2, 1.5, u), f=1500, hor=H * 0.42, h=0.9, focus=4.2 - lerp(1.2, 1.5, u), ap=1.6)
                render_world(fr, jarl_flank + [jarl], cam, t, None)
                # axe planting
                drop = eout(lt / 0.16)
                ax = axe_img(640, -6)
                axx, axy = W * 0.74, H * 0.52
                paste_safe(fr, ax, axx - ax.width / 2, axy - ax.height / 2 - (1 - drop) * 700)
                dust(fr, axx, axy + 640 * 0.6 - 20, (lt - 0.12) / 0.9)
                hero = Actor('hero', -0.55, 2.05, HERO_V | V(sweat=True), expr='scared', look=(1, -0.6), seed=5)
                render_world(fr, [hero], cam, t, None)
                if lt < 0.3: fr = shake(fr, 12 * (1 - lt / 0.3), t)
                glint(fr, axx + 100, axy - 240, 40, (lt - 0.3) / 0.5)
        elif name == 'wide100':
            fr = cam_bg(S['cool'], 1.0 + 0.04 * u, 0, -30)
            fr = fastblur(fr, 1.2)
            cam = dict(cx=lerp(-0.4, 0.4, u), cz=lerp(-2.5, -1.6, eio(u)), f=1500, hor=H * 0.36, h=2.3, focus=8.0, ap=0.8)
            render_world(fr, big + [Actor('hero', 0, 4.8, HERO_V, expr='worried', seed=6)], cam, t, None)
        elif name in ('vote', 'hope'):
            fr = fastblur(cam_bg(S['cool'], 1.06 + 0.03 * u, 0, -60), 5 * 0.35)
            if name == 'vote':
                cam = dict(cx=lerp(-0.6, 0.6, u), cz=lerp(0.4, 0.8, u), f=1500, hor=H * 0.43, h=1.35, focus=4.6 - lerp(0.4, 0.8, u), ap=1.2)
                render_world(fr, vote_row2 + vote_row, cam, t, None)
            else:
                cam = dict(cx=0, cz=lerp(0.2, 0.75, eio(u)), f=1500, hor=H * 0.43, h=1.35, focus=2.9 - lerp(0.2, 0.75, eio(u)), ap=1.6)
                pose = (lambda tt: 'up' if 21.0 < tt < 21.75 else 'down')
                expr = (lambda tt: 'happy' if tt < 21.75 else 'worried')
                render_world(fr, vote_row2 + vote_row + [Actor('hero', 0, 2.9, HERO_V, expr=expr, pose=pose, seed=7)], cam, t, None)
            kk = back((t - 18.25) / 0.4)
            if kk > 0.02:
                pb = vpanel.resize((max(1, int(vpanel.width * kk)), max(1, int(vpanel.height * kk))), Image.BILINEAR)
                paste_safe(fr, pb, W / 2 - pb.width / 2, 120 - pb.height / 2)
        elif name == 'grump':
            fr = fastblur(cam_bg(S['cool'], 1.1, 0, -60), 6 * 0.35)
            cam = dict(cx=0, cz=lerp(0.4, 0.6, u), f=1500, hor=H * 0.43, h=0.92, focus=2.6 - lerp(0.4, 0.6, u), ap=1.0)
            g = Actor('viking', 0.05, 2.6, V(coat='#5a4030', tunic='#4a3a2a', beard='#5a3b22', beard_dk='#3e2816', helmet=True, rim='#ffe2c4'), expr='angry', pose='crossed', look=(lambda tt: (1, 0) if tt < 23.1 else (-1, 0)), seed=8)
            render_world(fr, grump_bg + [g], cam, t, None)
            fr = Image.blend(fr, Image.new('RGBA', (W, H), (25, 30, 55, 255)), 0.22 * ease(u))
            if lt < 0.2: fr = Image.blend(fr, Image.new('RGBA', (W, H), (255, 255, 255, 255)), 0.3 * (1 - lt / 0.2))
        elif name == 'raft':
            fr = cam_bg(S['cool'], lerp(1.0, 1.05, u), 0, -150)
            fr = fastblur(fr, 1.5)
            d = ImageDraw.Draw(fr)
            rx, ry = W * 0.5, H * 0.47 - 20 * eout(u)
            for k in range(3):
                rr = 60 + k * 70 + lt * 60
                d.ellipse([rx - rr * 1.6, ry - rr * 0.25 + 10, rx + rr * 1.6, ry + rr * 0.25 + 10], outline=(255, 255, 255, max(0, 160 - k * 50)), width=3)
            d.rounded_rectangle([rx - 70, ry - 6, rx + 70, ry + 12], radius=6, fill=hexc('#7a5234'))
            hs = make_char_cached('hero', 9, HERO_V, 'worried', False, (0, 0), 'down')
            paste_safe(fr, hs, rx - hs.width / 2, ry - hs.height + 2)
            cam = dict(cx=0, cz=-1.0, f=1500, hor=H * 0.43, h=1.35, focus=4, ap=0.6)
            render_world(fr, [a for a in crowd(19, 1, 6, 3.5, 1, 3.8, exclude=lambda x, z: abs(x) < 1.6, rim='#ffe2c4')], cam, t, None)
            fr = Image.blend(fr, Image.new('RGBA', (W, H), (25, 30, 55, 255)), 0.25)
        elif name == 'day1':
            fr = fastblur(cam_bg(S['forest'], 1.05 + 0.02 * u), 9 * 0.35)
            snow(fr, t)
            k = back(lt / 0.4)
            if lt > 1.15: k = 1 - ease((lt - 1.15) / 0.35)
            if k > 0.02:
                tc = tcard.resize((max(1, int(tcard.width * k)), max(1, int(tcard.height * k))), Image.BILINEAR)
                paste_safe(fr, tc, W / 2 - tc.width / 2, H * 0.45 - tc.height / 2)
        elif name == 'march':
            fr = cam_bg(S['forest'], 1.0 + 0.04 * u)
            fr = fastblur(fr, 0.8)
            cz = lerp(0.0, 0.9, u)
            cam = dict(cx=0, cz=cz, f=1500, hor=H * 0.44, h=1.35, focus=3.2 - cz + 0.0 * u, ap=1.3)
            # actors walk toward camera slightly
            wz = 3.2 - 0.25 * u
            acts = [Actor('viking', -0.85, wz + 0.1, V(coat='#4f5f74', tunic='#4a3a2a', beard='#D9A441', beard_dk='#b5842a', weapon='axe', helmet=True, rim='#fff1d6'), expr='angry', seed=41, bob=1),
                    Actor('hero', 0, wz, HERO_V | V(sweat=True, rim='#fff1d6'), expr='worried', pose='tied', look=(lambda tt: (-0.8, 0) if tt < 28.2 else (0.8, 0)), seed=42, bob=1),
                    Actor('viking', 0.85, wz + 0.1, V(coat='#7a3b2e', tunic='#6d4a33', beard='#8A5A2B', beard_dk='#6a421f', shield=('#2E5E8C', '#E9C24A'), helmet=True, rim='#fff1d6'), expr='neutral', seed=43, bob=1)]
            render_world(fr, acts, cam, t, None)
            # blurred foreground pine branches
            fg = fg_branches()
            paste_safe(fr, fg, -60 * u, 0)
            snow(fr, t)
            k = back((lt - 0.05) / 0.4)
            if k > 0.02:
                pb = dpill.resize((max(1, int(dpill.width * k)), max(1, int(dpill.height * k))), Image.BILINEAR)
                paste_safe(fr, pb, 40, 36)
        # HUD
        if t >= 12.55 and name not in ('day1',):
            paste_safe(fr, counter, W - counter.width - 40, 36)
        # post
        if name not in ('flash',):
            fr = Image.alpha_composite(fr, glow_cache(name))
        fr = Image.alpha_composite(fr, haze)
        fr = Image.alpha_composite(fr, dark)
        caption(fr, t)
        rgb = fr.convert('RGB')
        ga, gb = grains[fi % 6]
        rgb = ImageChops.subtract(ImageChops.add(rgb, ga), gb)
        if t < 0.3: rgb = Image.blend(Image.new('RGB', (W, H)), rgb, t / 0.3)
        if t > DUR - 0.35: rgb = Image.blend(rgb, Image.new('RGB', (W, H)), (t - (DUR - 0.35)) / 0.35)
        if proc: proc.stdin.write(rgb.tobytes())
        else: rgb.save(os.path.join(D, f'prev/p_{t:05.2f}.jpg'), quality=90)
    if proc: proc.stdin.close(); proc.wait()

_mc = {}
def make_char_cached(kind, R, v, expr, blink, look, pose):
    key = (kind, R, json.dumps(v, sort_keys=True), expr, blink, look, pose)
    if key not in _mc: _mc[key] = make_char(kind, R, v, expr, blink, look, pose)
    return _mc[key]

_gc = {}
def glow_cache(name):
    if name not in _gc:
        if name in ('storm', 'crash'): _gc[name] = glow(W, H, W * 0.6, H * 0.25, 700, 360, '#ffb46a', 60)
        elif name in ('day1', 'march'): _gc[name] = glow(W, H, W * 0.55, H * 0.1, 900, 500, '#fff4dc', 90)
        elif name in ('grump', 'raft', 'vote', 'hope', 'wide100'): _gc[name] = glow(W, H, W * 0.35, H * 0.25, 900, 500, '#fff4e4', 80)
        else: _gc[name] = glow(W, H, W * 0.55, H * 0.36, 900, 480, '#fff0cc', 110)
    return _gc[name]

_fgb = {}
def fg_branches():
    if 'f' in _fgb: return _fgb['f']
    fg = Image.new('RGBA', (W + 200, H), (0, 0, 0, 0)); d = ImageDraw.Draw(fg)
    for (x, y, s) in [(20, H * 0.5, 1.4), (W + 120, H * 0.55, 1.5), (W * 0.08, H * 1.0, 1.1), (W * 1.02, H * 0.98, 1.2)]:
        for k in range(16):
            a = -math.pi / 2 + (k - 8) * 0.2
            L = 200 * s
            d.line([x, y + 50, x + math.cos(a) * L * 0.25, y + math.sin(a) * L], fill=hexc('#24503f'), width=int(20 * s))
        d.ellipse([x - 90 * s, y - 120 * s, x + 90 * s, y + 10 * s], fill=hexc('#f0f6f6', 200))
    fg = fastblur(fg, 14)
    _fgb['f'] = fg; return fg

SNOWP = [(random.Random(i).uniform(0, W), random.Random(i + 999).uniform(0, H), random.Random(i + 77).uniform(2, 7), random.Random(i + 55).uniform(0.3, 1)) for i in range(220)]
def snow(fr, t):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for (x, y, r, sp) in SNOWP:
        xx = (x + 26 * math.sin(t * 0.8 + y) + t * 25 * sp) % W; yy = (y + t * 80 * sp) % H
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 255, 255, int(210 * sp)))
    fr.alpha_composite(lay)

RAINP = [(random.Random(i).uniform(0, W * 1.3), random.Random(i + 5).uniform(0, H), random.Random(i + 9).uniform(0.5, 1)) for i in range(220)]
def rain(fr, t):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for (x, y, sp) in RAINP:
        yy = (y + t * 2000 * sp) % (H + 80) - 40; xx = (x - (y + t * 2000 * sp) * 0.3) % (W * 1.3) - 150
        d.line([xx, yy, xx - 16 * sp, yy + 50 * sp], fill=(235, 215, 180, int(120 * sp)), width=3)
    fr.alpha_composite(lay)

def dust(fr, x, y, k):
    if k <= 0 or k >= 1: return
    lay = Image.new('RGBA', (900, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(14):
        a = math.pi + i * math.pi / 13
        rr = 50 + 300 * eout(k)
        px = 450 + math.cos(a) * rr; py = 300 + math.sin(a) * rr * 0.28
        s = 26 + 50 * k
        d.ellipse([px - s, py - s * 0.8, px + s, py + s * 0.8], fill=(240, 214, 184, int(190 * (1 - k))))
    paste_safe(fr, fastblur(lay, 8), x - 450, y - 300)

def shake(fr, amp, t):
    dx = int(amp * math.sin(t * 91)); dy = int(amp * math.cos(t * 77))
    return ImageChops.offset(fr, dx, dy)

if __name__ == '__main__':
    if sys.argv[1] == 'prev':
        os.makedirs(os.path.join(D, 'prev'), exist_ok=True)
        run(0, 0, previews=[int(float(x) * FPS) for x in sys.argv[2:]])
    else:
        run(int(sys.argv[2]), int(sys.argv[3]), out=sys.argv[4])
