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
GAP = {'n02': 0.5, 'n03': 0.9, 'n04': 0.9}
FIX = {'law': 'law', 'speaker': 'speaker'}
TL = {}; t = 0.5
for lid, voice, text in LINES:
    t += GAP.get(lid, 0.25)
    d_ = dur(os.path.join(HD, 'vo', lid + '.mp3'))
    wj = json.load(open(os.path.join(HD, 'vo', lid + '.json'))); wj = wj[0] if isinstance(wj, list) else wj
    words = [(w['start'], w['end'], w['text'].replace('"', '')) for w in wj['words'] if w['type'] == 'word']
    TL[lid] = dict(st=t, en=t + d_, words=words, text=text, spk={'j': 'J', 'u': 'U'}.get(lid[0], 'N'))
    t += d_
DUR = t + 2.5
hook.TL = TL; hook.LABELS = {'J': 'J A R L', 'U': 'U L F'}
def S_(l): return TL[l]['st']
def wt(l, i): return TL[l]['st'] + TL[l]['words'][min(i, len(TL[l]['words']) - 1)][0]

SHOTS = [('choice', 0.0), ('comments', S_('n02') - 0.3), ('story', S_('n03') - 0.3), ('sub', S_('n04') - 0.3)]
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
    rock = rock_img()
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        if name == 'choice':
            fr = cam_bg(S['beach'], lerp(1.0, 1.08, eio(u)), 0, 0)
            b = boat_img(t, 0.16); paste_safe(fr, b, W * 0.2 - b.width / 2, H * 0.47 - b.height * 0.8)
            cam = dict(cx=0, cz=0.0, f=1500, hor=H * 0.55, h=1.4, focus=5.0, ap=0.3)
            render_world2(fr, [Actor('hero', 1.0, 5.0, HV, expr='worried', look=(-0.5, 0), seed=90)], cam, t)
            pop(fr, bigtxt('WHAT WOULD YOU DO?', 100), back((t - S_('n01')) / 0.3), W / 2, H * 0.15)
            if t > wt('n01', 7) - 0.1: pop(fr, label_box('BOAT HOME', '#ffffff', '#6f7cff'), back((t - wt('n01', 7)) / 0.3), W * 0.2, H * 0.3)
            if t > wt('n01', 9) - 0.1: pop(fr, bigtxt('OR', 110, '#E9BC3F'), back((t - wt('n01', 9)) / 0.3), W * 0.45, H * 0.3)
            if t > wt('n01', 14) - 0.1: pop(fr, label_box('STAY: LAWSPEAKER', '#ffffff', '#3e6a3a'), back((t - wt('n01', 14)) / 0.3), W * 0.7, H * 0.3)
        elif name == 'comments':
            pg = False; fr = fastblur(cam_bg(S['beach'], 1.08, 0, 0), 6.0)
            bx = Image.new('RGBA', (900, 240), (0, 0, 0, 0)); d = ImageDraw.Draw(bx)
            d.rounded_rectangle([0, 0, 899, 239], 40, fill=(255, 255, 255, 235))
            d.ellipse([30, 50, 150, 170], fill=hexc('#d24a3a')[:3] + (255,))
            d.rounded_rectangle([190, 60, 840, 95], 15, fill=(200, 200, 205, 255)); d.rounded_rectangle([190, 130, 640, 165], 15, fill=(215, 215, 220, 255))
            pop(fr, bx, back(lt / 0.35), W / 2, H * 0.55)
            pop(fr, bigtxt('TELL ME IN THE COMMENTS', 95), back((lt - 0.2) / 0.3), W / 2, H * 0.22)
        elif name == 'story':
            pg = False; fr = parchment(W, H)
            pop(fr, name_pill('STORY 1', 'ISLAND OF AMAZONS'), back((t - wt('n03', 4)) / 0.3), W * 0.27, H * 0.45)
            pop(fr, bigtxt('VS', 140, '#d24a3a'), back((t - wt('n03', 11)) / 0.3), W / 2, H * 0.45)
            pop(fr, name_pill('STORY 2', 'VIKING ISLAND'), back((t - wt('n03', 11)) / 0.3), W * 0.73, H * 0.45)
            if t > wt('n03', 14) - 0.1: pop(fr, bigtxt('WHICH WAS BETTER?', 100, '#5a4030'), back((t - wt('n03', 14)) / 0.3), W / 2, H * 0.72)
        elif name == 'sub':
            fr = night(S, 1.04)
            torches(fr, t, [W * 0.2, W * 0.8], H * 0.62)
            bt = Image.new('RGBA', (760, 190), (0, 0, 0, 0)); d = ImageDraw.Draw(bt)
            pressed = t > wt('n04', 1) + 0.3
            d.rounded_rectangle([0, 0, 759, 189], 40, fill=(110, 110, 115, 255) if pressed else (220, 30, 30, 255))
            f = fnt(NUN, 80, b'Black'); txt = 'SUBSCRIBED' if pressed else 'SUBSCRIBE'
            d.text((380 - f.getlength(txt) / 2, 45), txt, font=f, fill=(255, 255, 255, 255))
            pop(fr, bt, back(lt / 0.35) * (0.94 if abs(t - wt('n04', 1) - 0.3) < 0.1 else 1), W / 2, H * 0.42)
            if pressed: pop(fr, label_box('SMALL CREATOR. BIG THANKS!', '#ffffff', '#E9BC3F'), back((t - wt('n04', 6)) / 0.3), W / 2, H * 0.68)
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
