import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4', '/workspace/work/viking_full/day6'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day4 import stamp, bigtxt
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'n02': 0.5, 'n03': 0.3, 'n04': 0.6, 'n05': 0.3, 'n06': 0.4, 'n07': 0.5, 'n08': 0.7, 'u01': 0.5, 'n09': 0.8, 'n10': 0.4, 'n11': 0.4}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text']) for w in wj['words'] if w['type'] == 'word']
    if lid == 'n05' and len(words) >= 4:
        words = [words[0], (words[1][0], words[3][1], 'Skógarmaðr,')] + words[4:]
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'u': 'U'}.get(lid[0], 'N'))
    t += d_
DUR = t + 2.0
hook.TL = TL; hook.LABELS = {'U': 'U L F'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('trek', wt('n01', 3) - 0.1), ('knife', wt('n01', 10) - 0.1), ('five', S_('n02') - 0.3), ('outlaws', S_('n03') - 0.2),
         ('law', S_('n04') - 0.3), ('word', S_('n05') - 0.2), ('rules', S_('n06') - 0.2), ('grettir', S_('n07') - 0.3),
         ('leader', S_('n08') - 0.4), ('eyes', wt('n08', 10) - 0.1), ('ulf', S_('u01') - 0.3), ('fire', S_('n09') - 0.5),
         ('blamed', S_('n10') - 0.3), ('exile', S_('n11') - 0.3)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V
ULF_V = V(coat='#4a3f35', tunic='#3a2f25', fur='#8d8d8d', beard='#a8a39a', beard_dk='#7e7a72', helmet=False, hair='#a8a39a', rim='#F6B07A', weapon='axe')
def outlaw_v(i):
    return V(coat=['#3f3a30', '#4a4030', '#35322c', '#453a2e'][i % 4], tunic='#2e2a24', fur='#7d7d7d', beard=['#6b4a2b', '#3a2a1e', '#8a6a3a', '#5a3a22'][i % 4],
             beard_dk='#2a1e14', helmet=False, hair=['#6b4a2b', '#3a2a1e', '#8a6a3a', '#5a3a22'][i % 4], rim='#F6B07A', weapon='axe')
OUTLAWS = [(-1.6, 4.0), (-0.8, 3.7), (0.8, 3.7), (1.6, 4.0)]

def knife_img():
    im = Image.new('RGBA', (1100, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(0, 150), (760, 95), (1080, 150), (760, 190)], fill=hexc('#c9d1da')); d.line([(60, 150), (1000, 150)], fill=hexc('#eef3f8'), width=6)
    d.rounded_rectangle([700, 60, 760, 240], radius=10, fill=hexc('#5a3b24'))
    return im

def icon_card(txt, crossed, col='#1b1a2a'):
    im = Image.new('RGBA', (420, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 419, 259], radius=30, fill=hexc('#f4ead2'), outline=hexc('#5a4030'), width=6)
    f = fnt(FRED, 56, axes=[700, 100]); d.text((210 - f.getlength(txt) / 2, 95), txt, font=f, fill=hexc(col))
    if crossed: d.line([30, 30, 390, 230], fill=hexc('#d24a3a'), width=16); d.line([390, 30, 30, 230], fill=hexc('#d24a3a'), width=16)
    return im

def flames(fr, t, cx, cy, sc=1.0):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); rnd = random.Random(3)
    for i in range(22):
        x = cx + rnd.uniform(-260, 260) * sc; h = (180 + rnd.uniform(0, 200)) * sc * (0.8 + 0.25 * math.sin(t * 9 + i)); w_ = rnd.uniform(40, 80) * sc
        col = rnd.choice(['#ff6a1a', '#ff9f3a', '#ffd25a'])
        d.polygon([(x - w_, cy), (x + 10 * math.sin(t * 7 + i), cy - h), (x + w_, cy)], fill=hexc(col)[:3] + (220,))
    fr.alpha_composite(lay.filter(ImageFilter.GaussianBlur(3)))
    fr.alpha_composite(glow(W, H, cx, cy - 150 * sc, 520 * sc, 380 * sc, '#ff7a2a', 160))
    rnd = random.Random(5); d = ImageDraw.Draw(fr)
    for i in range(40):
        x = cx + rnd.uniform(-300, 300) * sc + 30 * math.sin(t * 2 + i); y = cy - ((rnd.uniform(0, 700) + t * 220) % 700) * sc
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 200, 90, 200))

