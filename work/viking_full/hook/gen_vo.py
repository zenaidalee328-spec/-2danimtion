import sys,json,concurrent.futures as cf
sys.path.insert(0,'/workspace/work/ai33'); from tts import tts
JOEL="elevenlabs_G7bJ0cnNDezf2z9EA3FB"; BRAD="elevenlabs_9z2KRE0crZu7bZt1ZfUH"
L=[("n01",JOEL,"You're the only woman on an island of one hundred Vikings."),
("n02",JOEL,"And every single one of them just dropped to his knees."),
("n03",JOEL,"Twelve hours ago, your sailboat broke apart in a North Atlantic storm."),
("n04",JOEL,"You held on to a piece of the mast, until the waves threw you onto a black stone beach."),
("n05",JOEL,"When you opened your eyes, a hundred warriors were standing over you."),
("n06",JOEL,"And then... they knelt."),
("j01",BRAD,"One moon. Thirty days."),
("n07",JOEL,"That's the law here. Anything the sea gives back stays for thirty days."),
("n08",JOEL,"On the thirtieth night, all hundred warriors vote with their axes."),
("n09",JOEL,"If every axe goes up, you stay forever."),
("n10",JOEL,"If even one stays down... you go back to the sea."),
("n11",JOEL,"But here's what nobody tells you on day one:"),
("n12",JOEL,"someone on this island wants you dead, before the vote ever happens."),
("n13",JOEL,"By day thirty, you'll know who. And you won't believe why.")]
json.dump(L,open('lines.json','w'))
with cf.ThreadPoolExecutor(5) as ex:
    list(ex.map(lambda x: tts(x[2],x[1],f"vo/{x[0]}.mp3",words=True), L))
