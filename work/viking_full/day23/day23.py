import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4', '/workspace/work/viking_full/day6', '/workspace/work/viking_full/day14', '/workspace/work/viking_full/day17'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day4 import stamp, bigtxt, chest_img, bone_img
from day14 import ULF_V, snowfall, flames
from day17 import GUN_V
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'n02': 0.6, 'n03': 0.3, 'n04': 0.4, 'n05': 0.6, 'n06': 0.7, 'n07': 0.4, 'n08': 0.8, 'n09': 0.2}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text'].replace('"', '')) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk='N')
    t += d_
DUR = t + 2.6
hook.TL = TL; hook.LABELS = {}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('puzzle', wt('n01', 3) - 0.1), ('young', S_('n02') - 0.4), ('burn', S_('n03') - 0.2),
         ('tree', S_('n04') - 0.3), ('saw', S_('n05') - 0.4), ('dark', wt('n05', 10) - 0.1), ('gift', S_('n06') - 0.4),
         ('dead', S_('n07') - 0.3), ('marsh', S_('n08') - 0.5), ('boots', S_('n09') - 0.2), ('end', TL['n09']['en'] + 0.4)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V
SEPIA = (110, 80, 45)

def piece(txt, col, w=380, h=260):
    im = Image.new('RGBA', (w + 60, h + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, 30, 30 + w, 30 + h], radius=24, fill=hexc(col))
    d.ellipse([30 + w - 30, 30 + h / 2 - 30, 30 + w + 30, 30 + h / 2 + 30], fill=hexc(col))
    f = fnt(FRED, 54, axes=[700, 100]); d.text((30 + w / 2 - f.getlength(txt) / 2, 30 + h / 2 - 32), txt, font=f, fill=hexc('#ffffff'))
    return im

def boot_print(d, x, y, s, col, outline=False):
    pts = [(x - 40 * s, y - 120 * s), (x + 40 * s, y - 120 * s), (x + 50 * s, y - 20 * s), (x + 35 * s, y + 40 * s), (x - 35 * s, y + 40 * s), (x - 50 * s, y - 20 * s)]
    if outline: d.polygon(pts, outline=hexc(col), width=8)
    else: d.polygon(pts, fill=hexc(col))
    if outline: d.ellipse([x - 35 * s, y + 60 * s, x + 35 * s, y + 130 * s], outline=hexc(col), width=8)
    else: d.ellipse([x - 35 * s, y + 60 * s, x + 35 * s, y + 130 * s], fill=hexc(col))

