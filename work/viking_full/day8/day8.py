import sys, os, json, math, random, subprocess
for p in ('/workspace/work/viking3', '/workspace/work/viking_full/hook', '/workspace/work/viking_full/day1', '/workspace/work/viking_full/day2', '/workspace/work/viking_full/day4', '/workspace/work/viking_full/day6'): sys.path.insert(0, p)
import v3, hook
from v3 import *
from hook import render_world2, label_box, big_card, pop, tint, dur
from day1 import village_set, bubble, name_pill, HAKON_V, JARL_V, parchment
from day2 import stint
from day4 import hall_set, stamp, bigtxt
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HD = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(os.path.join(HD, 'lines.json')))
GAP = {'h01': 0.4, 'h02': 0.25, 'n02': 0.5, 'n03': 0.5, 'n04': 0.3, 'y01': 0.6, 'j01': 0.7, 'y02': 0.4, 'n05': 0.6, 'n06': 0.4, 'n07': 0.7}
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

SHOTS = [('daycard', 0.0), ('herothink', wt('n01', 2) - 0.1), ('stand', wt('n01', 12) - 0.1), ('accuse', S_('h01') - 0.2),
         ('witch', S_('h02') - 0.15), ('trial', S_('n02') - 0.3), ('symptoms', S_('n03') - 0.3), ('hemlock', S_('n04') - 0.15),
         ('ask', S_('y01') - 0.3), ('jarl', S_('j01') - 0.4), ('who', S_('y02') - 0.3), ('whowide', wt('y02', 12) - 0.15),
         ('quiet', S_('n05') - 0.3), ('boots', wt('n05', 7) - 0.1), ('nothing', S_('n06') - 0.25), ('cleared', S_('n07') - 0.4),
         ('hunt', wt('n07', 3) - 0.1)]
SPANS = [(n, s, SHOTS[i + 1][1] if i + 1 < len(SHOTS) else DUR + 0.01) for i, (n, s) in enumerate(SHOTS)]
HV = HERO_V

