import sys, os, json, math, random, subprocess
sys.path.insert(0, '/workspace/work/viking3'); sys.path.insert(0, '/workspace/work/viking_full/hook'); sys.path.insert(0, '/workspace/work/viking_full/day1'); sys.path.insert(0, '/workspace/work/viking_full/day2')
import v3, hook, day1, day2
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, smoke, HAKON_V, JARL_V, parchment
from day2 import stint, tooth_img
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'j01': 0.35, 'n02': 0.35, 'j02': 0.35, 'n03': 0.6, 'n05': 0.5, 'n06': 0.5, 'n07': 0.9, 'n08': 0.3, 'n10': 0.15, 'n11': 0.5, 'n12': 0.5}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text']) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'j': 'J'}.get(lid[0], 'N'))
    t += d_
DUR = t + 2.0
hook.TL = TL; hook.LABELS = {'J': 'J A R L'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('job', wt('n01', 2) - 0.1), ('jarl', S_('j01') - 0.2), ('nav', S_('n02') - 0.2),
         ('chair', wt('n02', 4) - 0.1), ('fog', S_('j02') - 0.2), ('hut', S_('n03') - 0.3), ('chest', S_('n04') - 0.1),
         ('bone', wt('n04', 12) - 0.1), ('blanket', S_('n05') - 0.2), ('killed', S_('n06') - 0.25), ('night', wt('n06', 6) - 0.1),
         ('helm', S_('n07') - 0.4), ('birka', S_('n08') - 0.2), ('items', S_('n09') - 0.15), ('commander', S_('n10') - 0.1),
         ('assumed', S_('n11') - 0.25), ('dna', S_('n12') - 0.25)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V

def hall_set():
    img = vgrad(BW, BH, [(0, '#1a120c'), (0.5, '#3a2618'), (0.62, '#2a1c12'), (1, '#4a3424')])
    d = ImageDraw.Draw(img)
    for k in range(40):
        x = k * BW / 39; d.line([x, 0, x, BH * 0.62], fill=hexc('#24180f'), width=6)
    for k in range(6):
        x = BW * (0.08 + k * 0.17); d.rectangle([x - 34, 0, x + 34, BH * 0.66], fill=hexc('#2c1d12'))
        d.rectangle([x - 34, 0, x - 18, BH * 0.66], fill=hexc('#3e2a1a'))
    for k in range(5):  # shields on wall
        x = BW * (0.17 + k * 0.17); y = BH * 0.32
        d.ellipse([x - 60, y - 60, x + 60, y + 60], fill=hexc(['#7a2e22', '#2f4e6e', '#6e5a22', '#2f5e3e', '#7a2e22'][k]))
        d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=hexc('#9a9a9a'))
    img = Image.alpha_composite(img, glow(BW, BH, BW / 2, BH * 0.7, 700, 380, '#ff9f3a', 140))
    return img

def hut_set():
    img = vgrad(BW, BH, [(0, '#140f0b'), (0.6, '#2c2016'), (0.61, '#3a2a1c'), (1, '#2a1e14')])
    d = ImageDraw.Draw(img)
    for k in range(30):
        x = k * BW / 29; d.line([x, 0, x, BH * 0.6], fill=hexc('#1f1710'), width=8)
    d.rectangle([BW * 0.68, BH * 0.15, BW * 0.8, BH * 0.6], fill=hexc('#0c0907'))  # door
    img = Image.alpha_composite(img, glow(BW, BH, BW * 0.74, BH * 0.4, 320, 400, '#b8c8d8', 90))
    return img

def bed_layer(stains=0.0, sc=1.0, cx=W / 2, cy=H * 0.7):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    w, h = 1100 * sc, 260 * sc
    d.rectangle([cx - w / 2, cy - h * 0.2, cx + w / 2, cy + h * 0.6], fill=hexc('#4a3322'))
    d.rounded_rectangle([cx - w / 2 - 10, cy - h * 0.55, cx + w / 2 + 10, cy + h * 0.05], radius=int(30 * sc), fill=hexc('#7d6a52'))
    for k in range(9):
        x = cx - w / 2 + k * w / 8
        d.line([x, cy - h * 0.55, x, cy + h * 0.05], fill=hexc('#6a5842'), width=int(10 * sc))
    for k in range(3):
        y = cy - h * 0.45 + k * h * 0.2; d.line([cx - w / 2, y, cx + w / 2, y], fill=hexc('#8f7c62'), width=int(6 * sc))
    if stains > 0:
        rnd = random.Random(5)
        for i in range(9):
            x = cx + rnd.uniform(-w * 0.35, w * 0.35); y = cy - h * 0.3 + rnd.uniform(-h * 0.15, h * 0.2); r = rnd.uniform(20, 70) * sc
            d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=(52, 22, 20, int(200 * stains)))
    return im

