import requests,time,sys,json,os
H={"xi-api-key":os.environ["AI33_KEY"]}
B="https://api.ai33.pro"
def tts(text,voice,out,speed=1,words=False):
    r=requests.post(B+"/v3/text-to-speech",data={"text":text,"voice_id":voice,"speed":str(speed),"with_transcript":"true" if words else "false"},timeout=60,headers=H).json()
    tid=r.get("task_id"); 
    if not tid: print(r); return
    for _ in range(90):
        t=requests.get(f"{B}/v1/task/{tid}",timeout=30,headers=H).json()
        st=t.get("status")
        if st in("done","completed","success"):
            url=(t.get("metadata") or {}).get("audio_url"); 
            open(out,"wb").write(requests.get(url,timeout=60).content)
            if words and (t.get("metadata") or {}).get("json_url"):
                open(out.rsplit(".",1)[0]+".json","w").write(requests.get(t["metadata"]["json_url"],timeout=60).text)
            print(out,"ok"); return t
        if st in("failed","error"): print(t); return
        time.sleep(2)
    print("timeout",t)
if __name__=="__main__":
    line="Imagine waking up on a frozen beach. You're alone. And then you hear it. A hundred Vikings, and every single one of them is staring at you."
    for n,v in [("liam","elevenlabs_TX3LPaxmHKxFdv7VOQHJ"),("joel","elevenlabs_G7bJ0cnNDezf2z9EA3FB"),("brian","elevenlabs_nPczCjzI2devNBz1zQrb")]:
        tts(line,v,f"sample_{n}.mp3")
    tts("Stranger. You have one night to prove your worth to my village.","elevenlabs_SOYHLrjzK2X1ezoPC6cr","sample_jarl_harry.mp3")
