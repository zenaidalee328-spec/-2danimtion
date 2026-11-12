import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; U="elevenlabs_nPczCjzI2devNBz1zQrb"; Y="elevenlabs_EXAVITQu4vr4xnSDxMaL"
L=[("n01",J,"Day twenty. You're sitting by Ulf's fire when you notice the cord around his neck.",None),
("n02",J,"It's the same leather... but it's empty.",None),
("n03",J,"You pull the wolf tooth out of your pocket.",None),
("u01",U,"I watch the village from the cliffs, every day. I saw them throw you in.",None),
("y01",Y,"Why did you save me?",None),
("u02",U,"Because I know what it's like... when your whole village decides you belong to the sea.",None)]
json.dump([[a,b,c] for a,b,c,d in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[3] or x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
