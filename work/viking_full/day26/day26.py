import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4', '/workspace/work/viking_full/day6', '/workspace/work/viking_full/day14', '/workspace/work/viking_full/day17'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day4 import stamp, bigtxt
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'n02': 0.6, 'n03': 0.4, 'n04': 0.6, 'n05': 0.6, 'h01': 0.4, 'n06': 0.6, 'n07': 0.5, 'n08': 0.5}
FIX = {'Gunner,': 'Gunnar,', 'Gunner': 'Gunnar'}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], FIX.get(w['text'], w['text']).replace('"', '')) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk='H' if lid[0] == 'h' else 'N')
    t += d_
DUR = t + 2.8
hook.TL = TL; hook.LABELS = {'H': 'H A K O N'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('thing', wt('n01', 2) - 0.1), ('history', S_('n02') - 0.3), ('lawspeaker', S_('n03') - 0.3),
         ('rock', S_('n04') - 0.4), ('smile', S_('n05') - 0.4), ('hakon', S_('h01') - 0.3), ('forty', S_('n06') - 0.4),
         ('silver', wt('n06', 10) - 0.1), ('axes', S_('n07') - 0.4), ('lost', S_('n08') - 0.3), ('end', TL['n08']['en'] + 0.6)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V
OLD_V = V(coat='#5a5f7a', coat_dk='#454a62', hair='#e8e8e8', beard='#e8e8e8', rim='#F2A26A')

def rock_img(w=520, h=200):
    im = Image.new('RGBA', (w, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(20, h + 30), (60, 40), (180, 10), (360, 0), (470, 30), (w - 10, h + 30)], fill=hexc('#6f7380'))
    d.polygon([(60, 40), (180, 10), (360, 0), (470, 30), (440, 60), (90, 70)], fill=hexc('#8e93a0'))
    return im

def coin(d, x, y, r):
    d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=hexc('#d9dde4'), outline=hexc('#8a909c'), width=3)

