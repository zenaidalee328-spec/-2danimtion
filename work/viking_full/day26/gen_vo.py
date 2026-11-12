import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; C="elevenlabs_N2lVS1w4EtoT3dr4eOWO"
L=[("n01",J,"Day twenty-six. You call a Thing... the Viking assembly, where disputes were settled in front of everyone."),
("n02",J,"It's real history. Iceland's Thing, the Althing, began in the year nine thirty, and is one of the oldest parliaments in the world."),
("n03",J,"A lawspeaker stood on a great rock, and recited the law from memory."),
("n04",J,"You stand on that rock, and tell them everything. The fire. Gunnar. The poison. The runes."),
("n05",J,"Hakon just smiles."),
("h01",C,"The word of an outlaw means nothing under our law. And the word of a foreign woman... means even less."),
("n06",J,"Then forty warriors step behind him. His friends. His crew. Men he's been buying with silver for years."),
("n07",J,"And you realize what that means. Forty axes will never go up for you."),
("n08",J,"You've already lost the vote.")]
json.dump([list(x) for x in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
