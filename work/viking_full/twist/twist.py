import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4', '/workspace/work/viking_full/day6', '/workspace/work/viking_full/day14', '/workspace/work/viking_full/day17', '/workspace/work/viking_full/day26', '/workspace/work/viking_full/day30'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from day30 import night, torches, close
from day26 import rock_img, on_rock
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day4 import stamp, bigtxt
from day14 import ULF_V
from PIL import Image, ImageDraw, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'j01': 0.6, 'n02': 0.8, 'u01': 0.7, 'n03': 0.8, 'n04': 1.2, 'n05': 0.6}
FIX = {'law': 'law', 'speaker': 'speaker'}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text'].replace('"', '')) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'j': 'J', 'u': 'U'}.get(lid[0], 'N'))
    t += d_
DUR = t + 3.0
hook.TL = TL; hook.LABELS = {'J': 'J A R L', 'U': 'U L F'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('title', 0.0), ('jarl', S_('n01') - 0.1), ('noaxe', S_('n02') - 0.3), ('lay', wt('n02', 5) - 0.1), ('ulf', S_('u01') - 0.4),
         ('law', wt('u01', 16) - 0.1), ('voice', S_('n03') - 0.3), ('morning', S_('n04') - 0.6), ('ship', S_('n05') - 0.3), ('end', TL['n05']['en'] + 0.6)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V

def axe_on_ground(d, x, y, s, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    L = 110 * s; x2, y2 = x + ca * L, y + sa * L * 0.35
    d.line([x, y, x2, y2], fill=hexc('#6b4a30'), width=int(8 * s))
    d.polygon([(x2, y2), (x2 + 26 * s, y2 - 18 * s), (x2 + 30 * s, y2 + 16 * s)], fill=hexc('#cfd6de'))

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set()
    tcard = title_card('THE FINAL', 'TWIST')
    ring = crowd(71, 2, 9, 4.8, 1.3, 4.4, exclude=lambda x, z: abs(x) < 1.4 and z < 5.6)
    rock = rock_img(); s_law = stamp('LAWSPEAKER', '#E9BC3F', 120)
    rnd = random.Random(9); AX = [(rnd.uniform(0.2, 0.8), rnd.uniform(0.72, 0.92), rnd.uniform(-0.6, 3.7)) for _ in range(46)]
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        if name == 'title':
            fr = fastblur(night(S, 1.04), 3.0); k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.3: k = 1 - ease((lt - (s1 - s0 - 0.3)) / 0.3)
            pop(fr, tcard, k, W / 2, H * 0.45)
        elif name == 'jarl':
            fr = close(S, t, Actor('viking', 0.3, 3.0, JARL_V, expr='happy', look=(-0.6, 0), seed=71, size=1.08), u)
            if t > S_('j01'): pop(fr, bigtxt('THE VOTE FOR YOU', 100, '#E9BC3F'), back((t - wt('j01', 1)) / 0.3), W * 0.27, H * 0.3)
        elif name in ('noaxe', 'lay'):
            fr = night(S, 1.05 + 0.03 * u)
            torches(fr, t, [W * 0.08, W * 0.3, W * 0.7, W * 0.92], H * 0.62)
            cam = dict(cx=0, cz=lerp(-0.6, 0.0, eio(u)), f=1500, hor=H * 0.55, h=1.4, focus=4.5, ap=0.4)
            acts = [Actor(a.kind, a.x, a.z, a.v, expr='happy' if name == 'lay' else 'neutral', look=(-a.x * 0.2, -0.2), seed=a.seed, size=a.size) for a in ring]
            acts.append(Actor('hero', 0.0, 3.6, HV, expr='worried' if name == 'noaxe' else 'happy', look=(0, 0), seed=90))
            render_world2(fr, acts, cam, t)
            if name == 'noaxe':
                pop(fr, bigtxt('0 AXES?', 130, '#cfd3da'), back((t - wt('n02', 1)) / 0.3), W / 2, H * 0.24)
            else:
                d = ImageDraw.Draw(fr); n = int(len(AX) * clamp((t - wt('n02', 9)) / 2.0))
                for fx, fy, ang in AX[:n]: axe_on_ground(d, W * fx, H * fy, 0.8, ang)
                if t > wt('n02', 16) - 0.1: pop(fr, bigtxt('AT YOUR FEET', 110, '#E9BC3F'), back((t - wt('n02', 16)) / 0.3), W / 2, H * 0.24)
                pop(fr, label_box('100 AXES ON THE GROUND', '#ffffff', '#3e6a3a'), back((t - wt('n02', 9)) / 0.35), W / 2, 110)
        elif name == 'ulf':
            fr = close(S, t, Actor('viking', 0.3, 3.0, ULF_V, expr='happy', look=(-0.4, 0), seed=97, size=1.08), u)
            pop(fr, name_pill('ULF', 'HOME AGAIN'), back(lt / 0.3), W * 0.27, H * 0.14)
            if t > wt('u01', 7) - 0.1: pop(fr, label_box('BRINGS JUSTICE', '#ffffff', '#3e6a3a'), back((t - wt('u01', 7)) / 0.3), W * 0.27, H * 0.3)
            if t > wt('u01', 12) - 0.1: pop(fr, label_box('NOT A GUEST', '#ffffff', '#d24a3a'), back((t - wt('u01', 12)) / 0.3), W * 0.27, H * 0.42)
        elif name == 'law':
            fr = night(S, 1.08)
            torches(fr, t, [W * 0.15, W * 0.85], H * 0.66)
            cam = dict(cx=0, cz=lerp(0.4, 0.9, eio(u)), f=1500, hor=H * 0.55, h=1.2, focus=3.0, ap=0.8)
            on_rock(fr, Actor('hero', 0.0, 3.1, HV, expr='happy', look=(0, 0), seed=90, pose='up'), cam, t, W / 2, H * 0.9, rock, 160)
            pop(fr, s_law, back((t - wt('u01', 19)) / 0.3), W / 2, H * 0.16)
        elif name == 'voice':
            pg = False
            fr = parchment(W, H)
            pop(fr, name_pill('DAY 1', 'STRANGER'), back(lt / 0.3), W * 0.28, H * 0.45)
            if t > wt('n03', 7) - 0.1:
                p = ease((t - wt('n03', 7)) / 0.8)
                pop(fr, bigtxt(f'DAY {int(lerp(1, 30, p))}', 120, '#d24a3a'), 1.0, W / 2, H * 0.25)
                pop(fr, bigtxt('>>>', 120, '#5a4030'), 1.0, W / 2, H * 0.47)
            if t > wt('n03', 12) - 0.1: pop(fr, name_pill('DAY 30', 'VOICE OF THE LAW'), back((t - wt('n03', 12)) / 0.3), W * 0.72, H * 0.45)
        elif name in ('morning', 'ship', 'end'):
            z = {'morning': 1.02, 'ship': lerp(1.05, 1.35, eio(u)), 'end': 1.35}[name]
            fr = cam_bg(S['beach'], z, 0, 0)
            bx = W * 0.62 + (lt * 6 if name == 'morning' else 0)
            b = boat_img(t, 0.12 if name == 'morning' else lerp(0.12, 0.2, eio(u)) if name == 'ship' else 0.2)
            paste_safe(fr, b, bx - b.width / 2, H * 0.47 - b.height * 0.8)
            if name == 'morning':
                pop(fr, label_box('DAY 31', '#ffffff', '#6f7cff'), back((t - wt('n04', 4)) / 0.35), W / 2, 110)
                if t > wt('n04', 7) - 0.1: pop(fr, label_box('A BOAT!', '#ffffff', '#d24a3a'), back((t - wt('n04', 7)) / 0.3), bx, H * 0.3)
            elif name == 'ship':
                pop(fr, bigtxt('FIRST SHIP IN 10 YEARS', 90), back((t - wt('n05', 2)) / 0.3), W / 2, H * 0.2)
                if t > wt('n05', 12) - 0.1: pop(fr, bigtxt('HOME?', 160, '#E9BC3F'), back((t - wt('n05', 12)) / 0.3), W / 2, H * 0.7)
            else:
                fr = tint(fr, (10, 10, 30), clamp(lt / 1.5) * 0.5)
                pop(fr, bigtxt('STAY... OR GO?', 130, '#ffffff'), back((lt - 0.3) / 0.3), W / 2, H * 0.4)
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
