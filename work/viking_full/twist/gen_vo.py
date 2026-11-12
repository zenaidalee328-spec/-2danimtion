import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; B="elevenlabs_9z2KRE0crZu7bZt1ZfUH"; U="elevenlabs_nPczCjzI2devNBz1zQrb"
L=[("n01",J,"Then the Jarl turns to you."),
("j01",B,"Now. The vote for you."),
("n02",J,"But nobody raises an axe. Instead, all hundred warriors lay their axes on the ground... at your feet."),
("u01",U,"By our law, the one who brings justice to the Thing doesn't stay as a guest. She becomes the Lawspeaker."),
("n03",J,"You washed up as a stranger... and thirty days later, you're the voice of their law."),
("n04",J,"The next morning, on day thirty-one, a fishing boat appears on the horizon."),
("n05",J,"It's the first ship in ten years... and it could take you home.")]
json.dump([list(x) for x in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
