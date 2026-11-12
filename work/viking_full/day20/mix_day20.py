import subprocess, sys, os
import day20 as day1
from day20 import TL, SPANS, DUR, S_, wt
S = '/workspace/work/viking/sfx/'; S3 = '/workspace/work/viking3/sfx/'
sh = {n: (s, e) for n, s, e in SPANS}
m = [(S + 'pad.wav', 0.0, 0.45, DUR)]
def seg(f, a, b, vol): m.append((f, a, vol, b - a))
seg(S + 'crash.wav', sh['fire'][0], sh['cliff'][0], 0.12)
seg(S + 'storm.wav', sh['cliff'][0], sh['why'][0], 0.18)
seg(S + 'crash.wav', sh['why'][0], DUR, 0.12)
for nm in ('daycard', 'cord'): m.append((S + 'ding.wav', sh[nm][0] + 0.25, 0.5, 0.72))
m.append((S3 + 'ting.wav', sh['tooth'][0] + 1.0, 0.7, 1.0)); m.append((S + 'drum.wav', sh['tooth'][0] + 1.3, 0.8, 0.9))
m.append((S + 'drum.wav', wt('u01', 12) + 0.35, 0.7, 0.9))
m.append((S + 'boom.wav', wt('u02', 12), 0.6, 2.2)); m.append((S3 + 'ting.wav', sh['end'][0] + 0.1, 0.6, 1.0))
for n, s, e in SPANS[1:]: m.append((S3 + 'whoosh.wav', s - 0.2, 0.35, 0.5))
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
subprocess.run(['ffmpeg', '-y', '-v', 'error'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', '/tmp/d20_mix.m4a'], check=True)
print('ok')
