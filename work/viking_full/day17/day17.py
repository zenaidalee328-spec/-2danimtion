import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4', '/workspace/work/viking_full/day6', '/workspace/work/viking_full/day14'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day4 import stamp, bigtxt, bone_img
from day14 import ULF_V, outlaw_v, snowfall, flames
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'n02': 0.4, 'n03': 0.5, 'u01': 0.7, 'u02': 0.5, 'n04': 0.8, 'n05': 0.5}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text'].replace('"', '')) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'u': 'U'}.get(lid[0], 'N'))
    t += d_
DUR = t + 2.2
hook.TL = TL; hook.LABELS = {'U': 'U L F'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('daycard', 0.0), ('sneak', wt('n01', 2) - 0.1), ('snare', S_('n02') - 0.2), ('net', wt('n02', 6) - 0.1),
         ('show', S_('n03') - 0.3), ('pale', wt('n03', 6) - 0.1), ('read', S_('u01') - 0.4), ('saw', S_('u02') - 0.3), ('thing', wt('u02', 4) - 0.1),
         ('ten', S_('n04') - 0.5), ('tell', S_('n05') - 0.3), ('died', wt('n05', 6) - 0.1)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V
GUN_V = V(coat='#2f4e6e', tunic='#24384e', beard='#e6e2da', beard_dk='#c2bdb4', helmet=False, hair='#e6e2da', rim='#F6B07A', fur='#9a8a72')

def basket():
    im = Image.new('RGBA', (180, 140), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.arc([30, 0, 150, 110], 180, 360, fill=hexc('#7a5234'), width=8)
    d.ellipse([40, 40, 90, 80], fill=hexc('#d9a441')); d.ellipse([85, 35, 140, 78], fill=hexc('#c2502a'))
    d.polygon([(20, 60), (160, 60), (140, 135), (40, 135)], fill=hexc('#a07a48')); [d.line([30, y, 150, y], fill=hexc('#7a5234'), width=4) for y in (80, 105)]
    return im

def snare_draw(d, k, cx, cy):
    d.line([cx - 320, cy + 180, cx + 320, cy + 180], fill=hexc('#5a4030'), width=6)
    d.line([cx + 200, cy + 180, cx + 200, cy - 220], fill=hexc('#7a5234'), width=16)  # bent sapling
    bend = lerp(0, 1, k)
    pts = [(cx + 200, cy - 220)] + [(lerp(cx + 200, cx - 60, f), lerp(cy - 220, cy + 60, f) - 60 * math.sin(f * math.pi)) for f in [i / 12 for i in range(1, 13)]]
    d.line(pts[:int(1 + 12 * bend)], fill=hexc('#c9a87a'), width=6)
    if bend > 0.95: d.ellipse([cx - 140, cy + 60, cx + 20, cy + 175], outline=hexc('#c9a87a'), width=7)
    d.line([cx - 160, cy + 180, cx - 160, cy + 110], fill=hexc('#7a5234'), width=12)

def net_draw(d, k, cx, cy):
    n = 9; s = 70; ox = cx - n * s / 2; oy = cy - n * s / 2 + 20
    m = int(k * n * 2)
    for i in range(n + 1):
        if i <= m: d.line([ox, oy + i * s, ox + n * s, oy + i * s + 10 * math.sin(i)], fill=hexc('#5a4030'), width=5)
        if i <= m - n: d.line([ox + i * s, oy, ox + i * s + 6 * math.sin(i), oy + n * s], fill=hexc('#5a4030'), width=5)
    for i in range(n + 1):
        for j in range(n + 1):
            if i + j <= m: d.ellipse([ox + i * s - 7, oy + j * s - 7, ox + i * s + 7, oy + j * s + 7], fill=hexc('#3a2a1e'))

def camp_fire(fr, t, x, y, sc=0.4): flames(fr, t, x, y, sc)

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set()
    dcard = title_card('DAY 17', 'THE RUNES')
    bsk = basket(); bone = bone_img(1.0)
    s_tr = stamp('THE TRUTH', '#2f8a4a', 110); s_sil = stamp('SILENCED', '#d24a3a', 130)
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        if name == 'daycard':
            fr = fastblur(cam_bg(S['forest'], 1.04 + 0.02 * u), 3.0); fr = tint(fr, (10, 15, 35), 0.4)
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name == 'sneak':
            fr = cam_bg(S['forest'], 1.03 + 0.05 * u); fr = tint(fr, (10, 15, 40), 0.55)
            cam = dict(cx=0, cz=0.3, f=1500, hor=H * 0.62, h=1.2, focus=3.4, ap=0.7)
            hx = lerp(-2.0, 0.2, ease(u))
            render_world2(fr, [Actor('hero', hx, 3.4, HV, expr='neutral', look=(1, 0), seed=90, bob=1.0)], cam, t)
            sx = W / 2 + (hx - 0) / 3.4 * 1500 * 0.92; paste_safe(fr, bsk, sx + 40, H * 0.62 - 40 + 6 * math.sin(t * 9))
            pop(fr, label_box('FOOD FOR THE OUTLAWS', '#ffffff', '#E9BC3F'), back((t - wt('n01', 11)) / 0.35), W / 2, 110)
            snowfall(fr, t, 50)
        elif name in ('snare', 'net'):
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            k = ease((lt - 0.2) / 1.6)
            if name == 'snare':
                snare_draw(d, k, W * 0.45, H * 0.5)
                pop(fr, label_box('ULF TEACHES YOU', '#ffffff', '#6f7cff'), back(lt / 0.35), W / 2, H * 0.12)
                pop(fr, bigtxt('SNARE', 100, '#1b1a2a'), back((t - wt('n02', 5)) / 0.3), W * 0.8, H * 0.4)
            else:
                net_draw(d, k, W * 0.42, H * 0.5)
                pop(fr, label_box('YOU TEACH ULF', '#ffffff', '#E5453A'), back(lt / 0.35), W / 2, H * 0.12)
                if t > wt('n02', 17) - 0.1: pop(fr, bigtxt('NO TANGLE!', 90, '#2f8a4a'), back((t - wt('n02', 17)) / 0.3), W * 0.8, H * 0.45)
        elif name in ('show', 'pale', 'saw', 'thing'):
            fr = cam_bg(S['forest'], {'show': 1.08, 'pale': 1.2, 'saw': 1.2, 'thing': 1.1}[name]); fr = tint(fr, (10, 15, 40), 0.55)
            camp_fire(fr, t, W * 0.5, H * 0.86, 0.35)
            if name == 'show':
                cam = dict(cx=0, cz=lerp(0.4, 0.8, eio(u)), f=1500, hor=H * 0.58, h=1.2, focus=3.2, ap=0.7)
                render_world2(fr, [Actor('hero', -0.7, 3.3, HV, expr='neutral', look=(1, 0), seed=90, pose='up'),
                                   Actor('viking', 0.7, 3.4, ULF_V, expr='neutral', look=(-1, 0), seed=77, size=1.15)], cam, t)
                b = bone.resize((540, 120)); pop(fr, b, back((t - wt('n03', 5)) / 0.35), W * 0.5, H * 0.3)
                pop(fr, label_box("GUNNAR'S RUNES", '#ffffff', '#E9BC3F'), back((t - wt('n03', 4)) / 0.35), W / 2, 110)
            else:
                ex = {'pale': 'worried', 'saw': 'angry', 'thing': 'angry'}[name]
                cam = dict(cx=0.2, cz=lerp(1.0, 1.3, eio(u)), f=1500, hor=H * 0.5, h=0.95, focus=2.0, ap=1.2)
                lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                render_world2(lay, [Actor('viking', 0.3, 3.0, ULF_V, expr=ex, look=(-0.6, 0) if name != 'thing' else (0, 0), seed=77, size=1.15, pose='up' if name == 'thing' else 'down')], cam, t)
                if name == 'pale':
                    pk = ease(lt / 0.8); wl = Image.new('RGBA', (W, H), (235, 240, 250, 255)); wl.putalpha(lay.split()[3].point(lambda v: int(v * 0.35 * pk)))
                    lay.alpha_composite(wl)
                fr.alpha_composite(lay)
                if name == 'pale': pop(fr, bigtxt('PALE', 120, '#e6ecf5'), back((lt - 0.2) / 0.3), W * 0.25, H * 0.3)
                if name == 'saw':
                    pop(fr, bubble('I SAW WHO DID', '#ffffff', '#1b1a2a', 48), back((t - wt('u02', 1)) / 0.3), W * 0.25, H * 0.28)
                    if lt < 0.25: fr = shake(fr, 5, t)
                if name == 'thing':
                    pop(fr, label_box('THE THING', '#ffffff', '#E9BC3F'), back((t - wt('u02', 9)) / 0.35), W * 0.25, H * 0.25)
                    pop(fr, label_box('= VIKING ASSEMBLY', '#ffffff', '#6f7cff'), back((t - wt('u02', 9) - 0.3) / 0.35), W * 0.25, H * 0.35)
        elif name == 'read':
            pg = False
            fr = parchment(W, H)
            b = bone.resize((1100, 244)); pop(fr, b, 1.0, W / 2, H * 0.3)
            words = ['ULF', 'DID', 'NOT', 'LIGHT', 'THE', 'FIRE']
            f = fnt(FRED, 96, axes=[700, 100]); d = ImageDraw.Draw(fr)
            shown = [w for i, w in enumerate(words) if t > wt('u01', i + 2) - 0.05]
            txt = ' '.join(shown); tw = f.getlength(' '.join(words)); x0 = W / 2 - tw / 2
            d.text((x0 + 4, H * 0.55 + 4), txt, font=f, fill=hexc('#00000055')); d.text((x0, H * 0.55), txt, font=f, fill=hexc('#1b1a2a'))
            pop(fr, label_box('TRANSLATION', '#ffffff', '#6f7cff'), back((lt - 0.2) / 0.35), W / 2, H * 0.12)
            if t > wt('u01', 7) + 0.4: pop(fr, s_tr, back((t - wt('u01', 7) - 0.4) / 0.3), W / 2, H * 0.82)
        elif name == 'ten':
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            x0, x1, y = W * 0.12, W * 0.88, H * 0.6
            k = ease((lt - 0.2) / 1.6)
            d.line([x0, y, lerp(x0, x1, k), y], fill=hexc('#5a4030'), width=10)
            f = fnt(FRED, 40, axes=[700, 100])
            for i in range(11):
                if i / 10 <= k:
                    x = lerp(x0, x1, i / 10); d.line([x, y - 20, x, y + 20], fill=hexc('#5a4030'), width=6)
            d.text((x0 - 40, y + 40), 'THE FIRE', font=f, fill=hexc('#d24a3a'))
            if k > 0.98: d.text((x1 - 60, y + 40), 'TODAY', font=f, fill=hexc('#1b1a2a'))
            cam = dict(cx=0, cz=0.0, f=1500, hor=y - 250, h=1.1, focus=3.0, ap=0.0)
            render_world2(fr, [Actor('viking', lerp(-2.4, 2.4, k), 5.0, GUN_V, expr='worried', look=(1, 0), seed=88, size=0.9, bob=1.0)], cam, t)
            pop(fr, bigtxt('10 YEARS OF SILENCE', 90, '#1b1a2a'), back((lt - 0.3) / 0.3), W / 2, H * 0.16)
            pop(fr, name_pill('GUNNAR', 'KNEW THE TRUTH'), back((lt - 0.6) / 0.3), W / 2, H * 0.28)
        elif name in ('tell', 'died'):
            fr = cam_bg(S['village'], 1.08 + 0.03 * u, 0, -20)
            if name == 'tell':
                fr = tint(fr, (60, 45, 30), 0.25)
                cam = dict(cx=0, cz=lerp(0.5, 0.9, eio(u)), f=1500, hor=H * 0.58, h=1.1, focus=3.0, ap=0.8)
                render_world2(fr, [Actor('viking', 0.0, 3.2, GUN_V, expr='happy', look=(0, 0), seed=88, size=1.05, pose='up')], cam, t)
                pop(fr, bubble('I WILL TELL EVERYONE', '#ffffff', '#1b1a2a', 46), back((t - wt('n05', 4)) / 0.3), W * 0.3, H * 0.25)
            else:
                fr = tint(fr, (5, 8, 25), 0.78)
                # lone candle in a hut window going out
                d = ImageDraw.Draw(fr); cx_, cy_ = W * 0.5, H * 0.55
                d.rectangle([cx_ - 140, cy_ - 120, cx_ + 140, cy_ + 120], fill=hexc('#1a140e'))
                out_ = t > wt('n05', 12) - 0.05
                if not out_:
                    fr.alpha_composite(glow(W, H, cx_, cy_, 220, 200, '#ffb35a', 200))
                    d = ImageDraw.Draw(fr); d.rectangle([cx_ - 14, cy_, cx_ + 14, cy_ + 90], fill=hexc('#efe4cc'))
                    fl = 30 + 6 * math.sin(t * 13); d.polygon([(cx_ - 12, cy_), (cx_, cy_ - fl), (cx_ + 12, cy_)], fill=hexc('#ffd25a'))
                else:
                    d.rectangle([cx_ - 14, cy_, cx_ + 14, cy_ + 90], fill=hexc('#5a5046'))
                    for k in range(18):
                        a = clamp((t - wt('n05', 12)) * 1.5); yy = cy_ - k * 10 * a; xx = cx_ + 8 * math.sin(k * 0.6 + t * 2)
                        d.ellipse([xx - 3 - k * 0.3, yy - 3 - k * 0.3, xx + 3 + k * 0.3, yy + 3 + k * 0.3], fill=(180, 180, 190, int(150 * (1 - k / 18))))
                pop(fr, label_box('THE VERY NEXT NIGHT', '#ffffff', '#6f7cff'), back(lt / 0.35), W / 2, 110)
                if out_: pop(fr, s_sil, back((t - wt('n05', 12) - 0.6) / 0.3), W / 2, H * 0.25)
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
