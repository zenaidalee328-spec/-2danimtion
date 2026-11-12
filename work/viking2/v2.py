import json, math, os, random, sys, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H, FPS, DUR = 1280, 720, 30, 30.0
NF = int(DUR * FPS)
SS = 2  # supersample for sprites
random.seed(7)
D = os.path.dirname(os.path.abspath(__file__))

def font(sz, w=b'Black'):
    f = ImageFont.truetype(os.path.join(D, 'Nunito.ttf'), sz)
    f.set_variation_by_name(w); return f

# ---------------- timing ----------------
WORDS = json.load(open(os.path.join(D, 'vo/words.json')))
VO_START = [0.35, 4.6, 8.15, 12.75, 15.9, 20.55, 25.0]
SHOTS = [  # name, start, end
    ('A', 0.0, 4.45), ('B', 4.45, 7.7), ('C', 7.7, 12.45), ('D', 12.45, 15.7),
    ('E', 15.7, 20.45), ('E2', 20.45, 24.75), ('F', 24.75, 30.0)]

def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(t): t = clamp(t); return t * t * (3 - 2 * t)
def easeout(t): t = clamp(t); return 1 - (1 - t) ** 3
def back(t):
    t = clamp(t); c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

def hexc(h, a=255):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

# ---------------- painting helpers ----------------
def vgrad(w, h, stops):
    """stops: list of (pos, hex)"""
    col = Image.new('RGB', (1, h))
    px = col.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]; p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = (t - p0) / max(1e-6, p1 - p0)
                a, b = hexc(c0), hexc(c1)
                px[0, y] = tuple(int(lerp(a[j], b[j], k)) for j in range(3)); break
    return col.resize((w, h))

def radial(w, h, cx, cy, rad, color, alpha=255):
    m = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(m)
    steps = 40
    for i in range(steps):
        r = rad * (1 - i / steps)
        d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=int(alpha * (i / steps) ** 1.6))
    m = m.filter(ImageFilter.GaussianBlur(rad / 12))
    lay = Image.new('RGBA', (w, h), hexc(color)); lay.putalpha(m); return lay

def screen_add(base, lay):
    return Image.alpha_composite(base.convert('RGBA'), lay)

def grade(img, mul, add=(0, 0, 0)):
    r, g, b = img.convert('RGB').split()
    r = r.point(lambda v: min(255, int(v * mul[0] + add[0])))
    g = g.point(lambda v: min(255, int(v * mul[1] + add[1])))
    b = b.point(lambda v: min(255, int(v * mul[2] + add[2])))
    return Image.merge('RGB', (r, g, b))

def soft_shade(layer, shape_mask, side='right', strength=70, color=(0, 0, 0)):
    """darken one side of a shape softly"""
    w, h = layer.size
    g = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(g)
    if side == 'right':
        d.rectangle([w * 0.62, 0, w, h], fill=strength)
    else:
        d.rectangle([0, 0, w * 0.38, h], fill=strength)
    g = g.filter(ImageFilter.GaussianBlur(w * 0.08))
    g = ImageChops.multiply(g, shape_mask)
    dark = Image.new('RGBA', (w, h), color + (255,)); dark.putalpha(g)
    return Image.alpha_composite(layer, dark)

# ---------------- characters ----------------
INK = hexc('#15151c')

def mountain(d, pts, fill):
    d.polygon(pts, fill=fill)

def draw_face(d, cx, cy, r, expr, blink, look):
    lx, ly = look
    ex = 0.29 * r; ey = -0.04 * r
    ew, eh = 0.21 * r, 0.27 * r
    if expr == 'angry': eh *= 0.8
    for s in (-1, 1):
        x = cx + s * ex; y = cy + ey
        if blink:
            d.line([x - ew, y + 0.02 * r, x + ew, y + 0.02 * r], fill=(255, 255, 255, 255), width=max(2, int(0.05 * r)))
        else:
            d.ellipse([x - ew, y - eh, x + ew, y + eh], fill=(255, 255, 255, 255))
            pr = 0.11 * r
            px, py = x + lx * 0.07 * r, y + ly * 0.07 * r + 0.03 * r
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=INK)
            d.ellipse([px - pr * 0.35 + pr * 0.25, py - pr * 0.6, px + pr * 0.25 + pr * 0.25, py - pr * 0.05], fill=(255, 255, 255, 255))
        # brows
        bw = max(2, int(0.045 * r))
        by = y - eh - 0.12 * r
        if expr == 'worried':
            d.line([x - s * 0.13 * r, by - s * 0 - 0.06 * r * (1 if True else 0), x + s * 0.14 * r, by + 0.03 * r][::1] if False else
                   [x - 0.15 * r, by + (0.05 * r if s < 0 else -0.05 * r), x + 0.15 * r, by + (0.05 * r if s > 0 else -0.05 * r)],
                   fill=(255, 255, 255, 255), width=bw)
        elif expr == 'angry':
            d.line([x - 0.16 * r, by + (0.07 * r if s < 0 else -0.04 * r) * -1 + 0.04 * r, x + 0.16 * r, by + (0.07 * r if s > 0 else -0.04 * r) * -1 + 0.04 * r][::1],
                   fill=(255, 255, 255, 255), width=bw)
        else:
            d.arc([x - 0.15 * r, by - 0.02 * r, x + 0.15 * r, by + 0.12 * r], 200, 340, fill=(255, 255, 255, 255), width=bw)
    # mouth
    mw = max(2, int(0.045 * r))
    my = cy + 0.36 * r
    if expr == 'happy':
        d.arc([cx - 0.12 * r, my - 0.12 * r, cx + 0.12 * r, my + 0.06 * r], 20, 160, fill=(255, 255, 255, 255), width=mw)
    elif expr == 'worried':
        d.ellipse([cx - 0.05 * r, my - 0.05 * r, cx + 0.05 * r, my + 0.07 * r], fill=(255, 255, 255, 255))
    elif expr == 'angry':
        d.line([cx - 0.1 * r, my + 0.02 * r, cx + 0.1 * r, my - 0.01 * r], fill=(255, 255, 255, 255), width=mw)
    else:
        d.arc([cx - 0.09 * r, my - 0.08 * r, cx + 0.09 * r, my + 0.04 * r], 30, 150, fill=(255, 255, 255, 255), width=mw)

def head_with_rim(img, cx, cy, r, rim='#F4A86A', side=1):
    w, h = img.size
    rimL = Image.new('L', (w, h), 0); dd = ImageDraw.Draw(rimL)
    dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    cut = Image.new('L', (w, h), 0); dc = ImageDraw.Draw(cut)
    o = 0.09 * r * side
    dc.ellipse([cx - r - o, cy - r + 0.03 * r, cx + r - o, cy + r + 0.03 * r], fill=255)
    rimL = ImageChops.subtract(rimL, cut).filter(ImageFilter.GaussianBlur(max(1, r * 0.03)))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INK)
    lay = Image.new('RGBA', (w, h), hexc(rim)); lay.putalpha(rimL.point(lambda v: v * 0.85))
    img.alpha_composite(lay)

