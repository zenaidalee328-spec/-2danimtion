import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; U="elevenlabs_nPczCjzI2devNBz1zQrb"
L=[("n01",J,"Day fourteen. You follow the smoke deep into the forest... and walk straight into a knife.",None),
("n02",J,"There are five men living in the trees. They're thin and wild, dressed in wolf skins.",None),
("n03",J,"They're outlaws.",None),
("n04",J,"That's real Viking law. The worst punishment wasn't death. It was being made an outlaw.",None),
("n05",J,"A skógarmaðr. A forest man.","A skoh-gar-mathur. A forest man."),
("n06",J,"Nobody could feed you, shelter you, or help you. And anyone could kill you.",None),
("n07",J,"The famous outlaw Grettir the Strong survived like that for almost twenty years.",None),
("n08",J,"Their leader steps forward. He has grey in his beard... and the same eyes as the Jarl.",None),
("u01",U,"I am Ulf. The Jarl is my brother.",None),
("n09",J,"Ten years ago, the village grain store burned down in the middle of winter.",None),
("n10",J,"People starved, and Ulf was blamed.",None),
("n11",J,"His own brother made him an outlaw.",None)]
json.dump([[a,b,c] for a,b,c,d in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[3] or x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
