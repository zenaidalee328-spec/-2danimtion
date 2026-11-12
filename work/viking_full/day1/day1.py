import sys, os, json, math, random, subprocess
sys.path.insert(0, '/workspace/work/viking3'); sys.path.insert(0, '/workspace/work/viking_full/hook')
import v3, hook
from v3 import *
from hook import render_world2, kneel_sprite, label_box, big_card, pop, tint, dur
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'n02': 0.5, 'n03': 0.3, 'n04': 0.4, 'v01': 0.25, 'n06': 0.7, 'n08': 0.35, 'n10': 0.6, 'n12': 0.3, 'n13': 0.5, 'n14': 0.6, 'h01': 0.4, 'n16': 0.7}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.22)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text']) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'v': 'V', 'h': 'H'}.get(lid[0], 'N'))
    t += d_
DUR = t + 1.8
hook.TL = TL
hook.LABELS = {'V': 'V I K I N G', 'H': 'H A K O N'}
def S_(l): return TL[l]['st']
def E_(l): return TL[l]['en']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('nobind', S_('n02') - 0.3), ('carry', S_('n03') - 0.15),
         ('village', S_('n04') - 0.2), ('catch', S_('n05') - 0.1),
         ('gran', S_('n06') - 0.35), ('tree', wt('n06', 6) - 0.1), ('saga', S_('n07') - 0.1),
         ('onein3', S_('n08') - 0.15), ('daughter', S_('n09') - 0.15),
         ('ran', S_('n10') - 0.3), ('net', S_('n11') - 0.1), ('waves9', S_('n12') - 0.15),
         ('smug', S_('n13') - 0.2), ('part', S_('n14') - 0.3), ('hakonname', S_('n15') - 0.15),
         ('hakonline', S_('h01') - 0.2), ('silence', S_('n16') - 0.25)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]

HV = HERO_V
HAKON_V = V(coat='#2E3B55', tunic='#1f2a3e', beard='#E2C27A', beard_dk='#c4a55e', helmet=False, hair='#E2C27A', rim='#F6B07A', weapon='axe', fur='#d9d0c2')
JARL_V = V(coat='#7A3B2E', beard='#c2502a', beard_dk='#9c3e1f', helmet=True, rim='#F6B07A')

# ---------------- new sets
def village_set():
    sky = [(0, '#bfc9d6'), (0.3, '#e2dcd8'), (0.38, '#f0ddcc'), (1, '#d8cbb8')]
    img, hy = fjord_beach(sky=sky, sea=[(0, '#5f7c99'), (1, '#86a3b8')], sand=('#9c9a6a', '#7f7c52'),
                          mtn_cols=[('#8a93ab', 180, 80), ('#6c7590', 90, 22)], sun=(0.3, 260, '#fff6e6'), seed=8)
    d = ImageDraw.Draw(img); BWv, BHv = img.size
    gy = hy + 8 + int(BHv * 0.16)
    # meadow over the sea band so village sits on land
    img.paste(vgrad(BWv, BHv - int(hy + 6), [(0, '#a8ad78'), (0.4, '#8f9460'), (1, '#6f7046')]), (0, int(hy + 6)))
    d = ImageDraw.Draw(img); rnd = random.Random(4)
    houses = []
    for (x, y, s) in [(0.12, 0.05, 0.8), (0.3, 0.02, 0.65), (0.5, 0.0, 0.55), (0.68, 0.02, 0.65), (0.88, 0.05, 0.85), (0.22, 0.12, 1.15), (0.78, 0.13, 1.2)]:
        cx_, by = BWv * x, hy + 30 + BHv * y; w = 380 * s; h = 120 * s
        d.rectangle([cx_ - w / 2, by - h, cx_ + w / 2, by], fill=hexc('#6b4a30'))
        for k in range(9):
            xx = cx_ - w / 2 + k * w / 8; d.line([xx, by - h, xx, by], fill=hexc('#4f3522'), width=max(2, int(4 * s)))
        d.polygon([(cx_ - w / 2 - 30 * s, by - h + 6), (cx_ - w * 0.32, by - h - 95 * s), (cx_ + w * 0.32, by - h - 95 * s), (cx_ + w / 2 + 30 * s, by - h + 6)], fill=hexc('#5f7a3c'))
        d.polygon([(cx_ - w * 0.32, by - h - 95 * s), (cx_ + w * 0.32, by - h - 95 * s), (cx_ + w * 0.28, by - h - 80 * s), (cx_ - w * 0.28, by - h - 80 * s)], fill=hexc('#7d9a4e'))
        d.rounded_rectangle([cx_ - 22 * s, by - 75 * s, cx_ + 22 * s, by], radius=int(10 * s), fill=hexc('#2a1c12'))
        for sgn in (-1, 1):  # dragon gable heads
            gx = cx_ + sgn * w * 0.32
            d.line([gx, by - h - 95 * s, gx + sgn * 30 * s, by - h - 140 * s], fill=hexc('#4f3522'), width=max(3, int(9 * s)))
            d.ellipse([gx + sgn * 30 * s - 9 * s, by - h - 150 * s, gx + sgn * 30 * s + 9 * s, by - h - 132 * s], fill=hexc('#4f3522'))
        houses.append((cx_, by - h - 95 * s, s))
    for i in range(70):  # fence
        x = i * BWv / 69; y = hy + 175 + 8 * math.sin(i)
        d.line([x, y, x, y - 34], fill=hexc('#5a4030'), width=5)
    d.line([0, hy + 155, BWv, hy + 158], fill=hexc('#5a4030'), width=4)
    return img, hy, houses

