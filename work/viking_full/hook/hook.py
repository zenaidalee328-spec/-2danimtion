import sys, os, json, math, random, subprocess
sys.path.insert(0, '/workspace/work/viking3')
import v3
from v3 import *
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP_BEFORE = {'n02': 0.15, 'n03': 0.55, 'n05': 0.3, 'n06': 0.45, 'j01': 0.55, 'n07': 0.6, 'n11': 0.7, 'n12': 0.05, 'n13': 0.75}

def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))

# ---- timeline
TL = {}; t = 0.4
for lid, voice, text in LINES:
    t += GAP_BEFORE.get(lid, 0.2)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json')))
    wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text']) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk='J' if lid.startswith('j') else 'N')
    t += d_
DUR = t + 1.6
v3.DUR = DUR
def S_(l): return TL[l]['st']
def E_(l): return TL[l]['en']

# ---- shots (name, start)
def word_t(lid, idx):
    return TL[lid]['st'] + TL[lid]['words'][idx][0]

SHOTS = [
    ('alone', 0.0), ('reveal', word_t('n01', 6) - 0.25),          # "island"
    ('kneelwide', S_('n02') - 0.05), ('kneelclose', word_t('n02', 6) - 0.1),  # "dropped"
    ('flash', S_('n03') - 0.35), ('storm', S_('n03') + 0.75),
    ('crash', S_('n04') - 0.05), ('mast', S_('n04') + 1.6), ('wash', word_t('n04', 10) - 0.1),
    ('eyes', S_('n05') - 0.1), ('surround', word_t('n05', 5) - 0.1),
    ('kneelhero', S_('n06') - 0.2),
    ('jarl', S_('j01') - 0.35), ('moon', word_t('j01', 2) - 0.1),
    ('law', S_('n07') - 0.2), ('wide100', word_t('n07', 4) - 0.1),
    ('vote', S_('n08') - 0.1), ('axes_up', S_('n09') - 0.15), ('hope', word_t('n09', 4) - 0.1),
    ('grump', S_('n10') - 0.15), ('raft', word_t('n10', 5) - 0.1),
    ('night', S_('n11') - 0.4), ('stalker', S_('n12') - 0.1),
    ('title', S_('n13') - 0.2), ('end', E_('n13') + 0.2),
]
SHOT_SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]

# ---- kneel-aware render_world
def kneel_sprite(sp, k):
    if k <= 0.01: return sp
    h = sp.height; w = sp.width; R = h / 12.2; legf = 2.95 / 12.2
    top = sp.crop((0, 0, w, int(h * (1 - legf))))
    leg = sp.crop((0, int(h * (1 - legf)), w, h))
    nh = max(1, int(leg.height * (1 - 0.8 * k)))
    leg = leg.resize((w, nh), Image.BILINEAR)
    out = Image.new('RGBA', (w, top.height + nh), (0, 0, 0, 0))
    out.alpha_composite(leg, (0, top.height))
    if k > 0.5:  # bent knee: thigh pointing forward + shin on ground
        d = ImageDraw.Draw(out); y = top.height + nh * 0.2; cx = w / 2
        a = int(255 * clamp((k - 0.5) * 2.5))
        d.rounded_rectangle([cx + 0.05 * R, y - 0.35 * R, cx + 1.25 * R, y + 0.05 * R], radius=0.18 * R, fill=(42, 36, 32, a))
        d.ellipse([cx + 1.0 * R, y - 0.4 * R, cx + 1.45 * R, y + 0.12 * R], fill=(42, 36, 32, a))
    out.alpha_composite(top, (0, 0))
    if k > 0.2:
        out = out.rotate(-7 * k, resample=Image.BICUBIC, center=(out.width / 2, out.height))
    return out