def person(kind, r, expr='neutral', blink=False, look=(0, 0), extra=None):
    """returns RGBA sprite at final scale, anchor = bottom center (feet)."""
    extra = extra or {}
    R = r * SS
    wid = int(R * 5.2); hei = int(R * 8.4)
    img = Image.new('RGBA', (wid, hei), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = wid / 2
    feet = hei - 0.1 * R
    big = 1.0
    if kind == 'jarl': big = 1.0
    leg_len = 2.0 * R
    torso_h = 3.0 * R; torso_w = 1.62 * R
    if kind in ('viking', 'jarl'): torso_w = 1.95 * R; torso_h = 2.9 * R
    t_bot = feet - leg_len
    t_top = t_bot - torso_h
    hcy = t_top - 0.55 * R
    lw = max(3, int(0.13 * R))
    # legs
    for s in (-1, 1):
        x = cx + s * 0.32 * R
        d.line([x, t_bot - 0.2 * R, x + s * 0.04 * R, feet], fill=INK, width=lw)
        d.ellipse([x + s * 0.04 * R - 0.16 * R, feet - 0.12 * R, x + s * 0.04 * R + 0.16 * R, feet + 0.04 * R], fill=INK)
    # cape for jarl
    if kind == 'jarl':
        d.rounded_rectangle([cx - 1.35 * R, t_top - 0.1 * R, cx + 1.35 * R, t_bot + 0.55 * R], radius=0.6 * R, fill=hexc('#5c4a3d'))
        for i in range(9):
            x = cx - 1.3 * R + i * 0.33 * R
            d.ellipse([x - 0.22 * R, t_bot + 0.3 * R, x + 0.22 * R, t_bot + 0.72 * R], fill=hexc('#5c4a3d'))
    # torso
    coat = {'hero': '#F2B33D', 'viking': extra.get('coat', '#8B5E3C'), 'jarl': '#7A3B2E'}[kind]
    tm = Image.new('L', (wid, hei), 0)
    ImageDraw.Draw(tm).rounded_rectangle([cx - torso_w / 2, t_top, cx + torso_w / 2, t_bot], radius=torso_w * 0.42, fill=255)
    tl = Image.new('RGBA', (wid, hei), hexc(coat)); tl.putalpha(tm)
    tl = soft_shade(tl, tm, 'right', 90)
    img.alpha_composite(tl)
    d = ImageDraw.Draw(img)
    if kind == 'hero':
        # raincoat details: toggles + seam + pocket
        d.line([cx, t_top + 0.3 * R, cx, t_bot - 0.15 * R], fill=hexc('#C98A22'), width=max(2, int(0.05 * R)))
        for k in range(3):
            y = t_top + 0.75 * R + k * 0.6 * R
            d.rounded_rectangle([cx - 0.1 * R, y - 0.05 * R, cx + 0.1 * R, y + 0.05 * R], radius=0.04 * R, fill=hexc('#6b4a1e'))
        d.rounded_rectangle([cx - 0.62 * R, t_bot - 1.0 * R, cx - 0.2 * R, t_bot - 0.62 * R], radius=0.08 * R, outline=hexc('#C98A22'), width=max(2, int(0.04 * R)))
        # hood ring behind head
    if kind in ('viking', 'jarl'):
        # belt
        d.rectangle([cx - torso_w / 2 + 0.05 * R, t_bot - 0.95 * R, cx + torso_w / 2 - 0.05 * R, t_bot - 0.72 * R], fill=hexc('#3b2a1e'))
        d.rounded_rectangle([cx - 0.16 * R, t_bot - 0.98 * R, cx + 0.16 * R, t_bot - 0.69 * R], radius=0.05 * R, fill=hexc('#E0B34A'))
        # tunic hem
        for k in range(6):
            x = cx - torso_w / 2 + 0.2 * R + k * (torso_w - 0.4 * R) / 5
            d.ellipse([x - 0.05 * R, t_bot - 0.35 * R, x + 0.05 * R, t_bot - 0.25 * R], fill=hexc('#E0B34A'))
        # fur collar
        for k in range(7):
            x = cx - 0.95 * R + k * 0.32 * R
            d.ellipse([x - 0.25 * R, t_top - 0.12 * R, x + 0.25 * R, t_top + 0.32 * R], fill=hexc('#9c8a78' if kind == 'viking' else '#d8d0c4'))
    # hood ring / scarf
    if kind == 'hero':
        d.ellipse([cx - 0.9 * R, t_top - 0.25 * R, cx + 0.9 * R, t_top + 0.35 * R], fill=hexc('#D9952A'))
        d.rounded_rectangle([cx - 0.75 * R, t_top - 0.05 * R, cx + 0.75 * R, t_top + 0.28 * R], radius=0.14 * R, fill=hexc('#D9443A'))
    # arms (simple: hands at sides) unless custom
    hand_r = 0.17 * R
    arms = extra.get('arms', 'down')
    def hand(x, y):
        d.ellipse([x - hand_r, y - hand_r, x + hand_r, y + hand_r], fill=INK)
    if arms == 'down':
        hand(cx - torso_w / 2 - 0.02 * R, t_bot - 0.5 * R); hand(cx + torso_w / 2 + 0.02 * R, t_bot - 0.5 * R)
    elif arms == 'tied':
        hand(cx - 0.18 * R, t_bot - 0.55 * R); hand(cx + 0.18 * R, t_bot - 0.55 * R)
        d.ellipse([cx - 0.38 * R, t_bot - 0.72 * R, cx + 0.38 * R, t_bot - 0.38 * R], outline=hexc('#5aa04a'), width=max(3, int(0.07 * R)))
        d.line([cx, t_bot - 0.4 * R, cx + 0.15 * R, t_bot + 0.6 * R], fill=hexc('#5aa04a'), width=max(3, int(0.06 * R)))
    elif arms == 'crossed':
        d.rounded_rectangle([cx - torso_w / 2 + 0.05 * R, t_top + 1.0 * R, cx + torso_w / 2 - 0.05 * R, t_top + 1.45 * R], radius=0.2 * R, fill=hexc(coat))
        d.rounded_rectangle([cx - torso_w / 2 + 0.05 * R, t_top + 1.0 * R, cx + torso_w / 2 - 0.05 * R, t_top + 1.45 * R], radius=0.2 * R, outline=(0, 0, 0, 60), width=max(2, int(0.03 * R)))
        hand(cx - torso_w / 2 + 0.15 * R, t_top + 1.22 * R); hand(cx + torso_w / 2 - 0.15 * R, t_top + 1.22 * R)
    elif arms == 'head':  # one hand on head (storm)
        hand(cx - torso_w / 2 - 0.02 * R, t_bot - 0.5 * R)
        d.line([cx + torso_w / 2 - 0.1 * R, t_top + 0.4 * R, cx + 0.9 * R, hcy - 0.2 * R], fill=hexc(coat), width=int(0.3 * R))
        hand(cx + 0.85 * R, hcy - 0.35 * R)
    # weapon
    wpn = extra.get('weapon')
    if wpn == 'axe':
        hx = cx + torso_w / 2 + 0.05 * R
        d.line([hx, t_bot - 3.2 * R, hx, feet - 0.1 * R], fill=hexc('#7a5230'), width=max(3, int(0.12 * R)))
        ax = [(hx, t_bot - 3.2 * R), (hx + 0.85 * R, t_bot - 3.55 * R), (hx + 0.95 * R, t_bot - 2.65 * R), (hx, t_bot - 2.75 * R)]
        d.polygon(ax, fill=hexc('#aeb6bf'))
        d.polygon([(hx + 0.7 * R, t_bot - 3.48 * R), (hx + 0.95 * R, t_bot - 3.58 * R), (hx + 1.05 * R, t_bot - 2.6 * R), (hx + 0.8 * R, t_bot - 2.65 * R)], fill=hexc('#e6ebf0'))
        hand(hx, t_bot - 0.6 * R)
    # head
    head_with_rim(img, cx, hcy, R, extra.get('rim', '#F4A86A'), extra.get('rimside', 1))
    d = ImageDraw.Draw(img)
    if kind == 'hero':
        d.ellipse([cx + 0.55 * R, hcy - 0.95 * R, cx + 1.15 * R, hcy - 0.2 * R], fill=INK)
        d.polygon([(cx + 0.95 * R, hcy - 0.5 * R), (cx + 1.35 * R, hcy + 0.6 * R), (cx + 1.0 * R, hcy + 1.0 * R), (cx + 0.7 * R, hcy - 0.2 * R)], fill=INK)
        # bangs bump
        d.ellipse([cx - 0.95 * R, hcy - 1.08 * R, cx + 0.15 * R, hcy - 0.45 * R], fill=INK)
        d.ellipse([cx - 0.1 * R, hcy - 1.12 * R, cx + 0.9 * R, hcy - 0.5 * R], fill=INK)
    draw_face(d, cx, hcy + (0.08 * R if kind in ('viking', 'jarl') else 0), R, expr, blink, look)
    if kind in ('viking', 'jarl'):
        beard = extra.get('beard', '#C4622D')
        # beard below eyes
        bp = [(cx - 0.85 * R, hcy + 0.25 * R), (cx + 0.85 * R, hcy + 0.25 * R), (cx + 0.7 * R, hcy + 1.05 * R), (cx + 0.2 * R, hcy + 1.45 * R), (cx - 0.2 * R, hcy + 1.45 * R), (cx - 0.7 * R, hcy + 1.05 * R)]
        bm = Image.new('L', img.size, 0); ImageDraw.Draw(bm).polygon(bp, fill=255)
        bm = bm.filter(ImageFilter.GaussianBlur(0.04 * R))
        bl = Image.new('RGBA', img.size, hexc(beard)); bl.putalpha(bm)
        bl = soft_shade(bl, bm, 'right', 70)
        img.alpha_composite(bl); d = ImageDraw.Draw(img)
        # mouth gap in beard
        my = hcy + 0.55 * R
        if expr == 'angry':
            d.rounded_rectangle([cx - 0.2 * R, my - 0.04 * R, cx + 0.2 * R, my + 0.08 * R], radius=0.05 * R, fill=INK)
        else:
            d.ellipse([cx - 0.12 * R, my - 0.04 * R, cx + 0.12 * R, my + 0.08 * R], fill=INK)
        # moustache
        dk = hexc(extra.get('beard_dk', '#A44E22'))
        d.ellipse([cx - 0.5 * R, hcy + 0.3 * R, cx + 0.02 * R, hcy + 0.55 * R], fill=dk)
        d.ellipse([cx - 0.02 * R, hcy + 0.3 * R, cx + 0.5 * R, hcy + 0.55 * R], fill=dk)
        if kind == 'jarl':
            for s in (-1, 1):
                x = cx + s * 0.32 * R
                for k in range(3):
                    y = hcy + 1.35 * R + k * 0.28 * R
                    d.ellipse([x - 0.13 * R, y - 0.15 * R, x + 0.13 * R, y + 0.15 * R], fill=hexc(beard))
                d.ellipse([x - 0.08 * R, hcy + 2.1 * R, x + 0.08 * R, hcy + 2.25 * R], fill=hexc('#E0B34A'))
        # helmet
        hm = Image.new('L', img.size, 0); dh = ImageDraw.Draw(hm)
        dh.pieslice([cx - 1.04 * R, hcy - 1.08 * R, cx + 1.04 * R, hcy + 0.9 * R], 180, 360, fill=255)
        dh.rectangle([cx - 1.04 * R, hcy - 0.12 * R, cx + 1.04 * R, hcy - 0.1 * R], fill=255)
        hl = Image.new('RGBA', img.size, hexc('#9AA4AF')); hl.putalpha(hm)
        hl = soft_shade(hl, hm, 'right', 90)
        img.alpha_composite(hl); d = ImageDraw.Draw(img)
        d.rectangle([cx - 1.05 * R, hcy - 0.3 * R, cx + 1.05 * R, hcy - 0.1 * R], fill=hexc('#6d7782'))
        d.rectangle([cx - 0.07 * R, hcy - 1.05 * R, cx + 0.07 * R, hcy + 0.18 * R], fill=hexc('#6d7782'))
        d.arc([cx - 0.75 * R, hcy - 0.95 * R, cx + 0.2 * R, hcy - 0.2 * R], 200, 260, fill=(255, 255, 255, 150), width=max(2, int(0.06 * R)))
        if kind == 'jarl':
            for s in (-1, 1):
                d.polygon([(cx + s * 0.85 * R, hcy - 0.55 * R), (cx + s * 1.55 * R, hcy - 1.35 * R), (cx + s * 1.45 * R, hcy - 1.75 * R), (cx + s * 1.25 * R, hcy - 1.2 * R), (cx + s * 0.75 * R, hcy - 0.85 * R)], fill=hexc('#efe6d2'))
    # shield in front
    if extra.get('shield'):
        sc = extra['shield']
        sx, sy, sr = cx - 0.55 * R, t_bot - 1.3 * R, 1.05 * R
        if extra.get('shield_up'):
            sx, sy = cx + 0.2 * R, hcy - 1.6 * R
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=hexc('#5a5f66'))
        d.pieslice([sx - sr * 0.9, sy - sr * 0.9, sx + sr * 0.9, sy + sr * 0.9], 0, 90, fill=hexc(sc[0]))
        d.pieslice([sx - sr * 0.9, sy - sr * 0.9, sx + sr * 0.9, sy + sr * 0.9], 90, 180, fill=hexc(sc[1]))
        d.pieslice([sx - sr * 0.9, sy - sr * 0.9, sx + sr * 0.9, sy + sr * 0.9], 180, 270, fill=hexc(sc[0]))
        d.pieslice([sx - sr * 0.9, sy - sr * 0.9, sx + sr * 0.9, sy + sr * 0.9], 270, 360, fill=hexc(sc[1]))
        d.ellipse([sx - 0.22 * sr, sy - 0.22 * sr, sx + 0.22 * sr, sy + 0.22 * sr], fill=hexc('#c9ced4'))
        d.arc([sx - 0.8 * sr, sy - 0.8 * sr, sx + 0.8 * sr, sy + 0.8 * sr], 200, 250, fill=(255, 255, 255, 110), width=max(2, int(0.08 * sr)))
        hand(sx + 0.75 * sr, sy + 0.1 * sr)
    if extra.get('sweat'):
        x, y = cx - 0.95 * R, hcy - 0.15 * R
        d.polygon([(x, y - 0.3 * R), (x - 0.13 * R, y), (x + 0.13 * R, y)], fill=hexc('#8fd3ff'))
        d.ellipse([x - 0.13 * R, y - 0.13 * R, x + 0.13 * R, y + 0.14 * R], fill=hexc('#8fd3ff'))
        d.ellipse([x - 0.06 * R, y - 0.06 * R, x - 0.0 * R, y + 0.02 * R], fill=(255, 255, 255, 220))
    out = img.resize((wid // SS, hei // SS), Image.LANCZOS)
    return out

_cache = {}
def sprite(kind, r, **kw):
    key = (kind, r) + tuple(sorted((k, str(v)) for k, v in kw.items()))
    if key not in _cache:
        ex = kw.pop('extra', None)
        _cache[key] = person(kind, r, extra=ex, **kw)
    return _cache[key]

def blink_at(t, seed):
    random.seed(seed)
    times = [random.uniform(0.6, 2.2)]
    while times[-1] < 40: times.append(times[-1] + random.uniform(1.8, 3.6))
    return any(0 <= t - bt < 0.12 for bt in times)

# ---------------- backgrounds ----------------
def crowd_layer(w, h, horizon, n, rr, seed, blur, coats, shields_up=False, rim='#F4A86A', spread=None):
    random.seed(seed)
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    xs = spread or [lerp(-60, w + 60, i / (n - 1)) for i in range(n)]
    for i, x in enumerate(xs):
        r = rr * random.uniform(0.9, 1.08)
        sh = None if random.random() < 0.2 else random.choice([('#B23A2E', '#EFE3C8'), ('#2E5E8C', '#E9C24A'), ('#3D7A4A', '#EFE3C8'), ('#7A3B2E', '#E0B34A')])
        ex = {'coat': random.choice(coats), 'shield': sh, 'beard': random.choice(['#C4622D', '#8A5A2B', '#D9A441', '#5a3b22']), 'rim': rim, 'shield_up': shields_up, 'weapon': 'axe' if (sh is None) else None}
        s = person('viking', r, expr=random.choice(['neutral', 'angry', 'neutral']), extra=ex)
        y = horizon + random.uniform(-6, 10)
        lay.alpha_composite(s, (int(x - s.width / 2), int(y - s.height)))
    return lay.filter(ImageFilter.GaussianBlur(blur))

def beach_bg(w, h, sky, sea, sand, mtn, sun=None, horizon=0.47):
    img = vgrad(w, h, sky).convert('RGBA')
    d = ImageDraw.Draw(img)
    hy = int(h * horizon)
    # fjord mountains
    random.seed(3)
    for layer, (col, amp, base) in enumerate(mtn):
        pts = [(0, h)]
        x = -50
        while x < w + 100:
            pts.append((x, hy - base - random.uniform(0, amp)))
            x += random.uniform(70, 160)
        pts.append((w + 100, h))
        d.polygon(pts, fill=hexc(col))
        # snow caps hint
    if sun:
        img = screen_add(img, radial(w, h, sun[0], sun[1], sun[2], sun[3], 200))
        d = ImageDraw.Draw(img)
    sea_img = vgrad(w, int(h * 0.2), sea).convert('RGBA')
    img.paste(sea_img, (0, hy))
    d = ImageDraw.Draw(img)
    sy = hy + int(h * 0.2) - 30
    d.rectangle([0, sy, w, h], fill=hexc(sand[0]))
    sand_img = vgrad(w, h - sy, [(0, sand[0]), (1, sand[1])]).convert('RGBA')
    img.paste(sand_img, (0, sy))
    d = ImageDraw.Draw(img)
    # foam line
    d.line([(x, sy + 4 * math.sin(x / 70)) for x in range(0, w, 8)], fill=(255, 255, 255, 230), width=6)
    return img

def make_grain():
    gs = []
    for i in range(6):
        a = Image.frombytes('L', (W // 2, H // 2), os.urandom((W // 2) * (H // 2))).resize((W, H), Image.NEAREST)
        a = a.point(lambda v: v * 9 // 255)
        b = Image.frombytes('L', (W // 2, H // 2), os.urandom((W // 2) * (H // 2))).resize((W, H), Image.NEAREST)
        b = b.point(lambda v: v * 9 // 255)
        gs.append((Image.merge('RGB', (a, a, a)), Image.merge('RGB', (b, b, b))))
    return gs

# ---------------- UI ----------------
NAVY = hexc('#1c2340', 235)
GOLD = hexc('#E7B93C')

def pill(text_parts, h=46):
    f1 = font(26, b'Black'); f2 = font(15, b'ExtraBold')
    tw = 0
    for t, f, col, gap in text_parts:
        tw += f.getlength(t) + gap
    w = int(tw + 70)
    img = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([3, 3, w * 2 - 3, h * 2 - 3], radius=h - 3, fill=NAVY, outline=hexc('#8fa6d6', 140), width=4)
    img = img.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    x = 48
    for t, f, col, gap in text_parts:
        bb = f.getbbox(t)
        d.text((x, h / 2 - (bb[1] + bb[3]) / 2), t, font=f, fill=col)
        x += f.getlength(t) + gap
    return img

def counter_box(n):
    w, h = 136, 44
    img = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([3, 3, w * 2 - 3, h * 2 - 3], radius=22, fill=NAVY, outline=GOLD, width=5)
    img = img.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    axe_icon(d, 26, 22, 1.0)
    f = font(24, b'Black')
    t = f'{n} / 100'
    bb = f.getbbox(t)
    d.text((52, h / 2 - (bb[1] + bb[3]) / 2), t, font=f, fill=(255, 255, 255, 255))
    return img

def axe_icon(d, x, y, s):
    d.line([x - 9 * s, y + 10 * s, x + 7 * s, y - 8 * s], fill=GOLD, width=max(2, int(3 * s)))
    d.polygon([(x + 2 * s, y - 12 * s), (x + 12 * s, y - 6 * s), (x + 8 * s, y + 1 * s), (x + 4 * s, y - 4 * s)], fill=GOLD)

def big_panel(n, label='SHIELDS RAISED'):
    w, h = 370, 96
    img = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, w * 2 - 4, h * 2 - 4], radius=26, fill=NAVY, outline=GOLD, width=6)
    img = img.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    f = font(13, b'ExtraBold')
    t = '  '.join(label)
    t = ' '.join(label.replace(' ', '  '))
    d.text((w / 2 - f.getlength(t) / 2, 10), t, font=f, fill=hexc('#d9dcea'))
    axe_icon(d, 70, 52, 1.6)
    fb = font(44, b'Black'); fs = font(34, b'Black')
    # number pill
    num = str(n)
    nw = fb.getlength(num) + 20
    d.rounded_rectangle([150, 30, 150 + nw, 78], radius=14, fill=(255, 255, 255, 255))
    d.text((150 + 10, 30 + 2 - 4), num, font=fb, fill=hexc('#1c2340'))
    d.text((150 + nw + 8, 36), '/ 100', font=fs, fill=hexc('#8fb0ff'))
    # tick bar
    for k in range(50):
        x = 40 + k * 5.8
        d.line([x, 86, x, 90], fill=hexc('#5a6688'), width=2)
    return img

CAP_F = font(46, b'Black')
LBL_F = font(20, b'Black')

def text_stroke(d, xy, t, f, fill, sw=4):
    d.text(xy, t, font=f, fill=fill, stroke_width=sw, stroke_fill=hexc('#14141c'))

def caption(frame, t):
    for li, line in enumerate(WORDS):
        st = VO_START[li]
        ws = line['words']
        if not ws: continue
        # chunks
        chunks = []; cur = []
        for w_ in ws:
            cur.append(w_)
            if len(cur) >= 6 or w_[2].endswith((',', '.')) or (w_ is ws[-1]):
                chunks.append(cur); cur = []
        if cur: chunks.append(cur)
        # punctuation from text
        toks = line['text'].split()
        for ci, ch in enumerate(chunks):
            c0 = st + ch[0][0] - 0.05
            c1 = st + (chunks[ci + 1][0][0] - 0.05 if ci + 1 < len(chunks) else ch[-1][1] + 0.45)
            if c0 <= t < c1:
                draw_chunk(frame, ch, t - st, line, toks)
                return

TOKMAP = {}
def draw_chunk(frame, ch, lt, line, toks):
    # map words to display tokens with punctuation
    ws = line['words']
    idx0 = ws.index(ch[0])
    disp = [toks[idx0 + k] if idx0 + k < len(toks) else w_[2] for k, w_ in enumerate(ch)]
    d = ImageDraw.Draw(frame)
    space = CAP_F.getlength(' ')
    widths = [CAP_F.getlength(s) for s in disp]
    total = sum(widths) + space * (len(disp) - 1)
    x = W / 2 - total / 2; y = 612
    if line['spk'] == 'J':
        lab = 'JARL BJORN'
        text_stroke(d, (W / 2 - LBL_F.getlength(lab) / 2, y - 34), lab, LBL_F, hexc('#E7B93C'), 3)
    for k, (s, wd) in enumerate(zip(disp, widths)):
        w_ = ch[k]
        on = w_[0] - 0.02 <= lt < (ch[k + 1][0] if k + 1 < len(ch) else 99)
        col = hexc('#FFC93C') if on else (255, 255, 255, 255)
        # shadow
        d.text((x + 2, y + 4), s, font=CAP_F, fill=(0, 0, 0, 110), stroke_width=4, stroke_fill=(0, 0, 0, 110))
        text_stroke(d, (x, y), s, CAP_F, col, 4)
        x += wd + space

# ---------------- shots ----------------
def build():
    S = {}
    M = 1.12  # margin for camera
    BW, BH = int(W * M), int(H * M)
    # A: sunset fjord beach
    bgA = beach_bg(BW, BH, [(0, '#f7b9a4'), (0.45, '#f6c9a8'), (0.55, '#e8a3a8'), (1, '#c98ea8')], [(0, '#7f86b8'), (1, '#9aa6cf')], ('#e9c9a6', '#d9a98a'), [('#b98fb0', 90, 40), ('#9a7aa0', 60, 10)], sun=(BW * 0.7, BH * 0.38, 330, '#ffd9a0'))
    crowdA = crowd_layer(BW, BH, int(BH * 0.69), 9, 30, 11, 4.5, ['#8B5E3C', '#6f4a33', '#7c6a4a'], rim='#ffc79a')
    bgA = Image.alpha_composite(bgA, crowdA).filter(ImageFilter.GaussianBlur(2.5))
    S['A'] = dict(bg=bgA)
    # E: overcast fjord beach (vote) - cooler
    bgE = beach_bg(BW, BH, [(0, '#c7c2c8'), (0.5, '#d8cfc9'), (1, '#b9b4bf')], [(0, '#6c7c99'), (1, '#8796b3')], ('#d8c3a8', '#c5ab90'), [('#8a8fa6', 110, 50), ('#6f758e', 70, 15)], sun=(BW * 0.3, BH * 0.25, 360, '#fff2dc'))
    crowdE = crowd_layer(BW, BH, int(BH * 0.69), 8, 32, 21, 5.5, ['#8B5E3C', '#6f4a33', '#5d6b4a'], rim='#ffe2c4')
    S['E'] = dict(bg=Image.alpha_composite(bgE, crowdE).filter(ImageFilter.GaussianBlur(2.5)))
    crowdE2 = crowd_layer(BW, BH, int(BH * 0.66), 10, 26, 31, 5, ['#8B5E3C', '#6f4a33', '#5d6b4a'], shields_up=True, rim='#ffe2c4')
    S['E2'] = dict(bg=Image.alpha_composite(bgE, crowdE2).filter(ImageFilter.GaussianBlur(3)))
    # D: jarl - dusk beach warm
    bgD = beach_bg(BW, BH, [(0, '#e9a98e'), (0.5, '#f0bc9a'), (1, '#c7889a')], [(0, '#6f6f9f'), (1, '#8a8bb8')], ('#e2bf9c', '#cf9f80'), [('#a07d99', 100, 45), ('#84688a', 60, 10)], sun=(BW * 0.25, BH * 0.35, 300, '#ffd6a0'))
    crowdD = crowd_layer(BW, BH, int(BH * 0.68), 7, 30, 41, 6, ['#8B5E3C', '#6f4a33'], rim='#ffc79a')
    S['D'] = dict(bg=Image.alpha_composite(bgD, crowdD).filter(ImageFilter.GaussianBlur(3)))
    # B: axes close-up - pink haze
    bgB = vgrad(BW, BH, [(0, '#e7a6a6'), (0.5, '#d99aa8'), (1, '#9c7ea6')]).convert('RGBA')
    bgB = screen_add(bgB, radial(BW, BH, BW * 0.5, BH * 0.45, 420, '#ffd2a8', 170))
    crowdB = crowd_layer(BW, BH, int(BH * 1.02), 6, 58, 51, 9, ['#8B5E3C', '#6f4a33'], rim='#ffc79a')
    S['B'] = dict(bg=Image.alpha_composite(bgB, crowdB))
    # C: storm, sepia/amber
    bgC = vgrad(BW, BH, [(0, '#2a2018'), (0.5, '#4a3826'), (1, '#2b2119')]).convert('RGBA')
    dC = ImageDraw.Draw(bgC)
    random.seed(5)
    for i in range(14):  # clouds
        x = random.uniform(0, BW); y = random.uniform(0, BH * 0.35); r = random.uniform(80, 180)
        dC.ellipse([x - r * 1.6, y - r * 0.6, x + r * 1.6, y + r * 0.6], fill=hexc(random.choice(['#3b2d20', '#4b3a29', '#332619'])))
    bgC = bgC.filter(ImageFilter.GaussianBlur(14))
    bgC = screen_add(bgC, radial(BW, BH, BW * 0.65, BH * 0.25, 350, '#a8783e', 120))
    S['C'] = dict(bg=bgC)
    # F: snowy pine forest
    bgF = vgrad(BW, BH, [(0, '#bcd9e0'), (0.55, '#a9cfc9'), (1, '#6f9f8f')]).convert('RGBA')
    dF = ImageDraw.Draw(bgF)
    random.seed(9)
    for layer, (col, sc, y0, n) in enumerate([('#8fb6b2', 0.8, 0.62, 12), ('#5f8f83', 1.0, 0.74, 9)]):
        for i in range(n):
            x = random.uniform(-50, BW + 50); hh = random.uniform(220, 360) * sc; base = BH * y0 + random.uniform(-10, 20)
            for k in range(4):
                ww = hh * (0.42 - k * 0.08)
                top = base - hh * (0.3 + k * 0.22)
                dF.polygon([(x, top - hh * 0.28), (x - ww, top + hh * 0.22), (x + ww, top + hh * 0.22)], fill=hexc(col))
                dF.polygon([(x, top - hh * 0.28), (x - ww * 0.5, top - hh * 0.06), (x + ww * 0.5, top - hh * 0.06)], fill=hexc('#f2f7f7'))
    dF.rectangle([0, BH * 0.74, BW, BH], fill=hexc('#eef4f3'))
    path = [(BW * 0.38, BH), (BW * 0.47, BH * 0.74), (BW * 0.55, BH * 0.74), (BW * 0.72, BH)]
    dF.polygon(path, fill=hexc('#d5e1e1'))
    bgF = bgF.filter(ImageFilter.GaussianBlur(5))
    # light rays
    rays = Image.new('L', (BW, BH), 0); dr = ImageDraw.Draw(rays)
    for k in range(5):
        x = BW * (0.2 + k * 0.16)
        dr.polygon([(x, 0), (x + 60, 0), (x - 120, BH), (x - 260, BH)], fill=55)
    rays = rays.filter(ImageFilter.GaussianBlur(40))
    rl = Image.new('RGBA', (BW, BH), hexc('#fff6dc')); rl.putalpha(rays)
    bgF = Image.alpha_composite(bgF, rl)
    S['F'] = dict(bg=bgF)
    # foreground pine branches for F (blurred)
    fgF = Image.new('RGBA', (BW, BH), (0, 0, 0, 0)); dfg = ImageDraw.Draw(fgF)
    for (x, y, s) in [(30, BH * 0.55, 1.3), (BW - 40, BH * 0.6, 1.4), (BW * 0.1, BH * 0.95, 1.0), (BW * 0.95, BH * 0.95, 1.1)]:
        for k in range(14):
            a = -math.pi / 2 + (k - 7) * 0.22
            L = 160 * s
            ex, ey = x + math.cos(a) * L * 0.2, y + math.sin(a) * L
            dfg.line([x, y + 40, ex, ey], fill=hexc('#2f5e4a'), width=int(16 * s))
    fgF = fgF.filter(ImageFilter.GaussianBlur(9))
    S['F']['fg'] = fgF
    return S

def cam(img, zoom, cx=0.5, cy=0.5, shake=(0, 0)):
    """crop margin image with zoom (1 = full-frame W*1.0 crop from center of BW)"""
    BW, BH = img.size
    cw, ch = W / zoom, H / zoom
    x0 = (BW - cw) * cx + shake[0]; y0 = (BH - ch) * cy + shake[1]
    return img.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)

def place(frame, spr, x, y, scale=1.0):
    if abs(scale - 1) > 1e-3:
        spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BILINEAR)
    frame.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height)))

def zoom_pos(x, y, z, cx=W / 2, cy=H / 2):
    return cx + (x - cx) * z, cy + (y - cy) * z

SNOW = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4.5), random.uniform(0.3, 1)) for _ in range(140)]
DUST = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 3.5), random.uniform(0.2, 1)) for _ in range(40)]
RAIN = [(random.uniform(0, W * 1.3), random.uniform(0, H), random.uniform(0.6, 1)) for _ in range(160)]
PETAL = None