def chest_img(open_=0.0, s=1.0):
    im = Image.new('RGBA', (int(700 * s), int(560 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([60 * s, 260 * s, 640 * s, 520 * s], fill=hexc('#6b4a30'))
    for y in (300, 470): d.rectangle([60 * s, y * s, 640 * s, (y + 22) * s], fill=hexc('#3a3a3e'))
    lid_y = lerp(180, 20, open_) * s
    d.rounded_rectangle([50 * s, lid_y, 650 * s, lid_y + 90 * s], radius=int(30 * s), fill=hexc('#7d5838'))
    d.rectangle([320 * s, 255 * s, 380 * s, 320 * s], fill=hexc('#c9a24a'))
    return im

def bone_img(s=1.0, k=1.0):
    im = Image.new('RGBA', (int(900 * s), int(200 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20 * s, 50 * s, 880 * s, 150 * s], radius=int(50 * s), fill=hexc('#efe4cc'))
    rnd = random.Random(9); n = int(16 * k)
    for i in range(n):  # rune-like strokes
        x = 80 * s + i * 48 * s
        d.line([x, 70 * s, x, 130 * s], fill=hexc('#5a4030'), width=int(6 * s))
        a = rnd.choice([(0, 1), (1, 0), (1, 1), (0, 0)])
        d.line([x, (70 + 20 * a[0]) * s, x + 22 * s, (90 + 20 * a[1]) * s], fill=hexc('#5a4030'), width=int(5 * s))
    return im

def sword_icon(d, x, y, s, c='#d8dbe2'):
    d.polygon([(x - 10 * s, y + 60 * s), (x - 10 * s, y - 110 * s), (x, y - 140 * s), (x + 10 * s, y - 110 * s), (x + 10 * s, y + 60 * s)], fill=hexc(c))
    d.rectangle([x - 45 * s, y + 60 * s, x + 45 * s, y + 75 * s], fill=hexc('#8a6a3a')); d.rectangle([x - 8 * s, y + 75 * s, x + 8 * s, y + 130 * s], fill=hexc('#5a4030'))
def spear_icon(d, x, y, s):
    d.line([x, y + 140 * s, x, y - 90 * s], fill=hexc('#7a5234'), width=int(10 * s)); d.polygon([(x - 18 * s, y - 90 * s), (x, y - 150 * s), (x + 18 * s, y - 90 * s)], fill=hexc('#d8dbe2'))
def arrows_icon(d, x, y, s):
    for k in (-1, 0, 1):
        xx = x + k * 26 * s; d.line([xx, y + 120 * s, xx, y - 90 * s], fill=hexc('#7a5234'), width=int(6 * s))
        d.polygon([(xx - 10 * s, y - 90 * s), (xx, y - 120 * s), (xx + 10 * s, y - 90 * s)], fill=hexc('#d8dbe2'))
        d.polygon([(xx, y + 90 * s), (xx - 12 * s, y + 120 * s), (xx + 12 * s, y + 120 * s)], fill=hexc('#B23A2E'))
def horse_icon(d, x, y, s, c='#7a5234'):
    d.ellipse([x - 70 * s, y - 30 * s, x + 50 * s, y + 30 * s], fill=hexc(c))
    d.polygon([(x + 30 * s, y - 10 * s), (x + 60 * s, y - 80 * s), (x + 95 * s, y - 70 * s), (x + 60 * s, y)], fill=hexc(c))
    for lx in (-55, -30, 15, 35): d.line([x + lx * s, y + 20 * s, x + lx * s, y + 90 * s], fill=hexc(c), width=int(10 * s))
    d.line([x - 70 * s, y - 10 * s, x - 95 * s, y + 40 * s], fill=hexc('#3a2a1c'), width=int(10 * s))
def board_icon(d, x, y, s):
    d.rectangle([x - 90 * s, y - 90 * s, x + 90 * s, y + 90 * s], fill=hexc('#b08a5a'), outline=hexc('#5a4030'), width=int(6 * s))
    for k in range(1, 6):
        d.line([x - 90 * s + k * 30 * s, y - 90 * s, x - 90 * s + k * 30 * s, y + 90 * s], fill=hexc('#5a4030'), width=2)
        d.line([x - 90 * s, y - 90 * s + k * 30 * s, x + 90 * s, y - 90 * s + k * 30 * s], fill=hexc('#5a4030'), width=2)
    for (i, j, c) in [(2, 2, '#f3ead6'), (1, 2, '#1b1a2a'), (3, 2, '#1b1a2a'), (2, 1, '#1b1a2a'), (2, 3, '#1b1a2a')]:
        cx_, cy_ = x - 75 * s + i * 30 * s + 15 * s, y - 75 * s + j * 30 * s + 15 * s
        d.ellipse([cx_ - 11 * s, cy_ - 11 * s, cx_ + 11 * s, cy_ + 11 * s], fill=hexc(c))

def stamp(text, col='#B23A2E', sz=110, ang=-8):
    f = fnt(FRED, sz, axes=[700, 100]); w = int(f.getlength(text) + 80); h = sz + 60
    im = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 10 + w, 10 + h], radius=20, outline=hexc(col), width=10)
    bb = f.getbbox(text); d.text((10 + w / 2 - f.getlength(text) / 2, 10 + h / 2 - (bb[1] + bb[3]) / 2), text, font=f, fill=hexc(col))
    return im.rotate(ang, resample=Image.BICUBIC, expand=True)

def bigtxt(text, sz=150, col='#ffffff'):
    f = fnt(FRED, sz, axes=[700, 100]); w = int(f.getlength(text) + 60)
    im = Image.new('RGBA', (w, sz + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bb = f.getbbox(text); d.text((30, 40 + sz / 2 - (bb[1] + bb[3]) / 2), text, font=f, fill=hexc(col), stroke_width=10, stroke_fill=hexc('#15131a'))
    return im

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set(); S['hall'] = hall_set(); S['hut'] = hut_set()
    dcard = title_card('DAY 4', 'THE EMPTY CHAIR')
    navp = name_pill('NEW JOB', 'NAVIGATOR'); gp = name_pill('GUNNAR', 'THE OLD NAVIGATOR')
    c1878 = big_card('', '1878', 'BIRKA, SWEDEN', 'axe'); s_cmd = stamp('COMMANDER?', '#E9BC3F'); s_man = stamp('MAN', '#8a93ab', 130)
    s_wom = stamp('WOMAN', '#E9BC3F', 150); s_mur = stamp('NOT AN ACCIDENT', '#d24a3a', 90)
    hallcrowd = crowd(51, 2, 7, 4.6, 1.2, 4.6, exclude=lambda x, z: abs(x) < 1.2, expr_choices=('neutral', 'neutral', 'happy'))
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        if name == 'daycard':
            fr = fastblur(cam_bg(S['village'], 1.04 + 0.02 * u, 0, -20), 3.0)
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name in ('job', 'jarl', 'nav', 'chair'):
            fr = cam_bg(S['hall'], {'job': 1.0 + 0.04 * u, 'jarl': 1.12, 'nav': 1.08, 'chair': 1.15 + 0.06 * u}[name], 0, 40)
            fr = fastblur(fr, 1.0 if name == 'job' else 2.4)
            d = ImageDraw.Draw(fr)
            fl = 1 + 0.08 * math.sin(t * 11) + 0.05 * math.sin(t * 7)
            fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.8, 400 * fl, 200 * fl, '#ffb45a', 120))
            if name == 'job':
                cam = dict(cx=0, cz=lerp(-0.4, 0.1, eio(u)), f=1500, hor=H * 0.5, h=1.3, focus=4.2, ap=0.7)
                acts = hallcrowd + [Actor('jarl', -0.5, 5.2, JARL_V, expr='neutral', look=(0, 0), seed=76, size=1.18),
                                    Actor('hero', 0.55, 3.0, HV, expr='worried', look=(-1, -0.2), seed=90)]
                render_world2(fr, acts, cam, t)
            elif name == 'jarl':
                cam = dict(cx=-0.2, cz=1.0, f=1500, hor=H * 0.48, h=1.0, focus=2.2, ap=1.2)
                render_world2(fr, [Actor('jarl', -0.3, 3.2, JARL_V, expr='neutral', look=(1, 0), seed=76, size=1.18)], cam, t)
            elif name == 'nav':
                cam = dict(cx=0.2, cz=1.0, f=1500, hor=H * 0.48, h=0.95, focus=2.2, ap=1.2)
                render_world2(fr, [Actor('hero', 0.3, 3.0, HV, expr=(lambda tt: 'happy' if lt < 1.4 else 'worried'), look=(-1, 0), seed=90)], cam, t)
                pop(fr, navp, back((lt - 0.3) / 0.35), W / 2, 110)
            else:
                # empty chair, spotlight
                fr = tint(fr, (10, 8, 6), 0.45)
                fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.55, 300, 420, '#ffe4ad', 120))
                d = ImageDraw.Draw(fr); cx_, cy_ = W / 2, H * 0.7
                d.rectangle([cx_ - 120, cy_ - 380, cx_ - 90, cy_ + 160], fill=hexc('#5a3b24')); d.rectangle([cx_ + 90, cy_ - 380, cx_ + 120, cy_ + 160], fill=hexc('#5a3b24'))
                d.rectangle([cx_ - 120, cy_ - 380, cx_ + 120, cy_ - 330], fill=hexc('#6b4a30')); d.rectangle([cx_ - 120, cy_ - 250, cx_ + 120, cy_ - 220], fill=hexc('#6b4a30'))
                d.rectangle([cx_ - 140, cy_, cx_ + 140, cy_ + 40], fill=hexc('#7a5234'))
                d.rectangle([cx_ - 130, cy_ + 40, cx_ - 105, cy_ + 200], fill=hexc('#4a3322')); d.rectangle([cx_ + 105, cy_ + 40, cx_ + 130, cy_ + 200], fill=hexc('#4a3322'))
                for k in range(8):  # dust motes
                    rnd = random.Random(k); x = cx_ + rnd.uniform(-220, 220); y = (rnd.uniform(0, H) + t * 30) % H
                    d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 240, 200, 150))
        elif name == 'fog':
            pg = False
            fr = vgrad(W, H, [(0, '#0f1622'), (0.55, '#26354a'), (0.56, '#1a2433'), (1, '#0c1018')])
            g = make_char_cached('viking', 34, rand_viking(random.Random(91), rim='#9ab0d0'), 'neutral', False, (1, 0), 'down')
            g = stint(g, (60, 80, 110), 0.5)
            k = clamp(u * 1.1)
            x = lerp(W * 0.35, W * 0.62, k); sc_ = lerp(1.0, 0.7, k)
            gg = g.resize((int(g.width * sc_), int(g.height * sc_))); a = gg.getchannel('A').point(lambda p: int(p * (1 - 0.85 * ease((k - 0.4) / 0.6))))
            gg.putalpha(a); paste_safe(fr, gg, x - gg.width / 2, H * 0.62 - gg.height + 20 * math.sin(t * 6) * 0)
            fog = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fog)
            for i in range(14):
                rnd = random.Random(i); fx = (rnd.uniform(0, W) + t * rnd.uniform(20, 60)) % (W + 400) - 200; fy = rnd.uniform(H * 0.3, H * 0.75)
                fd.ellipse([fx - 300, fy - 70, fx + 300, fy + 70], fill=(190, 205, 220, 70))
            fr.alpha_composite(fastblur(fog, 30))
            fr = Image.alpha_composite(fr, glow(W, H, W * 0.75, H * 0.45, 500, 300, '#c8d6e6', int(100 * k)))
            pop(fr, gp, back((lt - 0.2) / 0.35), W / 2, 110)
        elif name in ('hut', 'chest', 'bone', 'blanket'):
            fr = cam_bg(S['hut'], {'hut': 1.0 + 0.04 * u, 'chest': 1.2, 'bone': 1.25, 'blanket': lerp(1.1, 1.35, eio(u))}[name], 0, 60)
            fr = fastblur(fr, 1.0 if name == 'hut' else 3.0)
            if name == 'hut':
                bl = bed_layer(0, 0.7, W * 0.32, H * 0.72); fr.alpha_composite(bl)
                cam = dict(cx=0, cz=0, f=1500, hor=H * 0.55, h=1.2, focus=3.3, ap=0.6)
                render_world2(fr, [Actor('hero', lerp(0.9, 0.5, ease(u)), 3.3, HV, expr='worried', look=(-1, 0), seed=92, bob=1 if u < 0.8 else 0)], cam, t)
            elif name == 'chest':
                d = ImageDraw.Draw(fr); d.rectangle([0, H * 0.1, W, H * 0.25], fill=hexc('#3a2618'))  # bed underside
                op = ease((t - wt('n04', 8)) / 0.8)
                ci = chest_img(op, 1.4); paste_safe(fr, ci, W / 2 - ci.width / 2, H * 0.92 - ci.height)
                if op > 0.1:
                    fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.62, 380, 160, '#ffe4ad', int(150 * op)))
                    d = ImageDraw.Draw(fr)
                    # tools
                    d.rectangle([W / 2 - 260, H * 0.62, W / 2 - 120, H * 0.62 + 24], fill=hexc('#8a8a8e')); d.rectangle([W / 2 - 150, H * 0.58, W / 2 - 110, H * 0.68], fill=hexc('#5a5a5e'))
                    d.ellipse([W / 2 + 120, H * 0.56, W / 2 + 230, H * 0.66], outline=hexc('#c9a24a'), width=8)
            elif name == 'bone':
                fr = tint(fr, (10, 8, 6), 0.4)
                fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.5, 600, 260, '#ffe4ad', 140))
                bi = bone_img(1.6, ease(lt / 1.0)).rotate(4 * math.sin(t), resample=Image.BICUBIC, expand=True)
                paste_safe(fr, bi, W / 2 - bi.width / 2, H * 0.48 - bi.height / 2)
                pop(fr, bubble('???', '#ffffff', '#1b1a2a', 50), back((lt - 1.0) / 0.3), W * 0.75, H * 0.2)
            else:
                st = ease((t - wt('n05', 9)) / 1.0)
                bl = bed_layer(st, 1.5, W / 2, H * 0.72); fr.alpha_composite(bl)
                hs = make_char_cached('hero', 36, HV | V(sweat=st > 0.5), 'scared' if st > 0.5 else 'worried', blink_at(t, 93), (0, 0.6), 'down')
                paste_safe(fr, hs, W * 0.82 - hs.width / 2, H * 0.98 - hs.height * 0.8)
                fr = tint(fr, (40, 10, 10), 0.12 * st)
        elif name in ('killed', 'night'):
            if name == 'killed':
                fr = fastblur(cam_bg(S['hut'], 1.3, 0, 60), 4.0)
                fr = tint(fr, (60, 10, 10), 0.25)
                cam = dict(cx=0, cz=1.1, f=1500, hor=H * 0.5, h=0.9, focus=2.0, ap=1.2)
                render_world2(fr, [Actor('hero', 0.0, 3.0, HV | V(sweat=True), expr='scared', look=(0, 0), seed=94)], cam, t)
                if lt < 0.25: fr = shake(fr, 8, t)
                pop(fr, s_mur, back((t - wt('n06', 2)) / 0.3), W / 2, H * 0.2)
            else:
                pg = False
                fr = vgrad(W, H, [(0, '#0a0f1c'), (0.6, '#1a2438'), (1, '#0a0d14')])
                fr = Image.alpha_composite(fr, glow(W, H, W * 0.75, H * 0.2, 120, 120, '#dfe8ff', 200))
                d = ImageDraw.Draw(fr)
                d.polygon([(W * 0.1, H * 0.85), (W * 0.1, H * 0.5), (W * 0.2, H * 0.38), (W * 0.3, H * 0.5), (W * 0.3, H * 0.85)], fill=hexc('#05070c'))
                d.rectangle([W * 0.17, H * 0.65, W * 0.23, H * 0.85], fill=hexc('#ffb45a', 120))
                sil = make_char_cached('viking', 30, rand_viking(random.Random(95)), 'neutral', False, (-1, 0), 'down')
                sil = Image.composite(Image.new('RGBA', sil.size, (4, 5, 9, 255)), Image.new('RGBA', sil.size, (0, 0, 0, 0)), sil.getchannel('A'))
                paste_safe(fr, sil, lerp(W * 0.7, W * 0.4, ease(u)) - sil.width / 2, H * 0.9 - sil.height)
                d.rectangle([0, H * 0.88, W, H], fill=hexc('#05070c'))
                pop(fr, label_box('THE NIGHT BEFORE YOU ARRIVED', '#cdd6ff', '#6f7cff'), back(lt / 0.35), W / 2, 110)
        elif name == 'helm':
            fr = cam_bg(S['cool'], 1.05 + 0.03 * u, 0, -30)
            waves(fr, t, '#3e5d7a', H * 0.7, 16, 0.5, 1.2)
            b = boat_img(t, 1.0)
            hs = make_char_cached('hero', 22, HV, 'happy', blink_at(t, 96), (1, 0), 'up')
            b.alpha_composite(hs, (int(470 - hs.width / 2), int(362 - hs.height)))
            bd = ImageDraw.Draw(b); bd.line([(500, 300), (540, 470)], fill=hexc('#4a3322'), width=12)
            b = b.resize((int(b.width * 1.6), int(b.height * 1.6)), Image.BILINEAR).rotate(3 * math.sin(t * 1.3), resample=Image.BICUBIC, expand=True)
            paste_safe(fr, b, W * 0.5 - b.width / 2, H * 0.72 - b.height * 0.68)
            waves(fr, t, '#2f4e6b', H * 0.84, 20, 2.0, 1.6)
            pop(fr, label_box('WOMEN AT THE HELM'), back((lt - 0.3) / 0.35), W / 2, 110)
        elif name in ('birka', 'items', 'commander', 'assumed', 'dna'):
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            if name == 'birka':
                # stylized Scandinavia map + pin
                z = lerp(1.0, 1.25, eio(u)); ox, oy = W * 0.55, H * 0.5
                def P(x, y): return (ox + (x - ox) * z, oy + (y - oy) * z)
                d.polygon([P(*p) for p in [(W * 0.36, H * 0.95), (W * 0.33, H * 0.7), (W * 0.42, H * 0.4), (W * 0.55, H * 0.12), (W * 0.66, H * 0.05), (W * 0.7, H * 0.2), (W * 0.62, H * 0.45), (W * 0.6, H * 0.7), (W * 0.52, H * 0.95)]], fill=hexc('#b9a77e'))
                d.line([P(W * 0.47, H * 0.62), P(W * 0.6, H * 0.6)], fill=hexc('#8a7a5a'), width=3)
                px, py = P(W * 0.555, H * 0.62)
                k = back((t - wt('n08', 12)) / 0.3)
                if k > 0.02:
                    d.ellipse([px - 18 * k, py - 18 * k, px + 18 * k, py + 18 * k], fill=hexc('#B23A2E'))
                    f = fnt(FRED, 54, axes=[700, 100]); d.text((px + 30, py - 40), 'BIRKA', font=f, fill=hexc('#1b1a2a'))
                pop(fr, c1878, back((lt - 0.2) / 0.35), W * 0.22, H * 0.3)
            elif name == 'items':
                f = fnt(FRED, 40, axes=[700, 100])
                specs = [(3, 'SWORD', sword_icon), (5, 'AXE', None), (7, 'SPEAR', spear_icon), (8, 'ARROWS', arrows_icon), (10, '2 HORSES', horse_icon), (15, 'BOARD GAME', board_icon)]
                for i, (wi, lab, fn) in enumerate(specs):
                    k = back((t - wt('n09', wi) + 0.05) / 0.3)
                    if k <= 0.02: continue
                    cx_ = W * (0.105 + i * 0.158); cy_ = H * 0.46
                    lay = Image.new('RGBA', (360, 460), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                    ld.rounded_rectangle([20, 20, 340, 440], radius=30, fill=hexc('#fff6dc'), outline=hexc('#5a4030'), width=5)
                    if lab == 'AXE':
                        ax = axe_img(260, -30); lay.alpha_composite(ax, (int(180 - ax.width / 2), int(200 - ax.height / 2)))
                    elif lab == '2 HORSES':
                        horse_icon(ld, 150, 150, 0.9); horse_icon(ld, 190, 270, 0.9, '#4a3322')
                    else:
                        fn(ld, 180, 210, 1.0)
                    ld.text((180 - f.getlength(lab) / 2, 370), lab, font=f, fill=hexc('#1b1a2a'))
                    lay = lay.resize((290, 370), Image.LANCZOS)
                    pop(fr, lay, k, cx_, cy_)
            elif name == 'commander':
                d.rounded_rectangle([W * 0.3, H * 0.25, W * 0.7, H * 0.8], radius=200, fill=hexc('#c9b48a'), outline=hexc('#8a7a5a'), width=8)
                sil = make_char_cached('viking', 30, rand_viking(random.Random(97)) | V(helmet=True), 'neutral', False, (0, 0), 'down')
                sil = Image.composite(Image.new('RGBA', sil.size, (90, 75, 55, 255)), Image.new('RGBA', sil.size, (0, 0, 0, 0)), sil.getchannel('A'))
                paste_safe(fr, sil, W / 2 - sil.width / 2, H * 0.78 - sil.height)
                pop(fr, s_cmd, back((t - wt('n10', 8)) / 0.3), W / 2, H * 0.2)
            elif name == 'assumed':
                yr = int(lerp(1878, 2008, ease(u * 1.2)))
                bt = bigtxt(str(yr), 170, '#ffffff'); paste_safe(fr, bt, W / 2 - bt.width / 2, H * 0.22)
                bt2 = bigtxt('130 YEARS', 70, '#E9BC3F'); paste_safe(fr, bt2, W / 2 - bt2.width / 2, H * 0.5)
                pop(fr, s_man, back((t - wt('n11', 8)) / 0.3), W / 2, H * 0.74)
            else:
                # DNA helix
                cx_ = W * 0.3
                for i in range(40):
                    y = H * 0.08 + i * H * 0.021; ph = i * 0.45 + t * 2.5
                    x1 = cx_ + 150 * math.sin(ph); x2 = cx_ - 150 * math.sin(ph)
                    d.line([x1, y, x2, y], fill=hexc('#a08a62'), width=3)
                    for (x, c) in ((x1, '#2f6e9e'), (x2, '#B23A2E')):
                        r = 9 + 4 * math.cos(ph); d.ellipse([x - r, y - r, x + r, y + r], fill=hexc(c))
                bt = bigtxt('2017', 150); paste_safe(fr, bt, W * 0.68 - bt.width / 2, H * 0.12)
                k = back((t - wt('n12', 8)) / 0.3)
                if k > 0.02:
                    hs = make_char_cached('hero', 36, HV | V(coat='#5a6e8a', coat_dk='#46566c', hair='#c9a24a'), 'happy', blink_at(t, 98), (0, 0), 'up')
                    paste_safe(fr, hs, W * 0.68 - hs.width / 2, H * 1.02 - hs.height)
                pop(fr, s_wom, k, W * 0.68, H * 0.45)
        if pg: fr = Image.alpha_composite(fr, glow_cache('x'))
        fr = Image.alpha_composite(fr, haze); fr = Image.alpha_composite(fr, dark)
        hook.caption2(fr, t)
        rgb = fr.convert('RGB'); ga, gb = grains[fi % 6]
        rgb = ImageChops.subtract(ImageChops.add(rgb, ga), gb)
        if t < 0.3: rgb = Image.blend(Image.new('RGB', (W, H)), rgb, t / 0.3)
        if t > DUR - 0.7: rgb = Image.blend(rgb, Image.new('RGB', (W, H)), clamp((t - (DUR - 0.7)) / 0.7))
        if proc: proc.stdin.write(rgb.tobytes())
        else: rgb.save(os.path.join(HD, f'prev/p_{t:05.2f}_{name}.jpg'), quality=85)
    if proc: proc.stdin.close(); proc.wait()

if __name__ == '__main__':
    if sys.argv[1] == 'info':
        print('DUR', DUR); [print(n, round(s, 2), round(e, 2)) for n, s, e in SPANS]
    elif sys.argv[1] == 'prev':
        os.makedirs(os.path.join(HD, 'prev'), exist_ok=True)
        ts = [float(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else [s + (e - s) * 0.7 for n, s, e in SPANS]
        run([int(x * FPS) for x in ts])
    else:
        a, b = int(sys.argv[2]), int(sys.argv[3]); run(range(a, b), out=sys.argv[4])