def render_world2(frame, actors, cam, t):
    cx, cz, f, hor, ch, foc, ap = cam['cx'], cam['cz'], cam['f'], cam['hor'], cam['h'], cam['focus'], cam['ap']
    items = []
    for a in actors:
        dz = a.z - cz
        if dz < 0.25: continue
        s = f / dz; R = HEAD_U * s * a.size
        if R < 3: continue
        sx = W / 2 + (a.x - cx) * s; fy = hor + ch * s
        if sx < -R * 6 or sx > W + R * 6: continue
        blur = ap * abs(1 / dz - 1 / foc) * 26
        items.append((dz, a, R, sx, fy, blur))
    items.sort(key=lambda i: -i[0])
    layer = None; lb = None; bbox = None
    def flush():
        nonlocal layer, lb, bbox
        if layer is None: return
        if lb >= 0.8 and bbox:
            x0, y0, x1, y1 = bbox; pad = int(lb * 3) + 4
            x0, y0 = max(0, x0 - pad), max(0, y0 - pad); x1, y1 = min(W, x1 + pad), min(H, y1 + pad)
            if x1 > x0 and y1 > y0:
                frame.alpha_composite(fastblur(layer.crop((x0, y0, x1, y1)), lb), (x0, y0))
        else:
            frame.alpha_composite(layer)
        layer = None; bbox = None
    for dz, a, R, sx, fy, blur in items:
        bq = round(blur * 2) / 2 if blur < 4 else round(blur)
        if layer is None or bq != lb:
            flush(); layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lb = bq
        ev = lambda x: x(t) if callable(x) else x
        sp = sprite(a.kind, a.v, ev(a.expr), blink_at(t, a.seed), ev(a.look), ev(a.pose), R)
        kn = ev(getattr(a, 'kneel', 0))
        sp = kneel_sprite(sp, kn)
        bob = a.bob * abs(math.sin(t * 5 + a.seed)) * R * 0.15
        dsh = ImageDraw.Draw(layer)
        dsh.ellipse([sx - R * 1.1, fy - R * 0.18, sx + R * 1.1, fy + R * 0.18], fill=(40, 20, 20, 70))
        px, py = int(sx - sp.width / 2), int(fy - sp.height - bob)
        paste_safe(layer, sp, px, py)
        bx = (max(0, px), max(0, py), min(W, px + sp.width), min(H, py + sp.height))
        bbox = bx if bbox is None else (min(bbox[0], bx[0]), min(bbox[1], bx[1]), max(bbox[2], bx[2]), max(bbox[3], bx[3]))
    flush()

def kneel_wave(t0, spread, x_of=None):
    """returns setter giving each actor a staggered kneel based on x"""
    def apply(acts):
        for a in acts:
            delay = (abs(a.x) / 6.0) * spread + random.Random(a.seed).uniform(0, 0.12)
            a.kneel = (lambda tt, d=delay: eout((tt - t0 - d) / 0.28))
        return acts
    return apply

# ---- UI bits
def label_box(text, col='#ffe4ad', glowc='#ff9f3a'):
    f = fnt(NUN, 34, b'Black'); tt = '   '.join(' '.join(w) for w in text.split(' '))
    w = int(f.getlength(tt) + 70)
    img, p = rr_img(w, 66, 12, hexc('#1a140e', 235), hexc('#ffcf7a'), 3, glow_col=glowc)
    d = ImageDraw.Draw(img); bb = f.getbbox(tt)
    d.text((p + 35, p + 33 - (bb[1] + bb[3]) / 2), tt, font=f, fill=hexc(col))
    return img

def big_card(top, main, sub, icon='moon'):
    w, h = 620, 320
    img, p = rr_img(w, h, 28, hexc('#141a2e', 240), hexc('#3a4560'), 3, glow_col='#9fc4ff')
    d = ImageDraw.Draw(img); cx = p + w / 2
    if icon == 'moon':
        d.ellipse([cx - 26, p + 30, cx + 26, p + 82], fill=hexc('#f4ecd0'))
        d.ellipse([cx - 12, p + 24, cx + 36, p + 72], fill=hexc('#141a2e'))
    else:
        axe_icon(d, cx, p + 56, 2.0)
    fb = fnt(FRED, 118, axes=[700, 100])
    bb = fb.getbbox(main); d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], p + 100 - bb[1]), main, font=fb, fill=WHITE)
    fs = fnt(NUN, 26, b'Black'); sw = fs.getlength(sub) + 40
    d.rounded_rectangle([cx - sw / 2, p + 250, cx + sw / 2, p + 290], radius=8, fill=GOLD)
    bb = fs.getbbox(sub); d.text((cx - fs.getlength(sub) / 2, p + 270 - (bb[1] + bb[3]) / 2), sub, font=fs, fill=hexc('#1b1a2a'))
    return img

def pop(fr, img, k, cx, cy):
    if k > 0.02:
        im = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.BILINEAR)
        paste_safe(fr, im, cx - im.width / 2, cy - im.height / 2)

