import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
J="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; B="elevenlabs_9z2KRE0crZu7bZt1ZfUH"; Y="elevenlabs_EXAVITQu4vr4xnSDxMaL"
L=[("n01",J,"Day twenty-eight. The Jarl comes to your hut... alone, in the middle of the night."),
("j01",B,"I knew."),
("n02",J,"He knew Hakon set the fire... from the very first night."),
("j02",B,"He was my only son. So I sent my brother to the forest instead. I have carried it... for ten years."),
("y01",Y,"And Gunnar?"),
("j03",B,"That... I did not know."),
("n03",J,"He looks a hundred years old."),
("j04",B,"In two nights, you will lose the vote. I cannot save you. I could not even save my brother.")]
json.dump([list(x) for x in L],open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex: list(ex.map(lambda x: tts(x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
