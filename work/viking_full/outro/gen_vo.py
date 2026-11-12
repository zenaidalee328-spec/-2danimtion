import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"
L=[("n01",J,"So what would you do? Take the boat home... or stay, and become the Lawspeaker of a hidden Viking island?"),
("n02",J,"Tell me in the comments."),
("n03",J,"And if you watched, The Only Man on an Island of Amazons, tell me which story was better."),
("n04",J,"Please subscribe. It really helps a small creator like me.")]
json.dump([list(x) for x in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(4) as ex: list(ex.map(lambda x: tts(x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