def underwater_set():
    img = vgrad(BW, BH, [(0, '#3f8fb0'), (0.4, '#1f5f84'), (1, '#0b2440')])
    rays = Image.new('L', (BW, BH), 0); dr = ImageDraw.Draw(rays)
    for k in range(7):
        x = BW * (0.1 + k * 0.13); dr.polygon([(x, 0), (x + 90, 0), (x + 260, BH), (x + 60, BH)], fill=55)
    rays = rays.filter(ImageFilter.GaussianBlur(40)); rl = Image.new('RGBA', (BW, BH), hexc('#bfefff')); rl.putalpha(rays)
    img = Image.alpha_composite(img, rl); d = ImageDraw.Draw(img)
    # sunken hall: pillars and roof
    base = BH * 0.86
    d.rectangle([BW * 0.2, base - 20, BW * 0.8, base + 30], fill=hexc('#0e3a52'))
    for k in range(7):
        x = BW * (0.24 + k * 0.087); d.rectangle([x - 26, base - 330, x + 26, base - 20], fill=hexc('#145070'))
        d.rectangle([x - 36, base - 350, x + 36, base - 325], fill=hexc('#1a6488'))
    d.polygon([(BW * 0.18, base - 345), (BW * 0.5, base - 520), (BW * 0.82, base - 345)], fill=hexc('#13506e'))
    rnd = random.Random(7)
    for i in range(40):  # seaweed
        x = rnd.uniform(0, BW); hgt = rnd.uniform(80, 260)
        d.line([(x + 14 * math.sin(k / 3), BH - k * hgt / 12) for k in range(13)], fill=hexc('#1f6b4f'), width=8)
    d.rectangle([0, BH * 0.93, BW, BH], fill=hexc('#0a2234'))
    return img

def parchment(w, h):
    img = vgrad(w, h, [(0, '#efe0bd'), (1, '#e0c999')])
    g = glow(w, h, w / 2, h / 2, w * 0.7, h * 0.7, '#fff6dc', 120)
    img = Image.alpha_composite(img, g)
    return img

