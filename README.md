---
name: viking-pov-video
description: Make long-form animated "POV / 30 days on an island" story videos for YouTube (script, character voices, 2D animated chapters, sound mix, full render, SEO metadata) the same way the Viking Island video was made. Use when the user asks for a new POV survival/mystery story video, a new chapter, or metadata.
---

# POV Story Video Skill (Viking Island method)

Goal: a 12–15 min, 1920x1080, 30 fps animated POV story ("YOU wake up on…") cut into short chapters, each built, previewed and delivered separately, then joined, then given SEO metadata. Nothing is skipped below.

## 0. Working rules (always)
- Talk to the user in Roman Urdu/English if they write that way; on-screen text and voiceover in English.
- One chapter per "next". Build -> preview contact sheet -> fix -> render -> deliver. Then wait for "next".
- Tell the user each chapter's length vs its script slot, and say honestly you did not listen to the audio.
- PG only: no romance/sexual content, deaths and killings happen off-screen, no gore (dark stains only), poison foam = blue bubble outlines.
- Flag history facts you have not verified (dates, numbers) instead of stating them as certain.
- Never print or commit API keys. TTS key comes from env var AI33_KEY.

## 1. Script (script.txt)
- Timestamped sections: `[0:00 – HOOK]`, `[1:00 – DAY 1]` … `[12:35 – THE FINAL TWIST]`, `[13:20 – OUTRO]`.
- Structure: Hook (60 s: the danger, the rule "30 DAYS", the deadline) -> Days (each one escalation + one clue) -> midpoint reveal -> villain revealed -> public trial/assembly -> vote -> final twist -> outro (question to viewer, plug previous video, subscribe ask).
- Speaker lines prefixed `JARL:`, `ULF:`, `YOU:` etc.; everything else is narrator.
- Mix real history into each chapter (law, outlaws, sagas, assembly, archaeology) as on-screen "REAL HISTORY" parchment cards with a counter or year.
- Each chapter ends on a hook card ("NEXT: DAY 30 — THE VOTE", "BUT CAN YOU PROVE IT?").
- Check for plot holes and ask the user (e.g. "only woman on the island" vs other characters).

## 2. Voices (ai33.pro TTS, ElevenLabs voices) – work/ai33/tts.py
- `POST https://api.ai33.pro/v3/text-to-speech` (form: text, voice_id, speed, with_transcript=true), header `xi-api-key`. Poll `GET /v1/task/{id}`; audio at `metadata.audio_url`, word timings at `metadata.json_url`.
- Cast used: Narrator Joel `elevenlabs_G7bJ0cnNDezf2z9EA3FB`; Jarl Brad `elevenlabs_9z2KRE0crZu7bZt1ZfUH`; Hakon Callum `elevenlabs_N2lVS1w4EtoT3dr4eOWO`; Torstein/crowd Harry `elevenlabs_SOYHLrjzK2X1ezoPC6cr`; YOU Sarah `elevenlabs_EXAVITQu4vr4xnSDxMaL`; Ulf Brian `elevenlabs_nPczCjzI2devNBz1zQrb`. Spare: Liam `elevenlabs_TX3LPaxmHKxFdv7VOQHJ`.
- Per chapter `gen_vo.py`: list of (id, voice, text); ids start with speaker letter (n narrator, j jarl, h hakon, u ulf, y you, t torstein). Generate in parallel, write `lines.json`, `vo/<id>.mp3`, `vo/<id>.json`. Print word lists with indexes – shots and pop-ups are timed to word indexes `wt(line, i)`.
- Spell hard names phonetically for TTS (Skógarmaðr), keep the real spelling in captions; fix TTS misspellings in caption FIX map.

## 3. Visual style (reference: YouTube UtXsABU4Cek style)
- Flat 2D bean characters (round black face, big white eyes, helmets/beards), layered parallax sets (village, beach, forest, cliff, night), haze, vignette, film grain, soft glow.
- 1–3 s shots, slow push-ins/pull-back reveals, rack focus (focus/ap in camera), speaker name pills, big bold pop-up words (Fredoka), spaced label boxes (Nunito), stamps (OUTLAW, LAWSPEAKER), parchment history cards, counters (0→40 WARRIORS, YEAR 930), word-by-word captions with the current word highlighted yellow.
- Hero "YOU" = red hooded character (HERO_V). Every chapter opens with a title card (DAY N / NAME).

