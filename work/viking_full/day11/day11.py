import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4', '/workspace/work/viking_full/day6'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day2 import stint
from day4 import stamp, bigtxt
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'n02': 0.4, 'n03': 0.3, 'y01': 0.5, 'h01': 0.3, 'n04': 0.5, 'n05': 0.6, 'n06': 0.4, 'n07': 0.6, 'n08': 0.9, 'n09': 0.4, 'n10': 0.4}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text']) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'h': 'H', 'j': 'J', 'y': 'Y'}.get(lid[0], 'N'))
    t += d_
DUR = t + 2.0
hook.TL = TL; hook.LABELS = {'H': 'H A K O N', 'J': 'J A R L', 'Y': 'Y O U'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('loading', wt('n01', 2) - 0.1), ('watch', S_('n02') - 0.25), ('graph', S_('n03') - 0.2),
         ('yell', S_('y01') - 0.3), ('hakon', S_('h01') - 0.2), ('jarl', S_('n04') - 0.3), ('stay', wt('n04', 9) - 0.1),
         ('storm', S_('n05') - 0.4), ('sea', S_('n06') - 0.3), ('axes', S_('n07') - 0.4), ('morning', S_('n08') - 0.6),
         ('smoke', wt('n08', 13) - 0.2), ('hundred', S_('n09') - 0.3), ('who', S_('n10') - 0.3)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V

def watch_img(p, t):
    im = Image.new('RGBA', (760, 760), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = 380
    d.rectangle([c - 150, 0, c + 150, 760], fill=hexc('#1b1d24'))
    d.ellipse([c - 330, c - 330, c + 330, c + 330], fill=hexc('#3a3f4a')); d.ellipse([c - 300, c - 300, c + 300, c + 300], fill=hexc('#0f1218'))
    for k in range(60):
        a = k / 60 * 2 * math.pi; r1 = 280; r2 = 255 if k % 5 == 0 else 268
        d.line([c + r1 * math.sin(a), c - r1 * math.cos(a), c + r2 * math.sin(a), c - r2 * math.cos(a)], fill=hexc('#e9e4d8'), width=6 if k % 5 == 0 else 2)
    d.arc([c - 220, c - 220, c + 220, c + 220], 150, 390, fill=hexc('#2f6e9e'), width=14)
    d.arc([c - 220, c - 220, c + 220, c + 220], 150, 200, fill=hexc('#d24a3a'), width=14)
    ang = math.radians(lerp(300, 175, p) - 90)
    d.line([c, c, c + 200 * math.cos(ang), c + 200 * math.sin(ang)], fill=hexc('#E9BC3F'), width=10); d.ellipse([c - 20, c - 20, c + 20, c + 20], fill=hexc('#E9BC3F'))
    f = fnt(FRED, 64, axes=[700, 100]); val = f'{int(lerp(1013, 978, p))} hPa'
    d.text((c - f.getlength(val) / 2, c + 90), val, font=f, fill=hexc('#d24a3a' if p > 0.5 else '#e9e4d8'))
    f2 = fnt(FRED, 30, axes=[700, 100]); d.text((c - f2.getlength('BARO') / 2, c - 150), 'BARO', font=f2, fill=hexc('#8a93ab'))
    return im

def rain(fr, t, n=160, a=120, slant=0.35):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); rnd = random.Random(7)
    for i in range(n):
        x0 = rnd.uniform(-200, W); sp = rnd.uniform(1800, 2600); y = (rnd.uniform(0, H) + t * sp) % (H + 100) - 50
        x = x0 + y * slant; d.line([x, y, x + 40 * slant, y + 40], fill=(200, 215, 235, a), width=2)
    fr.alpha_composite(lay)

def far_island(d, t, smoke_k=0.0, sc=1.0, ox=W * 0.7, oy=H * 0.52):
    d.polygon([(ox - 420 * sc, oy), (ox - 200 * sc, oy - 120 * sc), (ox, oy - 170 * sc), (ox + 260 * sc, oy - 90 * sc), (ox + 420 * sc, oy)], fill=hexc('#3e5a48'))
    for i in range(16):
        x = ox - 300 * sc + i * 40 * sc; y = oy - 80 * sc - 60 * sc * math.sin(i / 15 * math.pi)
        d.polygon([(x, y - 50 * sc), (x - 20 * sc, y + 10 * sc), (x + 20 * sc, y + 10 * sc)], fill=hexc('#2e4a3a'))
    if smoke_k > 0:
        sx, sy = ox + 60 * sc, oy - 150 * sc
        for k in range(40):
            yy = sy - k * 14 * sc * smoke_k; xx = sx + 18 * sc * math.sin(k * 0.35 - t * 1.5) + k * 2 * sc
            r = (4 + k * 0.6) * sc; d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(220, 220, 225, int(170 * (1 - k / 40))))

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set()
    dcard = title_card('DAY 11', 'THE STORM')
    s_storm = stamp('STORM COMING', '#d24a3a', 90)
    beachcrowd = crowd(91, 1, 7, 5.2, 1.0, 5.0, exclude=lambda x, z: abs(x) < 1.2, expr_choices=('happy', 'neutral', 'happy'))
    nightcrowd = crowd(93, 2, 8, 4.6, 1.1, 5.2, exclude=lambda x, z: abs(x) < 0.9, expr_choices=('happy', 'happy', 'happy'))
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
        elif name in ('loading', 'yell', 'stay'):
            fr = cam_bg(S['cool'], 1.03 + 0.03 * u, 0, -30)
            fr = Image.alpha_composite(fr, glow(W, H, W * 0.85, H * 0.12, 160, 160, '#fff6c0', 200))
            for i, bx in enumerate((0.18, 0.5, 0.82)):
                b = boat_img(t + i, 1.0).resize((520, 330), Image.BILINEAR)
                pull = ease((t - wt('n04', 13)) / 1.5) if name == 'stay' else 0
                paste_safe(fr, b, W * bx - b.width / 2, H * (0.66 + 0.08 * pull) - b.height * 0.7)
            cam = dict(cx=0, cz=0.3 if name != 'yell' else 0.9, f=1500, hor=H * 0.6, h=1.2, focus=3.6, ap=0.6)
            ex = {'loading': None, 'yell': 'worried', 'stay': 'neutral'}[name]
            acts = [Actor(a.kind, a.x, a.z, a.v, expr=ex or a.expr, look=(0, 0), seed=a.seed, size=a.size, bob=1.0 if name == 'loading' else 0) for a in beachcrowd]
            if name == 'yell':
                acts = [Actor('hero', 0.0, 3.0, HV, expr='angry', look=(0, 0), seed=90, pose='up')]
                if lt < 0.3: fr = shake(fr, 6, t)
            elif name == 'stay':
                acts.append(Actor('jarl', -0.4, 3.6, JARL_V, expr='neutral', look=(1, 0), seed=76, size=1.18, pose='up'))
                acts.append(Actor('hero', 0.6, 3.4, HV, expr='happy', look=(-1, 0), seed=90))
            render_world2(fr, acts, cam, t)
            if name == 'stay': pop(fr, label_box('SHIPS STAY ON THE BEACH', '#ffffff', '#2f6e9e'), back((t - wt('n04', 11)) / 0.35), W / 2, 110)
            if name == 'loading':
                pop(fr, label_box('CLEAR BLUE SKY', '#ffffff', '#2f6e9e'), back((lt - 0.3) / 0.35), W / 2, 110)
        elif name == 'watch':
            fr = fastblur(cam_bg(S['cool'], 1.3, 0, -30), 8.0)
            p = ease((t - wt('n02', 9)) / 2.0)
            sc = lerp(0.9, 1.05, eio(u)); wi = watch_img(p, t); wi = wi.resize((int(760 * sc), int(760 * sc)), Image.LANCZOS)
            if p > 0.6: wi = wi.rotate(1.5 * math.sin(t * 30), resample=Image.BICUBIC)
            paste_safe(fr, wi, W * 0.4 - wi.width / 2, H * 0.5 - wi.height / 2)
            pop(fr, label_box('DIVING WATCH', '#ffffff', '#2f6e9e'), back((t - wt('n02', 5)) / 0.35), W * 0.78, H * 0.3)
            if t > wt('n02', 10) - 0.1: pop(fr, label_box('BAROMETER', '#ffffff', '#E9BC3F'), back((t - wt('n02', 10)) / 0.35), W * 0.78, H * 0.42)
            if p > 0.3: pop(fr, bigtxt('PRESSURE DROPPING', 60, '#ff6a5a'), back((t - wt('n02', 15)) / 0.3), W * 0.78, H * 0.58)
        elif name == 'graph':
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            x0, x1, y0 = W * 0.12, W * 0.7, H * 0.35
            k = ease(lt / 1.4)
            pts = []
            for i in range(41):
                f_ = i / 40
                if f_ > k: break
                y = y0 + (0 if f_ < 0.5 else (f_ - 0.5) ** 2 * 4 * H * 0.42) + 8 * math.sin(i * 1.3)
                pts.append((lerp(x0, x1, f_), y))
            d.line([x0, H * 0.82, x1, H * 0.82], fill=hexc('#5a4030'), width=4); d.line([x0, H * 0.2, x0, H * 0.82], fill=hexc('#5a4030'), width=4)
            if len(pts) > 1: d.line(pts, fill=hexc('#d24a3a'), width=10)
            f = fnt(FRED, 40, axes=[700, 100]); d.text((x0 - 10, H * 0.14), 'AIR PRESSURE', font=f, fill=hexc('#1b1a2a'))
            if k > 0.95:
                cx_, cy_ = W * 0.83, H * 0.45
                for (dx, dy, r) in [(-80, 0, 80), (20, -40, 100), (110, 10, 75)]: d.ellipse([cx_ + dx - r, cy_ + dy - r, cx_ + dx + r, cy_ + dy + r], fill=hexc('#4a5568'))
                d.polygon([(cx_ + 10, cy_ + 50), (cx_ - 40, cy_ + 150), (cx_, cy_ + 150), (cx_ - 30, cy_ + 240), (cx_ + 60, cy_ + 120), (cx_ + 20, cy_ + 120), (cx_ + 50, cy_ + 50)], fill=hexc('#E9BC3F'))
            pop(fr, s_storm, back((t - wt('n03', 7)) / 0.3), W * 0.5, H * 0.2)
        elif name == 'hakon':
            fr = cam_bg(S['cool'], 1.15, 0, -60); fr = fastblur(fr, 2.0)
            fr = Image.alpha_composite(fr, glow(W, H, W * 0.85, H * 0.12, 160, 160, '#fff6c0', 220))
            cam = dict(cx=0.2, cz=1.1, f=1500, hor=H * 0.5, h=0.95, focus=2.0, ap=1.2)
            render_world2(fr, [Actor('viking', 0.35, 3.0, HAKON_V, expr='happy', look=(-0.5, -1), seed=75, size=1.08, pose='up', bob=0.5)], cam, t)
            pop(fr, bubble('NOT ONE CLOUD!', '#ffffff', '#1b1a2a', 46), back((lt - 0.5) / 0.3), W * 0.25, H * 0.25)
        elif name == 'jarl':
            fr = cam_bg(S['cool'], 1.15, 0, -60); fr = fastblur(fr, 2.4)
            cam = dict(cx=0.2, cz=lerp(0.9, 1.3, eio(u)), f=1500, hor=H * 0.48, h=1.0, focus=2.2, ap=1.2)
            render_world2(fr, [Actor('jarl', 0.35, 3.2, JARL_V, expr='neutral', look=(-1, 0), seed=76, size=1.18)], cam, t)
            pop(fr, bubble('. . .', '#ffffff', '#1b1a2a', 50), back((lt - 1.0) / 0.3), W * 0.25, H * 0.25)
        elif name == 'storm':
            pg = False
            fr = cam_bg(S['village'], 1.06 + 0.04 * u, 0, -20)
            fr = tint(fr, (15, 20, 35), 0.7)
            d = ImageDraw.Draw(fr)
            for (dx, dy, r) in [(0.2, 0.08, 260), (0.5, 0.05, 320), (0.8, 0.1, 280)]: d.ellipse([W * dx - r, H * dy - r * 0.6, W * dx + r, H * dy + r * 0.6], fill=hexc('#1c2230'))
            fk = ease((t - wt('n05', 10)) / 1.2)
            if fk > 0:
                rx, ry = lerp(W * 0.3, W * 1.1, fk), lerp(H * 0.42, -H * 0.1, fk)
                roof = Image.new('RGBA', (360, 140), (0, 0, 0, 0)); ImageDraw.Draw(roof).polygon([(0, 140), (180, 0), (360, 140)], fill=hexc('#4a6a3a'))
                roof = roof.rotate(fk * 540, resample=Image.BICUBIC, expand=True); paste_safe(fr, roof, rx - roof.width / 2, ry - roof.height / 2)
            rain(fr, t, 220, 140, 0.45)
            fl = (math.sin(t * 3.1) > 0.97) or (0 < t - wt('n05', 5) < 0.12)
            if fl: fr = Image.blend(fr, Image.new('RGBA', (W, H), (230, 235, 255, 255)), 0.55)
            fr = shake(fr, 3, t)
            pop(fr, label_box('3 HOURS LATER', '#ffffff', '#6f7cff'), back(lt / 0.3) * (1 - ease((lt - 1.8) / 0.3)), W / 2, 110)
        elif name == 'sea':
            pg = False
            fr = vgrad(W, H, [(0, '#0f2a3e'), (1, '#03070d')])
            for i in range(3):
                b = boat_img(0, 1.0).resize((480, 300)).rotate(-25 + i * 20, resample=Image.BICUBIC, expand=True)
                b = stint(b, (8, 20, 32), 0.75)
                paste_safe(fr, b, W * (0.2 + i * 0.3) - b.width / 2, lerp(H * 0.2, H * 0.55, ease(u)) + i * 40 - b.height / 2)
            rnd = random.Random(1); d = ImageDraw.Draw(fr)
            for i in range(30):
                x = rnd.uniform(0, W); y = (rnd.uniform(0, H) - t * 120) % H; d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(160, 200, 230, 120), width=2)
            pop(fr, label_box('HALF THE VILLAGE', '#ffffff', '#d24a3a'), back((t - wt('n06', 9)) / 0.35), W / 2, 110)
        elif name == 'axes':
            fr = cam_bg(S['village'], 1.08, 0, -20); fr = tint(fr, (8, 10, 25), 0.65)
            fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.75, 600, 300, '#ff9f3a', 150))
            cam = dict(cx=0, cz=lerp(0.0, 0.5, eio(u)), f=1500, hor=H * 0.5, h=1.3, focus=4.3, ap=0.6)
            up = t > wt('n07', 1) - 0.1
            acts = [Actor(a.kind, a.x, a.z, a.v, expr='happy', look=(0, -0.3), seed=a.seed, size=a.size, pose='up' if up else 'down', bob=1.0 if up else 0) for a in nightcrowd]
            acts.append(Actor('hero', 0.0, 3.4, HV, expr='happy', look=(0, 0), seed=90))
            render_world2(fr, acts, cam, t)
            if up: pop(fr, bigtxt('40 AXES', 120, '#E9BC3F'), back((t - wt('n07', 1)) / 0.3), W / 2, H * 0.15)
        elif name in ('morning', 'smoke', 'who'):
            fr = cam_bg(S['cool'], {'morning': 1.03, 'smoke': lerp(1.05, 1.15, eio(u)), 'who': 1.2}[name], 0, -30)
            fr = tint(fr, (60, 50, 70), 0.25)
            fr = Image.alpha_composite(fr, glow(W, H, W * 0.15, H * 0.4, 260, 200, '#ffc890', 160))
            d = ImageDraw.Draw(fr)
            sk = 0 if name == 'morning' else (ease((t - wt('n08', 16)) / 1.5) if name == 'smoke' else 1)
            if name == 'who':
                far_island(d, t, 1, 1.8, W * 0.55, H * 0.66)
            else:
                far_island(d, t, sk)
            d = ImageDraw.Draw(fr)
            for (dx, ang) in [(0.25, 20), (0.6, -10)]:  # debris
                d.line([W * dx, H * 0.86, W * dx + 160 * math.cos(math.radians(ang)), H * 0.86 + 160 * math.sin(math.radians(ang))], fill=hexc('#5a3b24'), width=14)
            if name != 'who':
                cam = dict(cx=0, cz=0.4, f=1500, hor=H * 0.62, h=1.2, focus=3.3, ap=0.6)
                hx = lerp(-1.4, -0.6, ease(u)) if name == 'morning' else -0.6
                render_world2(fr, [Actor('hero', hx, 3.3, HV, expr='worried' if name == 'smoke' else 'neutral', look=(1, -0.4) if name == 'smoke' else (1, 0), seed=90, bob=1 if name == 'morning' else 0)], cam, t)
            if name == 'smoke' and sk > 0.2:
                pop(fr, label_box('THE FAR SIDE OF THE ISLAND', '#ffffff', '#6f7cff'), back((t - wt('n08', 23)) / 0.35), W / 2, 110)
            if name == 'who':
                pop(fr, bigtxt('WHO LIT THAT FIRE?', 110), back((lt - 0.2) / 0.3), W / 2, H * 0.18)
        elif name == 'hundred':
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            n = int(clamp(lt / 1.5) * 100)
            for i in range(n):
                r_, c_ = divmod(i, 20); x = W * 0.17 + c_ * 66; y = H * 0.32 + r_ * 100
                d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=hexc('#5a4030')); d.rounded_rectangle([x - 18, y + 18, x + 18, y + 60], radius=10, fill=hexc('#5a4030'))
            pop(fr, bigtxt(f'{n} PEOPLE', 100), back(lt / 0.3), W / 2, H * 0.14)
            if lt > 1.8:
                k = back((lt - 1.8) / 0.3); x, y = W * 0.86, H * 0.86
                pop(fr, bubble('+ 1 ?', '#d24a3a', '#ffffff', 60), k, x, y)
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