def marsh_bg(t, z=1.0):
    fr = vgrad(W, H, [(0, '#2a3a40'), (0.45, '#4a5a50'), (0.46, '#3a4a34'), (1, '#1e2a1c')])
    d = ImageDraw.Draw(fr); rnd = random.Random(4)
    for i in range(7):
        x = rnd.uniform(0, W); y = rnd.uniform(H * 0.55, H * 0.95); r = rnd.uniform(120, 260)
        d.ellipse([x - r, y - r * 0.25, x + r, y + r * 0.25], fill=hexc('#2c3e44'))
    for i in range(120):
        x = rnd.uniform(0, W); y = rnd.uniform(H * 0.47, H); h = rnd.uniform(30, 110) * (0.5 + y / H)
        sw = 6 * math.sin(t * 1.5 + i)
        d.line([x, y, x + sw, y - h], fill=hexc(rnd.choice(['#5a6a3a', '#6a7a44', '#4a5a30'])), width=4)
    fr = fr.resize((int(W * z), int(H * z)), Image.BILINEAR).crop((int((W * z - W) / 2), int((H * z - H) / 2), int((W * z - W) / 2) + W, int((H * z - H) / 2) + H))
    return fr.convert('RGBA')

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set()
    dcard = title_card('DAY 23', 'THE KILLER')
    pcs = [piece('THE FIRE', '#d24a3a'), piece('GUNNAR', '#2f4e6e'), piece('THE RUNES', '#8a6a3a'), piece('HEMLOCK', '#3e6a3a')]
    s_k = stamp('THE KILLER', '#d24a3a', 120); s_m = stamp('SIZE MATCH', '#d24a3a', 110); s_l = stamp('LIED', '#d24a3a', 120)
    chest = chest_img(0.0, 0.5)
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        if name == 'daycard':
            fr = fastblur(tint(cam_bg(S['village'], 1.04 + 0.02 * u, 0, -20), (10, 10, 30), 0.5), 3.0)
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name == 'puzzle':
            pg = False
            fr = parchment(W, H)
            tgt = [(W * 0.38, H * 0.36), (W * 0.62, H * 0.36), (W * 0.38, H * 0.64), (W * 0.62, H * 0.64)]
            srcs = [(-300, -200), (W + 300, -200), (-300, H + 200), (W + 300, H + 200)]
            for i, p_ in enumerate(pcs):
                k = ease((lt - 0.15 * i) / 0.6)
                x = lerp(srcs[i][0], tgt[i][0], k); y = lerp(srcs[i][1], tgt[i][1], k)
                paste_safe(fr, p_, x - p_.width / 2, y - p_.height / 2)
            if lt > 1.3 and lt < 1.5: fr = shake(fr, 5, t)
            if lt > 1.3: pop(fr, label_box('IT ALL FITS', '#ffffff', '#1b1a2a'), back((lt - 1.3) / 0.3), W / 2, H * 0.1)
        elif name in ('young', 'burn', 'saw'):
            fr = cam_bg(S['village'], 1.06 + 0.03 * u, 0, -20); fr = tint(fr, (30, 20, 15) if name != 'young' else SEPIA, 0.55)
            cam = dict(cx=0, cz=lerp(0.4, 0.8, eio(u)), f=1500, hor=H * 0.6, h=1.2, focus=3.2, ap=0.7)
            acts = []
            if name == 'young':
                acts = [Actor('viking', 0.0, 2.8, HAKON_V, expr='happy', look=(0, 0), seed=75, size=0.85, pose='up')]
            if name == 'burn':
                flames(fr, t, W * 0.45, H * 0.66, 0.9)
                acts = [Actor('viking', lerp(0.8, 2.6, ease(u)), 3.6, HAKON_V, expr='worried', look=(1, 0), seed=75, size=0.85, bob=1.0)]
            if name == 'saw':
                flames(fr, t, W * 0.3, H * 0.66, 0.6)
                acts = [Actor('viking', 1.2, 3.3, GUN_V, expr='worried', look=(-1, 0), seed=88, size=0.95)]
            render_world2(fr, acts, cam, t)
            fr = tint(fr, SEPIA, 0.25)
            if name == 'young':
                pop(fr, label_box('FLASHBACK: 10 YEARS AGO', '#ffffff', '#8a6a3a'), back(lt / 0.35), W / 2, 110)
                pop(fr, name_pill('HAKON', 'AGE 16'), back((t - wt('n02', 4)) / 0.3), W / 2, H * 0.3)
            if name == 'burn':
                pop(fr, label_box('THE GRAIN STORE', '#ffffff', '#d24a3a'), back((t - wt('n03', 7)) / 0.35), W / 2, 110)
            if name == 'saw':
                pop(fr, bigtxt('GUNNAR SAW IT', 100, '#ffffff'), back((lt - 0.4) / 0.3), W / 2, H * 0.18)
        elif name == 'tree':
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            pj = name_pill('JARL', 'FATHER'); pu = name_pill('ULF', 'UNCLE'); ph = name_pill('HAKON', 'SON')
            d.line([W * 0.3, H * 0.3, W * 0.7, H * 0.3], fill=hexc('#5a4030'), width=6)
            f = fnt(FRED, 36, axes=[700, 100]); d.text((W / 2 - f.getlength('BROTHERS') / 2, H * 0.22), 'BROTHERS', font=f, fill=hexc('#5a4030'))
            d.line([W * 0.3, H * 0.33, W * 0.3, H * 0.62], fill=hexc('#5a4030'), width=6)
            pop(fr, pj, back(lt / 0.3), W * 0.3, H * 0.3)
            pop(fr, pu, back((lt - 0.2) / 0.3), W * 0.7, H * 0.3)
            pop(fr, ph, back((lt - 0.4) / 0.3), W * 0.3, H * 0.66)
            if t > wt('n04', 4) - 0.1:
                ka = ease((t - wt('n04', 4)) / 0.6)
                d.line([W * 0.38, H * 0.64, lerp(W * 0.38, W * 0.66, ka), lerp(H * 0.64, H * 0.36, ka)], fill=hexc('#d24a3a'), width=10)
                pop(fr, label_box('BLAMED HIS UNCLE', '#ffffff', '#d24a3a'), back((t - wt('n04', 4) - 0.3) / 0.3), W * 0.62, H * 0.56)
            if t > wt('n04', 12) - 0.1: pop(fr, s_l, back((t - wt('n04', 12)) / 0.3), W * 0.3, H * 0.84)
        elif name == 'dark':
            fr = cam_bg(S['village'], 1.1, 0, -20); fr = tint(fr, (5, 5, 18), 0.82)
            d = ImageDraw.Draw(fr); cx_, cy_ = W * 0.55, H * 0.55
            d.rectangle([cx_ - 140, cy_ - 120, cx_ + 140, cy_ + 120], fill=hexc('#1a140e'))
            fr.alpha_composite(glow(W, H, cx_, cy_, 220, 200, '#ffb35a', int(200 * (1 - ease((lt - 0.8) / 0.3)))))
            cam = dict(cx=0, cz=0.6, f=1500, hor=H * 0.58, h=1.1, focus=3.0, ap=0.0)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            render_world2(lay, [Actor('viking', lerp(-2.2, -0.9, ease(u * 1.6)), 3.2, HAKON_V, expr='angry', look=(1, 0), seed=75, size=1.05)], cam, t)
            a = lay.split()[3]; sil = Image.new('RGBA', (W, H), (6, 6, 10, 255)); sil.putalpha(a); fr.alpha_composite(sil)
            fr = Image.alpha_composite(fr, Image.new('RGBA', (W, H), (120, 0, 0, int(60 * ease((lt - 0.8) / 0.3)))))
            pop(fr, s_k, back((t - wt('n05', 11)) / 0.3), W / 2, H * 0.2)
        elif name == 'gift':
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            pop(fr, name_pill('JARL', 'GIVES YOU'), back(lt / 0.3), W / 2, H * 0.12)
            # hut icon
            if t > wt('n06', 9) - 0.1:
                k = back((t - wt('n06', 9)) / 0.3); hx, hy = W * 0.3, H * 0.48
                hut = Image.new('RGBA', (360, 300), (0, 0, 0, 0)); hd = ImageDraw.Draw(hut)
                hd.polygon([(0, 140), (180, 0), (360, 140)], fill=hexc('#4a6a3a')); hd.rectangle([40, 140, 320, 300], fill=hexc('#7a5234')); hd.rectangle([150, 200, 210, 300], fill=hexc('#3a2a1e'))
                pop(fr, hut, k, hx, hy); pop(fr, label_box("GUNNAR'S HUT", '#ffffff', '#2f4e6e'), k, hx, H * 0.75)
            if t > wt('n06', 12) - 0.1:
                k = back((t - wt('n06', 12)) / 0.3)
                pop(fr, chest, k, W * 0.7, H * 0.5); pop(fr, label_box("GUNNAR'S CHEST", '#ffffff', '#2f4e6e'), k, W * 0.7, H * 0.75)
            if t > wt('n06', 16) - 0.1:
                b = bone_img(0.6); pop(fr, b, back((t - wt('n06', 16)) / 0.3), W * 0.7, H * 0.32)
        elif name == 'dead':
            fr = cam_bg(S['village'], 1.15, 0, -60); fr = fastblur(fr, 2.4); fr = tint(fr, (60, 0, 0), 0.45)
            cam = dict(cx=0.2, cz=lerp(1.0, 1.35, eio(u)), f=1500, hor=H * 0.5, h=0.95, focus=2.0, ap=1.2)
            render_world2(fr, [Actor('viking', 0.3, 3.0, HAKON_V, expr='angry', look=(-0.4, 0), seed=75, size=1.08)], cam, t)
            pop(fr, bigtxt('FROM DAY ONE', 110, '#ff6a5a'), back((t - wt('n07', 6)) / 0.3), W * 0.27, H * 0.3)
            if lt < 0.3: fr = shake(fr, 5, t)
        elif name == 'marsh':
            fr = marsh_bg(t, lerp(1.0, 1.08, eio(u)))
            d = ImageDraw.Draw(fr)
            n = int(clamp((t - wt('n08', 9)) / 1.0) * 5) if t > wt('n08', 9) - 0.05 else 0
            for i in range(n):
                x = W * (0.25 + i * 0.12); y = H * (0.72 + 0.06 * (i % 2))
                d.ellipse([x - 60, y - 22, x + 60, y + 22], fill=hexc('#1a120a')); d.ellipse([x - 80, y - 12, x - 40, y + 4], fill=hexc('#4a3420'))
            if t > wt('n08', 11) - 0.1:
                pop(fr, label_box('WATER HEMLOCK ROOTS', '#ffffff', '#3e6a3a'), back((t - wt('n08', 11)) / 0.35), W * 0.5, H * 0.56)
            pop(fr, label_box('THE NORTH MARSH', '#ffffff', '#6f7cff'), back((lt - 0.3) / 0.35), W / 2, 110)
            if n: pop(fr, bigtxt('FRESH HOLES', 100), back((t - wt('n08', 9)) / 0.3), W / 2, H * 0.3)
        elif name in ('boots', 'end'):
            fr = marsh_bg(t, 1.12); fr = tint(fr, (10, 10, 20), 0.35 if name == 'boots' else 0.6)
            d = ImageDraw.Draw(fr)
            for i in range(3):
                if lt > 0.25 * i or name == 'end': boot_print(d, W * (0.3 + 0.12 * i), H * (0.72 - 0.08 * (i % 2)), 0.9, '#1a120a')
            if name == 'boots':
                k = ease((t - wt('n09', 4)) / 0.6)
                if k > 0:
                    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); boot_print(ImageDraw.Draw(lay), lerp(W * 0.85, W * 0.42, k), H * 0.64, 0.9, '#E9BC3F', True); fr.alpha_composite(lay)
                if k >= 1: pop(fr, s_m, back((t - wt('n09', 4) - 0.6) / 0.3), W / 2, H * 0.25)
                if k > 0: pop(fr, label_box("HAKON'S BOOT", '#ffffff', '#E9BC3F'), back((t - wt('n09', 4)) / 0.3), W * 0.75, H * 0.45)
            else:
                pop(fr, name_pill('HAKON', 'THE KILLER'), back((lt - 0.1) / 0.3), W / 2, H * 0.45)
                pop(fr, bigtxt('BUT CAN YOU PROVE IT?', 80, '#ffffff'), back((lt - 0.7) / 0.3), W / 2, H * 0.62)
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
        ts = [float(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else [s + (e - s) * 0.8 for n, s, e in SPANS]
        run([int(x * FPS) for x in ts])
    else:
        a, b = int(sys.argv[2]), int(sys.argv[3]); run(range(a, b), out=sys.argv[4])
