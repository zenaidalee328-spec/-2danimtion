import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; C="elevenlabs_N2lVS1w4EtoT3dr4eOWO"; R="elevenlabs_SOYHLrjzK2X1ezoPC6cr"
L=[("n01",J,"Day six. The village throws a feast in your honor: smoked fish, mutton, mead, and drums.",None),
("n02",J,"Hakon himself brings you a plate.",None),
("h01",C,"For the daughter of the sea.",None),
("n03",J,"But before you can eat, a big warrior called Torstein grabs a piece off your plate, and laughs.",None),
("t01",R,"Goddesses don't get hungry!",None),
("n04",J,"Thirty seconds later, he's shaking. Then he's on the floor... and then he stops breathing.",None),
("n05",J,"Back home, you're a lifeguard, so you do the one thing nobody here has ever seen.",None),
("n06",J,"You tilt his head back, and push on his chest. Thirty times, then two breaths. Again, and again.",None),
("n07",J,"The whole hall goes silent.",None),
("n08",J,"Modern CPR was only invented around 1960.","Modern CPR was only invented around nineteen sixty."),
("n09",J,"To these people, you look like you're pushing life back into a dead man.",None),
("n10",J,"Then Torstein coughs. He's alive.",None),
("n11",J,"And that food... was meant for you.",None)]
json.dump([[a,b,c] for a,b,c,d in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[3] or x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
