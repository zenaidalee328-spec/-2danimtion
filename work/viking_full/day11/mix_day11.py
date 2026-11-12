import subprocess, sys, os
import day11 as day1
from day11 import TL, SPANS, DUR, S_, wt
S = '/workspace/work/viking/sfx/'; S3 = '/workspace/work/viking3/sfx/'
sh = {n: (s, e) for n, s, e in SPANS}
m = [(S + 'pad.wav', 0.0, 0.45, DUR)]
def seg(f, a, b, vol): m.append((f, a, vol, b - a))
seg(S + 'waves.wav', sh['loading'][0], sh['storm'][0], 0.35)
seg(S + 'crowd.wav', sh['loading'][0], sh['watch'][0], 0.25)
seg(S + 'storm.wav', sh['storm'][0], sh['sea'][1], 0.75)
seg(S + 'crowd.wav', sh['axes'][0], sh['morning'][0], 0.5)
seg(S + 'waves.wav', sh['morning'][0], DUR, 0.3)
for nm in ('daycard', 'watch', 'graph', 'hundred'): m.append((S + 'ding.wav', sh[nm][0] + 0.25, 0.5, 0.72))
m.append((S + 'drum.wav', wt('n03', 7), 0.7, 0.9)); m.append((S + 'drum.wav', sh['stay'][0] + 0.1, 0.6, 0.9))
m.append((S + 'thunder.wav', wt('n05', 5), 1.0, 3.0)); m.append((S + 'rain.wav', sh['storm'][0], 0.6, 6.0)); m.append((S + 'boom.wav', wt('n07', 1), 0.8, 2.2)); m.append((S + 'boom.wav', sh['who'][0] + 0.2, 0.9, 2.2))
for n, s, e in SPANS[1:]: m.append((S3 + 'whoosh.wav', s - 0.2, 0.4, 0.5))
inputs = []; fc = []; labs = []
for i, (f, st, vol, dd) in enumerate(m):
    st = max(0, st); inputs += ['-i', f]
    fc.append(f'[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo,aloop=loop=-1:size=2000000000,atrim=0:{dd},afade=t=out:st={max(0, dd - 0.3)}:d=0.3,volume={vol},adelay={int(st * 1000)}|{int(st * 1000)}[m{i}]')
    labs.append(f'[m{i}]')
n = len(m)
fc.append(''.join(labs) + f'amix=inputs={n}:normalize=0,atrim=0:{DUR}[mus]')
vl = []
for k, (lid, L) in enumerate(TL.items()):
    inputs += ['-i', os.path.join(day1.HD, 'vo', lid + '.mp3')]; st = L['st']
    fc.append(f'[{n + k}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.6,adelay={int(st * 1000)}|{int(st * 1000)}[v{k}]'); vl.append(f'[v{k}]')
fc.append(''.join(vl) + f'amix=inputs={len(vl)}:normalize=0,apad=whole_dur={DUR},asplit=2[vo][vsc]')
fc.append('[mus][vsc]sidechaincompress=threshold=0.03:ratio=5:attack=15:release=250[duck]')
fc.append(f'[duck][vo]amix=inputs=2:normalize=0,atrim=0:{DUR},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[out]')
subprocess.run(['ffmpeg', '-y', '-v', 'error'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', '/tmp/d11_mix.m4a'], check=True)
print('ok')
