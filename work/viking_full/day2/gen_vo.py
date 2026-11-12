import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; CAL="elevenlabs_N2lVS1w4EtoT3dr4eOWO"
L=[("n01",J,"Day two.",None),
("n02",J,"They row you out past the rocks at dawn, the whole village watching from the cliffs.",None),
("h01",CAL,"Go home to your mother.",None),
("n03",J,"And they push you in.",None),
("n04",J,"The water is so cold your chest locks. You can't breathe.",None),
("n05",J,"Your boots fill up and pull you down, and the light above you gets smaller... and smaller...",None),
("n06",J,"Then a hand grabs your jacket and pulls you up hard.",None),
("n07",J,"You hit the surface. A wave throws you onto the rocks, and when you look back, there's nobody there.",None),
("n08",J,"But there's something in your fist that wasn't there before:",None),
("n09",J,"a wolf's tooth on a leather cord.",None),
("n10",J,"On the cliff, a hundred Vikings are cheering.",None),
("n11",J,"The sea gave you back, so you really must be Rán's daughter.","The sea gave you back, so you really must be Rawn's daughter."),
("n12",J,"Only Hakon isn't cheering. He's staring at the water, trying to work out who saved you.",None),
("n13",J,"So are you. Keep that wolf tooth in mind.",None)]
json.dump([[a,b,c] for a,b,c,d in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[3] or x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
