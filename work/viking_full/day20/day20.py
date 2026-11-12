import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4', '/workspace/work/viking_full/day6', '/workspace/work/viking_full/day14'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day2 import tooth_img, splash
from day4 import stamp, bigtxt
from day14 import ULF_V, snowfall, flames
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'n02': 0.4, 'n03': 0.4, 'u01': 0.8, 'y01': 0.5, 'u02': 0.6}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text'].replace('"', '')) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'u': 'U', 'y': 'Y'}.get(lid[0], 'N'))
    t += d_
DUR = t + 2.6
hook.TL = TL; hook.LABELS = {'U': 'U L F', 'Y': 'Y O U'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('fire', wt('n01', 2) - 0.1), ('cord', wt('n01', 9) - 0.1), ('tooth', S_('n03') - 0.2),
         ('cliff', S_('u01') - 0.4), ('throw', wt('u01', 9) - 0.1), ('why', S_('y01') - 0.3), ('ulfsad', S_('u02') - 0.3),
         ('wide', wt('u02', 6) - 0.1), ('end', TL['u02']['en'] + 0.5)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V

def empty_cord(s=1.0):
    im = Image.new('RGBA', (int(400 * s), int(400 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.arc([40 * s, -260 * s, 360 * s, 300 * s], 20, 160, fill=hexc('#6b4a30'), width=int(10 * s))
    d.ellipse([180 * s, 270 * s, 220 * s, 310 * s], fill=hexc('#6b4a30'))
    return im

def night_forest(S, z):
    fr = cam_bg(S['forest'], z); return tint(fr, (10, 15, 40), 0.58)

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set()
    dcard = title_card('DAY 20', 'THE WOLF TOOTH')
    s_match = stamp('PERFECT MATCH', '#2f8a4a', 100); s_solved = stamp('CLUE #1 SOLVED', '#2f8a4a', 100)
    ec = empty_cord(1.0)
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        if name == 'daycard':
            fr = fastblur(night_forest(S, 1.04 + 0.02 * u), 3.0)
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name in ('fire', 'wide'):
            fr = night_forest(S, 1.05 + 0.04 * u if name == 'fire' else lerp(1.15, 1.0, eio(u)))
            fr.alpha_composite(glow(W, H, W / 2, H * 0.75, 700, 380, '#ff8a3a', 120))
            cam = dict(cx=0, cz=lerp(0.2, 0.6, eio(u)) if name == 'fire' else lerp(0.8, 0.0, eio(u)), f=1500, hor=H * 0.6, h=1.2, focus=3.3, ap=0.7)
            render_world2(fr, [Actor('hero', -0.8, 3.3, HV, expr='neutral' if name == 'fire' else 'worried', look=(1, 0), seed=90),
                               Actor('viking', 0.8, 3.4, ULF_V, expr='neutral', look=(-1, 0.3), seed=77, size=1.15)], cam, t)
            flames(fr, t, W * 0.5, H * 0.86, 0.33)
            snowfall(fr, t, 40)
            if name == 'fire': pop(fr, label_box("ULF'S CAMP", '#ffffff', '#6f7cff'), back((lt - 0.3) / 0.35), W / 2, 110)
            if name == 'wide': pop(fr, bigtxt('YOU BELONG TO THE SEA', 90, '#9fd3ff'), back((t - wt('u02', 12)) / 0.3), W / 2, H * 0.16)
        elif name == 'cord':
            fr = fastblur(night_forest(S, 1.3), 8.0)
            fr.alpha_composite(glow(W, H, W * 0.4, H * 0.6, 600, 400, '#ff8a3a', 90))
            sc = lerp(1.2, 1.45, eio(u)); e = ec.resize((int(400 * sc), int(400 * sc)), Image.LANCZOS)
            paste_safe(fr, e, W * 0.42 - e.width / 2, H * 0.2)
            d = ImageDraw.Draw(fr); cx_, cy_ = W * 0.42, H * 0.2 + 290 * sc
            if t > wt('n02', 5) - 0.1:
                d.ellipse([cx_ - 70, cy_ - 20, cx_ + 70, cy_ + 200], outline=hexc('#d24a3a'), width=8)
                pop(fr, bigtxt('EMPTY', 110, '#ff6a5a'), back((t - wt('n02', 6)) / 0.3), W * 0.75, H * 0.5)
            pop(fr, label_box('SAME LEATHER', '#ffffff', '#E9BC3F'), back((t - wt('n02', 3)) / 0.35), W * 0.75, H * 0.3)
        elif name == 'tooth':
            fr = fastblur(night_forest(S, 1.3), 8.0)
            fr.alpha_composite(glow(W, H, W * 0.5, H * 0.5, 500, 400, '#ffe8b0', 110))
            e = ec.resize((480, 480)); paste_safe(fr, e, W * 0.3 - 240, H * 0.15)
            k = ease((lt - 0.2) / 0.9)
            ti = tooth_img(0.8).rotate(6 * math.sin(t * 2.2), resample=Image.BICUBIC, expand=True)
            paste_safe(fr, ti, lerp(W * 0.85, W * 0.62, k) - ti.width / 2, lerp(H * 1.1, H * 0.2, k))
            if lt > 1.3: pop(fr, s_match, back((lt - 1.3) / 0.3), W / 2, H * 0.82)
            pop(fr, label_box('CLUE #1', '#ffffff', '#d24a3a'), back((lt - 0.4) / 0.35), W / 2, 110)
        elif name == 'cliff':
            fr = cam_bg(S['village'], 1.0, 0, 40); fr = tint(fr, (60, 55, 80), 0.35)
            d = ImageDraw.Draw(fr)
            d.polygon([(0, H * 0.42), (W * 0.32, H * 0.38), (W * 0.42, H * 0.5), (W * 0.38, H), (0, H)], fill=hexc('#2a2a33'))
            cam = dict(cx=0, cz=0.0, f=1500, hor=H * 0.5, h=1.2, focus=3.0, ap=0.0)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            render_world2(lay, [Actor('viking', -1.1, 3.6, ULF_V, expr='neutral', look=(1, 0.3), seed=77, size=1.0)], cam, t)
            a = lay.split()[3]; sil = Image.new('RGBA', (W, H), hexc('#16161c')[:3] + (255,)); sil.putalpha(a)
            paste_safe(fr, sil, lerp(-60, -20, u), -H * 0.16)
            pop(fr, label_box('EVERY DAY', '#ffffff', '#6f7cff'), back((t - wt('u01', 7)) / 0.35), W * 0.65, 110)
        elif name == 'throw':
            fr = cam_bg(S['cool'], 1.1, 0, -30); fr = tint(fr, (90, 70, 40), 0.45)
            d = ImageDraw.Draw(fr)
            kk = clamp((t - wt('u01', 12)) / 0.9)
            x, y = W * 0.6, H * 0.62
            if kk < 0.4:
                fy = lerp(H * 0.2, y, ease(kk / 0.4)); d.ellipse([x - 40, fy - 40, x + 40, fy + 40], fill=hexc('#E5453A'))
            splash(fr, x, y, (kk - 0.4) / 0.6, 1.0)
            pop(fr, label_box('FLASHBACK: DAY 1', '#ffffff', '#8a6a3a'), back(lt / 0.35), W / 2, 110)
            pop(fr, bigtxt('HE SAW EVERYTHING', 90), back((t - wt('u01', 10)) / 0.3), W / 2, H * 0.3)
        elif name in ('why', 'ulfsad'):
            fr = night_forest(S, 1.2); fr = fastblur(fr, 2.0)
            fr.alpha_composite(glow(W, H, W * 0.5, H * 0.9, 600, 300, '#ff8a3a', 110))
            cam = dict(cx=0.2 if name == 'ulfsad' else -0.2, cz=lerp(1.0, 1.25, eio(u)), f=1500, hor=H * 0.5, h=0.95, focus=2.0, ap=1.2)
            if name == 'why':
                render_world2(fr, [Actor('hero', -0.3, 3.0, HV, expr='worried', look=(0.6, 0), seed=90)], cam, t)
                pop(fr, bubble('WHY SAVE ME?', '#ffffff', '#1b1a2a', 48), back((lt - 0.3) / 0.3), W * 0.72, H * 0.28)
            else:
                render_world2(fr, [Actor('viking', 0.3, 3.0, ULF_V, expr='worried', look=(-0.6, 0.3), seed=77, size=1.15)], cam, t)
        elif name == 'end':
            fr = night_forest(S, 1.0); fr = fastblur(fr, 4.0)
            ti = tooth_img(0.6).rotate(8 * math.sin(t * 2), resample=Image.BICUBIC, expand=True)
            paste_safe(fr, ti, W / 2 - ti.width / 2, H * 0.3)
            pop(fr, s_solved, back((lt - 0.1) / 0.3), W / 2, H * 0.2)
            pop(fr, name_pill('THE SAVIOR', 'ULF'), back((lt - 0.5) / 0.3), W / 2, H * 0.82)
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