def particles(frame, kind, t):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if kind == 'dust':
        for (x, y, r, sp) in DUST:
            xx = (x + t * 14 * sp) % W; yy = (y - t * 9 * sp + 6 * math.sin(t + x)) % H
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 240, 210, int(70 * sp)))
    elif kind == 'snow':
        for (x, y, r, sp) in SNOW:
            xx = (x + 20 * math.sin(t * 0.8 + y) + t * 18 * sp) % W; yy = (y + t * 55 * sp) % H
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 255, 255, int(200 * sp)))
    elif kind == 'rain':
        for (x, y, sp) in RAIN:
            yy = (y + t * 1400 * sp) % (H + 60) - 30; xx = (x - (y + t * 1400 * sp) * 0.35) % (W * 1.3) - 100
            d.line([xx, yy, xx - 12 * sp, yy + 34 * sp], fill=(230, 210, 180, int(110 * sp)), width=2)
    frame.alpha_composite(lay)

def axe_shape(L, ang, steel='#b7bfc8'):
    s = 2
    w_, h_ = int(L * 1.4 * s), int(L * 1.4 * s)
    im = Image.new('RGBA', (w_, h_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, cy = w_ / 2, h_ / 2
    # axe pointing up along -y, handle down
    d.line([cx, cy - L * 0.55 * s, cx, cy + L * 0.6 * s], fill=hexc('#7a5230'), width=int(L * 0.07 * s))
    d.line([cx + L * 0.015 * s, cy - L * 0.5 * s, cx + L * 0.015 * s, cy + L * 0.55 * s], fill=hexc('#9a6a40'), width=int(L * 0.02 * s))
    bx = cx; by = cy - L * 0.42 * s
    d.polygon([(bx, by - L * 0.12 * s), (bx + L * 0.3 * s, by - L * 0.26 * s), (bx + L * 0.36 * s, by + L * 0.18 * s), (bx, by + L * 0.08 * s)], fill=hexc(steel))
    d.polygon([(bx + L * 0.25 * s, by - L * 0.24 * s), (bx + L * 0.33 * s, by - L * 0.28 * s), (bx + L * 0.4 * s, by + L * 0.2 * s), (bx + L * 0.31 * s, by + L * 0.17 * s)], fill=hexc('#eef2f5'))
    d.rectangle([cx - L * 0.05 * s, cy - L * 0.5 * s, cx + L * 0.05 * s, cy - L * 0.3 * s], fill=hexc('#5d6670'))
    im = im.rotate(ang, resample=Image.BICUBIC)
    return im.resize((w_ // s, h_ // s), Image.LANCZOS)

def boat(t):
    s = 2; w_, h_ = 520 * s, 460 * s
    im = Image.new('RGBA', (w_, h_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    S_ = s
    # hull
    d.polygon([(40 * S_, 330 * S_), (480 * S_, 330 * S_), (420 * S_, 410 * S_), (100 * S_, 410 * S_)], fill=hexc('#6b4630'))
    d.line([(60 * S_, 345 * S_), (465 * S_, 345 * S_)], fill=hexc('#8a5c3d'), width=8 * S_)
    # cabin
    d.rounded_rectangle([280 * S_, 250 * S_, 420 * S_, 332 * S_], radius=10 * S_, fill=hexc('#d9c7a6'))
    for k in range(3):
        x = 305 * S_ + k * 40 * S_
        d.ellipse([x - 11 * S_, 280 * S_, x + 11 * S_, 302 * S_], fill=hexc('#2a241e'))
    # mast + sail
    d.line([(200 * S_, 40 * S_), (200 * S_, 330 * S_)], fill=hexc('#4a3322'), width=9 * S_)
    flap = 12 * math.sin(t * 7)
    d.polygon([(206 * S_, 50 * S_), (206 * S_, 300 * S_), ((360 + flap) * S_, 300 * S_)], fill=hexc('#e9dcc0'))
    d.polygon([(194 * S_, 70 * S_), (194 * S_, 300 * S_), ((80 - flap) * S_, 300 * S_)], fill=hexc('#d8c9aa'))
    return im.resize((w_ // s, h_ // s), Image.LANCZOS)

def waves(frame, t, col, y0, amp, ph, sp, alpha=255):
    d = ImageDraw.Draw(frame)
    pts = [(x, y0 + amp * math.sin(x / 110 + t * sp + ph) + amp * 0.4 * math.sin(x / 47 - t * sp * 1.7)) for x in range(-20, W + 40, 16)]
    d.polygon(pts + [(W + 40, H), (-20, H)], fill=hexc(col, alpha))
    d.line(pts, fill=hexc('#e6cfa6', 160), width=3)

def label_box(text, sub=None):
    f = font(30, b'Black')
    w = int(f.getlength(text) + 60); h = 58
    img = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    g = Image.new('RGBA', img.size, (0, 0, 0, 0)); dg = ImageDraw.Draw(g)
    dg.rounded_rectangle([20, 20, 20 + w, 20 + h], radius=12, fill=hexc('#ffb54a', 150))
    g = g.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(g)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], radius=12, fill=hexc('#1c1712', 230), outline=hexc('#ffcf7a'), width=3)
    bb = f.getbbox(text)
    d.text((20 + 30, 20 + h / 2 - (bb[1] + bb[3]) / 2), text, font=f, fill=hexc('#ffe2a8'))
    return img

def dust_puff(frame, x, y, k):
    if k <= 0 or k >= 1: return
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(10):
        a = math.pi + i * math.pi / 9
        rr = 40 + 160 * easeout(k)
        px = x + math.cos(a) * rr * (1 if i % 2 else 0.7); py = y + math.sin(a) * rr * 0.25
        s = 18 + 30 * k
        d.ellipse([px - s, py - s, px + s, py + s], fill=(235, 210, 180, int(170 * (1 - k))))
    frame.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6)))

_BUILT={}
def render(start=0, end=NF, out=None):
    if 'S' not in _BUILT: _BUILT['S']=build(); _BUILT['g']=make_grain()
    S=_BUILT['S']; grains=_BUILT['g']
    counter = counter_box(0)
    day1 = pill([('DAY 1', font(26, b'Black'), (255, 255, 255, 255), 14), ('THE FJORD', font(15, b'ExtraBold'), hexc('#8fd0ff'), 0)])
    lastnight = label_box('LAST NIGHT')
    panel = big_panel(0)
    title_f = font(18, b'Bold')
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in range(start, end):
        t = fi / FPS
        shot = next(s for s in SHOTS if s[1] <= t < s[2]) if t < SHOTS[-1][2] else SHOTS[-1]
        name, s0, s1 = shot; lt = t - s0; u = lt / (s1 - s0)
        if name == 'A':
            z = lerp(1.0, 1.07, ease(u))
            fr = cam(S['A']['bg'], lerp(1.0, 1.035, u)).convert('RGBA')
            particles(fr, 'dust', t)
            sp = sprite('hero', 56, expr='worried' if lt > 1.6 else 'neutral', blink=blink_at(t, 1), look=((-1, 0) if 2.2 < lt < 3.4 else (0, 0)), extra={'rim': '#ffc28c'})
            br = 1 + 0.008 * math.sin(t * 2.4)
            x, y = zoom_pos(W * 0.5, H * 0.42 + 5.65 * 56, z)
            place(fr, sp, x, y, z * br)
        elif name == 'B':
            z = lerp(1.05, 1.13, ease(u))
            fr = cam(S['B']['bg'], lerp(1.0, 1.04, u)).convert('RGBA')
            sp = sprite('hero', 95, expr='worried', blink=blink_at(t, 2), look=((1, -0.5) if lt < 1.2 else (-1, -0.5)), extra={'rim': '#ffc28c', 'sweat': lt > 0.9})
            hx, hy = zoom_pos(W * 0.5, H * 0.52 + 5.65 * 95, z)
            place(fr, sp, hx, hy, z)
            headx, heady = zoom_pos(W * 0.5, H * 0.52, z)
            for i in range(7):
                th = math.radians(-175 + i * (170 / 6))
                k = easeout((lt - 0.06 * i) / 0.45)
                L = 245 * z
                dist = lerp(L * 1.9, L * 0.55 + 95 * z * 1.95, k)
                im = axe_shape(L, 90 - math.degrees(th))
                jit = 2 * math.sin(t * 13 + i)
                ax_ = headx + math.cos(th) * dist; ay_ = heady + math.sin(th) * dist
                fr.alpha_composite(im, (int(ax_ - im.width / 2), int(ay_ - im.height / 2 + jit)))
            particles(fr, 'dust', t)
        elif name == 'C':
            z = lerp(1.0, 1.06, ease(u))
            fr = cam(S['C']['bg'], z * 0.98 + 0.02).convert('RGBA')
            waves(fr, t, '#3a2c1f', H * 0.62, 26, 1.0, 1.6)
            tilt = 9 * math.sin(t * 1.9) - 4
            bob = 14 * math.sin(t * 1.9 + 0.8)
            bt = boat(t)
            hero = sprite('hero', 19, expr='worried', blink=blink_at(t, 3), extra={'rim': '#d79a54', 'arms': 'head'})
            bt2 = bt.copy(); bt2.alpha_composite(hero, (int(150 - hero.width / 2 + 10), int(332 - hero.height)))
            bt2 = bt2.rotate(tilt, resample=Image.BICUBIC, expand=True)
            bx, by = zoom_pos(W * 0.47, H * 0.74 + bob, z)
            sc = z * 1.05
            bt2 = bt2.resize((int(bt2.width * sc), int(bt2.height * sc)), Image.BILINEAR)
            fr.alpha_composite(bt2, (int(bx - bt2.width / 2), int(by - bt2.height / 2 - 60)))
            waves(fr, t, '#2a1f16', H * 0.8, 30, 2.3, 2.1)
            waves(fr, t, '#1e160f', H * 0.92, 22, 4.1, 2.6)
            particles(fr, 'rain', t)
            # lightning flash
            for ft in (1.55, 1.75):
                if 0 <= lt - ft < 0.12:
                    fr = Image.blend(fr, Image.new('RGBA', (W, H), (255, 236, 205, 255)), 0.55 * (1 - (lt - ft) / 0.12))
            k = back(lt / 0.35)
            if k > 0.02:
                lb = lastnight.resize((max(1, int(lastnight.width * k)), max(1, int(lastnight.height * k))), Image.BILINEAR)
                fr.alpha_composite(lb, (int(W / 2 - lb.width / 2), int(58 - lb.height / 2 + 30)))
        elif name == 'D':
            z = lerp(1.0, 1.08, ease(u))
            shake = (0, 0)
            if lt < 0.25: shake = (random.uniform(-6, 6), random.uniform(-4, 4))
            fr = cam(S['D']['bg'], lerp(1.0, 1.03, u), shake=shake).convert('RGBA')
            particles(fr, 'dust', t)
            ax = axe_shape(330 * z, 0)
            axx, axy = zoom_pos(W * 0.74, H * 0.6, z)
            dropk = easeout(lt / 0.18)
            fr.alpha_composite(ax, (int(axx - ax.width / 2), int(axy - ax.height / 2 - (1 - dropk) * 300)))
            dust_puff(fr, axx, axy + 190 * z, (lt - 0.15) / 0.9)
            sp = sprite('jarl', 72, expr='angry', blink=blink_at(t, 4), look=(-0.6, 0), extra={'rim': '#ffc28c', 'beard': '#c2502a', 'beard_dk': '#9c3e1f'})
            x, y = zoom_pos(W * 0.44, H * 0.36 + 5.55 * 72, z)
            place(fr, sp, x, y, z * (1 + 0.01 * math.sin(t * 2)))
        elif name in ('E', 'E2'):
            fr = cam(S[name]['bg'], lerp(1.0, 1.03, u)).convert('RGBA')
            z = lerp(1.0, 1.07, ease(u))
            particles(fr, 'dust', t)
            if name == 'E':
                sp = sprite('hero', 52, expr='worried' if lt > 2.2 else 'neutral', blink=blink_at(t, 5), look=((0, -1) if lt < 1.4 else (0, 0)), extra={'rim': '#ffe0bf'})
                x, y = zoom_pos(W * 0.5, H * 0.45 + 5.65 * 52, z)
                place(fr, sp, x, y, z)
                k = back(lt / 0.4)
                if k > 0.02:
                    pb = panel.resize((max(1, int(panel.width * k)), max(1, int(panel.height * k))), Image.BILINEAR)
                    fr.alpha_composite(pb, (int(W / 2 - pb.width / 2), int(96 - pb.height / 2)))
            else:
                sp = sprite('viking', 64, expr='angry', blink=blink_at(t, 6), look=(0.7 if lt < 2 else -0.7, 0), extra={'rim': '#ffe0bf', 'arms': 'crossed', 'beard': '#5a3b22', 'beard_dk': '#3e2816', 'coat': '#6f4a33'})
                x, y = zoom_pos(W * 0.52, H * 0.42 + 5.55 * 64, z)
                place(fr, sp, x, y, z)
                # ominous darken at "the sea takes you back"
                dk = clamp((lt - 2.3) / 1.2)
                if dk > 0:
                    fr = Image.blend(fr, Image.new('RGBA', (W, H), (20, 28, 48, 255)), 0.35 * dk)
        elif name == 'F':
            z = lerp(1.0, 1.06, ease(u))
            fr = cam(S['F']['bg'], lerp(1.0, 1.03, u)).convert('RGBA')
            walk = math.sin(t * 6)
            hero = sprite('hero', 42, expr='worried', blink=blink_at(t, 7), look=(-0.6, 0) if lt < 2 else (0.6, 0), extra={'rim': '#fff1d6', 'arms': 'tied', 'sweat': True})
            v1 = sprite('viking', 44, expr='angry', blink=blink_at(t, 8), extra={'rim': '#fff1d6', 'weapon': 'axe', 'beard': '#d9a441', 'beard_dk': '#b8862c'})
            v2 = sprite('viking', 44, expr='neutral', blink=blink_at(t, 9), extra={'rim': '#fff1d6', 'shield': ('#2E5E8C', '#E9C24A'), 'beard': '#8a5a2b', 'beard_dk': '#6b4420'})
            for spr, xx, ph in ((v1, 0.31, 0), (hero, 0.5, 1.2), (v2, 0.69, 2.1)):
                x, y = zoom_pos(W * xx, H * 0.47 + 5.6 * spr.height / 8.4 - abs(math.sin(t * 5 + ph)) * 5, z)
                place(fr, spr, x, y, z)
            fg = cam(S['F']['fg'], lerp(1.0, 1.09, u))
            fr.alpha_composite(fg)
            particles(fr, 'snow', t)
            k = back((lt - 0.1) / 0.4)
            if k > 0.02:
                pb = day1.resize((max(1, int(day1.width * k)), max(1, int(day1.height * k))), Image.BILINEAR)
                fr.alpha_composite(pb, (34, 30))
        # counter (from shot D onwards like ref keeps it)
        if name in ('D', 'E', 'E2', 'F'):
            fr.alpha_composite(counter, (W - counter.width - 34, 30))
        caption(fr, t)
        if t < 3.2:  # video title like ref opening hold
            pass
        rgb = fr.convert('RGB')
        ga, gb = grains[fi % len(grains)]
        rgb = ImageChops.subtract(ImageChops.add(rgb, ga), gb)
        if t < 0.35:
            rgb = Image.blend(Image.new('RGB', (W, H)), rgb, t / 0.35)
        if t > DUR - 0.4:
            rgb = Image.blend(rgb, Image.new('RGB', (W, H)), (t - (DUR - 0.4)) / 0.4)
        if proc:
            proc.stdin.write(rgb.tobytes())
        else:
            rgb.save(os.path.join(D, f'prev/f_{fi:04d}.png'))
    if proc:
        proc.stdin.close(); proc.wait()

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'prev':
        os.makedirs(os.path.join(D, 'prev'), exist_ok=True)
        for tt in [float(x) for x in sys.argv[2:]]:
            fi = int(tt * FPS); render(fi, fi + 1)
    else:
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        render(a, b, out)
