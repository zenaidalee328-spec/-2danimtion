import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; C="elevenlabs_N2lVS1w4EtoT3dr4eOWO"; B="elevenlabs_9z2KRE0crZu7bZt1ZfUH"; Y="elevenlabs_EXAVITQu4vr4xnSDxMaL"
L=[("n01",J,"Day eight. You'd think saving a man would make you a hero. Instead, Hakon stands up at the assembly.",None),
("h01",C,"The food was on HER plate. She brought death to our feast.","The food was on her plate! She brought death to our feast."),
("h02",C,"She is no goddess. She is a witch!",None),
("n02",J,"Now you're on trial for poisoning the man you saved.",None),
("n03",J,"But you saw Torstein's symptoms: shaking, foaming at the mouth, seizures.",None),
("n04",J,"That's water hemlock, one of the most poisonous plants in Europe, and it only grows in wet ground.",None),
("y01",Y,"Where is the marsh on this island?",None),
("j01",B,"...The north side.","The north side."),
("y02",Y,"I've never been to the north side. You've watched me every day. Who has?",None),
("n05",J,"The hall goes quiet. Nobody answers, but somebody's boots are still caked in black marsh mud.",None),
("n06",J,"You can't prove anything yet, so you say nothing.",None),
("n07",J,"You're cleared. But now the killer knows you're hunting him.",None)]
json.dump([[a,b,c] for a,b,c,d in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[3] or x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
