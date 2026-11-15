import json, hashlib, os, re, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from course_data import UNITS, SOUNDS
from TTS.utils.synthesizer import Synthesizer

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "site")
AUD_DIR = os.path.join(OUT, "audio")
os.makedirs(AUD_DIR, exist_ok=True)
VITS = "/home/claude/tts2/tts_models--de--thorsten--vits"
# F = natural voice (narration, vocabulary, Herr Weber); M = 2 semitones lower (Herr Miller); R = natural (voicemails)
PITCH = {"F": None, "M": 0.89, "R": None}

def tts_key(t):
    t = re.sub(r"\s*/\s*", ", ", t)
    t = re.sub(r"[„“\"]", "", t)
    return t.replace("…", "").strip()

# respellings for words the German dictionary gets wrong (applied to speech input only)
RESPELL = [(r"\bWiederhören\b","Wieder-hören"),(r"\bHandy\b","Händi"),(r"\bChefin\b","Schäffin"),(r"\bChef\b","Schäff"),
  (r"Meeting","Mieting"),(r"\bChicago\b","Schikago"),(r"\bUSA\b","Uh Es Ah"),(r"\bIT\b","Ih-Teh"),(r"\bE-Mail\b","Ih-mehl"),
  (r"\bBudget\b","Büdsche"),(r"\bSoftware\b","Sofftwär"),(r"nalyst","nalüst"),(r"nalyse","nalüse"),(r"bteilung","btailung"),
  (r"\bvier\b","fier"),(r"\b([Vv])ielen\b",lambda m:("F" if m.group(1)=="V" else "f")+"ielen"),(r"\bProblem\b","Problehm"),
  (r"\bMontag\b","Mohntag"),(r"\brufe\b","ruhfe")]

pairs = {}
def need(text, v="F"):
    if v == "W": v = "F"
    k = tts_key(text)
    if k: pairs[(v, k)] = None

for s in SOUNDS: need(s["ex"])
for u in UNITS:
    if not u.get("full"): continue
    B = u["bruecke"]
    for c in B["cognates"]: need(c["de"])
    for r in B["rules"]:
        for p in r["ex"] + r["guess"]: need(p[1])
    for x in B["extra"]: need(x["de"])
    for v in u["vocab"]: need(v["de"])
    for l in u["dialog"]["lines"]: need(l["de"], "F" if l["s"] == "W" else "M")
    need(u["hoeren"]["text"], u["hoeren"]["voice"])
    for d in u["hoeren"]["diktat"]: need(d)
    for d in u["denken"]: need(d["de"], "M")
    for b in u["builder"]:
        for a in b["a"]: need(a, "M")
    for t in u["tippen"]: need(t)
    if "lesen" in u:
        for x in u["lesen"]["sentences"]: need(x["de"])
        for w in u["lesen"]["gloss"]: need(w)
need("Ich wohne in Chicago.")

MESSAGES = {tts_key(u['hoeren']['text']) for u in UNITS if u.get('full')}
syn = Synthesizer(tts_checkpoint=f"{VITS}/model_file.pth", tts_config_path=f"{VITS}/config.json", use_cuda=False)

def synth(v, text, path_wav, kind="normal"):
    sr = syn.output_sample_rate
    t = text
    for a, b in RESPELL: t = re.sub(a, b, t)
    segs = [x.strip() for x in re.split(r",\s*", t) if x.strip()]
    short = all(len(x.split()) <= 3 for x in segs)
    if kind == "message": scale, segs = 1.1, [t]
    elif short: scale = 1.4                      # single words / short items: slow and clear, one by one
    else: scale, segs = 1.2, [t]                 # sentences: a bit slower than natural
    syn.tts_model.length_scale = scale
    parts = [np.zeros(int(sr*0.15), dtype=np.float32)]
    for sg in segs:
        w = np.asarray(syn.tts(sg), dtype=np.float32).flatten()
        thr = 0.02 * (np.max(np.abs(w)) or 1); idx = np.where(np.abs(w) > thr)[0]
        if len(idx): w = w[max(0, idx[0]-int(sr*0.04)): idx[-1]+int(sr*0.08)]   # trim engine padding, keep soft edges
        parts += [w, np.zeros(int(sr*0.6), dtype=np.float32)]
    a = np.concatenate(parts); peak = float(np.max(np.abs(a))) or 1.0
    a = (a / peak * 0.9 * 32767).astype(np.int16)
    with wave.open(path_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(a.tobytes())
    if PITCH.get(v):
        tmp = path_wav + ".p.wav"
        subprocess.run(["ffmpeg","-loglevel","error","-y","-i",path_wav,"-af",f"rubberband=pitch={PITCH[v]}:formant=preserved",tmp], check=True)
        os.replace(tmp, path_wav)

aud = {}
made = 0
for (v, k) in sorted(pairs):
    h = hashlib.sha1(f"v5|{v}|{k}".encode()).hexdigest()[:10]
    fn = f"{v}{h}.mp3"
    mp3 = os.path.join(AUD_DIR, fn)
    if not os.path.exists(mp3):
        wav = mp3[:-4] + ".wav"
        synth(v, k, wav, 'message' if k in MESSAGES else 'normal')
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-ac", "1", "-b:a", "56k", mp3], check=True)
        os.remove(wav); made += 1
    aud[f"{v}|{k}"] = f"audio/{fn}"

tpl = open(os.path.join(BASE, "template.html"), encoding="utf-8").read()
html = (tpl.replace("__CSS__", open(os.path.join(BASE,"base.css"),encoding="utf-8").read()).replace("__UNITS__", json.dumps(UNITS, ensure_ascii=False))
           .replace("__SOUNDS__", json.dumps(SOUNDS, ensure_ascii=False))
           .replace("__AUD__", json.dumps(aud, ensure_ascii=False)))
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html)
total = sum(os.path.getsize(os.path.join(AUD_DIR, f)) for f in os.listdir(AUD_DIR))
print(f"clips: {len(aud)} (new {made}), audio total {total/1e6:.2f} MB, html {len(html)/1e3:.0f} KB")