# ---------------- helpers
def bubble(text, col='#ffffff', tc='#1b1a2a', sz=40):
    f = fnt(NUN, sz, b'Black'); w = int(f.getlength(text) + 60); h = sz + 40
    img = Image.new('RGBA', (w + 20, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, 10 + w, 10 + h], radius=h // 2, fill=hexc(col), outline=hexc('#15131a'), width=4)
    d.polygon([(w * 0.35, 10 + h - 2), (w * 0.3 + 10, h + 36), (w * 0.5, 10 + h - 2)], fill=hexc(col))
    bb = f.getbbox(text); d.text((10 + w / 2 - f.getlength(text) / 2, 10 + h / 2 - (bb[1] + bb[3]) / 2), text, font=f, fill=hexc(tc))
    return img

def name_pill(name, sub):
    f1 = fnt(NUN, 30, b'Black'); f2 = fnt(NUN, 20, b'ExtraBold')
    w = int(f1.getlength(name) + f2.getlength(sub) + 80)
    img, p = rr_img(w, 56, 14, NAVY, GOLD, 3)
    d = ImageDraw.Draw(img)
    bb = f1.getbbox(name); d.text((p + 26, p + 28 - (bb[1] + bb[3]) / 2), name, font=f1, fill=WHITE)
    bb = f2.getbbox(sub); d.text((p + 26 + f1.getlength(name) + 24, p + 28 - (bb[1] + bb[3]) / 2), sub, font=f2, fill=GOLD)
    return img

RUNES = 'ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ'
def rune_text(seed, n):
    r = random.Random(seed); return ''.join(r.choice(RUNES) for _ in range(n))

def smoke(fr, houses, cam_zoom, ox, oy, t):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for (hx, hy_, s) in houses:
        x0 = (hx - (BW - W / cam_zoom) / 2 - ox) * cam_zoom; y0 = (hy_ - (BH - H / cam_zoom) / 2 - oy) * cam_zoom
        for k in range(6):
            ph = (t * 0.35 + k / 6) % 1
            r = (12 + 40 * ph) * s * cam_zoom
            d.ellipse([x0 + 30 * ph * s - r + 10 * math.sin(t + k), y0 - 260 * ph * s - r, x0 + 30 * ph * s + r, y0 - 260 * ph * s + r], fill=(235, 235, 240, int(110 * (1 - ph))))
    fr.alpha_composite(fastblur(lay, 6))

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], S['village_hor'], houses = village_set()
    S['under'] = underwater_set()
    dcard = title_card('DAY 1', 'THE DAUGHTER OF THE SEA')
    hk_pill = name_pill('HAKON', "THE JARL'S SON"); ran_pill = name_pill('RÁN', 'GODDESS OF THE SEA')
    dau_pill = name_pill('DAUGHTER OF RÁN', '?'); c800 = big_card('', '800', 'YEARS OLD SAGAS', 'axe')
    b_ran = bubble('RÁN!', '#FFC93C', '#1b1a2a', 54)
    gib = [bubble(w, '#ffffff', '#3a3550', 34) for w in ['HVAT?', 'KONA!', 'SJA HANA', 'HON LIFIR', 'UNDR!', 'HAFIT...']]
    ring = crowd(31, 2, 8, 3.6, 1.3, 3.8, exclude=lambda x, z: abs(x) < 0.9 and z < 4.6, expr_choices=('neutral', 'happy', 'neutral'))
    vil = crowd(32, 3, 9, 4.2, 1.4, 4.8, exclude=lambda x, z: abs(x) < 0.8 and z < 5.0, expr_choices=('neutral', 'happy', 'neutral'))
    awe = crowd(33, 2, 9, 3.4, 1.3, 4.0, exclude=lambda x, z: abs(x) < 0.9 and z < 4.4, expr_choices=('happy', 'neutral'))
    for a in awe: a.kneel = 1.0
    part = crowd(34, 3, 8, 3.6, 1.2, 3.6, expr_choices=('neutral', 'neutral', 'angry'))
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0)
        post_glow = True
        if name == 'daycard':
            fr = fastblur(cam_bg(S['beach'], 1.04 + 0.02 * u, 0, -40), 3.0)
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name == 'nobind':
            fr = fastblur(cam_bg(S['beach'], 1.06 + 0.03 * u, 0, -50), 1.2)
            cz = lerp(-0.1, 0.35, eio(u))
            cam = dict(cx=0, cz=cz, f=1500, hor=H * 0.44, h=1.2, focus=2.7 - cz, ap=0.9)
            ex = (lambda tt: 'scared' if lt < 1.2 else 'worried')
            render_world2(fr, ring + [Actor('hero', 0, 2.7, HV | V(sweat=True), expr=ex, look=(lambda tt: (-1, 0.2) if math.sin(tt * 2.2) > 0 else (1, 0.2)), seed=51)], cam, t)
            # a dropped rope coil and an axe being lowered
            k = eout((lt - 0.3) / 0.5)
            ax = axe_img(380, lerp(-35, -95, k))
            paste_safe(fr, ax, W * 0.78 - ax.width / 2, H * 0.55 - ax.height / 2 + 120 * k)
        elif name == 'carry':
            img = S['village']
            ox = lerp(-160, 120, u)
            fr = fastblur(cam_bg(img, 1.05, ox, -20), 1.6)
            smoke(fr, houses, 1.05, ox, -20, t)
            # litter carried by 4 vikings walking right
            cam = dict(cx=0, cz=0, f=1500, hor=H * 0.43, h=1.3, focus=3.2, ap=0.6)
            x0 = lerp(-1.6, 0.4, u)
            carriers = []
            for i, dx in enumerate((-0.55, -0.18, 0.18, 0.55)):
                carriers.append(Actor('viking', x0 + dx, 3.2 + (0.05 if i % 2 else -0.05), rand_viking(random.Random(60 + i)) | V(shield=None, weapon=None), expr='neutral', pose='up', seed=60 + i, bob=1))
            for a in carriers: a.v.pop('shield', None); a.v.pop('weapon', None)
            render_world2(fr, carriers[0::2], cam, t)
            s_ = 1500 / 3.2; R = HEAD_U * s_
            sx = W / 2 + x0 * s_; ty = H * 0.43 + 1.3 * s_ - R * 12.2 * 0.83 + 4 * math.sin(t * 5)
            d = ImageDraw.Draw(fr)
            d.rounded_rectangle([sx - 1.0 * s_ * 0.8, ty - R * 0.6, sx + 1.0 * s_ * 0.8, ty + R * 0.5], radius=int(R * 0.5), fill=hexc('#a8957f'))
            for k in range(10):
                xx = sx - 0.78 * s_ + k * 0.17 * s_; d.ellipse([xx - R * 0.35, ty - R * 0.9, xx + R * 0.35, ty - R * 0.2], fill=hexc('#c2b29a'))
            hs = make_char_cached('hero', int(R * 0.9), HV, 'worried', blink_at(t, 61), (0, -1), 'down').rotate(90, expand=True)
            paste_safe(fr, hs, sx - hs.width / 2 + R, ty - hs.height * 0.75)
            d = ImageDraw.Draw(fr)
            for k in range(7):
                xx = sx - 0.7 * s_ + k * 0.22 * s_; d.ellipse([xx - R * 0.5, ty - R * 0.45, xx + R * 0.5, ty + R * 0.35], fill=hexc('#d9cdb8'))
            render_world2(fr, carriers[1::2], cam, t)
            # glass sparkle
            for g in range(3): glint(fr, sx + (g - 1) * R * 3, ty - R * 1.8, 26, ((lt - 1.0 - g * 0.5) % 2.2) / 0.5)
        elif name in ('village', 'catch', 'daughter', 'smug', 'part', 'hakonname', 'hakonline', 'silence', 'onein3'):
            zb = {'village': 1.0 + 0.04 * u, 'catch': 1.12, 'daughter': 1.05, 'smug': 1.15, 'part': 1.04, 'hakonname': 1.1, 'hakonline': 1.14, 'silence': 1.0 + 0.05 * u, 'onein3': 1.1}[name]
            fr = cam_bg(S['village'], zb, 0, -20)
            fr = fastblur(fr, {'village': 0.8, 'silence': 0.8}.get(name, 1.6))
            smoke(fr, houses, zb, 0, -20, t)
            if name == 'village':
                cz = lerp(-0.6, 0.0, eio(u))
                cam = dict(cx=lerp(-0.3, 0.3, u), cz=cz, f=1500, hor=H * 0.42, h=1.35, focus=3.6 - cz, ap=0.8)
                render_world2(fr, vil + [Actor('hero', 0, 3.6, HV | V(sweat=True), expr='worried', look=(lambda tt: (-1, 0) if math.sin(tt * 1.7) > 0 else (1, 0)), seed=62)], cam, t)
                for i, b in enumerate(gib):
                    k = back((lt - 0.2 - i * 0.3) / 0.3) * (1 - ease((lt - 1.6 - i * 0.3) / 0.3))
                    pop(fr, b, k, W * (0.15 + i * 0.14), H * (0.2 + 0.08 * (i % 2)))
            elif name == 'catch':
                cam = dict(cx=0, cz=lerp(0.4, 0.7, u), f=1500, hor=H * 0.44, h=0.95, focus=2.6 - lerp(0.4, 0.7, u), ap=1.0)
                spk = Actor('viking', -0.55, 2.6, rand_viking(random.Random(70)), expr='happy', look=(1, 0), seed=70)
                hero = Actor('hero', 0.6, 2.75, HV, expr=(lambda tt: 'scared' if tt > S_('v01') + 0.2 else 'worried'), look=(-1, 0), seed=71)
                render_world2(fr, crowd(35, 2, 7, 4.4, 1.4, 3.6) + [spk, hero], cam, t)
                if t > S_('v01') - 0.05:
                    pop(fr, b_ran, back((t - S_('v01') + 0.05) / 0.3), W * 0.3, H * 0.18)
                    if t - S_('v01') < 0.25: fr = shake(fr, 6, t)
            elif name == 'onein3':
                cam = dict(cx=0, cz=0.5, f=1500, hor=H * 0.44, h=0.95, focus=2.2, ap=1.0)
                render_world2(fr, crowd(36, 2, 7, 4.4, 1.4, 3.6) + [Actor('viking', 0.0, 2.7, rand_viking(random.Random(72)), expr='happy', look=(0, 0), seed=72)], cam, t)
                for i in range(3):
                    lit = (i == 1) and lt > 1.3
                    b = bubble('SEA' if lit else '???', '#FFC93C' if lit else '#dfe2ea', '#1b1a2a', 44)
                    pop(fr, b, back((lt - 0.15 - i * 0.25) / 0.3), W * (0.3 + i * 0.2), H * 0.16)
            elif name == 'daughter':
                cz = lerp(-0.3, 0.3, eio(u))
                cam = dict(cx=0, cz=cz, f=1500, hor=H * 0.43, h=1.2, focus=3.0 - cz, ap=0.8)
                lay_g = glow(W, H, W / 2, H * 0.45, 380, 420, '#bfefff', int(150 * ease(u * 2)))
                fr = Image.alpha_composite(fr, lay_g)
                render_world2(fr, awe + [Actor('hero', 0, 3.0, HV, expr='worried', look=(0, -0.5), seed=73)], cam, t)
                pop(fr, dau_pill, back((t - wt('n09', 9)) / 0.35), W / 2, 110)
            elif name == 'smug':
                cam = dict(cx=0.1, cz=0.9, f=1500, hor=H * 0.46, h=0.85, focus=2.0, ap=1.1)
                render_world2(fr, crowd(37, 2, 7, 3.8, 1.3, 3.2, exclude=lambda x, z: abs(x) < 0.6) + [Actor('hero', 0.05, 2.9, HV, expr=(lambda tt: 'happy' if lt > 0.7 else 'neutral'), look=(lambda tt: (1, 0) if lt > 0.7 else (0, 0)), seed=74)], cam, t)
                glint(fr, W * 0.56, H * 0.3, 30, (lt - 0.9) / 0.4)
            elif name == 'part':
                cz = lerp(-0.4, 0.1, eio(u))
                cam = dict(cx=0, cz=cz, f=1500, hor=H * 0.42, h=1.35, focus=lerp(6.0, 3.6, ease(u)) - cz, ap=1.0)
                hz = lerp(7.2, 3.8, eio(u))
                acts = []
                for a in part:
                    side = 1 if a.x >= 0 else -1
                    near = clamp(1 - abs(a.z - hz) / 1.5)
                    push = side * 0.55 * eout(clamp((7.4 - a.z) / 4 * 1.0 + (u - 0.15) * 1.6 - 0.2)) if abs(a.x) < 1.6 else 0
                    acts.append(Actor('viking', a.x + push, a.z, a.v, expr=a.expr, look=(side, 0), seed=a.seed))
                hak = Actor('viking', 0.0, hz, HAKON_V, expr='smirk', look=(0, 0), seed=75, size=1.14, bob=1 if u < 0.9 else 0)
                render_world2(fr, acts + [hak], cam, t)
            elif name == 'hakonname':
                cam = dict(cx=-0.3, cz=0.6, f=1500, hor=H * 0.43, h=1.1, focus=2.6, ap=1.0)
                hak = Actor('viking', -0.35, 3.2, HAKON_V, expr='smirk', look=(1, 0), seed=75, size=1.14)
                jarl = Actor('jarl', -1.4, 6.0, JARL_V, expr='neutral', look=(1, 0), seed=76, size=1.18)
                render_world2(fr, crowd(38, 1, 6, 5.5, 1, 3.6, exclude=lambda x, z: abs(x + 1.4) < 0.8) + [jarl, hak], cam, t)
                pop(fr, hk_pill, back((t - wt('n15', 3)) / 0.35), W * 0.33, H * 0.12)
            elif name == 'hakonline':
                rf = ease((t - wt('h01', 6)) / 0.6)
                cam = dict(cx=0.2, cz=lerp(0.7, 0.9, u), f=1500, hor=H * 0.43, h=0.95, focus=lerp(2.5, 4.2, rf) - lerp(0.7, 0.9, u), ap=1.6)
                hak = Actor('viking', -0.4, 2.5, HAKON_V, expr='smirk', look=(lambda tt: (1, 0) if rf < 0.5 else (0.6, 0.3)), seed=75, size=1.14)
                hero = Actor('hero', 0.9, 4.2, HV | V(sweat=rf > 0.5), expr=(lambda tt: 'scared' if rf > 0.5 else 'worried'), look=(-1, 0), seed=77)
                render_world2(fr, crowd(39, 1, 6, 6.2, 1, 3.6, exclude=lambda x, z: abs(x - 0.9) < 0.7) + [hero, hak], cam, t)
                fr = tint(fr, (40, 30, 60), 0.12 * rf)
            elif name == 'silence':
                cz = lerp(-1.2, -0.6, u)
                cam = dict(cx=0, cz=cz, f=1500, hor=H * 0.40, h=1.6, focus=5.0, ap=0.5)
                render_world2(fr, vil + [Actor('hero', 0.5, 4.2, HV, expr='worried', look=(-1, 0), seed=78), Actor('viking', -0.5, 4.3, HAKON_V, expr='smirk', look=(1, 0), seed=75, size=1.14)], cam, t)
                fr = tint(fr, (30, 30, 50), 0.18 + 0.1 * u)
        elif name == 'gran':
            post_glow = False
            pg = parchment(W, H); d = ImageDraw.Draw(pg)
            # fireplace glow
            pg = Image.alpha_composite(pg, glow(W, H, W * 0.78, H * 0.62, 300, 260, '#ff9f3a', 150))
            d = ImageDraw.Draw(pg)
            fl = 18 * math.sin(t * 9)
            d.polygon([(W * 0.74, H * 0.72), (W * 0.78, H * 0.55 + fl), (W * 0.82, H * 0.72)], fill=hexc('#e9883a'))
            d.rectangle([W * 0.7, H * 0.72, W * 0.86, H * 0.76], fill=hexc('#5a4030'))
            gran = make_char_cached('hero', 70, V(coat='#6a7f9a', coat_dk='#53657d', hair='#d8d4cc', rim='#ffd9a8'), 'happy', blink_at(t, 80), (1, 0), 'down')
            kid = make_char_cached('hero', 50, HV | V(hair='#3a2216'), 'happy', blink_at(t, 81), (-1, 0), 'down')
            paste_safe(pg, gran, W * 0.36 - gran.width / 2, H * 0.84 - gran.height)
            paste_safe(pg, kid, W * 0.55 - kid.width / 2, H * 0.84 - kid.height)
            d = ImageDraw.Draw(pg)
            d.polygon([(W * 0.4, H * 0.6), (W * 0.47, H * 0.56), (W * 0.54, H * 0.6), (W * 0.47, H * 0.64)], fill=hexc('#7a3b2e'))
            pg = pg.convert('LA').convert('RGBA')
            fr = Image.blend(pg, Image.new('RGBA', (W, H), hexc('#c9a46a')), 0.35)
            fr = cam_bg(fr, 1.0 + 0.05 * u) if False else fr
            pop(fr, label_box('GRANDMA'), back(lt / 0.35), W / 2, 110)
        elif name == 'tree':
            post_glow = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            fb = fnt(FRED, 64, axes=[700, 100]); fs = fnt(FRED, 46, axes=[700, 100])
            k0 = back(lt / 0.35)
            root = ('OLD NORSE', W / 2, H * 0.28)
            kids = [('ICELANDIC', W * 0.17), ('NORWEGIAN', W * 0.39), ('DANISH', W * 0.61), ('SWEDISH', W * 0.83)]
            for i, (nm, x) in enumerate(kids):
                k = eout((lt - 0.5 - i * 0.18) / 0.4)
                if k <= 0: continue
                d.line([W / 2, H * 0.36, lerp(W / 2, x, k), lerp(H * 0.36, H * 0.6, k)], fill=hexc('#5a4030'), width=8)
                if k > 0.9:
                    hl = nm in ('NORWEGIAN', 'ICELANDIC')
                    w = fs.getlength(nm) + 40
                    d.rounded_rectangle([x - w / 2, H * 0.6, x + w / 2, H * 0.6 + 80], radius=18, fill=hexc('#FFC93C' if hl else '#e8dcc0'), outline=hexc('#5a4030'), width=4)
                    bb = fs.getbbox(nm); d.text((x - fs.getlength(nm) / 2, H * 0.6 + 40 - (bb[1] + bb[3]) / 2), nm, font=fs, fill=hexc('#1b1a2a'))
            w = fb.getlength(root[0]) + 60
            if k0 > 0.02:
                box = Image.new('RGBA', (int(w) + 10, 120), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
                bd.rounded_rectangle([4, 4, w, 112], radius=24, fill=hexc('#1b2140'), outline=GOLD, width=5)
                bb = fb.getbbox(root[0]); bd.text((w / 2 + 2 - fb.getlength(root[0]) / 2, 58 - (bb[1] + bb[3]) / 2), root[0], font=fb, fill=WHITE)
                pop(fr, box, k0, root[1], root[2])
            d = ImageDraw.Draw(fr)
        elif name == 'saga':
            post_glow = False
            fr = Image.new('RGBA', (W, H), hexc('#3a2a1e'))
            fr = Image.alpha_composite(fr, glow(W, H, W / 2, H / 2, 900, 520, '#ffcf8a', 160))
            d = ImageDraw.Draw(fr)
            z = lerp(1.0, 1.08, u)
            bw_, bh_ = 1300 * z, 700 * z; cx_, cy_ = W / 2, H * 0.52
            d.rounded_rectangle([cx_ - bw_ / 2 - 20, cy_ - bh_ / 2 - 20, cx_ + bw_ / 2 + 20, cy_ + bh_ / 2 + 20], radius=30, fill=hexc('#5a3020'))
            for sgn in (-1, 1):
                d.rounded_rectangle([cx_ + (0 if sgn > 0 else -bw_ / 2), cy_ - bh_ / 2, cx_ + (bw_ / 2 if sgn > 0 else 0), cy_ + bh_ / 2], radius=16, fill=hexc('#efe0bd'))
                for ln in range(13):
                    y = cy_ - bh_ / 2 + 60 * z + ln * 46 * z
                    x0 = cx_ + (40 * z if sgn > 0 else -bw_ / 2 + 50 * z)
                    L = (bw_ / 2 - 100 * z) * (0.6 + 0.4 * random.Random(ln * 3 + sgn).random())
                    d.line([x0, y, x0 + L * eout((lt - 0.1 - ln * 0.05) / 0.4), y], fill=hexc('#4a3a2a', 200), width=int(7 * z))
            d.line([cx_, cy_ - bh_ / 2, cx_, cy_ + bh_ / 2], fill=hexc('#b39a6e'), width=6)
            d.rectangle([cx_ - bw_ / 2 + 50 * z, cy_ - bh_ / 2 + 40 * z, cx_ - bw_ / 2 + 140 * z, cy_ - bh_ / 2 + 130 * z], fill=hexc('#B23A2E'))
            pop(fr, c800, back((t - wt('n07', 14)) / 0.35), W / 2, H * 0.45)
        elif name in ('ran', 'net'):
            post_glow = False
            zz = 1.0 + 0.04 * u
            fr = cam_bg(S['under'], zz if name == 'ran' else 1.08 + 0.03 * u, 0, 0 if name == 'ran' else 60)
            # Rán: large glowing figure
            rs = make_char_cached('hero', 80, V(coat='#2aa3a0', coat_dk='#1f7f7d', hair='#e8f6f4', rim='#bfefff'), 'neutral', blink_at(t, 90), (0, 0.3), 'up')
            fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.42, 420, 520, '#7fe9ff', 120))
            sw = 10 * math.sin(t * 1.3)
            paste_safe(fr, rs, W / 2 - rs.width / 2 + sw, H * 0.92 - rs.height)
            d = ImageDraw.Draw(fr)
            # crown
            cx_ = W / 2 + sw; cy_ = H * 0.92 - rs.height + 325
            for k in range(5):
                x = cx_ - 70 + k * 35; d.polygon([(x - 14, cy_ - 90), (x, cy_ - 140 - (10 if k == 2 else 0)), (x + 14, cy_ - 90)], fill=hexc('#E9BC3F'))
            if name == 'net':
                # net mesh stretched between hands
                nx0, nx1, ny0, ny1 = W * 0.2, W * 0.8, H * 0.08, H * 0.42
                sag = 60 * math.sin(t * 1.5)
                for i in range(13):
                    x = lerp(nx0, nx1, i / 12); d.line([(x, ny0), (lerp(W / 2, x, 0.8), ny1 + sag)], fill=(220, 240, 245, 150), width=3)
                for j in range(7):
                    y = lerp(ny0, ny1, j / 6); d.line([(lerp(nx0, W / 2 - (W / 2 - nx0) * 0.8, j / 6), y + sag * j / 6), (lerp(nx1, W / 2 + (nx1 - W / 2) * 0.8, j / 6), y + sag * j / 6)], fill=(220, 240, 245, 150), width=3)
                for i in range(4):  # sinking sailors drifting into net
                    sv = make_char_cached('viking', 22, rand_viking(random.Random(95 + i), rim='#bfefff'), 'scared', False, (0, -1), 'up')
                    ph = clamp((lt - i * 0.5) / 2.6)
                    x = W * (0.28 + i * 0.15) + 20 * math.sin(t * 2 + i); y = lerp(-120, H * 0.3, eout(ph))
                    paste_safe(fr, sv.rotate(15 * math.sin(t + i), expand=True), x - 40, y - 100)
            pop(fr, ran_pill, back((lt - 0.4) / 0.35) if name == 'ran' else 0, W / 2, 110)
            # bubbles
            for i in range(30):
                rnd = random.Random(i); x = rnd.uniform(0, W); y = (rnd.uniform(0, H) - t * 120 * rnd.uniform(0.5, 1.2)) % H
                r = rnd.uniform(4, 12); d.ellipse([x - r, y - r, x + r, y + r], outline=(220, 245, 255, 170), width=2)
        elif name == 'waves9':
            post_glow = False
            fr = vgrad(W, H, [(0, '#b9d6e6'), (0.45, '#e9eef0'), (0.46, '#4f86a8'), (1, '#1f4f74')])
            fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.3, 700, 300, '#fff6e6', 200))
            d = ImageDraw.Draw(fr)
            for i in range(9):
                x = W * (0.08 + i * 0.105); k = back((lt - i * 0.12) / 0.35)
                if k <= 0.02: continue
                hgt = 220 * k; y = H * 0.66 + 14 * math.sin(t * 3 + i)
                wv = Image.new('RGBA', (240, 320), (0, 0, 0, 0)); wd = ImageDraw.Draw(wv)
                wd.pieslice([20, 320 - hgt * 1.3, 220, 320 + hgt * 0.7], 180, 360, fill=hexc('#7fc4e0'))
                wd.ellipse([110, 320 - hgt * 1.25, 230, 320 - hgt * 0.75], fill=hexc('#e9f7fb'))
                wd.ellipse([95, 320 - hgt * 1.2, 160, 320 - hgt * 0.95], fill=hexc('#7fc4e0'))
                ey = 320 - hgt * 0.62
                for sx in (85, 135):
                    if blink_at(t, 100 + i): wd.line([sx - 13, ey, sx + 13, ey], fill=INK, width=5)
                    else:
                        wd.ellipse([sx - 15, ey - 16, sx + 15, ey + 16], fill=WHITE); wd.ellipse([sx - 7, ey - 6, sx + 7, ey + 9], fill=INK)
                wd.arc([95, ey + 10, 125, ey + 34], 20, 160, fill=INK, width=4)
                paste_safe(fr, wv, x - 120, y - 320)
            waves(fr, t, '#2f6a90', H * 0.78, 18, 0.3, 1.2, line='#e9f7fb', la=200)
            fb = fnt(FRED, 80, axes=[700, 100]); s = '9 DAUGHTERS'
            k = back((lt - 1.0) / 0.35)
            if k > 0.02:
                box = Image.new('RGBA', (700, 140), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
                bb = fb.getbbox(s); bd.text((350 - fb.getlength(s) / 2, 70 - (bb[1] + bb[3]) / 2), s, font=fb, fill=WHITE, stroke_width=8, stroke_fill=hexc('#15131a'))
                pop(fr, box, k, W / 2, H * 0.2)
        if post_glow: fr = Image.alpha_composite(fr, glow_cache('x'))
        fr = Image.alpha_composite(fr, haze); fr = Image.alpha_composite(fr, dark)
        hook.caption2(fr, t)
        rgb = fr.convert('RGB'); ga, gb = grains[fi % 6]
        rgb = ImageChops.subtract(ImageChops.add(rgb, ga), gb)
        if t < 0.3: rgb = Image.blend(Image.new('RGB', (W, H)), rgb, t / 0.3)
        if t > DUR - 0.6: rgb = Image.blend(rgb, Image.new('RGB', (W, H)), clamp((t - (DUR - 0.6)) / 0.6))
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
