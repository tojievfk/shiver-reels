"""Generates the demo reel assets in demo/ (images + narration) from demo/story.json.

Usage: POLLINATIONS_KEY=sk_... python tools/make_demo.py
Uses the same requests the web app makes, so it doubles as an API check.
"""
import io, json, os, sys, time, urllib.parse
import requests
from PIL import Image

API = "https://gen.pollinations.ai"
KEY = os.environ.get("POLLINATIONS_KEY") or sys.exit("Set POLLINATIONS_KEY first.")
HDR = {"Authorization": f"Bearer {KEY}"}
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "demo")
story = json.load(open(os.path.join(ROOT, "story.json")))


def retry(fn, tries=4):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            print("  retry:", e)
            time.sleep(2 * (i + 1))
    sys.exit("failed")


def image(prompt, seed, out):
    url = f"{API}/image/{urllib.parse.quote(prompt)}?model=klein&width=720&height=1280&seed={seed}&nologo=true"
    def go():
        r = requests.get(url, headers=HDR, timeout=180)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        print("  image", im.size, len(r.content))
        im.save(out, quality=84, optimize=True)
    retry(go)


def voice(text, out):
    def go():
        r = requests.post(f"{API}/v1/audio/speech", headers=HDR, timeout=180,
                          json={"model": "microsoft/mai-voice-2.1", "voice": story["voice"],
                                "input": text, "response_format": "mp3"})
        r.raise_for_status()
        if len(r.content) < 1500:
            raise ValueError("audio too short")
        open(out, "wb").write(r.content)
        print("  voice", len(r.content))
    retry(go)


for i, line in enumerate(story["lines"], 1):
    p = f"{story['style']}. {line['scene']}. The narrator: {story['character']}. Vertical 9:16 composition, no text, no watermark."
    if not os.path.exists(os.path.join(ROOT, f"{i}.jpg")):
        image(p, 4100 + i, os.path.join(ROOT, f"{i}.jpg"))
    if not os.path.exists(os.path.join(ROOT, f"v{i}.mp3")):
        voice(line["say"], os.path.join(ROOT, f"v{i}.mp3"))
if not os.path.exists(os.path.join(ROOT, "vq.mp3")):
    voice(story["question"], os.path.join(ROOT, "vq.mp3"))
print("done")
