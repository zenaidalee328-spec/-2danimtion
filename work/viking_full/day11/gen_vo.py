import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; C="elevenlabs_N2lVS1w4EtoT3dr4eOWO"; Y="elevenlabs_EXAVITQu4vr4xnSDxMaL"
L=[("n01",J,"Day eleven. The sky is clear and blue, and the men are loading the longships for a big fishing trip.",None),
("n02",J,"Then you glance at your diving watch. It has a barometer, and the pressure is dropping fast.",None),
("n03",J,"When air pressure crashes like that, a storm is coming.",None),
("y01",Y,"Nobody goes out. A storm is coming.",None),
("h01",C,"There isn't a cloud in the sky!",None),
("n04",J,"The Jarl looks at you for a long moment... then he orders the ships to stay on the beach.",None),
("n05",J,"Three hours later, the storm hits so hard it tears roofs off the longhouses.",None),
("n06",J,"If those ships had gone out, half the village would be at the bottom of the sea.",None),
("n07",J,"Forty axes go up that night, just for you.",None),
("n08",J,"But the next morning, walking the beach after the storm, you see a thin line of smoke rising from the forest, on the far side of the island.",None),
("n09",J,"The Jarl told you there are only a hundred people here.",None),
("n10",J,"So who lit that fire?",None)]
json.dump([[a,b,c] for a,b,c,d in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[3] or x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
