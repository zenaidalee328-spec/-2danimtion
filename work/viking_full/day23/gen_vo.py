import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"
L=[("n01",J,"Day twenty-three. The pieces finally fit together.",None),
("n02",J,"Ten years ago, Hakon was sixteen.",None),
("n03",J,"He was playing with fire in the grain store... and burned it down.",None),
("n04",J,"He let his uncle take the blame. And his father, the Jarl, believed him.",None),
("n05",J,"Gunnar saw it. And Gunnar was about to tell everyone... so Hakon killed him.",None),
("n06",J,"Then you washed up, and the Jarl gave you Gunnar's hut... and Gunnar's chest, with the runes.",None),
("n07",J,"That's why Hakon wanted you dead from day one.",None),
("n08",J,"You go to the north marsh, and find fresh holes where water hemlock roots were dug up...",None),
("n09",J,"and boot prints the size of Hakon's.",None)]
json.dump([[a,b,c] for a,b,c,d in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[3] or x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