# ---- captions
LABELS = {'J': 'J A R L'}
def caption2(frame, t):
    d = ImageDraw.Draw(frame)
    for lid, L in TL.items():
        if not (L['st'] - 0.1 <= t < L['en'] + 0.5): continue
        ws = L['words']; toks = L['text'].replace('...', '… ').split()
        toks = [x for x in toks if x != '…'] if len(toks) != len(ws) else toks
        if len(toks) != len(ws): toks = [w[2] for w in ws]
        chunks = []; cur = []
        for i in range(len(ws)):
            cur.append(i)
            if len(cur) >= 4 or toks[i].endswith((',', '.', ':', '…', '?')) or i == len(ws) - 1:
                chunks.append(cur); cur = []
        lt = t - L['st']
        for ci, ch in enumerate(chunks):
            c0 = ws[ch[0]][0] - 0.08
            c1 = ws[chunks[ci + 1][0]][0] - 0.08 if ci + 1 < len(chunks) else ws[ch[-1]][1] + 0.45
            if ci == 0: c0 = min(c0, 0)
            if not (c0 <= lt < c1): continue
            disp = [toks[i].upper() for i in ch]
            sp = 22; widths = [tracked_w(s) for s in disp]
            total = sum(widths) + sp * (len(disp) - 1)
            x = W / 2 - total / 2; y = 948
            if L['spk'] in LABELS:
                lab = LABELS[L['spk']]; lw = LBL.getlength(lab) + 34
                d.rounded_rectangle([W / 2 - lw / 2, y - 46, W / 2 + lw / 2, y - 10], radius=10, fill=hexc('#1b1a10', 220), outline=GOLD, width=2)
                bb = LBL.getbbox(lab); d.text((W / 2 - LBL.getlength(lab) / 2, y - 28 - (bb[1] + bb[3]) / 2), lab, font=LBL, fill=GOLD)
            for k, (i, s, wd) in enumerate(zip(ch, disp, widths)):
                on = ws[i][0] - 0.03 <= lt
                nxt = ws[ch[k + 1]][0] if k + 1 < len(ch) else 99
                col = hexc('#FFC93C') if (ws[i][0] - 0.03 <= lt < nxt) else WHITE
                xx = x
                for c in s:
                    d.text((xx + 3, y + 5), c, font=CAP, fill=(0, 0, 0, 110), stroke_width=7, stroke_fill=(0, 0, 0, 110)); xx += CAP.getlength(c) + TRACK
                xx = x
                for c in s:
                    d.text((xx, y), c, font=CAP, fill=col, stroke_width=6, stroke_fill=hexc('#15131a')); xx += CAP.getlength(c) + TRACK
                x += wd + sp
            return

