import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day2 import stint
from day4 import hall_set, stamp, bigtxt
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'n02': 0.35, 'h01': 0.3, 'n03': 0.35, 't01': 0.3, 'n04': 0.5, 'n05': 0.7, 'n06': 0.3, 'n07': 0.5, 'n08': 0.9, 'n09': 0.4, 'n10': 0.6, 'n11': 0.6}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text']) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'h': 'H', 't': 'T'}.get(lid[0], 'N'))
    t += d_
DUR = t + 2.0
hook.TL = TL; hook.LABELS = {'H': 'H A K O N', 'T': 'T O R S T E I N'}
def S_(l): return TL[l]['st']
def E_(l): return TL[l]['en']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('feast', wt('n01', 2) - 0.1), ('plate', S_('n02') - 0.2), ('hakon', S_('h01') - 0.2),
         ('grab', S_('n03') - 0.2), ('laugh', S_('t01') - 0.2), ('shake', S_('n04') - 0.3), ('fall', wt('n04', 5) - 0.1),
         ('lifeguard', S_('n05') - 0.4), ('cpr', S_('n06') - 0.2), ('silent', S_('n07') - 0.2), ('y1960', S_('n08') - 0.4),
         ('magic', S_('n09') - 0.25), ('cough', S_('n10') - 0.3), ('meant', S_('n11') - 0.4)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V
TOR_V = rand_viking(random.Random(311)) | V(coat='#5a6b3a', beard='#3a2a1c', beard_dk='#2a1e14', helmet=False, hair='#3a2a1c', rim='#F6B07A')

def table_layer(cx, cy, w, s=1.0, plate_food=True):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([cx - w / 2, cy, cx + w / 2, cy + 50 * s], fill=hexc('#6b4a30'))
    d.rectangle([cx - w / 2, cy + 50 * s, cx + w / 2, cy + 70 * s], fill=hexc('#4a3322'))
    for k in range(int(w / (220 * s))):
        x = cx - w / 2 + 110 * s + k * 220 * s; rnd = random.Random(k)
        typ = k % 4
        if typ == 0:  # fish
            d.ellipse([x - 60 * s, cy - 30 * s, x + 40 * s, cy + 5 * s], fill=hexc('#c98a4a')); d.polygon([(x + 30 * s, cy - 12 * s), (x + 70 * s, cy - 35 * s), (x + 70 * s, cy + 10 * s)], fill=hexc('#c98a4a'))
        elif typ == 1:  # mutton leg
            d.ellipse([x - 50 * s, cy - 50 * s, x + 30 * s, cy + 5 * s], fill=hexc('#8a3e22')); d.line([x + 20 * s, cy - 25 * s, x + 70 * s, cy - 50 * s], fill=hexc('#f3ead6'), width=int(14 * s))
        elif typ == 2:  # mead horn
            d.polygon([(x - 40 * s, cy - 70 * s), (x - 10 * s, cy - 70 * s), (x + 20 * s, cy), (x - 5 * s, cy)], fill=hexc('#e7d7b0')); d.rectangle([x - 40 * s, cy - 76 * s, x - 10 * s, cy - 66 * s], fill=hexc('#c9a24a'))
        else:  # bread
            d.ellipse([x - 45 * s, cy - 35 * s, x + 45 * s, cy + 5 * s], fill=hexc('#d9a35a'))
    return im

