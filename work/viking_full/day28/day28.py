import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4', '/workspace/work/viking_full/day6', '/workspace/work/viking_full/day14', '/workspace/work/viking_full/day17'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day4 import stamp, bigtxt
from day14 import ULF_V, flames
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'j01': 0.8, 'n02': 0.6, 'j02': 0.6, 'y01': 0.7, 'j03': 1.8, 'n03': 0.7, 'j04': 0.8}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text'].replace('"', '')) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'j': 'J', 'y': 'Y'}.get(lid[0], 'N'))
    t += d_
DUR = t + 2.8
hook.TL = TL; hook.LABELS = {'J': 'J A R L', 'Y': 'Y O U'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('arrive', wt('n01', 2) - 0.1), ('knew', S_('j01') - 0.4), ('flash', S_('n02') - 0.3),
         ('choice', S_('j02') - 0.3), ('years', wt('j02', 14) - 0.1), ('ask', S_('y01') - 0.3), ('pause', TL['y01']['en'] + 0.3),
         ('old', S_('n03') - 0.3), ('two', S_('j04') - 0.4), ('cannot', wt('j04', 8) - 0.1), ('end', TL['j04']['en'] + 0.6)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V

def candle(fr, t, cx, cy, s=1.0):
    fr.alpha_composite(glow(W, H, cx, cy, 380 * s, 320 * s, '#ffb35a', 150))
    d = ImageDraw.Draw(fr)
    d.rectangle([cx - 14 * s, cy, cx + 14 * s, cy + 90 * s], fill=hexc('#efe4cc'))
    fl = (30 + 6 * math.sin(t * 13)) * s; d.polygon([(cx - 12 * s, cy), (cx, cy - fl), (cx + 12 * s, cy)], fill=hexc('#ffd25a'))

def interior(S, z=1.1):
    fr = cam_bg(S['village'], z, 0, -30); fr = tint(fr, (25, 15, 10), 0.8); fr = fastblur(fr, 3.0)
    d = ImageDraw.Draw(fr)
    for i in range(9): d.rectangle([i * W / 8 - 8, 0, i * W / 8 + 8, H], fill=(40, 26, 16, 255))
    return fr

def close(S, t, actor, u, side=0.3, z0=1.0, z1=1.3):
    fr = interior(S, 1.15)
    cam = dict(cx=side, cz=lerp(z0, z1, eio(u)), f=1500, hor=H * 0.5, h=0.95, focus=2.0, ap=1.2)
    render_world2(fr, [actor], cam, t)
    candle(fr, t, W * (0.85 if side > 0 else 0.15), H * 0.72, 0.8)
    return fr

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set()
    dcard = title_card('DAY 28', 'THE FATHER')
    s_knew = stamp('HE KNEW', '#d24a3a', 120)
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    jarl = lambda ex, lk=(-0.4, 0): Actor('viking', 0.3, 3.0, JARL_V, expr=ex, look=lk, seed=71, size=1.08)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        if name == 'daycard':
            fr = fastblur(tint(cam_bg(S['village'], 1.04 + 0.02 * u, 0, -20), (5, 8, 30), 0.7), 3.0)
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name == 'arrive':
            fr = cam_bg(S['village'], 1.06 + 0.03 * u, 0, -20); fr = tint(fr, (5, 8, 30), 0.72)
            cam = dict(cx=0, cz=lerp(-0.4, 0.2, eio(u)), f=1500, hor=H * 0.58, h=1.2, focus=3.6, ap=0.4)
            x = lerp(-2.6, -0.4, ease(u * 1.1))
            render_world2(fr, [Actor('viking', x, 3.6, JARL_V, expr='sad', look=(1, 0), seed=71, bob=1.0)], cam, t)
            p = cam_project(cam, x, 3.6) if 'cam_project' in globals() else None
            fr.alpha_composite(glow(W, H, W / 2 + (x * 300), H * 0.62, 200, 200, '#ffb35a', 120))
            pop(fr, label_box('MIDNIGHT', '#ffffff', '#6f7cff'), back((lt - 0.2) / 0.35), W / 2, 110)
            if t > wt('n01', 8) - 0.1: pop(fr, bigtxt('ALONE', 120), back((t - wt('n01', 8)) / 0.3), W / 2, H * 0.25)
        elif name == 'knew':
            fr = close(S, t, jarl('sad'), u)
            pop(fr, name_pill('JARL', 'YOUR HUT'), back(lt / 0.3), W * 0.27, H * 0.14)
            if t > S_('j01') + 0.2: pop(fr, bigtxt('"I KNEW."', 140, '#ffffff'), back((t - S_('j01') - 0.2) / 0.3), W * 0.27, H * 0.35)
        elif name == 'flash':
            fr = cam_bg(S['village'], 1.08, 0, -20); fr = tint(fr, (30, 20, 15), 0.55)
            flames(fr, t, W * 0.62, H * 0.66, 0.8)
            cam = dict(cx=0, cz=lerp(0.4, 0.7, eio(u)), f=1500, hor=H * 0.6, h=1.2, focus=3.2, ap=0.6)
            render_world2(fr, [Actor('viking', -0.9, 3.3, JARL_V, expr='worried', look=(1, 0), seed=71),
                               Actor('viking', 0.4, 3.6, HAKON_V, expr='worried', look=(-1, 0), seed=75, size=0.85)], cam, t)
            fr = tint(fr, (110, 80, 45), 0.25)
            pop(fr, label_box('FLASHBACK: THE FIRST NIGHT', '#ffffff', '#8a6a3a'), back(lt / 0.35), W / 2, 110)
            if t > wt('n02', 1) - 0.1: pop(fr, s_knew, back((t - wt('n02', 1)) / 0.3), W * 0.3, H * 0.3)
        elif name == 'choice':
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            pop(fr, label_box("THE JARL'S CHOICE", '#ffffff', '#1b1a2a'), back(lt / 0.3), W / 2, 110)
            pop(fr, name_pill('HAKON', 'ONLY SON'), back((t - wt('j02', 3)) / 0.3), W * 0.28, H * 0.42)
            if t > wt('j02', 3) + 0.3: pop(fr, label_box('PROTECTED', '#ffffff', '#3e6a3a'), back((t - wt('j02', 3) - 0.3) / 0.3), W * 0.28, H * 0.58)
            if t > wt('j02', 8) - 0.1:
                k = ease((t - wt('j02', 12)) / 0.8)
                pop(fr, name_pill('ULF', 'BROTHER'), back((t - wt('j02', 8)) / 0.3), lerp(W * 0.72, W * 0.82, k), lerp(H * 0.42, H * 0.7, k))
            if t > wt('j02', 12) - 0.1: pop(fr, label_box('SENT TO THE FOREST', '#ffffff', '#d24a3a'), back((t - wt('j02', 12)) / 0.3), W * 0.62, H * 0.52)
            d.line([W / 2, H * 0.3, W / 2, H * 0.8], fill=hexc('#5a4030'), width=6)
        elif name == 'years':
            fr = close(S, t, jarl('sad', (-0.2, 0.4)), u, 0.3, 1.2, 1.4)
            p = ease((t - wt('j02', 19)) / 0.6) if t > wt('j02', 19) - 0.1 else 0
            if p: pop(fr, bigtxt(f'{int(lerp(1, 10, p))} YEARS', 140, '#E9BC3F'), 1.0, W * 0.27, H * 0.3)
        elif name == 'ask':
            fr = close(S, t, Actor('hero', -0.3, 3.0, HV, expr='worried', look=(0.4, 0), seed=90, size=1.05), u, -0.3)
            pop(fr, bubble('AND GUNNAR?', '#ffffff', '#E5453A', 56), back((lt - 0.2) / 0.3), W * 0.72, H * 0.25)
        elif name == 'pause':
            fr = close(S, t, jarl('worried', (-0.2, 0.3)), u, 0.3, 1.25, 1.55)
            if t < S_('j03'): pop(fr, bigtxt('...', 160), back((lt - 0.3) / 0.3), W * 0.27, H * 0.3)
            else: pop(fr, label_box('HE DID NOT KNOW', '#ffffff', '#2f4e6e'), back((t - S_('j03') - 0.6) / 0.3), W * 0.27, H * 0.3)
        elif name == 'old':
            fr = close(S, t, jarl('sad', (0, 0.5)), u, 0.3, 1.0, 0.8)
            k = ease(lt / 1.0)
            fr = Image.blend(fr, ImageEnhance.Color(fr.convert('RGB')).enhance(0.15).convert('RGBA'), k)
            pop(fr, bigtxt('100 YEARS OLD', 120, '#cfd3da'), back((t - S_('n03') - 0.5) / 0.3), W * 0.27, H * 0.3)
        elif name in ('two', 'cannot'):
            fr = interior(S, 1.08 + 0.03 * u)
            cam = dict(cx=0, cz=lerp(0.4, 0.7, eio(u)), f=1500, hor=H * 0.55, h=1.1, focus=3.0, ap=0.8)
            render_world2(fr, [Actor('viking', -0.8, 3.2, JARL_V, expr='sad', look=(1, 0), seed=71, size=1.05),
                               Actor('hero', 0.9, 3.2, HV, expr='sad' if name == 'cannot' else 'worried', look=(-1, 0), seed=90)], cam, t)
            candle(fr, t, W / 2, H * 0.74, 0.9)
            if name == 'two':
                pop(fr, label_box('2 NIGHTS LEFT', '#ffffff', '#d24a3a'), back((t - wt('j04', 1)) / 0.3), W / 2, 110)
                if t > wt('j04', 5) - 0.1: pop(fr, bigtxt('YOU WILL LOSE', 110, '#ff6a5a'), back((t - wt('j04', 5)) / 0.3), W / 2, H * 0.26)
            else:
                pop(fr, bigtxt('"I CANNOT SAVE YOU"', 100), back(lt / 0.3), W / 2, H * 0.2)
                if t > wt('j04', 16) - 0.1: pop(fr, label_box('NOT EVEN HIS BROTHER', '#ffffff', '#1b1a2a'), back((t - wt('j04', 16)) / 0.3), W / 2, H * 0.34)
        elif name == 'end':
            fr = interior(S, 1.1); fr = tint(fr, (0, 0, 0), clamp(lt / 1.2) * 0.6)
            if lt < 0.8: candle(fr, t, W / 2, H * 0.6, 1.2)
            else:
                d = ImageDraw.Draw(fr); d.rectangle([W / 2 - 17, H * 0.6, W / 2 + 17, H * 0.6 + 108], fill=hexc('#5a5046'))
            pop(fr, label_box('NEXT: DAY 30 — THE VOTE', '#ffffff', '#d24a3a'), back((lt - 1.0) / 0.3), W / 2, H * 0.4)
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
