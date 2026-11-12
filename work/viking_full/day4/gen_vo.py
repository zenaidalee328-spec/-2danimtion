import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; B="elevenlabs_9z2KRE0crZu7bZt1ZfUH"
L=[("n01",J,"Day four. The Jarl gives you a job.",None),
("j01",B,"Rán's daughter knows the sea. You will read it for us.","Rawn's daughter knows the sea. You will read it for us."),
("n02",J,"You're their new navigator. You ask what happened to the old one.",None),
("j02",B,"Gunnar. He walked into the fog one night, and did not come back. The sea took him.",None),
("n03",J,"You get Gunnar's hut.",None),
("n04",J,"Under his bed you find a wooden chest. Inside are his tools, and a strip of bone carved with runes you can't read.",None),
("n05",J,"Then you look closer at the blanket. It's covered in dark stains... the kind fog doesn't leave.",None),
("n06",J,"Gunnar didn't walk into the sea. Somebody killed him the night before you arrived.",None),
("n07",J,"And women at the helm isn't just a story.",None),
("n08",J,"In 1878, archaeologists in Sweden opened a famous Viking warrior's grave at Birka.","In eighteen seventy-eight, archaeologists in Sweden opened a famous Viking warrior's grave at Birka."),
("n09",J,"It held a sword, an axe, a spear, arrows, two horses, and a strategy board game,",None),
("n10",J,"so it looked like the grave of a commander.",None),
("n11",J,"For 130 years everyone assumed it was a man.","For a hundred and thirty years, everyone assumed it was a man."),
("n12",J,"In 2017, DNA proved the warrior was a woman.","In twenty seventeen, DNA proved the warrior was a woman.")]
json.dump([[a,b,c] for a,b,c,d in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[3] or x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