def hemlock_img(k=1.0):
    im = Image.new('RGBA', (700, 900), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    top = lerp(880, 140, k)
    d.line([350, 880, 350, top], fill=hexc('#5f8a3a'), width=16)
    for y in range(880, int(top), -60): d.line([343, y, 357, y - 25], fill=hexc('#7a3a6a'), width=5)  # purple streaks
    if k > 0.6:
        kk = (k - 0.6) / 0.4
        for a in range(-3, 4):
            ex, ey = 350 + a * 70 * kk, top - 90 * kk + abs(a) * 25
            d.line([350, top, ex, ey], fill=hexc('#5f8a3a'), width=6)
            for b in range(-2, 3):
                fx, fy = ex + b * 14, ey - 18 + abs(b) * 4
                d.line([ex, ey, fx, fy], fill=hexc('#5f8a3a'), width=2); d.ellipse([fx - 7, fy - 7, fx + 7, fy + 7], fill=hexc('#f6f2e4'), outline=hexc('#b8b0a0'))
        for side in (-1, 1):  # leaves
            ly = top + 300; d.polygon([(350, ly), (350 + side * 200, ly - 60), (350 + side * 230, ly - 20), (350 + side * 60, ly + 30)], fill=hexc('#6a9a44'))
    return im

def boots_img(s=1.0):
    im = Image.new('RGBA', (int(900 * s), int(600 * s)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rnd = random.Random(4)
    for bx in (200, 560):
        d.rectangle([bx * s, 0, (bx + 140) * s, 330 * s], fill=hexc('#1f2a3e'))  # trousers (navy)
        d.rounded_rectangle([(bx - 10) * s, 300 * s, (bx + 150) * s, 470 * s], radius=int(20 * s), fill=hexc('#5a3b24'))
        d.rounded_rectangle([(bx - 10) * s, 420 * s, (bx + 230) * s, 520 * s], radius=int(40 * s), fill=hexc('#5a3b24'))
        for i in range(14):
            x = (bx + rnd.uniform(-10, 220)) * s; y = rnd.uniform(380, 520) * s; r = rnd.uniform(14, 34) * s
            d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=hexc('#141210'))
        for i in range(3):
            x = (bx + rnd.uniform(0, 200)) * s; d.ellipse([x - 10 * s, 540 * s, x + 10 * s, 560 * s], fill=hexc('#141210'))
    return im

def symptom_card(lab, kind, t):
    lay = Image.new('RGBA', (420, 460), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([10, 10, 410, 450], radius=34, fill=hexc('#fff6dc'), outline=hexc('#5a4030'), width=6)
    c = (210, 190)
    if kind == 'shake':
        for k in range(3):
            pts = [(80 + i * 26, 130 + k * 55 + (14 if i % 2 else -14) * math.sin(t * 20 + k)) for i in range(11)]
            d.line(pts, fill=hexc('#B23A2E'), width=8)
    elif kind == 'foam':
        rnd = random.Random(2)
        for i in range(12):
            x = c[0] + rnd.uniform(-110, 110); y = c[1] + rnd.uniform(-90, 90) - (t * 40 % 30); r = rnd.uniform(14, 36)
            d.ellipse([x - r, y - r, x + r, y + r], outline=hexc('#5a8ab0'), width=5)
    else:
        d.polygon([(230, 80), (150, 210), (210, 210), (170, 320), (280, 170), (215, 170), (260, 80)], fill=hexc('#E9BC3F'), outline=hexc('#5a4030'))
    f = fnt(FRED, 46, axes=[700, 100]); d.text((210 - f.getlength(lab) / 2, 370), lab, font=f, fill=hexc('#1b1a2a'))
    return lay

def island_map(north=0.0):
    im = Image.new('RGBA', (520, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 520, 520], radius=30, fill=hexc('#efe2c2'), outline=hexc('#5a4030'), width=6)
    d.polygon([(260, 60), (380, 120), (440, 260), (390, 420), (240, 470), (110, 400), (80, 240), (140, 110)], fill=hexc('#b9a77e'))
    if north > 0:
        d.polygon([(260, 60), (380, 120), (400, 190), (120, 190), (140, 110)], fill=(70, 90, 60, int(255 * north)))
        for i in range(6):
            x = 170 + i * 38; d.line([x, 150, x + 10, 135], fill=hexc('#2e4428'), width=4)
    f = fnt(FRED, 54, axes=[700, 100]); d.text((470 - f.getlength('N'), 20), 'N', font=f, fill=hexc('#B23A2E'))
    d.polygon([(450, 90), (440, 120), (460, 120)], fill=hexc('#B23A2E'))
    return im

def run(frames, out=None):
    S = build(); dark, haze, grains = make_post()
    S['village'], _, houses = village_set(); S['hall'] = hall_set()
    dcard = title_card('DAY 8', 'THE TRIAL')
    hp = name_pill('HAKON', 'STANDS UP'); s_clear = stamp('CLEARED', '#2f8a4e', 130); s_trial = label_box('ON TRIAL FOR POISONING', '#ffffff', '#d24a3a')
    hallcrowd = crowd(81, 2, 8, 5.0, 1.2, 5.0, exclude=lambda x, z: abs(x) < 1.0, expr_choices=('neutral', 'angry', 'neutral'))
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        name, s0, s1 = next(s for s in SPANS if s[1] <= t < s[2])
        lt = t - s0; u = lt / max(0.01, s1 - s0); pg = True
        fl = 1 + 0.08 * math.sin(t * 11) + 0.05 * math.sin(t * 7)
        def hallbg(z, blur, warm=120):
            f_ = fastblur(cam_bg(S['hall'], z, 0, 40), blur)
            return Image.alpha_composite(f_, glow(W, H, W / 2, H * 0.8, 400 * fl, 200 * fl, '#ffb45a', warm))
        if name == 'daycard':
            fr = fastblur(cam_bg(S['village'], 1.04 + 0.02 * u, 0, -20), 3.0)
            k = back(lt / 0.4)
            if lt > (s1 - s0) - 0.35: k = 1 - ease((lt - (s1 - s0 - 0.35)) / 0.35)
            pop(fr, dcard, k, W / 2, H * 0.45)
        elif name == 'herothink':
            fr = fastblur(cam_bg(S['village'], 1.15, 0, -20), 3.0)
            cam = dict(cx=0, cz=1.0, f=1500, hor=H * 0.5, h=1.0, focus=2.2, ap=1.2)
            render_world2(fr, [Actor('hero', -0.3, 3.0, HV, expr='happy', look=(1, -0.3), seed=90)], cam, t)
            k = back((t - wt('n01', 8)) / 0.3)
            bt = bubble('HERO?', '#E9BC3F', '#1b1a2a', 70); pop(fr, bt, k, W * 0.66, H * 0.3)
            if t > wt('n01', 11) + 0.3:
                d = ImageDraw.Draw(fr); kk = ease((t - wt('n01', 11) - 0.3) / 0.25)
                d.line([W * 0.56, H * 0.22, lerp(W * 0.56, W * 0.76, kk), lerp(H * 0.22, H * 0.38, kk)], fill=hexc('#d24a3a'), width=18)
        elif name in ('stand', 'witch', 'quiet', 'whowide'):
            fr = hallbg(1.0 + 0.04 * u, 1.0, 100)
            if name == 'witch': fr = tint(fr, (60, 10, 10), 0.25)
            if name in ('quiet', 'whowide'): fr = tint(fr, (10, 10, 20), 0.3)
            cam = dict(cx=0, cz=lerp(-0.4, 0.1, eio(u)), f=1500, hor=H * 0.5, h=1.3, focus=4.5, ap=0.6)
            ex = {'stand': None, 'witch': 'angry', 'quiet': 'neutral', 'whowide': 'worried'}[name]
            acts = [Actor(a.kind, a.x, a.z, a.v, expr=ex or a.expr, look=(0, 0), seed=a.seed, size=a.size, bob=1.0 if name == 'witch' else 0) for a in hallcrowd]
            if name == 'stand':
                acts.append(Actor('viking', 0.9, 4.2, HAKON_V, expr='angry', look=(-1, 0), seed=75, size=1.08))
                acts.append(Actor('hero', -0.5, 3.4, HV, expr='worried', look=(1, 0), seed=90))
            else:
                acts.append(Actor('hero', 0.0, 3.4, HV, expr='scared' if name == 'witch' else 'neutral', look=(0, 0), seed=90))
            render_world2(fr, acts, cam, t)
            if name == 'stand': pop(fr, hp, back((lt - 0.3) / 0.35), W / 2, 110)
            if name == 'witch':
                for i, (bx, by) in enumerate([(0.18, 0.3), (0.82, 0.25), (0.3, 0.15), (0.7, 0.42)]):
                    pop(fr, bubble('WITCH!', '#ffffff', '#d24a3a', 48), back((t - wt('h02', 5) - i * 0.15) / 0.25), W * bx, H * by)
                if t > wt('h02', 5): fr = shake(fr, 4, t)
            if name == 'quiet': pop(fr, bubble('. . .', '#ffffff', '#1b1a2a', 50), back((lt - 0.6) / 0.3), W / 2, H * 0.2)
            if name == 'whowide': pop(fr, bigtxt('WHO?', 120), back(lt / 0.25), W / 2, H * 0.2)
        elif name == 'accuse':
            fr = hallbg(1.15, 2.4)
            cam = dict(cx=0.2, cz=1.1, f=1500, hor=H * 0.48, h=0.95, focus=2.0, ap=1.2)
            render_world2(fr, [Actor('viking', 0.35, 3.0, HAKON_V, expr='angry', look=(-1, 0), seed=75, size=1.08, bob=0.3)], cam, t)
            if t > wt('h01', 4) - 0.1: fr = shake(fr, 3, t)
        elif name == 'trial':
            fr = hallbg(1.08, 3.0, 40); fr = tint(fr, (5, 5, 10), 0.6)
            fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.55, 330, 480, '#ffe4ad', 140))
            cam = dict(cx=0, cz=lerp(0.4, 0.9, eio(u)), f=1500, hor=H * 0.5, h=1.1, focus=3.0, ap=0.8)
            render_world2(fr, [Actor('hero', 0.0, 3.0, HV | V(sweat=True), expr='scared', look=(0, 0), seed=90)], cam, t)
            pop(fr, s_trial, back((lt - 0.4) / 0.35), W / 2, 110)
        elif name in ('symptoms', 'hemlock'):
            pg = False
            fr = parchment(W, H); d = ImageDraw.Draw(fr)
            if name == 'symptoms':
                pop(fr, bigtxt("TORSTEIN'S SYMPTOMS", 70, '#ffffff'), back(lt / 0.3), W / 2, H * 0.14)
                for i, (wi, lab, kd) in enumerate([(5, 'SHAKING', 'shake'), (6, 'FOAMING', 'foam'), (10, 'SEIZURES', 'zap')]):
                    k = back((t - wt('n03', wi) + 0.05) / 0.3)
                    if k > 0.02: pop(fr, symptom_card(lab, kd, t), k, W * (0.25 + i * 0.25), H * 0.55)
            else:
                k = ease((t - wt('n04', 1)) / 1.3)
                hi = hemlock_img(k); paste_safe(fr, hi, W * 0.3 - hi.width / 2, H * 0.92 - hi.height)
                if t > wt('n04', 14) - 0.2:
                    mk = ease((t - wt('n04', 14) + 0.2) / 0.5)
                    d.ellipse([W * 0.3 - 380 * mk, H * 0.88, W * 0.3 + 380 * mk, H * 0.98], fill=hexc('#3e5a62'))
                    pop(fr, label_box('ONLY IN WET GROUND', '#ffffff', '#2f6e9e'), back((t - wt('n04', 14)) / 0.3), W * 0.7, H * 0.68)
                pop(fr, bigtxt('WATER HEMLOCK', 100), back((t - wt('n04', 1)) / 0.3), W * 0.68, H * 0.2)
                pop(fr, stamp('MOST POISONOUS IN EUROPE', '#B23A2E', 54, -4), back((t - wt('n04', 7)) / 0.3), W * 0.68, H * 0.44)
        elif name in ('ask', 'who', 'nothing'):
            fr = hallbg(1.15, 2.4, 110)
            if name == 'nothing': fr = tint(fr, (10, 10, 20), 0.3)
            cam = dict(cx=-0.2, cz=1.1, f=1500, hor=H * 0.48, h=0.95, focus=2.0, ap=1.2)
            render_world2(fr, [Actor('hero', -0.3, 3.0, HV, expr={'ask': 'angry', 'who': 'angry', 'nothing': 'neutral'}[name], look=(1, 0) if name != 'nothing' else (0.6, 0.2), seed=90)], cam, t)
            if name == 'nothing':
                pop(fr, label_box('SAY NOTHING... YET', '#ffffff', '#6f7cff'), back((lt - 0.5) / 0.35), W / 2, 110)
                pop(fr, bubble('...', '#ffffff', '#1b1a2a', 50), back((lt - 1.0) / 0.3), W * 0.65, H * 0.25)
        elif name == 'jarl':
            fr = hallbg(1.15, 2.4)
            cam = dict(cx=0.2, cz=1.0, f=1500, hor=H * 0.48, h=1.0, focus=2.2, ap=1.2)
            render_world2(fr, [Actor('jarl', 0.35, 3.2, JARL_V, expr='worried', look=(-1, 0), seed=76, size=1.18)], cam, t)
            k = back((t - wt('j01', 1)) / 0.35)
            if k > 0.02:
                mp = island_map(ease((t - wt('j01', 1)) / 0.6)); pop(fr, mp.resize((416, 416), Image.LANCZOS), k, W * 0.24, H * 0.4)
        elif name == 'boots':
            fr = hallbg(1.3, 5.0, 60); fr = tint(fr, (10, 10, 20), 0.35)
            d = ImageDraw.Draw(fr); d.rectangle([0, H * 0.82, W, H], fill=hexc('#3a2a1c'))
            sc = lerp(1.0, 1.15, eio(u)); bi = boots_img(sc)
            paste_safe(fr, bi, W / 2 - bi.width / 2, H * 0.95 - bi.height)
            if t > wt('n05', 13): pop(fr, label_box('BLACK MARSH MUD', '#ffffff', '#141210'), back((t - wt('n05', 13)) / 0.3), W / 2, 110)
        elif name in ('cleared', 'hunt'):
            if name == 'cleared':
                fr = hallbg(1.05, 1.5, 130)
                cam = dict(cx=0, cz=0.6, f=1500, hor=H * 0.5, h=1.1, focus=3.0, ap=0.8)
                render_world2(fr, [Actor('hero', 0.0, 3.0, HV, expr='happy', look=(0, 0), seed=90)], cam, t)
                pop(fr, s_clear, back((lt - 0.3) / 0.3), W / 2, H * 0.22)
            else:
                pg = False
                fr = vgrad(W, H, [(0, '#05060a'), (1, '#0d0f18')])
                d = ImageDraw.Draw(fr)
                k = ease(lt / 1.2)
                sil = make_char_cached('viking', 72, HAKON_V, 'angry', False, (0, 0), 'down')
                sil2 = Image.composite(Image.new('RGBA', sil.size, (3, 4, 8, 255)), Image.new('RGBA', sil.size, (0, 0, 0, 0)), sil.getchannel('A'))
                fr = Image.alpha_composite(fr, glow(W, H, W / 2, H * 0.5, 600, 500, '#3a1010', int(140 * k)))
                paste_safe(fr, sil2, W / 2 - sil2.width / 2, H * 1.12 - sil2.height)
                bb_ = sil2.getchannel('A').getbbox(); ex, ey = W / 2 - sil2.width / 2 + (bb_[0] + bb_[2]) / 2, H * 1.12 - sil2.height + bb_[1] + (bb_[3] - bb_[1]) * 0.19
                d = ImageDraw.Draw(fr)
                for dx in (-38, 38):
                    d.ellipse([ex + dx - 14, ey - 8, ex + dx + 14, ey + 8], fill=(255, 70, 50, int(255 * k)))
                if t > wt('n07', 8): pop(fr, label_box('THE KILLER KNOWS', '#ffffff', '#d24a3a'), back((t - wt('n07', 8)) / 0.3), W / 2, 110)
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
