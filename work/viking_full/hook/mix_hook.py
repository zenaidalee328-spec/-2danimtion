import subprocess, sys, os
sys.argv = ['x', 'info']
import hook
from hook import TL, SHOT_SPANS, DUR, S_, E_, word_t
S = '/workspace/work/viking/sfx/'; S3 = '/workspace/work/viking3/sfx/'
sh = {n: (s, e) for n, s, e in SHOT_SPANS}
m = [(S + 'pad.wav', 0.0, 0.45, DUR)]
def seg(f, a, b, vol):
    m.append((f, a, vol, b - a))
seg(S + 'waves.wav', 0, sh['kneelclose'][1], 0.45)
seg(S + 'crowd.wav', sh['reveal'][0], sh['kneelclose'][1], 0.25)
seg(S + 'storm.wav', sh['flash'][0] + 0.5, sh['mast'][1], 0.85)
seg(S + 'rain.wav', sh['flash'][0] + 0.5, sh['mast'][1], 0.55)
m.append((S + 'thunder.wav', sh['storm'][0] + 0.9, 1.0, 2.5))
m.append((S + 'thunder.wav', sh['storm'][0] + 2.2, 0.7, 2.5))
m.append((S + 'crash.wav', sh['crash'][0], 1.0, 1.6)); m.append((S + 'boom.wav', sh['crash'][0], 0.6, 2.2))
seg(S + 'waves.wav', sh['wash'][0], sh['law'][1], 0.4)
seg(S + 'crowd.wav', sh['surround'][0], sh['jarl'][1], 0.22)
seg(S + 'waves.wav', sh['wide100'][0], sh['raft'][1], 0.3)
seg(S + 'crowd.wav', sh['wide100'][0], sh['hope'][1], 0.25)
seg(S + 'storm.wav', sh['night'][0], sh['end'][1], 0.18)
# kneel thuds
kc0 = word_t('n02', 6)
for d in (0.0, 0.12, 0.22): m.append((S + 'drum.wav', kc0 + d + 0.18, 0.8, 0.9))
m.append((S + 'boom.wav', S_('n02') + 1.1, 0.5, 2.2))
m.append((S + 'boom.wav', S_('n06') + 1.2, 0.9, 2.2))
m.append((S + 'drum.wav', S_('n06') + 1.25, 0.9, 0.9))
# clashes / tings
m.append((S3 + 'clash.wav', sh['surround'][0] + 0.25, 0.8, 0.4)); m.append((S3 + 'clash.wav', sh['surround'][0] + 0.4, 0.7, 0.4))
for nm in ('surround', 'axes_up', 'hope'): m.append((S3 + 'ting.wav', sh[nm][0] + 0.45, 0.5, 0.6))
# card pops
for nm in ('storm', 'moon', 'law', 'vote', 'title'): m.append((S + 'ding.wav', sh[nm][0] + 0.15, 0.6, 0.72))
m.append((S + 'boom.wav', sh['jarl'][0] + 0.3, 0.8, 2.2))
m.append((S + 'drum.wav', sh['grump'][0], 0.9, 0.9)); m.append((S + 'boom.wav', sh['raft'][0], 0.6, 2.2))
m.append((S + 'boom.wav', sh['stalker'][0] + 1.2, 0.8, 2.2))
for i in range(5): m.append((S + 'drumn.wav', sh['stalker'][0] + 1.6 + i * 0.75, 0.45, 0.3))
m.append((S + 'boom.wav', sh['title'][0] + 0.1, 0.9, 2.2))
for n, s, e in SHOT_SPANS[1:]:
    m.append((S3 + 'whoosh.wav', s - 0.2, 0.45, 0.5))
inputs = []; fc = []; labs = []
for i, (f, st, vol, dd) in enumerate(m):
    st = max(0, st)
    inputs += ['-i', f]
    fc.append(f'[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo,aloop=loop=-1:size=2000000000,atrim=0:{dd},afade=t=out:st={max(0, dd - 0.3)}:d=0.3,volume={vol},adelay={int(st * 1000)}|{int(st * 1000)}[m{i}]')
    labs.append(f'[m{i}]')
n = len(m)
fc.append(''.join(labs) + f'amix=inputs={n}:normalize=0,atrim=0:{DUR}[mus]')
vl = []
for k, (lid, L) in enumerate(TL.items()):
    inputs += ['-i', os.path.join(hook.HD, 'vo', lid + '.mp3')]
    st = L['st']
    fc.append(f'[{n + k}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.6,adelay={int(st * 1000)}|{int(st * 1000)}[v{k}]')
    vl.append(f'[v{k}]')
fc.append(''.join(vl) + f'amix=inputs={len(vl)}:normalize=0,apad=whole_dur={DUR},asplit=2[vo][vsc]')
fc.append('[mus][vsc]sidechaincompress=threshold=0.03:ratio=5:attack=15:release=250[duck]')
fc.append(f'[duck][vo]amix=inputs=2:normalize=0,atrim=0:{DUR},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[out]')
subprocess.run(['ffmpeg', '-y', '-v', 'error'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', '/tmp/hook_mix.m4a'], check=True)
print('ok')