# ---- scenes
def tint(fr, col, a):
    return Image.blend(fr, Image.new('RGBA', fr.size, col + (255,)), a)

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['night'] = tint(S['cool'], (18, 26, 58), 0.62)
    S['night'] = Image.alpha_composite(S['night'], glow(S['night'].width, S['night'].height, S['night'].width * 0.7, S['night'].height * 0.18, 260, 260, '#dfe8ff', 200))
    dd = ImageDraw.Draw(S['night']); mx, my = S['night'].width * 0.7, S['night'].height * 0.18
    dd.ellipse([mx - 60, my - 60, mx + 60, my + 60], fill=hexc('#f4efdc'))
    S['night_hor'] = S['cool_hor']
    c0, c100 = counter_img(0), counter_img(100)
    vpanel = vote_panel(0); vfull = vote_panel(100)
    lbl12 = label_box('12 HOURS AGO'); lbljarl = None
    moon = big_card('', '30 DAYS', 'ONE MOON', 'moon')
    lawc = big_card('', 'THE LAW', 'WHAT THE SEA GIVES BACK STAYS', 'axe')
    tcard = big_card('', 'DAY 30', 'WHO WANTS YOU DEAD?', 'axe')
    HV = HERO_V
    ring = crowd(11, 3, 9, 4.4, 1.3, 4.6, exclude=lambda x, z: abs(x) < 0.7 and z < 5.2)
    bigr = crowd(15, 8, 13, 4.6, 0.8, 6.5, exclude=lambda x, z: abs(x) < 0.5 and z < 5.4)
    kneel_wave(S_('n02') + 0.9, 0.9)(bigr)
    close3 = [Actor('viking', -1.2, 3.0, V(coat='#7c6a4a', tunic='#5a4030', beard='#C4622D', beard_dk='#9a4a20', shield=('#B23A2E', '#EFE3C8'), helmet=True, rim='#F6B07A'), expr='neutral', seed=21),
              Actor('viking', 0.0, 3.2, V(coat='#4f5f74', tunic='#4a3a2a', beard='#D9A441', beard_dk='#b5842a', weapon='axe', helmet=False, hair='#D9A441', rim='#F6B07A'), expr='neutral', seed=22),
              Actor('viking', 1.2, 3.0, V(coat='#7a3b2e', tunic='#6d4a33', beard='#5a3b22', beard_dk='#3e2816', shield=('#2E5E8C', '#E9C24A'), helmet=True, rim='#F6B07A'), expr='neutral', seed=23)]
    kc0 = word_t('n02', 6)
    for i, a in enumerate(close3):
        a.kneel = (lambda tt, d=[0.12, 0.0, 0.22][i]: eout((tt - kc0 - d) / 0.22))
    close_bg = crowd(12, 2, 8, 5.6, 1.5, 5.0)
    kneel_wave(kc0 - 0.3, 0.6)(close_bg)
    surround_bg = crowd(13, 2, 7, 2.6, 1.4, 2.6, exclude=lambda x, z: abs(x) < 0.55)
    kh_ring = crowd(21, 2, 8, 3.3, 1.2, 3.4, exclude=lambda x, z: abs(x) < 0.8 and z < 4.2)
    kneel_wave(S_('n06') + 1.1, 0.7)(kh_ring)
    jarl = Actor('jarl', 0.25, 4.2, V(coat='#7A3B2E', beard='#c2502a', beard_dk='#9c3e1f', helmet=True, rim='#F6B07A'), expr='neutral', look=(-0.6, 0), seed=31, size=1.18)
    jarl_flank = crowd(14, 2, 8, 5.3, 1.5, 4.4, exclude=lambda x, z: abs(x - 0.25) < 1.4)
    for a in jarl_flank: a.kneel = 1.0
    big = crowd(15, 9, 14, 5.0, 0.75, 6.5, exclude=lambda x, z: abs(x) < 0.4 and z < 5.6)
    vote_row = crowd(16, 1, 7, 4.6, 1, 3.2, exclude=lambda x, z: abs(x) < 0.7, rim='#ffe2c4')
    vote_row2 = crowd(17, 2, 9, 6.4, 1.4, 4.6, rim='#ffe2c4')
    grump_bg = crowd(18, 2, 8, 4.4, 1.3, 3.8, shields_up=True, exclude=lambda x, z: abs(x) < 0.9, rim='#ffe2c4', expr_choices=('happy', 'neutral'))
    night_v = crowd(22, 1, 5, 6.0, 1, 4.0, exclude=lambda x, z: abs(x) < 1.0, rim='#9fb4ff')
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SHOT_SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0)
        counter = None
        if name in ('alone', 'reveal'):
            if name == 'alone': z = lerp(1.12, 1.0, eio(u)); cz = lerp(-1.2, -0.6, eio(u)); foc = 3.0
            else: z = 1.0; cz = lerp(-0.6, -3.6, eio(u)); foc = lerp(3.0, 5.6, eio(u))
            fr = fastblur(cam_bg(S['beach'], 1.0 + 0.02 * z, 0, -40), 0.8)
            cam = dict(cx=0, cz=cz, f=1500 * z, hor=H * 0.43, h=1.4, focus=foc - cz, ap=1.0)
            acts = [Actor('hero', 0, 3.0, HV | V(sweat=name == 'reveal'), expr='worried', look=(0.4, 0) if name == 'alone' else (-1, 0), seed=1)]
            if name == 'reveal': acts += ring
            render_world2(fr, acts, cam, t)
        elif name == 'kneelwide':
            fr = cam_bg(S['cool'], 1.0 + 0.03 * u, 0, -30)
            cam = dict(cx=lerp(-0.3, 0.3, u), cz=lerp(-2.4, -1.9, eio(u)), f=1500, hor=H * 0.36, h=2.3, focus=8.0, ap=0.5)
            render_world2(fr, bigr + [Actor('hero', 0, 4.6, HV, expr='worried', seed=6)], cam, t)
        elif name == 'kneelclose':
            fr = fastblur(cam_bg(S['beach'], 1.06 + 0.02 * u, 0, -40), 1.2)
            cam = dict(cx=0, cz=lerp(0.3, 0.45, u), f=1500, hor=H * 0.45, h=0.92, focus=3.0 - lerp(0.3, 0.45, u), ap=0.9)
            render_world2(fr, close_bg + close3, cam, t)
            for i, d_ in enumerate([0.12, 0.0, 0.22]):
                if 0 <= t - kc0 - d_ - 0.2 < 0.15: fr = shake(fr, 10, t)
            dust(fr, W * 0.5, H * 0.95, (t - kc0 - 0.2) / 0.8)
        elif name == 'flash':
            img = Image.new('RGBA', (W, H), hexc('#efe9df')); d = ImageDraw.Draw(img)
            b = boat_img(t, 1.4).convert('LA').convert('RGBA'); b.putalpha(b.getchannel('A').point(lambda v: v // 3))
            paste_safe(img, b, W * 0.5 - b.width / 2, H * 0.48 - b.height / 2)
            for k in range(4):
                d.line([(x, H * 0.75 + k * 30 + 12 * math.sin(x / 80 + k)) for x in range(0, W, 12)], fill=(160, 150, 140, 90), width=3)
            fr = Image.blend(img, cam_bg(S['storm'], 1.0), ease((lt - 0.5) / 0.5))
        elif name in ('storm', 'crash'):
            zz = lerp(1.0, 1.06, ease(u)) if name == 'storm' else lerp(1.15, 1.22, u)
            fr = cam_bg(S['storm'], zz)
            waves(fr, t, '#3c2d1f', H * 0.6, 34, 1.0, 1.6)
            tilt = (9 * math.sin(t * 1.9) - 3) if name == 'storm' else lerp(-6, 24, eout(u * 1.5))
            bob = 18 * math.sin(t * 1.9 + 0.8)
            b = boat_img(t, 1.0)
            hs = make_char_cached('hero', 26, HV, 'scared', blink_at(t, 3), (0, -1), 'cling')
            b.alpha_composite(hs, (int(160 - hs.width / 2), int(362 - hs.height)))
            b = b.rotate(tilt, resample=Image.BICUBIC, expand=True)
            sc = 1.25 if name == 'storm' else 2.0
            b = b.resize((int(b.width * sc * zz), int(b.height * sc * zz)), Image.BILINEAR)
            paste_safe(fr, b, (W * 0.5 if name == 'storm' else W * 0.42) - b.width / 2, H * 0.6 + bob - b.height * 0.62)
            if name == 'crash':
                d = ImageDraw.Draw(fr)
                d.polygon([(W * 0.48, H), (W * 0.58, H * 0.68), (W * 0.66, H * 0.62), (W * 0.78, H * 0.74), (W * 0.86, H)], fill=hexc('#1a130d'))
            waves(fr, t, '#2a1f16', H * 0.8, 36, 2.3, 2.1); waves(fr, t, '#1d150e', H * 0.93, 26, 4.1, 2.6)
            rain(fr, t)
            for ft in ((0.9, 2.2) if name == 'storm' else (0.15,)):
                if 0 <= lt - ft < 0.12: fr = Image.blend(fr, Image.new('RGBA', (W, H), (255, 236, 205, 255)), 0.6 * (1 - (lt - ft) / 0.12))
            if name == 'crash' and lt < 0.35: fr = shake(fr, 14 * (1 - lt / 0.35), t)
            if name == 'storm': pop(fr, lbl12, back(lt / 0.35), W / 2, 120)
        elif name == 'mast':
            fr = cam_bg(S['storm'], 1.1 + 0.04 * u)
            waves(fr, t, '#3c2d1f', H * 0.55, 30, 0.4, 1.4)
            # floating mast piece with hero clinging
            mx, my = W * 0.5 + 60 * math.sin(t * 0.9), H * 0.66 + 22 * math.sin(t * 1.7)
            ang = 8 * math.sin(t * 1.3)
            pl = Image.new('RGBA', (900, 300), (0, 0, 0, 0)); pd = ImageDraw.Draw(pl)
            pd.rounded_rectangle([60, 120, 840, 175], radius=24, fill=hexc('#5a3b24'))
            pd.line([110, 130, 790, 130], fill=hexc('#7a5234'), width=6)
            pd.line([700, 150, 760, 40], fill=hexc('#ecdcbc'), width=5)
            hs = make_char_cached('hero', 30, HV | V(sweat=True), 'scared', blink_at(t, 9), (0.5, -0.5), 'cling')
            hs = hs.crop((0, 0, hs.width, int(hs.height * 0.62)))
            pl.alpha_composite(hs, (int(430 - hs.width / 2), int(150 - hs.height + 20)))
            pl = pl.rotate(ang, resample=Image.BICUBIC, expand=True); pl = pl.resize((int(pl.width*1.6), int(pl.height*1.6)), Image.BILINEAR)
            paste_safe(fr, pl, mx - pl.width / 2, my - pl.height / 2)
            waves(fr, t, '#2a1f16', H * 0.74, 34, 2.3, 2.0); waves(fr, t, '#1d150e', H * 0.9, 24, 4.1, 2.5)
            rain(fr, t)
        elif name == 'wash':
            fr = cam_bg(S['cool'], lerp(1.3, 1.22, u), 0, 220)
            fr = tint(fr, (30, 30, 40), 0.35)
            d = ImageDraw.Draw(fr)
            for i in range(26):  # black stones
                rnd = random.Random(i); x = rnd.uniform(0, W); y = rnd.uniform(H * 0.6, H)
                r = rnd.uniform(30, 90) * (y / H)
                d.ellipse([x - r * 1.4, y - r * 0.6, x + r * 1.4, y + r * 0.6], fill=hexc(rnd.choice(['#1d1d22', '#2a2a30', '#141418'])))
            # hero thrown in by a wave
            k = eout(u * 1.6)
            hs = make_char_cached('hero', 40, HV, 'worried', True, (0, 0), 'down').rotate(90, expand=True)
            paste_safe(fr, hs, lerp(W * 0.1, W * 0.45, k) - hs.width / 2, H * 0.74 - hs.height / 2)
            wash = 0.5 + 0.5 * math.cos(lt * 3.0)
            foam = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(foam)
            fy = H * 0.45 + wash * H * 0.3
            pts = [(x, fy + 18 * math.sin(x / 120 + lt * 2)) for x in range(-20, W + 40, 20)]
            fd.polygon([(-20, 0), (W + 40, 0)] + pts[::-1], fill=(120, 160, 180, 150)); fd.line(pts, fill=(255, 255, 255, 235), width=14)
            fr.alpha_composite(foam)
        elif name == 'eyes':
            # POV: eyelids opening on ring of faces against sky
            fr = vgrad(W, H, [(0, '#b9c3d3'), (1, '#e7d9cf')])
            fr = Image.alpha_composite(fr, glow(W, H, W * 0.5, H * 0.5, 500, 400, '#fff6e6', 230))
            cxp, cyp = W / 2, H / 2
            for i in range(9):
                a = i / 9 * 2 * math.pi + 0.2
                sp_ = make_char_cached('viking', 60, rand_viking(random.Random(40 + i), rim='#ffe2c4'), 'neutral', blink_at(t, 40 + i), (-math.cos(a), -math.sin(a)), 'down')
                sp_ = sp_.crop((0, 0, sp_.width, int(sp_.height * 0.55)))
                rot = sp_.rotate(-math.degrees(a) - 90, expand=True, resample=Image.BICUBIC)
                rr = 470
                paste_safe(fr, rot, cxp + math.cos(a) * rr - rot.width / 2, cyp + math.sin(a) * rr * 0.75 - rot.height / 2)
            fr = fastblur(fr, lerp(9, 0.5, ease(u * 1.4)))
            op = ease(u * 1.3); lid = int(H / 2 * (1 - op))
            d = ImageDraw.Draw(fr)
            if lid > 0:
                d.rectangle([0, 0, W, lid], fill=(10, 6, 6, 255)); d.rectangle([0, H - lid, W, H], fill=(10, 6, 6, 255))
        elif name == 'surround':
            fr = fastblur(cam_bg(S['beach'], 1.2, 0, -80), 2.0)
            cz = lerp(-0.4, -0.2, u)
            cam = dict(cx=0, cz=cz, f=1500, hor=H * 0.42, h=0.95, focus=2.4 - cz, ap=1.4)
            render_world2(fr, surround_bg, cam, t)
            hero = Actor('hero', 0, 2.4, HV | V(sweat=True), expr='scared', look=(lambda tt: (1, -1) if lt < 1.0 else (-1, -1)), seed=2)
            render_world2(fr, [hero], cam, t)
            dz = 2.4 - cz; s_ = 1500 / dz; hx, hy = W / 2, H * 0.42 + 0.95 * s_
            headY = hy - HEAD_U * s_ * 8.2; R = HEAD_U * s_
            for i in range(6):
                th = math.radians(-172 + i * 32.8); k = eout((lt - 0.04 * i) / 0.32); L = 340
                dist = lerp(L * 1.8, R * 3.1 + L * 0.5, k)
                ax = axe_img(L, 90 - math.degrees(th))
                paste_safe(fr, ax, hx + math.cos(th) * dist - ax.width / 2, headY + math.sin(th) * dist - ax.height / 2)
            for (gx, gy, gt) in [(-0.8, -0.9, 0.42), (0.7, -1.0, 0.5)]:
                glint(fr, hx + gx * R * 1.9, headY + gy * R * 1.6, 46, (lt - gt) / 0.4)
        elif name == 'kneelhero':
            fr = fastblur(cam_bg(S['beach'], 1.08 + 0.03 * u, 0, -50), 1.2)
            cz = lerp(-0.2, 0.3, eio(u))
            cam = dict(cx=0, cz=cz, f=1500, hor=H * 0.44, h=1.1, focus=2.6 - cz, ap=0.9)
            ex = (lambda tt: 'scared' if tt < S_('n06') + 1.2 else 'worried')
            render_world2(fr, kh_ring + [Actor('hero', 0, 2.6, HV | V(sweat=True), expr=ex, look=(lambda tt: (-1, 0) if math.sin(tt * 3) > 0 else (1, 0)), seed=3)], cam, t)
            tk = S_('n06') + 1.2
            if 0 <= t - tk < 0.25: fr = shake(fr, 8 * (1 - (t - tk) / 0.25), t)
        elif name == 'jarl':
            fr = fastblur(cam_bg(S['beach'], 1.04 + 0.03 * u, 60, -60), 1.4)
            cz = lerp(-0.4, 0.5, eio(u))
            cam = dict(cx=lerp(0.6, 0.3, eio(u)), cz=cz, f=1500, hor=H * 0.42, h=1.35, focus=4.2 - cz, ap=1.0)
            render_world2(fr, jarl_flank + [jarl, Actor('hero', 2.05, 2.1, HV | V(sweat=True), expr='worried', look=(-1, -0.5), seed=4)], cam, t)
        elif name == 'moon':
            fr = fastblur(cam_bg(S['night'], 1.0 + 0.04 * u, 0, -60), 1.0)
            pop(fr, moon, back(lt / 0.4), W / 2, H * 0.43)
        elif name == 'law':
            fr = fastblur(cam_bg(S['cool'], 1.05 + 0.03 * u, -50, -80), 3.0)
            waves(fr, t, '#6f8fae', H * 0.72, 10, 0.3, 1.0, line='#ffffff', la=120)
            pop(fr, lawc, back(lt / 0.4), W / 2, H * 0.43)
        elif name == 'wide100':
            fr = fastblur(cam_bg(S['cool'], 1.0 + 0.04 * u, 0, -30), 0.8)
            cam = dict(cx=lerp(-0.4, 0.4, u), cz=lerp(-2.5, -1.6, eio(u)), f=1500, hor=H * 0.36, h=2.3, focus=8.0, ap=0.5)
            render_world2(fr, big + [Actor('hero', 0, 4.8, HV, expr='worried', seed=6)], cam, t)
            counter = c0
        elif name in ('vote', 'hope'):
            fr = fastblur(cam_bg(S['cool'], 1.06 + 0.03 * u, 0, -60), 1.6)
            if name == 'vote':
                cam = dict(cx=lerp(-0.6, 0.6, u), cz=lerp(0.4, 0.8, u), f=1500, hor=H * 0.43, h=1.35, focus=4.6 - lerp(0.4, 0.8, u), ap=1.0)
                render_world2(fr, vote_row2 + vote_row, cam, t)
                pop(fr, vpanel, back(lt / 0.4), W / 2, 120)
            else:
                cam = dict(cx=0, cz=lerp(0.2, 0.75, eio(u)), f=1500, hor=H * 0.43, h=1.35, focus=2.9 - lerp(0.2, 0.75, eio(u)), ap=1.0)
                render_world2(fr, vote_row2 + vote_row + [Actor('hero', 0, 2.9, HV, expr='happy', pose='up', seed=7)], cam, t)
                pop(fr, vfull, 1.0, W / 2, 120)
                for gx in (0.3, 0.7): glint(fr, W * gx, H * 0.3, 40, (lt - 0.2 - gx) / 0.5)
        elif name == 'axes_up':
            fr = fastblur(cam_bg(S['beach'], 1.12 + 0.03 * u, 0, -140), 2.4)
            fr = Image.alpha_composite(fr, glow(W, H, W * 0.55, H * 0.42, 520, 300, '#fff4d8', 230))
            for i in range(7):
                x = W * (0.08 + i * 0.14) + 30 * math.sin(i * 2.1); rise = eout((lt - 0.05 * i) / 0.35)
                L = 430 + 60 * math.sin(i * 1.7); yb = H * 0.66 + 50 * math.sin(i * 2.3)
                ax = axe_img(L, (i - 3) * 6 + 5 * math.sin(i))
                paste_safe(fr, ax, x - ax.width / 2, yb - ax.height / 2 + (1 - rise) * 500)
                glint(fr, x + L * 0.25, yb - L * 0.45 + (1 - rise) * 500, 30, (lt - 0.25 - 0.08 * i) / 0.45)
            counter = c100
        elif name == 'grump':
            fr = fastblur(cam_bg(S['cool'], 1.1, 0, -60), 2.0)
            cz = lerp(0.4, 0.6, u)
            cam = dict(cx=0, cz=cz, f=1500, hor=H * 0.43, h=0.92, focus=2.6 - cz, ap=0.9)
            g = Actor('viking', 0.05, 2.6, V(coat='#5a4030', tunic='#4a3a2a', beard='#5a3b22', beard_dk='#3e2816', helmet=True, rim='#ffe2c4'), expr='angry', pose='crossed', look=(lambda tt: (1, 0) if lt < 0.7 else (-1, 0)), seed=8)
            render_world2(fr, grump_bg + [g], cam, t)
            fr = tint(fr, (25, 30, 55), 0.22 * ease(u))
            if lt < 0.2: fr = Image.blend(fr, Image.new('RGBA', (W, H), (255, 255, 255, 255)), 0.3 * (1 - lt / 0.2))
            counter = counter_img(99)
        elif name == 'raft':
            fr = fastblur(cam_bg(S['cool'], lerp(1.0, 1.05, u), 0, -150), 1.2)
            d = ImageDraw.Draw(fr); rx, ry = W * 0.5, H * 0.47 - 20 * eout(u)
            for k in range(3):
                rr = 60 + k * 70 + lt * 60
                d.ellipse([rx - rr * 1.6, ry - rr * 0.25 + 10, rx + rr * 1.6, ry + rr * 0.25 + 10], outline=(255, 255, 255, max(0, 160 - k * 50)), width=3)
            d.rounded_rectangle([rx - 70, ry - 6, rx + 70, ry + 12], radius=6, fill=hexc('#7a5234'))
            hs = make_char_cached('hero', 9, HV, 'worried', False, (0, 0), 'down')
            paste_safe(fr, hs, rx - hs.width / 2, ry - hs.height + 2)
            cam = dict(cx=0, cz=-1.0, f=1500, hor=H * 0.43, h=1.35, focus=4, ap=0.5)
            render_world2(fr, crowd(19, 1, 6, 3.5, 1, 3.8, exclude=lambda x, z: abs(x) < 1.6, rim='#ffe2c4'), cam, t)
            fr = tint(fr, (25, 30, 55), 0.25)
        elif name == 'night':
            fr = cam_bg(S['night'], 1.0 + 0.05 * u, 0, -40)
            cam = dict(cx=lerp(-0.2, 0.2, u), cz=lerp(-0.5, 0.0, u), f=1500, hor=H * 0.40, h=1.35, focus=4.0, ap=0.7)
            render_world2(fr, night_v + [Actor('hero', 0.0, 4.0, HV | V(rim='#9fb4ff'), expr='worried', look=(lambda tt: (1, 0) if lt > 1.2 else (0, 0)), seed=12)], cam, t)
        elif name == 'stalker':
            fr = cam_bg(S['night'], 1.08 + 0.03 * u, 40, -40)
            cam = dict(cx=0.4, cz=0.0, f=1500, hor=H * 0.40, h=1.35, focus=lerp(1.4, 4.2, ease((lt - 0.8) / 0.8)), ap=1.2)
            hero = Actor('hero', 1.0, 4.2, HV | V(rim='#9fb4ff'), expr='worried', look=(-1, 0), seed=13)
            sil = Actor('viking', -0.15, 1.45, V(coat='#0d0f18', tunic='#0d0f18', beard='#10121c', beard_dk='#0a0b12', helmet=True, rim='#3a4a8a', weapon='axe'), expr='angry', look=(1, 0), seed=14)
            render_world2(fr, [hero], cam, t)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            render_world2(lay, [sil], cam, t)
            # darken silhouette heavily, keep eyes visible
            dkl = Image.new('RGBA', (W, H), (6, 8, 16, 255)); dkl.putalpha(lay.getchannel('A').point(lambda v: int(v * 0.86)))
            fr.alpha_composite(lay); fr.alpha_composite(dkl)
            fr = tint(fr, (60, 0, 10), 0.12 * ease(u))
            glint(fr, W * 0.47, H * 0.2, 34, (lt - 1.3) / 0.5)
        elif name in ('title', 'end'):
            fr = fastblur(cam_bg(S['night'], 1.03 + 0.03 * u, 0, -60), 2.5)
            pop(fr, tcard, back(lt / 0.4) if name == 'title' else 1.0, W / 2, H * 0.43)
        if counter is not None: paste_safe(fr, counter, W - counter.width - 40, 36)
        if name not in ('flash', 'eyes', 'night', 'stalker', 'moon', 'title', 'end'):
            fr = Image.alpha_composite(fr, glow_cache(name if name in ('storm', 'crash', 'grump', 'raft', 'vote', 'hope', 'wide100') else 'x'))
        fr = Image.alpha_composite(fr, haze); fr = Image.alpha_composite(fr, dark)
        caption2(fr, t)
        rgb = fr.convert('RGB'); ga, gb = grains[fi % 6]
        rgb = ImageChops.subtract(ImageChops.add(rgb, ga), gb)
        if t < 0.3: rgb = Image.blend(Image.new('RGB', (W, H)), rgb, t / 0.3)
        if t > DUR - 0.6: rgb = Image.blend(rgb, Image.new('RGB', (W, H)), clamp((t - (DUR - 0.6)) / 0.6))
        if proc: proc.stdin.write(rgb.tobytes())
        else: rgb.save(os.path.join(HD, f'prev/p_{t:05.2f}_{name}.jpg'), quality=85)
    if proc: proc.stdin.close(); proc.wait()

if __name__ == '__main__':
    if sys.argv[1] == 'info':
        print('DUR', DUR); [print(n, round(s, 2), round(e, 2)) for n, s, e in SHOT_SPANS]
    elif sys.argv[1] == 'prev':
        os.makedirs(os.path.join(HD, 'prev'), exist_ok=True)
        if len(sys.argv) > 2:
            ts = [float(x) for x in sys.argv[2:]]
        else:
            ts = [(s + e) / 2 for n, s, e in SHOT_SPANS]
        run([int(x * FPS) for x in ts])
    else:
        a, b = int(sys.argv[2]), int(sys.argv[3]); run(range(a, b), out=sys.argv[4])
