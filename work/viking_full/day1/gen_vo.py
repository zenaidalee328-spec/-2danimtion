import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
JOEL="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; HARRY="elevenlabs_SOYHLrjzK2X1ezoPC6cr"; CAL="elevenlabs_N2lVS1w4EtoT3dr4eOWO"
L=[("n01",JOEL,"Day one.",None),
("n02",JOEL,"Nobody ties your hands. Nobody points a weapon at you.",None),
("n03",JOEL,"They wrap you in furs and carry you up to the village, like you're made of glass.",None),
("n04",JOEL,"You don't understand a word they say.",None),
("n05",JOEL,"Then you catch one:",None),
("v01",HARRY,"Rán.","Rawn."),
("n06",JOEL,"Your grandmother was Norwegian, and Norwegian grew out of Old Norse, the language the Vikings spoke.",None),
("n07",JOEL,"Icelandic stayed so close to it that Icelanders today can still read sagas written 800 years ago.","Icelandic stayed so close to it that Icelanders today can still read sagas written eight hundred years ago."),
("n08",JOEL,"So you understand one word in three.",None),
("n09",JOEL,"It's enough to work out that they think you're the daughter of Rán.","It's enough to work out that they think you're the daughter of Rawn."),
("n10",JOEL,"In Norse myth, Rán was the goddess of the sea.","In Norse myth, Rawn was the goddess of the sea."),
("n11",JOEL,"She caught drowning sailors in her net, and took them to her hall under the waves.",None),
("n12",JOEL,"Her nine daughters were the waves.",None),
("n13",JOEL,"You're not going to correct them.",None),
("n14",JOEL,"Then a young man pushes through the crowd. He's tall, with a cold smile.",None),
("n15",JOEL,"This is Hakon, the Jarl's son.",None),
("h01",CAL,"If she is Rán's daughter... then the sea cannot drown her.","If she is Rawn's daughter... then the sea cannot drown her."),
("n16",JOEL,"Nobody says a word.",None)]
json.dump([[a,b,c] for a,b,c,d in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex:
    list(ex.map(lambda x: tts(x[3] or x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