def snowfall(fr, t, n=90):
    d = ImageDraw.Draw(fr); rnd = random.Random(11)
    for i in range(n):
        x = (rnd.uniform(0, W) + 40 * math.sin(t + i)) % W; y = (rnd.uniform(0, H) + t * rnd.uniform(60, 140)) % H; r = rnd.uniform(2, 5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(240, 245, 255, 200))

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set()
    dcard = title_card('DAY 14', 'THE OUTLAWS')
    s_out = stamp('OUTLAWS', '#d24a3a', 120); s_bro = stamp('BROTHER', '#d24a3a', 110); s_blame = stamp('BLAMED', '#d24a3a', 120); s_exile = stamp('OUTLAW', '#d24a3a', 120)
    kn = knife_img()
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        if name == 'daycard':
            fr = fastblur(cam_bg(S['forest'], 1.04 + 0.02 * u), 3.0)
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name == 'trek':
            fr = cam_bg(S['forest'], 1.02 + 0.06 * u)
            fr = tint(fr, (20, 30, 40), 0.25)
            d = ImageDraw.Draw(fr)
            for k in range(36):
                yy = H * 0.3 - k * 9; xx = W * 0.72 + 14 * math.sin(k * 0.35 - t * 1.5); r = 3 + k * 0.5
                d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(225, 225, 230, int(160 * (1 - k / 36))))
            cam = dict(cx=0, cz=lerp(0.0, 0.6, eio(u)), f=1500, hor=H * 0.62, h=1.2, focus=3.5, ap=0.7)
            render_world2(fr, [Actor('hero', lerp(-1.0, 0.0, ease(u)), 3.4, HV, expr='neutral', look=(1, -0.4), seed=90, bob=1.0)], cam, t)
            snowfall(fr, t)
        elif name == 'knife':
            fr = fastblur(cam_bg(S['forest'], 1.2), 6.0); fr = tint(fr, (20, 30, 40), 0.3)
            cam = dict(cx=0, cz=1.5, f=1500, hor=H * 0.55, h=1.0, focus=2.0, ap=1.2)
            render_world2(fr, [Actor('hero', -0.3, 2.6, HV, expr='worried', look=(1, 0), seed=90, pose='up')], cam, t)
            kx = lerp(W + 100, W * 0.45, back(lt / 0.25))
            paste_safe(fr, kn, kx, H * 0.42 - kn.height / 2)
            if lt < 0.35: fr = shake(fr, 9, t)
            pop(fr, bigtxt('KNIFE!', 110, '#ff6a5a'), back((lt - 0.15) / 0.3), W * 0.7, H * 0.18)
        elif name in ('five', 'outlaws', 'leader', 'ulf'):
            fr = cam_bg(S['forest'], {'five': 1.05 + 0.04 * u, 'outlaws': 1.1, 'leader': 1.08, 'ulf': 1.2}[name])
            fr = tint(fr, (25, 30, 40), 0.35)
            acts = []
            if name in ('five', 'outlaws', 'leader'):
                n = 5 if name != 'five' else int(clamp((lt - 0.3) / 1.8) * 5 + 0.999) if lt > 0.3 else 0
                for i, (x, z) in enumerate(OUTLAWS):
                    if i < n: acts.append(Actor('viking', x, z, outlaw_v(i), expr='angry', look=(0, 0), seed=300 + i, size=0.92))
                uz = lerp(4.1, 3.2, ease((lt - 0.4) / 1.4)) if name == 'leader' else 4.1
                if n >= 3 or name != 'five': acts.append(Actor('viking', 0.0, uz, ULF_V, expr='angry', look=(0, 0), seed=77, size=1.15))
                cam = dict(cx=0, cz=0.2 if name != 'leader' else lerp(0.2, 0.7, eio(u)), f=1500, hor=H * 0.6, h=1.2, focus=3.8, ap=0.6)
            else:
                acts = [Actor('viking', 0.3, 3.0, ULF_V, expr='neutral', look=(-0.6, 0), seed=77, size=1.15)]
                cam = dict(cx=0.2, cz=lerp(1.0, 1.25, eio(u)), f=1500, hor=H * 0.5, h=0.95, focus=2.0, ap=1.2)
            render_world2(fr, acts, cam, t)
            snowfall(fr, t, 60)
            if name == 'five':
                pop(fr, bigtxt(f'{n} MEN', 100), back((lt - 0.3) / 0.3) if n else 0, W / 2, H * 0.15)
                if t > wt('n02', 11) - 0.1: pop(fr, label_box('WOLF SKINS', '#ffffff', '#6f7cff'), back((t - wt('n02', 11)) / 0.35), W * 0.8, H * 0.3)
            if name == 'outlaws': pop(fr, s_out, back((lt - 0.2) / 0.3), W / 2, H * 0.2)
            if name == 'leader': pop(fr, label_box('THE LEADER', '#ffffff', '#E9BC3F'), back((lt - 0.4) / 0.35), W / 2, 110)
            if name == 'ulf':
                pop(fr, name_pill('ULF', 'THE OUTLAW'), back((t - wt('u01', 2)) / 0.3), W * 0.3, H * 0.55)
                if t > wt('u01', 7) - 0.1: pop(fr, s_bro, back((t - wt('u01', 7)) / 0.3), W * 0.3, H * 0.25)
        elif name == 'eyes':
            fr = Image.new('RGBA', (W, H), hexc('#0c0e14')[:3] + (255,))
            for i, (v, sd, lab, c) in enumerate([(ULF_V, 77, 'ULF', '#6f7cff'), (JARL_V, 76, 'JARL', '#E9BC3F')]):
                half = cam_bg(S['forest'] if i == 0 else S['village'], 1.3, 0, -40).resize((W // 2, H // 2)).resize((W, H))
                half = tint(half, (20, 25, 35), 0.4)
                cam = dict(cx=0, cz=1.4, f=1500, hor=H * 0.45, h=0.95, focus=1.6, ap=1.2)
                render_world2(half, [Actor('viking', 0, 3.0, v, expr='angry', look=(0.6 if i == 0 else -0.6, 0), seed=sd, size=1.15)], cam, t)
                sl = half.crop((W // 4, 0, W // 4 + W // 2, H))
                fr.paste(sl, (i * W // 2 + int((1 - ease(lt / 0.35)) * (-200 if i == 0 else 200)), 0))
                pop(fr, label_box(lab, '#ffffff', c), back((lt - 0.3) / 0.3), i * W // 2 + W // 4, H * 0.85)
            d = ImageDraw.Draw(fr); d.line([W / 2, 0, W / 2, H], fill=hexc('#ffffff'), width=6)
            pop(fr, bigtxt('SAME EYES', 100, '#E9BC3F'), back((t - wt('n08', 12)) / 0.3), W / 2, H * 0.14)
        elif name == 'law':
            pg = False
            fr = parchment(W, H)
            pop(fr, bigtxt('WORST PUNISHMENT?', 90), back(lt / 0.3), W / 2, H * 0.15)
            pop(fr, icon_card('DEATH', t > wt('n04', 8) + 0.3), back((t - wt('n04', 8)) / 0.3), W * 0.3, H * 0.52)
            pop(fr, icon_card('OUTLAW', False, '#d24a3a'), back((t - wt('n04', 11)) / 0.3), W * 0.7, H * 0.52)
            if t > wt('n04', 11) + 0.4:
                d = ImageDraw.Draw(fr); d.ellipse([W * 0.7 - 260, H * 0.52 - 170, W * 0.7 + 260, H * 0.52 + 170], outline=hexc('#d24a3a'), width=10)
            pop(fr, label_box('REAL VIKING LAW', '#ffffff', '#2f6e9e'), back((lt - 0.3) / 0.35), W / 2, H * 0.85)
        elif name == 'word':
            pg = False
            fr = parchment(W, H)
            pop(fr, bigtxt('SKÓGARMAÐR', 140, '#1b1a2a'), back(lt / 0.3), W / 2, H * 0.4)
            pop(fr, label_box('= " FOREST MAN "', '#ffffff', '#3e5a48'), back((t - wt('n05', 3)) / 0.35), W / 2, H * 0.62)
            pop(fr, label_box('OLD NORSE', '#ffffff', '#6f7cff'), back((lt - 0.3) / 0.35), W / 2, H * 0.18)
        elif name == 'rules':
            pg = False
            fr = parchment(W, H)
            for i, (lab, wi) in enumerate([('FOOD', 2), ('SHELTER', 4), ('HELP', 7)]):
                pop(fr, icon_card(lab, t > wt('n06', wi) + 0.25), back((t - wt('n06', wi)) / 0.3), W * (0.2 + 0.3 * i), H * 0.38)
            if t > wt('n06', 10) - 0.1:
                pop(fr, bigtxt('ANYONE COULD KILL YOU', 90, '#d24a3a'), back((t - wt('n06', 10)) / 0.3), W / 2, H * 0.72)
                if t - wt('n06', 12) < 0.3 and t > wt('n06', 12): fr = shake(fr, 6, t)
        elif name == 'grettir':
            pg = False
            fr = parchment(W, H)
            cam = dict(cx=0, cz=0.8, f=1500, hor=H * 0.62, h=1.1, focus=3.0, ap=0.0)
            sil = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            render_world2(sil, [Actor('viking', -0.9, 3.0, V(coat='#2a2018', beard='#2a2018', beard_dk='#2a2018', helmet=False, hair='#2a2018', fur='#2a2018', weapon='axe'), expr='angry', seed=500, size=1.2)], cam, t)
            a = sil.split()[3]; sil = Image.new('RGBA', (W, H), hexc('#3a2a1e')[:3] + (255,)); sil.putalpha(a); fr.alpha_composite(sil)
            pop(fr, label_box('GRETTIR THE STRONG', '#ffffff', '#E9BC3F'), back((t - wt('n07', 3)) / 0.35), W * 0.3, H * 0.15)
            yrs = int(clamp((lt - 1.2) / 2.8) * 19)
            pop(fr, bigtxt(f'{yrs} YEARS', 140, '#1b1a2a'), back((lt - 1.0) / 0.3), W * 0.68, H * 0.45)
            if yrs >= 19: pop(fr, label_box('AS AN OUTLAW', '#ffffff', '#d24a3a'), back((lt - 4.0) / 0.3), W * 0.68, H * 0.62)
            pop(fr, label_box('ICELANDIC SAGA', '#ffffff', '#6f7cff'), back((lt - 0.4) / 0.35), W * 0.68, H * 0.25)
        elif name in ('fire', 'blamed', 'exile'):
            fr = cam_bg(S['village'], 1.08 + 0.03 * u, 0, -20); fr = tint(fr, (8, 10, 28), 0.7)
            if name == 'fire':
                flames(fr, t, W * 0.5, H * 0.66, 1.1)
                pop(fr, label_box('10 YEARS AGO', '#ffffff', '#6f7cff'), back(lt / 0.3), W / 2, 110)
                if t > wt('n09', 5) - 0.1: pop(fr, label_box('THE GRAIN STORE', '#ffffff', '#d24a3a'), back((t - wt('n09', 5)) / 0.35), W / 2, H * 0.22)
            else:
                flames(fr, t, W * 0.5, H * 0.66, 0.35)
            cam = dict(cx=0, cz=0.3, f=1500, hor=H * 0.6, h=1.2, focus=3.6, ap=0.6)
            acts = []
            if name == 'blamed':
                acts = [Actor('viking', 0.0, 3.4, V(**{**ULF_V, 'beard': '#8a5a2a', 'hair': '#8a5a2a', 'beard_dk': '#6a4220'}), expr='worried', look=(0, 0), seed=77, size=1.1)]
                acts += [Actor('viking', x, 4.4, outlaw_v(i + 1), expr='angry', look=(-x, 0), seed=600 + i, pose='up' if i % 2 else 'down') for i, x in enumerate((-1.6, -0.9, 0.9, 1.6))]
            if name == 'exile':
                acts = [Actor('jarl', -0.9, 3.4, JARL_V, expr='angry', look=(1, 0), seed=76, size=1.18, pose='up'),
                        Actor('viking', lerp(0.4, 2.4, ease(u)), 3.6, V(**{**ULF_V, 'beard': '#8a5a2a', 'hair': '#8a5a2a', 'beard_dk': '#6a4220'}), expr='worried', look=(1, 0), seed=77, size=1.1, bob=1.0)]
            render_world2(fr, acts, cam, t); snowfall(fr, t, 120)
            if name == 'blamed':
                pop(fr, label_box('PEOPLE STARVED', '#ffffff', '#6f7cff'), back(lt / 0.35), W / 2, 110)
                pop(fr, s_blame, back((t - wt('n10', 5)) / 0.3), W / 2, H * 0.32)
            if name == 'exile':
                pop(fr, label_box('HIS OWN BROTHER', '#ffffff', '#E9BC3F'), back((t - wt('n11', 1)) / 0.35), W / 2, 110)
                pop(fr, s_exile, back((t - wt('n11', 6)) / 0.3), W / 2, H * 0.32)
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
        ts = [float(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else [s + (e - s) * 0.75 for n, s, e in SPANS]
        run([int(x * FPS) for x in ts])
    else:
        a, b = int(sys.argv[2]), int(sys.argv[3]); run(range(a, b), out=sys.argv[4])
