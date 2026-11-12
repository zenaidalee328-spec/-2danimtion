import sys, os, json, math, random, subprocess
sys.path.insert(0, '/workspace/work/viking3'); sys.path.insert(0, '/workspace/work/viking_full/hook'); sys.path.insert(0, '/workspace/work/viking_full/day1')
import v3, hook, day1
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, smoke, HAKON_V
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'n02': 0.5, 'h01': 0.35, 'n03': 0.3, 'n04': 0.6, 'n06': 0.5, 'n07': 0.4, 'n08': 0.6, 'n09': 0.15, 'n10': 0.6, 'n12': 0.5, 'n13': 0.6}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text']) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'h': 'H'}.get(lid[0], 'N'))
    t += d_
DUR = t + 2.0
hook.TL = TL; hook.LABELS = {'H': 'H A K O N'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('row', S_('n02') - 0.3), ('hakon', S_('h01') - 0.2), ('push', S_('n03') - 0.1),
         ('cold', S_('n04') - 0.2), ('sink', S_('n05') - 0.1), ('hand', S_('n06') - 0.15),
         ('surface', S_('n07') - 0.1), ('rocks', wt('n07', 4) - 0.1), ('empty', wt('n07', 13) - 0.1),
         ('fist', S_('n08') - 0.2), ('tooth', S_('n09') - 0.1), ('cliff', S_('n10') - 0.25),
         ('rans', S_('n11') - 0.1), ('stare', S_('n12') - 0.25), ('who', wt('n12', 7) - 0.1), ('keep', S_('n13') - 0.25)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V

def stint(im, col, a):
    al = im.getchannel('A'); o = Image.blend(im, Image.new('RGBA', im.size, col + (255,)), a); o.putalpha(al); return o

def dawn_sea():
    img = vgrad(BW, BH, [(0, '#f3c9a8'), (0.33, '#fbe3c6'), (0.42, '#fdf0dc'), (0.43, '#7c9db5'), (1, '#2f5876')])
    img = Image.alpha_composite(img, glow(BW, BH, BW * 0.62, BH * 0.42, 420, 160, '#fff3d6', 230))
    d = ImageDraw.Draw(img)
    # cliffs on left with tiny crowd silhouettes
    d.polygon([(0, BH * 0.18), (BW * 0.18, BH * 0.2), (BW * 0.27, BH * 0.32), (BW * 0.3, BH * 0.62), (0, BH * 0.62)], fill=hexc('#3b3440'))
    d.polygon([(0, BH * 0.18), (BW * 0.18, BH * 0.2), (BW * 0.2, BH * 0.23), (0, BH * 0.22)], fill=hexc('#6f8a52'))
    rnd = random.Random(3)
    for i in range(46):
        x = rnd.uniform(BW * 0.01, BW * 0.18); y = BH * 0.2 - 2
        d.rounded_rectangle([x - 5, y - 26, x + 5, y], radius=4, fill=hexc('#2a2430')); d.ellipse([x - 6, y - 38, x + 6, y - 26], fill=hexc('#2a2430'))
    for (x, y, r) in [(0.42, 0.47, 50), (0.5, 0.49, 30), (0.84, 0.46, 60), (0.9, 0.5, 34)]:
        d.ellipse([BW * x - r * 2, BH * y - r, BW * x + r * 2, BH * y + r * 0.6], fill=hexc('#24252e'))
    return img

def rocks_shore():
    img = vgrad(BW, BH, [(0, '#e6d3bd'), (0.38, '#f6e6d0'), (0.4, '#6f93ad'), (1, '#41698a')])
    return img

def deep(t, depth):
    top = (int(lerp(70, 10, depth)), int(lerp(150, 30, depth)), int(lerp(190, 60, depth)))
    img = vgrad(W, H, [(0, '#%02x%02x%02x' % top), (1, '#06101c')])
    return img

def hand_img(open_=0.0, s=1.0):
    im = Image.new('RGBA', (int(360 * s), int(700 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([100 * s, 0, 260 * s, 470 * s], radius=int(40 * s), fill=hexc('#5c4a3a'))  # sleeve
    d.rectangle([100 * s, 380 * s, 260 * s, 430 * s], fill=hexc('#3e3027'))
    d.rounded_rectangle([90 * s, 440 * s, 270 * s, 620 * s], radius=int(60 * s), fill=hexc('#d9a77e'))
    for k in range(4):
        x = 105 * s + k * 42 * s
        L = lerp(40, 90, open_) * s
        d.rounded_rectangle([x, 590 * s, x + 36 * s, 590 * s + L], radius=int(18 * s), fill=hexc('#cf9a70'))
    d.rounded_rectangle([60 * s, 470 * s, 110 * s, 560 * s], radius=int(24 * s), fill=hexc('#cf9a70'))
    return im

def tooth_img(s=1.0, glowk=0.0):
    im = Image.new('RGBA', (int(400 * s), int(620 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.arc([40 * s, -260 * s, 360 * s, 300 * s], 20, 160, fill=hexc('#6b4a30'), width=int(10 * s))  # cord
    d.ellipse([180 * s, 270 * s, 220 * s, 310 * s], fill=hexc('#6b4a30'))
    d.polygon([(150 * s, 300 * s), (250 * s, 300 * s), (235 * s, 400 * s), (205 * s, 540 * s), (185 * s, 560 * s), (172 * s, 440 * s)], fill=hexc('#f3ead6'))
    d.polygon([(205 * s, 300 * s), (250 * s, 300 * s), (235 * s, 400 * s), (205 * s, 540 * s)], fill=hexc('#ddd0b4'))
    d.line([(165 * s, 330 * s), (190 * s, 470 * s)], fill=hexc('#ffffff'), width=int(6 * s))
    return im

def splash(fr, x, y, k, sc=1.0):
    if not (0 < k < 1): return
    d = ImageDraw.Draw(fr); rnd = random.Random(int(x))
    for i in range(26):
        a = math.radians(rnd.uniform(200, 340)); v = rnd.uniform(120, 360) * sc
        px = x + math.cos(a) * v * k; py = y + math.sin(a) * v * k + 500 * k * k * sc
        r = 14 * sc * (1 - k) + 4
        d.ellipse([px - r, py - r, px + r, py + r], fill=(235, 248, 255, int(230 * (1 - k))))

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['dawn'] = dawn_sea(); S['village'], _, houses = village_set()
    dcard = title_card('DAY 2', 'THE TEST')
    tooth_card = big_card('', 'TOOTH', "A WOLF'S TOOTH ON A CORD", 'axe')
    dau = name_pill('DAUGHTER OF RÁN', 'CONFIRMED'); qm = bubble('WHO?', '#FFC93C', '#1b1a2a', 60)
    keep = big_card('', 'CLUE #1', 'THE WOLF TOOTH', 'axe')
    cheer = crowd(41, 3, 10, 3.2, 1.2, 5.0, expr_choices=('happy', 'happy', 'neutral'))
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        if name == 'daycard':
            fr = fastblur(cam_bg(S['dawn'], 1.04 + 0.02 * u), 3.0)
            waves(fr, t, '#5a7f9c', H * 0.8, 14, 0.5, 1.0, line='#fdf0dc')
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name in ('row', 'push'):
            zz = (1.0 + 0.04 * u) if name == 'row' else 1.12
            fr = cam_bg(S['dawn'], zz, lerp(-60, 60, u) if name == 'row' else 40)
            waves(fr, t, '#4f7896', H * 0.62, 12, 0.3, 0.8, line='#fdf0dc', la=120)
            b = boat_img(t, 1.0)
            # crew: rowers + Hakon + hero
            for i, (kind, bx, v, ex, sd) in enumerate([('viking', 110, rand_viking(random.Random(80)), 'neutral', 80), ('viking', 250, HAKON_V, 'smirk', 75), ('viking', 470, rand_viking(random.Random(81)), 'neutral', 81)]):
                sp = make_char_cached(kind, 20 if v is not HAKON_V else 22, v, ex, blink_at(t, sd), (1, 0), 'down')
                b.alpha_composite(sp, (int(bx - sp.width / 2), int(362 - sp.height)))
            if name == 'row':
                hs = make_char_cached('hero', 18, HV, 'worried', blink_at(t, 82), (-1, 0), 'down')
                b.alpha_composite(hs, (int(370 - hs.width / 2), int(362 - hs.height)))
            bd = ImageDraw.Draw(b)
            for ox in (80, 440):
                a = 0.5 * math.sin(t * 2.4)
                bd.line([(ox, 380), (ox - 90 + 40 * a, 470)], fill=hexc('#4a3322'), width=8)
            sc = 1.0 if name == 'row' else 1.5
            b = b.rotate(3 * math.sin(t * 1.4), resample=Image.BICUBIC, expand=True)
            b = b.resize((int(b.width * sc), int(b.height * sc)), Image.BILINEAR)
            bx0 = lerp(W * 0.42, W * 0.6, u) if name == 'row' else W * 0.5
            paste_safe(fr, b, bx0 - b.width / 2, H * 0.64 - b.height * 0.68 + 8 * math.sin(t * 1.4))
            if name == 'push':
                k = clamp((t - wt('n03', 3)) / 0.7)
                hs = make_char_cached('hero', 27, HV | V(sweat=True), 'scared', False, (0, 1), 'up')
                hs = hs.rotate(lerp(0, 70, k), expand=True)
                hx = bx0 + 0.1 * b.width + 260 * k; hy = H * 0.64 - b.height * 0.68 + 362 * sc * 0.9 - hs.height + lerp(0, 380, k * k)
                if k < 0.9: paste_safe(fr, hs, hx - hs.width / 2, hy)
                splash(fr, bx0 + 0.1 * b.width + 260, H * 0.7, (t - wt('n03', 3) - 0.6) / 0.9, 1.4)
                if 0.55 < k < 0.8: fr = shake(fr, 10, t)
            waves(fr, t, '#3c6582', H * 0.72, 18, 1.5, 1.2, line='#fdf0dc', la=140)
            waves(fr, t, '#2f5876', H * 0.86, 20, 3.0, 1.6, line='#fdf0dc', la=110)
        elif name == 'hakon':
            fr = fastblur(cam_bg(S['dawn'], 1.2, 120, 40), 4.0)
            cam = dict(cx=0, cz=1.0, f=1500, hor=H * 0.5, h=0.9, focus=1.9, ap=1.2)
            render_world2(fr, [Actor('viking', -0.25, 2.9, HAKON_V, expr='smirk', look=(1, 0.1), seed=75, size=1.14),
                               Actor('hero', 0.75, 3.2, HV | V(sweat=True), expr='scared', look=(-1, 0), seed=82)], cam, t)
            waves(fr, t, '#3c6582', H * 0.86, 16, 1.5, 1.2, line='#fdf0dc', la=140)
        elif name in ('cold', 'sink'):
            pg = False
            depth = 0.2 + 0.2 * u if name == 'cold' else 0.4 + 0.5 * u
            fr = deep(t, depth)
            # surface light at top shrinking
            rad = lerp(700, 420, u) if name == 'cold' else lerp(420, 70, eio(u))
            fr = Image.alpha_composite(fr, glow(W, H, W / 2, -40, rad * 1.4, rad * 0.8, '#cdefff', int(lerp(200, 140, depth))))
            d = ImageDraw.Draw(fr)
            hs = make_char_cached('hero', 40 if name == 'cold' else int(lerp(40, 24, u)), HV, 'scared', blink_at(t, 83) if name == 'sink' else False, (0, -1), 'up')
            hs = stint(hs, (40, 90, 140), 0.35)
            hy = H * 0.5 - hs.height / 2 + (lerp(-40, 40, u) if name == 'cold' else lerp(40, 260, u))
            paste_safe(fr, hs.rotate(6 * math.sin(t * 1.5), expand=True), W / 2 - hs.width / 2, hy)
            for i in range(14):
                rnd = random.Random(i); x = W / 2 + rnd.uniform(-40, 40) + 10 * math.sin(t * 3 + i); y = (hy + 150 - ((t * 260 + i * 90) % 700))
                r = rnd.uniform(5, 14); d.ellipse([x - r, y - r, x + r, y + r], outline=(220, 245, 255, 200), width=3)
            if name == 'cold':
                # frost creeping in from edges + chest lock rings
                fl = Image.new('L', (W, H), 0); fd = ImageDraw.Draw(fl)
                k = ease(u * 1.5)
                fd.rectangle([0, 0, W, H], fill=int(140 * k)); fd.ellipse([-W * 0.05 + W * 0.06 * k, -H * 0.05 + H * 0.06 * k, W * 1.05 - W * 0.06 * k, H * 1.05 - H * 0.06 * k], fill=0)
                fl = fl.filter(ImageFilter.GaussianBlur(60)); ice = Image.new('RGBA', (W, H), hexc('#e6f6ff')); ice.putalpha(fl)
                fr = Image.alpha_composite(fr, ice)
                if t > wt('n04', 7): pop(fr, label_box("CAN'T BREATHE", '#cdefff', '#6fc8ff'), back((t - wt('n04', 7)) / 0.3), W / 2, 110)
            else:
                v = Image.new('L', (W, H), 0); vd = ImageDraw.Draw(v)
                k = ease(u); vd.rectangle([0, 0, W, H], fill=255); vd.ellipse([W * 0.3 * k, H * 0.25 * k, W - W * 0.3 * k, H - H * 0.25 * k], fill=int(255 * (1 - k)))
                v = v.filter(ImageFilter.GaussianBlur(90)); blk = Image.new('RGBA', (W, H), (2, 6, 12, 255)); blk.putalpha(v.point(lambda p: int(p * 0.85)))
                fr = Image.alpha_composite(fr, blk)
        elif name == 'hand':
            pg = False
            k = clamp(lt / 0.6); pull = clamp((u - 0.4) / 0.55)
            fr = deep(t, lerp(0.9, 0.4, pull))
            fr = Image.alpha_composite(fr, glow(W, H, W / 2, -40, lerp(100, 700, pull), lerp(60, 400, pull), '#cdefff', 200))
            hs = stint(make_char_cached('hero', 44, HV, 'scared', False, (0, -1), 'up'), (40, 90, 140), 0.35)
            hy = lerp(H * 0.42, -hs.height * 0.6, eio(pull))
            hi = hand_img(lerp(1, 0.2, clamp((lt - 0.55) / 0.2)), 0.8)
            hi = stint(hi, (30, 60, 100), 0.4)
            paste_safe(fr, hs, W / 2 - hs.width / 2, hy)
            gy = hy + hs.height * 0.5 - hi.height * 0.88
            paste_safe(fr, hi, W / 2 + 115 - hi.width / 2, lerp(-hi.height, gy, eout(k)) if pull == 0 else gy)
            if 0.5 < lt < 0.75: fr = shake(fr, 8, t)
            if u > 0.9: fr = Image.blend(fr, Image.new('RGBA', (W, H), (240, 250, 255, 255)), (u - 0.9) / 0.1 * 0.8)
        elif name == 'surface':
            fr = cam_bg(S['dawn'], 1.3, 300, 80)
            waves(fr, t, '#3c6582', H * 0.6, 22, 1.5, 1.4, line='#fdf0dc', la=160)
            k = eout(lt / 0.5)
            hs = make_char_cached('hero', 36, HV | V(sweat=True), 'scared', False, (0, 1), 'up')
            paste_safe(fr, hs, W / 2 - hs.width / 2, lerp(H * 0.9, H * 0.62, k) - hs.height * 0.45)
            splash(fr, W / 2, H * 0.62, lt / 0.9, 1.6)
            waves(fr, t, '#2f5876', H * 0.7, 26, 3.0, 1.8, line='#fdf0dc', la=160)
            if lt < 0.12: fr = Image.blend(fr, Image.new('RGBA', (W, H), (255, 255, 255, 255)), 0.7 * (1 - lt / 0.12))
        elif name in ('rocks', 'empty'):
            fr = fastblur(cam_bg(S['dawn'], 1.1, 200 if name == 'rocks' else 260, 60), 1.5)
            waves(fr, t, '#3c6582', H * 0.62, 16, 1.5, 1.2, line='#fdf0dc', la=140)
            d = ImageDraw.Draw(fr)
            if name == 'rocks':
                tk = eout(lt / 0.8)
                hs = make_char_cached('hero', 32, HV | V(sweat=True), 'scared', blink_at(t, 84), (lambda: (1, 0) if lt > 1.6 else (0, 0))(), 'down')
                hs = hs.rotate(lerp(80, 0, ease((lt - 0.9) / 0.6)), expand=True)
                paste_safe(fr, hs, lerp(W * 0.7, W * 0.4, tk) - hs.width / 2, H * 0.86 - hs.height)
                splash(fr, W * 0.42, H * 0.82, (lt - 0.6) / 0.8, 1.2)
                if 0.7 < lt < 0.9: fr = shake(fr, 10, t)
            else:
                pop(fr, bubble('?', '#ffffff', '#1b1a2a', 80), back((lt - 0.5) / 0.3), W * 0.55, H * 0.32)
            d = ImageDraw.Draw(fr)
            for (x, y, r) in [(0.1, 0.92, 260), (0.4, 0.97, 300), (0.75, 0.95, 240), (1.0, 0.9, 260)]:
                d.ellipse([W * x - r * 1.3, H * y - r * 0.6, W * x + r * 1.3, H * y + r * 0.6], fill=hexc('#1c1a1e'))
                d.ellipse([W * x - r, H * y - r * 0.55, W * x + r * 0.2, H * y - r * 0.35], fill=hexc('#3a363c'))
            waves(fr, t, '#2f5876', H * 1.02, 12, 3.0, 1.6, line='#fdf0dc', la=120)
        elif name in ('fist', 'tooth'):
            pg = False
            fr = Image.new('RGBA', (W, H), hexc('#1a181c'))
            fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.5, 700, 420, '#4a4250', 220))
            d = ImageDraw.Draw(fr)
            for i in range(30):
                rnd = random.Random(i); x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(60, 180)
                d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=hexc('#2a272c'))
            if name == 'fist':
                op = ease((t - wt('n08', 5)) / 0.8)
                hi = hand_img(op, 1.3).rotate(180, expand=True)
                paste_safe(fr, hi, W / 2 - hi.width / 2, H * 0.62 - hi.height * 0.2)
                if op > 0.4:
                    fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.28, 160, 120, '#fff1c9', int(150 * op)))
            else:
                fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.55, 380, 380, '#fff1c9', int(130 + 40 * math.sin(t * 4))))
                ti = tooth_img(1.1).rotate(8 * math.sin(t * 2.2), resample=Image.BICUBIC, expand=True)
                paste_safe(fr, ti, W / 2 - ti.width / 2, H * 0.5 - ti.height * 0.55)
                glint(fr, W * 0.48, H * 0.55, 40, ((lt - 0.4) % 1.4) / 0.5)
                pop(fr, tooth_card, back((lt - 0.5) / 0.35), W / 2, H * 0.15)
        elif name in ('cliff', 'stare', 'rans'):
            fr = fastblur(cam_bg(S['dawn'], 1.1 + 0.03 * u, 0, -160), 2.0)
            waves(fr, t, '#4f7896', H * 0.75, 12, 0.3, 0.8, line='#fdf0dc', la=120)
            if name == 'rans':
                fr = fastblur(cam_bg(S['dawn'], 1.25, 260, 80), 1.5)
                fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.5, 420, 520, '#bfefff', 150))
                hs = make_char_cached('hero', 40, HV, (lambda: 'happy' if lt > 1.0 else 'worried')(), blink_at(t, 85), (-0.5, -0.4), 'down')
                paste_safe(fr, hs, W / 2 - hs.width / 2, H * 1.0 - hs.height)
                d = ImageDraw.Draw(fr)
                d.ellipse([W * 0.2, H * 0.92, W * 0.8, H * 1.15], fill=hexc('#1c1a1e'))
                for i in range(40):  # tiny cheering silhouettes on cliff
                    x = W * 0.02 + i * 14; y = H * 0.36 - 6 * abs(math.sin(t * 7 + i))
                    d.rectangle([x - 4, y - 18, x + 4, y], fill=hexc('#2a2430')); d.line([x, y - 16, x - 6 + 12 * (i % 2), y - 30], fill=hexc('#2a2430'), width=3)
                pop(fr, dau, back((t - wt('n11', 9)) / 0.35), W / 2, 110)
            else:
                d = ImageDraw.Draw(fr)
                cam = dict(cx=0, cz=0.2 if name == 'cliff' else 0.8, f=1500, hor=H * 0.5, h=1.1, focus=3.4 if name == 'cliff' else 2.3, ap=0.8 if name == 'cliff' else 1.4)
                d.polygon([(0, H * 0.52), (W, H * 0.5), (W, H), (0, H)], fill=hexc('#6f8a52'))
                acts = []
                for a in cheer:
                    if name == 'stare' and abs(a.x) < 0.9 and a.z < 3.4: continue
                    acts.append(Actor('viking', a.x, a.z, a.v, expr='happy', look=(0, -0.3), seed=a.seed, pose='up', bob=1))
                if name == 'stare':
                    acts.append(Actor('viking', 0.2, 2.6, HAKON_V, expr='angry', look=(lambda tt: (0.6, 0.6)), seed=75, size=1.14))
                render_world2(fr, acts, cam, t)
                if name == 'cliff':
                    c = counter_img(100) if 'counter_img' in globals() else None
                    pop(fr, label_box('100 VIKINGS CHEERING'), back((lt - 0.3) / 0.35), W / 2, 110)
        elif name == 'who':
            fr = cam_bg(S['dawn'], 1.15 + 0.05 * u, 300, 160)
            waves(fr, t, '#3c6582', H * 0.5, 16, 1.5, 1.0, line='#fdf0dc', la=140)
            waves(fr, t, '#2f5876', H * 0.75, 20, 3.0, 1.3, line='#fdf0dc', la=140)
            d = ImageDraw.Draw(fr)
            # a faint dark shape under water (the rescuer) slipping away
            x = lerp(W * 0.55, W * 0.9, u)
            sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh); sd.ellipse([x - 90, H * 0.66, x + 90, H * 0.72], fill=(10, 20, 30, 110))
            fr.alpha_composite(fastblur(sh, 10))
            pop(fr, qm, back((lt - 0.3) / 0.3), W * 0.5, H * 0.3)
            fr = tint(fr, (30, 40, 70), 0.15)
        elif name == 'keep':
            fr = fastblur(cam_bg(S['dawn'], 1.2, 220, 60), 4.0)
            cam = dict(cx=0, cz=1.0, f=1500, hor=H * 0.5, h=0.9, focus=2.0, ap=1.2)
            render_world2(fr, [Actor('hero', -0.4, 3.0, HV, expr='worried', look=(1, -0.2), seed=86)], cam, t)
            ti = tooth_img(0.55).rotate(10 * math.sin(t * 2), resample=Image.BICUBIC, expand=True)
            fr = Image.alpha_composite(fr, glow(W, H, W * 0.62, H * 0.45, 150, 150, '#fff1c9', 150))
            paste_safe(fr, ti, W * 0.62 - ti.width / 2, H * 0.45 - ti.height / 2)
            pop(fr, keep, back((t - wt('n13', 3)) / 0.35), W * 0.5, H * 0.15)
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
