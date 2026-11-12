import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; U="elevenlabs_nPczCjzI2devNBz1zQrb"
L=[("n01",J,"Day seventeen. You keep sneaking back to the outlaw camp with food.",None),
("n02",J,"Ulf teaches you to set snares, and you teach him how to make a fishing net that doesn't tangle.",None),
("n03",J,"Then you show him Gunnar's runes... and Ulf goes pale.",None),
("u01",U,"It says... Ulf did not light the fire.",None),
("u02",U,"I saw who did. I will speak at the Thing.",None),
("n04",J,"Gunnar knew the truth for ten years.",None),
("n05",J,"He finally decided to tell everyone... and the very next night, he died.",None)]
json.dump([[a,b,c] for a,b,c,d in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[3] or x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
