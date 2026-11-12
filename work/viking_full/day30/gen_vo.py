import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; B="elevenlabs_9z2KRE0crZu7bZt1ZfUH"; Y="elevenlabs_EXAVITQu4vr4xnSDxMaL"; C="elevenlabs_N2lVS1w4EtoT3dr4eOWO"; R="elevenlabs_SOYHLrjzK2X1ezoPC6cr"
L=[("n01",J,"Day thirty. The last night. Torches burn on the cliff... and a hundred Vikings stand in a circle, with their axes."),
("j01",B,"Daughter of the sea. Ask the Thing to let you stay."),
("n02",J,"You don't. Instead, you say:"),
("y01",Y,"I ask the Thing... to bring Ulf home."),
("n03",J,"Silence. Hakon laughs."),
("h01",C,"Forty axes say no."),
("n04",J,"Then Torstein steps out of Hakon's forty. The man who died at the feast... and came back."),
("t01",R,"I was dead on that floor. And your plate put me there, Hakon. She brought me back."),
("n05",J,"He raises his axe. Then another man steps out... and another. And one by one, Hakon's forty fall apart."),
("n06",J,"Finally, only two axes are still down. Hakon's... and his father's."),
("n07",J,"The Jarl looks at his son for a very long time. Then he raises his axe."),
("j02",B,"Brother. Come home."),
("n08",J,"Ulf walks out of the trees... and the whole cliff roars."),
("n09",J,"Hakon gets the sentence he gave his uncle. The forest.")]
json.dump([list(x) for x in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