## 4. Code map (work/)
- `viking3/v3.py`: renderer core – `build()` sets, `crowd()`, `Actor(kind,x,z,look,expr,pose,size)`, `rand_viking`, `cam_bg`, `boat_img`, `waves`, `make_post`, `fastblur`, `glow_cache`, easing (`ease`, `eio`, `back`, `lerp`, `clamp`), `title_card`, `paste_safe`, constants W,H,FPS.
- `viking_full/hook/hook.py`: `render_world2(frame, actors, cam, t)`, `caption2` (word captions from TL), `label_box`, `big_card`, `pop(frame,img,scale,x,y)`, `tint`, `dur`.
- `day1`: `village_set`, `bubble`, `name_pill`, `parchment`, `HAKON_V`, `JARL_V`. `day2`: `tooth_img`, `splash`. `day4`: `stamp`, `bigtxt`, `bone_img`, `chest_img`. `day6`: `TOR_V`. `day14`: `ULF_V`, `outlaw_v`, `snowfall`, `flames`. `day17`: `GUN_V`. `day26`: `rock_img`, `on_rock`. `day30`: `night`, `torches`, `close` (character close-up).
- Each chapter folder: `gen_vo.py`, `dayN.py` (timeline TL from VO + GAP pauses, SHOTS list, `run(frames,out)`), `mix_dayN.py`.
- `viking/sfx`: boom, crash, crowd, ding, drum, pad (music bed), rain, storm, thunder, waves. `viking3/sfx`: clash, ting, whoosh. There is NO wind.wav.

## 5. Build a new chapter (exact steps)
1. Read its section: `awk '/\[12:35/,/\[13:20/' script.txt`.
2. Copy the newest chapter folder's `gen_vo.py`, edit lines and voices, run it with the python that has `requests`.
3. Copy the newest `dayN.py` (twist/outro are the cleanest templates). Edit: sys.path list, GAP dict, SHOTS (name, start time from `S_(id)` / `wt(id, word)`), and the `if name == ...` shot blocks. Keep post (glow, haze, dark, captions, grain, fade in/out).
4. `python3 dayN.py info` (duration and shot spans). `python3 dayN.py prev` -> JPEGs in prev/, tile them: `ffmpeg -pattern_type glob -i 'prev/*.jpg' -vf "scale=480:-2,tile=4x3" -frames:v 1 sheet.jpg`. Look at it, fix overlaps, unreadable text, missing glyphs (no "→" in the fonts; use ">>>"), oversized characters.
5. Mix: copy the previous `mix_*.py` and replace only the cue block between `seg(S + 'crash.wav', sh['fire']` (or the first `seg(`) and `inputs = []`. Cues: `seg(file, start, end, vol)` for beds, `m.append((file, time, vol, length))` for hits. Whoosh on every cut, ding on label pops, drum on reveals, boom on stamps/ending. Music ducks (sidechain) under VO; loudnorm -14 LUFS.
6. Render in two halves in parallel to /tmp: `python3 dayN.py render 0 HALF /tmp/a.mp4 & python3 dayN.py render HALF N /tmp/b.mp4 & wait` (libx264 veryfast, crf 18–21, yuv420p). Concat with the mix: `ffmpeg -f concat -safe 0 -i list.txt -i mix.m4a -map 0:v -map 1:a -c copy -shortest -movflags +faststart out.mp4`. Check duration, then copy to out/ as `viking_chNN_name.mp4`.
7. Deliver with one short line: what happens in it, its length vs slot, any known flaw.
- Gotchas: `hexc(x)[:3] + (a,)` not `hexc(x)+(a,)`; encode to /tmp then copy; don't probe a file still being written; no `pgrep -f` wait loops; ~3–4 min render per 30 s on 2 CPUs.

## 6. Full video
- All chapters share codec settings, so join losslessly: `for i in 1..16: file 'viking_chi_*.mp4'` -> `ffmpeg -f concat -c copy`. That gave 14:18 at 2.1 GB; re-encode for delivery: `-c:v libx264 -preset veryfast -crf 27 -c:a aac -b:a 160k -movflags +faststart` -> about 100 MB.
- Compute YouTube chapter timestamps from real file durations (cumulative ffprobe), not from the script.

## 7. YouTube metadata
- Title under ~65 chars, curiosity + stakes + number ("You Washed Up on a Hidden Viking Island. You Have 30 Days.") plus 2 A/B alternatives.
- Description: 2-line hook, what the viewer will see, comment question, CHAPTERS from real timestamps (start 0:00, each ≥10 s), plug of the previous video, subscribe ask, 3 hashtags.
- Tags under 500 characters: main topic, POV/survival, history terms, animation terms, "what if" phrasing.

## 8. Setup on a new machine
`unzip`, `./setup.sh` (rewrites paths, installs pillow/requests/numpy), `export AI33_KEY=...`, install ffmpeg. Fonts are in work/viking2.
