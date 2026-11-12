import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4', '/workspace/work/viking_full/day6', '/workspace/work/viking_full/day14', '/workspace/work/viking_full/day17'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from day6 import TOR_V
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day4 import stamp, bigtxt
from day14 import ULF_V, snowfall
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'j01': 0.6, 'n02': 0.5, 'y01': 0.4, 'n03': 1.0, 'h01': 0.4, 'n04': 0.7, 't01': 0.5, 'n05': 0.6, 'n06': 0.6, 'n07': 0.6, 'j02': 1.0, 'n08': 0.6, 'n09': 1.0}
FIX = {"Haakon's": "Hakon's", 'Håkon': 'Hakon'}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], FIX.get(w['text'], w['text']).replace('"', '')) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'j': 'J', 'y': 'Y', 'h': 'H', 't': 'T'}.get(lid[0], 'N'))
    t += d_
DUR = t + 3.0
hook.TL = TL; hook.LABELS = {'J': 'J A R L', 'Y': 'Y O U', 'H': 'H A K O N', 'T': 'T O R S T E I N'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('cliff', wt('n01', 2) - 0.1), ('jarl', S_('j01') - 0.4), ('you', S_('n02') - 0.3),
         ('silence', S_('n03') - 0.3), ('hakon', wt('n03', 1) - 0.1), ('torstein', S_('n04') - 0.4), ('tline', S_('t01') - 0.3),
         ('fall', S_('n05') - 0.3), ('two', S_('n06') - 0.4), ('look', S_('n07') - 0.3), ('raise', wt('n07', 11) - 0.1),
         ('ulf', S_('n08') - 0.5), ('sentence', S_('n09') - 0.4), ('end', TL['n09']['en'] + 0.6)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V

def night(S, z=1.06, cz_shift=-20):
    fr = cam_bg(S['village'], z, 0, cz_shift); fr = tint(fr, (8, 10, 30), 0.68)
    return fr

def torches(fr, t, xs, y):
    d = ImageDraw.Draw(fr)
    for i, x in enumerate(xs):
        fr.alpha_composite(glow(W, H, x, y - 60, 160, 160, '#ff9f3a', 140))
        d = ImageDraw.Draw(fr); d.line([x, y, x, y - 90], fill=hexc('#4a3420'), width=8)
        fl = 34 + 8 * math.sin(t * 11 + i); d.polygon([(x - 14, y - 90), (x, y - 90 - fl), (x + 14, y - 90)], fill=hexc('#ffb33a'))

def close(S, t, actor, u, side=0.3, z0=1.0, z1=1.3):
    fr = night(S, 1.15, -60); fr = fastblur(fr, 2.4)
    fr.alpha_composite(glow(W, H, W * (0.85 if side > 0 else 0.15), H * 0.4, 400, 400, '#ff9f3a', 90))
    cam = dict(cx=side, cz=lerp(z0, z1, eio(u)), f=1500, hor=H * 0.5, h=0.95, focus=2.0, ap=1.2)
    render_world2(fr, [actor], cam, t)
    return fr

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set()
    dcard = title_card('DAY 30', 'THE VOTE')
    ring = crowd(71, 2, 9, 4.8, 1.3, 4.4, exclude=lambda x, z: abs(x) < 1.4 and z < 5.6)
    forty = crowd(72, 2, 7, 4.4, 1.1, 2.8, expr_choices=('angry', 'neutral', 'angry'))
    order = list(range(len(forty))); random.Random(3).shuffle(order)
    s_home = stamp('ULF IS HOME', '#3e6a3a', 120); s_out = stamp('OUTLAW', '#d24a3a', 140)
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        if name == 'daycard':
            fr = fastblur(night(S, 1.04 + 0.02 * u), 3.0)
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name in ('cliff', 'silence'):
            fr = night(S, 1.05 + 0.03 * u)
            torches(fr, t, [W * 0.08, W * 0.3, W * 0.7, W * 0.92], H * 0.62)
            cam = dict(cx=0, cz=lerp(-1.2, -0.4, eio(u)) if name == 'cliff' else -0.2, f=1500, hor=H * 0.55, h=1.4, focus=4.5, ap=0.4)
            acts = [Actor(a.kind, a.x, a.z, a.v, expr='neutral', look=(-a.x * 0.2, -0.2), seed=a.seed, size=a.size) for a in ring]
            acts.append(Actor('hero', 0.0, 3.6, HV, expr='worried' if name == 'cliff' else 'angry', look=(0, 0), seed=90))
            render_world2(fr, acts, cam, t)
            if name == 'cliff':
                pop(fr, label_box('THE LAST NIGHT', '#ffffff', '#d24a3a'), back((t - wt('n01', 3)) / 0.35), W / 2, 110)
                if t > wt('n01', 12) - 0.2:
                    p = ease((t - wt('n01', 12)) / 0.8); pop(fr, bigtxt(f'{int(lerp(1, 100, p))} VIKINGS', 120, '#E9BC3F'), 1.0, W / 2, H * 0.26)
            else:
                pop(fr, bigtxt('SILENCE...', 120, '#cfd3da'), back((lt - 0.2) / 0.3), W / 2, H * 0.24)
        elif name == 'jarl':
            fr = close(S, t, Actor('viking', 0.3, 3.0, JARL_V, expr='neutral', look=(-0.4, 0), seed=71, size=1.08), u)
            pop(fr, name_pill('JARL', 'THE VOTE'), back(lt / 0.3), W * 0.27, H * 0.14)
            if t > wt('j01', 5) - 0.1: pop(fr, label_box('ASK TO STAY', '#ffffff', '#3e6a3a'), back((t - wt('j01', 5)) / 0.3), W * 0.27, H * 0.3)
        elif name == 'you':
            fr = close(S, t, Actor('hero', -0.3, 3.0, HV, expr='angry' if t > S_('y01') else 'neutral', look=(0.4, 0), seed=90, size=1.05), u, -0.3)
            if t < S_('y01'): pop(fr, bigtxt("YOU DON'T.", 110), back((t - wt('n02', 1)) / 0.3), W * 0.72, H * 0.28)
            else: pop(fr, bubble('BRING ULF HOME', '#ffffff', '#E5453A', 60), back((t - wt('y01', 6)) / 0.3), W * 0.72, H * 0.25)
        elif name == 'hakon':
            fr = close(S, t, Actor('viking', 0.3, 3.0, HAKON_V, expr='happy', look=(-0.4, 0), seed=75, size=1.08, bob=1.0 if t < S_('h01') else 0), u)
            if t < S_('h01'): pop(fr, bigtxt('HA HA HA', 110, '#E9BC3F'), back(lt / 0.3), W * 0.27, H * 0.3)
            else: pop(fr, bigtxt('40 AXES SAY NO', 100, '#ff6a5a'), back((t - S_('h01') - 0.2) / 0.3), W * 0.27, H * 0.3)
        elif name in ('torstein', 'fall', 'two'):
            fr = night(S, 1.06)
            torches(fr, t, [W * 0.06, W * 0.94], H * 0.62)
            cam = dict(cx=0, cz=lerp(0.0, 0.3, eio(u)), f=1500, hor=H * 0.55, h=1.3, focus=3.6, ap=0.6)
            if name == 'torstein': nup = 0
            elif name == 'fall':
                k1 = wt('n05', 1); k2 = wt('n05', 18) + 0.4
                nup = 1 + int(clamp((t - k1) / (k2 - k1)) * (len(forty) - 1)) if t > k1 - 0.1 else 0
            else: nup = len(forty)
            ups = set(order[:nup])
            acts = []
            for i, a in enumerate(forty):
                up = i in ups
                acts.append(Actor(a.kind, a.x * 0.75 - 1.2, a.z, a.v, expr='happy' if up else 'angry', look=(0.3, 0), seed=a.seed, size=a.size, pose='up' if up else 'down', bob=1.0 if up else 0))
            if name == 'torstein':
                tx = lerp(-0.6, 0.6, ease(u * 1.4)); tup = False
            else:
                tx = 0.6; tup = True
            acts.append(Actor('viking', tx, 3.2, TOR_V, expr='angry' if not tup else 'happy', look=(-1, 0), seed=311, size=1.25, pose='up' if tup else 'down'))
            acts.append(Actor('viking', -1.1, 2.7, HAKON_V, expr='angry' if name != 'torstein' else 'happy', look=(1, 0), seed=75, size=1.05))
            if name == 'two': acts.append(Actor('viking', -0.3, 2.7, JARL_V, expr='sad', look=(1, 0), seed=71, size=1.05))
            acts.append(Actor('hero', 1.3, 3.0, HV, expr='happy' if name != 'torstein' else 'worried', look=(-1, 0), seed=90))
            render_world2(fr, acts, cam, t)
            if name == 'torstein':
                pop(fr, name_pill('TORSTEIN', 'DIED AT THE FEAST'), back((t - wt('n04', 1)) / 0.3), W / 2, H * 0.14)
                if t > wt('n04', 15) - 0.1: pop(fr, label_box('...AND CAME BACK', '#ffffff', '#3e6a3a'), back((t - wt('n04', 15)) / 0.3), W / 2, H * 0.28)
            elif name == 'fall':
                if t > wt('n05', 1) - 0.1:
                    pop(fr, bigtxt(f"HAKON'S MEN: {40 - int(40 * nup / len(forty))}", 100, '#ff6a5a'), 1.0, W / 2, H * 0.14)
                if t > wt('n05', 17) - 0.1: pop(fr, label_box('FALLING APART', '#ffffff', '#d24a3a'), back((t - wt('n05', 17)) / 0.3), W / 2, H * 0.28)
            else:
                pop(fr, bigtxt('2 AXES STILL DOWN', 100, '#ff6a5a'), back((t - wt('n06', 2)) / 0.3), W / 2, H * 0.14)
                if t > wt('n06', 7) - 0.1: pop(fr, label_box('HAKON', '#ffffff', '#d24a3a'), back((t - wt('n06', 7)) / 0.3), W * 0.4, H * 0.3)
                if t > wt('n06', 10) - 0.1: pop(fr, label_box('HIS FATHER', '#ffffff', '#d24a3a'), back((t - wt('n06', 10)) / 0.3), W * 0.5, H * 0.38)
        elif name == 'tline':
            fr = close(S, t, Actor('viking', 0.3, 3.0, TOR_V, expr='angry', look=(-0.4, 0), seed=311, size=1.2), u)
            if t > wt('t01', 7) - 0.1: pop(fr, label_box("HAKON'S PLATE", '#ffffff', '#d24a3a'), back((t - wt('t01', 7)) / 0.3), W * 0.27, H * 0.24)
            if t > wt('t01', 13) - 0.1: pop(fr, bigtxt('SHE BROUGHT ME BACK', 60, '#7fe0a0'), back((t - wt('t01', 13)) / 0.3), W * 0.22, H * 0.38)
        elif name in ('look', 'raise'):
            up = name == 'raise' and t > wt('n07', 13) - 0.1
            fr = close(S, t, Actor('viking', 0.3, 3.0, JARL_V, expr='sad' if not up else 'neutral', look=(-0.6, 0), seed=71, size=1.08, pose='up' if up else 'down'),
                       u, 0.3, 1.1 if name == 'look' else 1.0, 1.45 if name == 'look' else 1.0)
            if name == 'look': pop(fr, label_box('A VERY LONG TIME...', '#ffffff', '#1b1a2a'), back((t - wt('n07', 8)) / 0.35), W * 0.27, H * 0.2)
            else:
                if up: pop(fr, bigtxt('THE JARL VOTES', 100, '#E9BC3F'), back((t - wt('n07', 13)) / 0.3), W * 0.27, H * 0.22)
                if t > S_('j02'): pop(fr, bubble('BROTHER. COME HOME.', '#ffffff', '#7A3B2E', 50), back((t - S_('j02')) / 0.3), W * 0.27, H * 0.4)
        elif name == 'ulf':
            fr = night(S, 1.05)
            torches(fr, t, [W * 0.08, W * 0.3, W * 0.7, W * 0.92], H * 0.62)
            cam = dict(cx=0, cz=lerp(-0.8, -0.3, eio(u)), f=1500, hor=H * 0.55, h=1.4, focus=4.0, ap=0.4)
            roar = t > wt('n08', 9) - 0.1
            acts = [Actor(a.kind, a.x, a.z, a.v, expr='happy', look=(0, -0.2), seed=a.seed, size=a.size, pose='up', bob=1.0 if roar else 0.3) for a in ring]
            acts.append(Actor('viking', lerp(-3.4, -0.6, ease(u * 1.3)), 3.6, ULF_V, expr='happy', look=(1, 0), seed=97, bob=1.0))
            acts.append(Actor('viking', 0.6, 3.6, JARL_V, expr='happy', look=(-1, 0), seed=71))
            acts.append(Actor('hero', 1.5, 3.4, HV, expr='happy', look=(-1, 0), seed=90))
            render_world2(fr, acts, cam, t)
            if roar:
                fr = shake(fr, 6 * (1 - clamp((t - wt('n08', 9)) / 0.8)), t)
                pop(fr, s_home, back((t - wt('n08', 10)) / 0.3), W / 2, H * 0.2)
        elif name in ('sentence', 'end'):
            fr = cam_bg(S['village'], 1.1, 0, -20); fr = tint(fr, (20, 30, 50), 0.7)
            d = ImageDraw.Draw(fr); rnd = random.Random(8)
            for i in range(14):
                x = rnd.uniform(0, W); h = rnd.uniform(380, 620); y = H * 0.75
                d.polygon([(x - 90, y), (x, y - h), (x + 90, y)], fill=hexc('#1c2a24'))
            snowfall(fr, t)
            cam = dict(cx=0, cz=lerp(0.3, 0.0, eio(u)), f=1500, hor=H * 0.58, h=1.2, focus=3.4, ap=0.6)
            render_world2(fr, [Actor('viking', lerp(0.6, -0.4, ease(u)) if name == 'sentence' else -0.4, 3.4, HAKON_V, expr='sad', look=(-1, 0), seed=75, size=1.0, bob=1.0 if name == 'sentence' else 0)], cam, t)
            if name == 'sentence':
                pop(fr, label_box('THE SAME SENTENCE', '#ffffff', '#1b1a2a'), back((t - wt('n09', 3)) / 0.3), W / 2, 110)
                if t > wt('n09', 9) - 0.1: pop(fr, s_out, back((t - wt('n09', 9)) / 0.3), W / 2, H * 0.3)
            else:
                pop(fr, s_out, 1.0, W / 2, H * 0.3)
                pop(fr, label_box('BUT THE STORY IS NOT OVER...', '#ffffff', '#6f7cff'), back((lt - 0.5) / 0.35), W / 2, H * 0.48)
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