def food_icon(kind, s=1.0):
    im = Image.new('RGBA', (int(300 * s), int(300 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([10 * s, 10 * s, 290 * s, 290 * s], fill=hexc('#fff6dc'), outline=hexc('#5a4030'), width=int(6 * s))
    c = 150 * s
    if kind == 'fish':
        d.ellipse([c - 90 * s, c - 40 * s, c + 50 * s, c + 40 * s], fill=hexc('#c98a4a')); d.polygon([(c + 40 * s, c), (c + 100 * s, c - 45 * s), (c + 100 * s, c + 45 * s)], fill=hexc('#c98a4a')); d.ellipse([c - 70 * s, c - 12 * s, c - 50 * s, c + 8 * s], fill=hexc('#1b1a2a'))
    elif kind == 'mutton':
        d.ellipse([c - 90 * s, c - 60 * s, c + 30 * s, c + 50 * s], fill=hexc('#8a3e22')); d.line([c + 10 * s, c, c + 90 * s, c - 60 * s], fill=hexc('#f3ead6'), width=int(22 * s)); d.ellipse([c + 70 * s, c - 85 * s, c + 110 * s, c - 45 * s], fill=hexc('#f3ead6'))
    elif kind == 'mead':
        d.polygon([(c - 70 * s, c - 90 * s), (c - 20 * s, c - 90 * s), (c + 60 * s, c + 80 * s), (c + 20 * s, c + 80 * s)], fill=hexc('#e7d7b0')); d.rectangle([c - 72 * s, c - 100 * s, c - 18 * s, c - 82 * s], fill=hexc('#c9a24a'))
    else:  # drum
        d.ellipse([c - 90 * s, c - 70 * s, c + 90 * s, c - 10 * s], fill=hexc('#efe4cc')); d.rectangle([c - 90 * s, c - 40 * s, c + 90 * s, c + 60 * s], fill=hexc('#8a3e22')); d.ellipse([c - 90 * s, c + 30 * s, c + 90 * s, c + 90 * s], fill=hexc('#8a3e22'))
        d.ellipse([c - 90 * s, c - 70 * s, c + 90 * s, c - 10 * s], fill=hexc('#efe4cc'))
    return im

def plate_img(s=1.0, bite=False):
    im = Image.new('RGBA', (int(320 * s), int(140 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([10 * s, 50 * s, 310 * s, 130 * s], fill=hexc('#7d5838')); d.ellipse([30 * s, 58 * s, 290 * s, 118 * s], fill=hexc('#9a6e46'))
    d.ellipse([70 * s, 40 * s, 170 * s, 95 * s], fill=hexc('#c98a4a'))
    if not bite: d.ellipse([160 * s, 30 * s, 250 * s, 90 * s], fill=hexc('#8a3e22'))
    return im

def heart(d, x, y, r, col='#E04848'):
    d.ellipse([x - r, y - r * 0.6, x, y + r * 0.3], fill=hexc(col)); d.ellipse([x, y - r * 0.6, x + r, y + r * 0.3], fill=hexc(col))
    d.polygon([(x - r * 0.97, y), (x + r * 0.97, y), (x, y + r)], fill=hexc(col))

def lying(v, R, expr, kind='viking', ang=90):
    sp = make_char_cached(kind, R, v, expr, False, (0, -1), 'down')
    return sp.rotate(ang, resample=Image.BICUBIC, expand=True)

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set(); S['hall'] = hall_set()
    dcard = title_card('DAY 6', 'THE FEAST')
    hp = name_pill('HAKON', "THE JARL'S SON"); tp = name_pill('TORSTEIN', 'BIG WARRIOR')
    s_meant = stamp('MEANT FOR YOU', '#d24a3a', 100); c30 = label_box('30 SECONDS LATER', '#ffffff', '#d24a3a')
    icons = {k: food_icon(k, 0.9) for k in ('fish', 'mutton', 'mead', 'drum')}
    hallcrowd = crowd(61, 2, 8, 5.0, 1.2, 5.0, exclude=lambda x, z: abs(x) < 1.0, expr_choices=('happy', 'happy', 'neutral'))
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        fl = 1 + 0.08 * math.sin(t * 11) + 0.05 * math.sin(t * 7)
        def hallbg(z, blur, warm=120):
            f_ = fastblur(cam_bg(S['hall'], z, 0, 40), blur)
            return Image.alpha_composite(f_, glow(W, H, W / 2, H * 0.8, 400 * fl, 200 * fl, '#ffb45a', warm))
        if name == 'daycard':
            fr = fastblur(cam_bg(S['village'], 1.04 + 0.02 * u, 0, -20), 3.0)
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name == 'feast':
            fr = hallbg(1.0 + 0.04 * u, 1.0)
            cam = dict(cx=0, cz=lerp(-0.6, 0.0, eio(u)), f=1500, hor=H * 0.5, h=1.3, focus=4.5, ap=0.6)
            acts = [Actor(a.kind, a.x, a.z, a.v, expr=a.expr, look=a.look, seed=a.seed, size=a.size, bob=1.0) for a in hallcrowd] + [Actor('hero', 0.0, 3.4, HV, expr='happy', look=(0, 0), seed=90)]
            render_world2(fr, acts, cam, t)
            fr.alpha_composite(table_layer(W / 2, H * 0.86, W * 1.1, 1.3))
            for i, (wi, kname) in enumerate([(10, 'fish'), (12, 'mutton'), (13, 'mead'), (15, 'drum')]):
                k = back((t - wt('n01', wi) + 0.05) / 0.3)
                bounce = 8 * math.sin(t * 14) if kname == 'drum' and k > 0.9 else 0
                if k > 0.02: pop(fr, icons[kname], k, W * (0.2 + i * 0.2), H * 0.28 + bounce)
        elif name in ('plate', 'hakon', 'grab', 'laugh'):
            fr = hallbg({'plate': 1.05, 'hakon': 1.15, 'grab': 1.08, 'laugh': 1.18}[name], 2.4)
            if name == 'plate':
                cam = dict(cx=0, cz=0.6, f=1500, hor=H * 0.5, h=1.1, focus=3.0, ap=0.8)
                hx = lerp(1.6, 0.55, ease(u * 1.3))
                render_world2(fr, [Actor('hero', -0.5, 3.0, HV, expr='happy', look=(1, 0), seed=90),
                                   Actor('viking', hx, 3.0, HAKON_V, expr='smirk', look=(-1, 0), seed=75, size=1.08, bob=1 if u < 0.75 else 0)], cam, t)
                pl = plate_img(1.2); paste_safe(fr, pl, W / 2 + (hx - 0.55) * 900 + 60 - pl.width / 2, H * 0.62)
                pop(fr, hp, back((lt - 0.3) / 0.35), W / 2, 110)
            elif name == 'hakon':
                cam = dict(cx=0.2, cz=1.1, f=1500, hor=H * 0.48, h=0.95, focus=2.0, ap=1.2)
                render_world2(fr, [Actor('viking', 0.35, 3.0, HAKON_V, expr='smirk', look=(-1, 0), seed=75, size=1.08)], cam, t)
                pl = plate_img(1.6); paste_safe(fr, pl, W * 0.38 - pl.width / 2, H * 0.72)
            elif name == 'grab':
                cam = dict(cx=0, cz=0.7, f=1500, hor=H * 0.5, h=1.1, focus=3.0, ap=0.8)
                gk = ease((t - wt('n03', 13)) / 0.4)
                render_world2(fr, [Actor('hero', -0.4, 3.0, HV, expr='worried' if gk > 0.5 else 'happy', look=(1, 0), seed=90),
                                   Actor('viking', lerp(1.3, 0.55, ease(u * 1.6)), 3.0, TOR_V, expr='happy', look=(-1, 0), seed=311, size=1.32)], cam, t)
                pl = plate_img(1.2, bite=gk > 0.5); paste_safe(fr, pl, W * 0.5 - pl.width / 2, H * 0.68)
                if gk > 0.5:
                    d = ImageDraw.Draw(fr); mx = lerp(W * 0.55, W * 0.68, gk); d.ellipse([mx - 50, H * 0.5, mx + 40, H * 0.56], fill=hexc('#8a3e22'))
                pop(fr, tp, back((lt - 0.4) / 0.35), W / 2, 110)
            else:
                cam = dict(cx=-0.1, cz=1.1, f=1500, hor=H * 0.5, h=1.0, focus=2.0, ap=1.2)
                render_world2(fr, [Actor('viking', -0.2, 3.0, TOR_V, expr='happy', look=(1, 0), seed=311, size=1.32, bob=0.6)], cam, t)
                fr = shake(fr, 3, t)
                pop(fr, bubble('HA HA!', '#ffffff', '#1b1a2a', 56), back((lt - 0.2) / 0.3), W * 0.72, H * 0.22)
        elif name in ('shake', 'fall'):
            fr = hallbg(1.1, 2.4, 90)
            cam = dict(cx=0, cz=0.8, f=1500, hor=H * 0.5, h=1.1, focus=3.0, ap=0.8)
            if name == 'shake':
                jitter = 0.04 * math.sin(t * 60) * clamp((t - wt('n04', 4)) / 0.3)
                render_world2(fr, [Actor('hero', -0.6, 3.2, HV, expr='worried', look=(1, 0), seed=90),
                                   Actor('viking', 0.3 + jitter, 3.0, TOR_V | V(sweat=True), expr='scared', look=(0, 0), seed=311, size=1.32)], cam, t)
                if t > wt('n04', 4): fr = shake(fr, 4, t)
                pop(fr, c30, back(lt / 0.3) * (1 - ease((lt - 1.6) / 0.3)), W / 2, 110)
            else:
                fk = ease((lt) / 0.6)
                render_world2(fr, [Actor('hero', -0.6, 3.2, HV | V(sweat=True), expr='scared', look=(1, 0.3), seed=90)], cam, t)
                ly = lying(TOR_V, 115, 'neutral', ang=lerp(0, 88, fk))
                paste_safe(fr, ly, W * 0.62 - ly.width / 2, H * lerp(0.92, 1.18, fk) - ly.height)
                if 0.0 < lt - 0.6 < 0.3: fr = shake(fr, 12, t)
                for i, (bx, by) in enumerate([(0.2, 0.25), (0.85, 0.3)]):
                    pop(fr, bubble('!', '#ffffff', '#d24a3a', 60), back((lt - 0.7 - i * 0.15) / 0.25), W * bx, H * by)
                if t > wt('n04', 13): fr = tint(fr, (10, 10, 30), 0.3 * ease((t - wt('n04', 13)) / 0.6))
        elif name == 'lifeguard':
            pg = False
            fr = vgrad(W, H, [(0, '#8fd0f0'), (0.55, '#d8f0fa'), (0.56, '#2fa8d8'), (0.75, '#4fc0e0'), (0.76, '#f2dca0'), (1, '#e8cc88')])
            fr = Image.alpha_composite(fr, glow(W, H, W * 0.8, H * 0.15, 160, 160, '#fff6c0', 230))
            d = ImageDraw.Draw(fr)
            d.rectangle([W * 0.3, H * 0.45, W * 0.32, H * 0.9], fill=hexc('#ffffff')); d.rectangle([W * 0.42, H * 0.45, W * 0.44, H * 0.9], fill=hexc('#ffffff'))
            d.rectangle([W * 0.28, H * 0.45, W * 0.46, H * 0.49], fill=hexc('#ffffff'))
            d.ellipse([W * 0.62, H * 0.6, W * 0.72, H * 0.72], outline=hexc('#E04848'), width=22)
            hs = make_char_cached('hero', 30, HV | V(coat='#E04848', coat_dk='#b83a3a'), 'happy', blink_at(t, 97), (1, 0), 'down')
            paste_safe(fr, hs, W * 0.37 - hs.width / 2, H * 0.46 - hs.height + 10)
            fr = Image.blend(fr.convert('RGB'), stint(fr, (200, 170, 120), 0.35).convert('RGB'), 0.5).convert('RGBA')
            pop(fr, label_box('BACK HOME: LIFEGUARD', '#ffffff', '#E04848'), back((lt - 0.2) / 0.35), W / 2, 110)
        elif name in ('cpr', 'magic'):
            fr = hallbg(1.15, 3.0, 110)
            d = ImageDraw.Draw(fr); d.rectangle([0, H * 0.82, W, H], fill=hexc('#3a2a1c'))
            ly = lying(TOR_V, 95, 'neutral', ang=88); paste_safe(fr, ly, W * 0.6 - ly.width / 2, H * 1.16 - ly.height)
            pumping = name == 'magic' or t > wt('n06', 6)
            pb = abs(math.sin(t * math.pi * 1.8)) if pumping else 0
            hs = make_char_cached('hero', 95, HV | V(sweat=True), 'angry' if pumping else 'worried', blink_at(t, 90), (1, 0.6), 'down')
            paste_safe(fr, hs, W * 0.36 - hs.width / 2, H * 1.22 - hs.height + 40 * pb)
            if name == 'cpr':
                if t > wt('n06', 10) - 0.2:
                    n = int(clamp((t - (wt('n06', 6))) / (wt('n06', 12) - wt('n06', 6))) * 30) if t < wt('n06', 13) else 30
                    bt = bigtxt(f'{max(1, n)} / 30', 110, '#ffffff'); paste_safe(fr, bt, W * 0.8 - bt.width / 2, H * 0.12)
                if t > wt('n06', 13) - 0.1:
                    pop(fr, label_box('+ 2 BREATHS', '#ffffff', '#2f6e9e'), back((t - wt('n06', 13) + 0.1) / 0.3), W * 0.8, H * 0.36)
                hk = 1 + 0.15 * pb; heart(ImageDraw.Draw(fr), W * 0.12, H * 0.2, 60 * hk, '#E04848' if pumping else '#555555')
            else:
                # life sparks rising + crowd eyes
                rnd = random.Random(3); lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                for i in range(26):
                    x = W * 0.55 + rnd.uniform(-260, 260); ph = (t * rnd.uniform(0.3, 0.6) + rnd.random()) % 1
                    y = H * 0.85 - ph * H * 0.6; r = 7 * (1 - ph) + 2
                    ld.ellipse([x - r, y - r, x + r, y + r], fill=(255, 220, 140, int(220 * (1 - ph))))
                fr.alpha_composite(lay)
                fr = Image.alpha_composite(fr, glow(W, H, W * 0.55, H * 0.75, 400, 200, '#ffe4ad', int(90 + 40 * pb)))
                pop(fr, bubble('MAGIC?!', '#ffffff', '#1b1a2a', 56), back((lt - 0.8) / 0.3), W * 0.8, H * 0.2)
        elif name == 'silent':
            fr = hallbg(1.0 + 0.05 * u, 1.0, 80)
            fr = tint(fr, (10, 10, 20), 0.3)
            cam = dict(cx=0, cz=lerp(0.0, 0.4, eio(u)), f=1500, hor=H * 0.5, h=1.3, focus=4.5, ap=0.6)
            acts = [Actor(a.kind, a.x, a.z, a.v, expr='scared', look=(0, 0.4), seed=a.seed, size=a.size) for a in hallcrowd]
            render_world2(fr, acts, cam, t)
            ly = lying(TOR_V, 40, 'neutral', ang=88); paste_safe(fr, ly, W * 0.52 - ly.width / 2, H * 1.0 - ly.height)
            hs = make_char_cached('hero', 40, HV | V(sweat=True), 'angry', False, (1, 0.6), 'down'); paste_safe(fr, hs, W * 0.42 - hs.width / 2, H * 0.92 - hs.height)
            pop(fr, bubble('. . .', '#ffffff', '#1b1a2a', 50), back((lt - 0.4) / 0.3), W / 2, H * 0.2)
        elif name == 'y1960':
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            k = ease(lt / 1.2)
            d.line([W * 0.08, H * 0.6, W * 0.08 + W * 0.84 * k, H * 0.6], fill=hexc('#5a4030'), width=8)
            f = fnt(FRED, 48, axes=[700, 100])
            if k > 0.15:
                d.rectangle([W * 0.12, H * 0.56, W * 0.32, H * 0.64], fill=hexc('#B23A2E'))
                d.text((W * 0.12, H * 0.67), 'VIKING AGE', font=f, fill=hexc('#1b1a2a')); d.text((W * 0.12, H * 0.73), '793 - 1066', font=f, fill=hexc('#5a4030'))
            if k > 0.95:
                d.ellipse([W * 0.86 - 22, H * 0.6 - 22, W * 0.86 + 22, H * 0.6 + 22], fill=hexc('#E04848'))
            pop(fr, bigtxt('CPR ~1960', 130, '#ffffff'), back((t - wt('n08', 6)) / 0.3), W * 0.72, H * 0.33)
            if k > 0.95: heart(d, W * 0.86, H * 0.47, 40)
        elif name == 'cough':
            fr = hallbg(1.12, 2.4, 130)
            cam = dict(cx=0, cz=0.8, f=1500, hor=H * 0.5, h=1.1, focus=3.0, ap=0.8)
            ck = ease((t - wt('n10', 2)) / 0.4)
            render_world2(fr, [Actor('hero', -0.6, 3.2, HV, expr='happy' if ck > 0.5 else 'worried', look=(1, 0), seed=90)], cam, t)
            ly = lying(TOR_V | V(sweat=True), 115, 'scared' if ck < 1 else 'happy', ang=lerp(88, 0, ck))
            paste_safe(fr, ly, W * 0.6 - ly.width / 2, H * lerp(1.18, 0.92, ck) - ly.height)
            if 0 < t - wt('n10', 2) < 0.3: fr = shake(fr, 10, t)
            pop(fr, bubble('COUGH!', '#ffffff', '#1b1a2a', 60), back((t - wt('n10', 2)) / 0.25), W * 0.75, H * 0.2)
            if t > wt('n10', 4): pop(fr, label_box('ALIVE', '#ffffff', '#2f8a4e'), back((t - wt('n10', 4)) / 0.3), W / 2, 110)
        elif name == 'meant':
            fr = hallbg(lerp(1.1, 1.3, eio(u)), 4.0, 70)
            fr = tint(fr, (40, 8, 8), 0.35)
            # Hakon blurred in background
            hk = make_char_cached('viking', 70, HAKON_V, 'smirk', False, (-1, 0), 'down')
            hk = hk.filter(ImageFilter.GaussianBlur(5)); hk = stint(hk, (20, 10, 10), 0.4)
            paste_safe(fr, hk, W * 0.78 - hk.width / 2, H * 0.62 - hk.height)
            sc = lerp(1.8, 2.4, eio(u)); pl = plate_img(sc, bite=True); paste_safe(fr, pl, W * 0.42 - pl.width / 2, H * 0.72)
            fr = Image.alpha_composite(fr, glow(W, H, W * 0.42, H * 0.78, 380, 160, '#ffe4ad', 90))
            pop(fr, s_meant, back((t - wt('n11', 4)) / 0.3), W * 0.42, H * 0.25)
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