def on_rock(fr, actor, cam, t, rx, ry, rock, lift):
    paste_safe(fr, rock, rx - rock.width / 2, ry - rock.height + 30)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); render_world2(lay, [actor], cam, t)
    fr.alpha_composite(lay, (0, -int(lift)))

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set()
    dcard = title_card('DAY 26', 'THE THING')
    ring = crowd(61, 2, 9, 4.6, 1.3, 4.2, exclude=lambda x, z: abs(x) < 1.3 and z < 5.4)
    back_c = crowd(62, 2, 8, 4.4, 1.1, 3.2, expr_choices=('angry', 'happy', 'angry'))
    rock = rock_img(); rock_s = rock_img(380, 140)
    s_nothing = stamp('MEANS NOTHING', '#d24a3a', 100); s_lost = stamp('VOTE LOST', '#d24a3a', 130)
    cards = {9 + 1: ('THE FIRE', '#d24a3a'), 11: ('GUNNAR', '#2f4e6e'), 13: ('THE POISON', '#3e6a3a'), 15: ('THE RUNES', '#8a6a3a')}
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
        elif name in ('thing', 'rock'):
            fr = cam_bg(S['village'], 1.05 + 0.03 * u, 0, -20)
            cam = dict(cx=0, cz=lerp(-1.0, -0.2, eio(u)) if name == 'thing' else lerp(0.3, 0.9, eio(u)), f=1500, hor=H * 0.55, h=1.3, focus=4.5, ap=0.5)
            acts = [Actor(a.kind, a.x, a.z, a.v, expr='neutral' if name == 'thing' else 'worried', look=(-a.x * 0.2, -0.2), seed=a.seed, size=a.size) for a in ring]
            render_world2(fr, acts, cam, t)
            if name == 'thing':
                paste_safe(fr, rock_s, W / 2 - rock_s.width / 2, H * 0.62 - rock_s.height + 30)
                pop(fr, label_box('THE THING = VIKING ASSEMBLY', '#ffffff', '#6f7cff'), back((lt - 0.3) / 0.35), W / 2, 110)
                if t > wt('n01', 12) - 0.1: pop(fr, bigtxt('IN FRONT OF EVERYONE', 80), back((t - wt('n01', 12)) / 0.3), W / 2, H * 0.3)
            else:
                on_rock(fr, Actor('hero', 0.0, 3.1, HV, expr='angry', look=(0, 0), seed=90, pose='up' if t > wt('n04', 8) else 'down'), cam, t, W / 2, H * 0.86, rock, 150)
                ks = sorted(cards)
                for j, wi in enumerate(ks):
                    if t > wt('n04', wi) - 0.1:
                        txt, col = cards[wi]; x = W * (0.2 + 0.2 * j)
                        pop(fr, label_box(txt, '#ffffff', col), back((t - wt('n04', wi)) / 0.3), x, H * 0.16)
        elif name == 'history':
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            pop(fr, label_box('REAL HISTORY', '#ffffff', '#1b1a2a'), back(lt / 0.3), W / 2, 110)
            pop(fr, bigtxt('ICELAND: THE ALTHING', 90, '#2f4e6e'), back((t - wt('n02', 3)) / 0.3), W / 2, H * 0.3)
            if t > wt('n02', 10) - 0.2:
                p = ease((t - wt('n02', 10)) / 0.9); yr = int(lerp(1, 930, p))
                pop(fr, bigtxt(f'YEAR {yr}', 200, '#d24a3a'), 1.0, W / 2, H * 0.52)
            if t > wt('n02', 18) - 0.1:
                pop(fr, label_box('ONE OF THE OLDEST PARLIAMENTS', '#ffffff', '#3e6a3a'), back((t - wt('n02', 18)) / 0.35), W / 2, H * 0.74)
        elif name == 'lawspeaker':
            fr = cam_bg(S['village'], 1.12, 0, -40); fr = tint(fr, (90, 70, 50), 0.35)
            cam = dict(cx=0, cz=lerp(0.6, 1.0, eio(u)), f=1500, hor=H * 0.55, h=1.2, focus=3.0, ap=0.8)
            on_rock(fr, Actor('viking', 0.0, 3.0, OLD_V, expr='neutral', look=(0, 0), seed=66, pose='up'), cam, t, W / 2, H * 0.9, rock, 160)
            pop(fr, name_pill('LAWSPEAKER', 'LÖGSÖGUMAÐR'), back((lt - 0.2) / 0.3), W / 2, H * 0.12)
            if t > wt('n03', 9) - 0.1: pop(fr, label_box('THE LAW FROM MEMORY', '#ffffff', '#8a6a3a'), back((t - wt('n03', 9)) / 0.35), W * 0.78, H * 0.4)
        elif name in ('smile', 'hakon'):
            fr = cam_bg(S['village'], 1.15, 0, -60); fr = fastblur(fr, 2.4)
            cam = dict(cx=0.25, cz=lerp(1.0, 1.35, eio(u)) if name == 'smile' else 1.2, f=1500, hor=H * 0.5, h=0.95, focus=2.0, ap=1.2)
            render_world2(fr, [Actor('viking', 0.3, 3.0, HAKON_V, expr='happy', look=(-0.4, 0), seed=75, size=1.08)], cam, t)
            if name == 'smile': pop(fr, bigtxt('...SMILES', 110, '#E9BC3F'), back((lt - 0.5) / 0.3), W * 0.27, H * 0.3)
            else:
                pop(fr, name_pill('HAKON', 'JARL\'S SON'), back(lt / 0.3), W * 0.27, H * 0.14)
                if t > wt('h01', 4) - 0.1: pop(fr, label_box('OUTLAW = NOTHING', '#ffffff', '#d24a3a'), back((t - wt('h01', 4)) / 0.3), W * 0.27, H * 0.32)
                if t > wt('h01', 15) - 0.1: pop(fr, label_box('FOREIGN WOMAN = LESS', '#ffffff', '#d24a3a'), back((t - wt('h01', 15)) / 0.3), W * 0.27, H * 0.46)
        elif name in ('forty', 'axes'):
            fr = cam_bg(S['village'], 1.06, 0, -20); fr = tint(fr, (40, 10, 10), 0.3 if name == 'forty' else 0.5)
            cam = dict(cx=0, cz=lerp(0.0, 0.4, eio(u)), f=1500, hor=H * 0.55, h=1.3, focus=3.6, ap=0.6)
            kshow = ease((t - wt('n06', 1)) / 1.2) if name == 'forty' else 1
            nshow = int(len(back_c) * kshow)
            up = name == 'axes' and t > wt('n07', 6) - 0.1
            acts = [Actor(a.kind, a.x * 0.7 - 1.6, a.z, a.v, expr='angry' if name == 'forty' else 'happy', look=(0.3, 0), seed=a.seed, size=a.size, pose='up' if up else 'down', bob=1.0 if up else 0) for a in back_c[:nshow]]
            acts.append(Actor('viking', -1.2, 3.3, HAKON_V, expr='happy', look=(1, 0), seed=75, size=1.05))
            acts.append(Actor('hero', 1.15, 3.0, HV, expr='worried', look=(-1, 0), seed=90))
            render_world2(fr, acts, cam, t)
            if name == 'forty':
                pop(fr, bigtxt(f'{int(lerp(0, 40, kshow))} WARRIORS', 120, '#ff6a5a'), back((t - wt('n06', 1)) / 0.3), W * 0.35, H * 0.14)
            else:
                pop(fr, label_box('YOU', '#ffffff', '#E5453A'), back(lt / 0.3), W * 0.74, H * 0.3)
                if up: pop(fr, bigtxt('40 AXES... FOR HAKON', 100, '#ff6a5a'), back((t - wt('n07', 6)) / 0.3), W * 0.38, H * 0.14)
        elif name == 'silver':
            fr = cam_bg(S['village'], 1.1, 0, -30); fr = tint(fr, (20, 15, 10), 0.55); d = ImageDraw.Draw(fr)
            rnd = random.Random(5)
            for i in range(60):
                x = rnd.uniform(W * 0.1, W * 0.9); sp = rnd.uniform(500, 900); y0 = rnd.uniform(-800, 0)
                y = min(y0 + lt * sp, H * 0.8 + rnd.uniform(-60, 60)); coin(d, x, y, rnd.uniform(18, 30))
            fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.75, 600, 220, '#e8eef8', 110))
            pop(fr, bigtxt('BOUGHT WITH SILVER', 110, '#e8eef8'), back((t - wt('n06', 15)) / 0.3), W / 2, H * 0.25)
            if t > wt('n06', 17) - 0.1: pop(fr, label_box('FOR YEARS', '#ffffff', '#1b1a2a'), back((t - wt('n06', 17)) / 0.3), W / 2, H * 0.4)
        elif name in ('lost', 'end'):
            fr = cam_bg(S['village'], 1.0, 0, -10); fr = tint(fr, (10, 10, 25), 0.55 if name == 'lost' else 0.75)
            cam = dict(cx=0, cz=lerp(-0.6, -1.4, eio(u)) if name == 'lost' else -1.4, f=1500, hor=H * 0.55, h=1.4, focus=4.0, ap=0.3)
            acts = [Actor(a.kind, a.x * 0.8 - 1.4, a.z, a.v, expr='happy', look=(0.3, 0), seed=a.seed, size=a.size, pose='up', bob=1.0) for a in back_c]
            acts.append(Actor('hero', 2.4, 3.2, HV, expr='sad', look=(0, 0), seed=90))
            render_world2(fr, acts, cam, t)
            if name == 'lost': pop(fr, s_lost, back((t - S_('n08') - 0.6) / 0.3), W / 2, H * 0.3)
            else:
                pop(fr, s_lost, 1.0, W / 2, H * 0.3)
                pop(fr, label_box('THE VOTE: DAY 30', '#ffffff', '#d24a3a'), back((lt - 0.4) / 0.3), W / 2, H * 0.48)
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
