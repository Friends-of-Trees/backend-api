from dotenv import load_dotenv
import os

# ✅ FORCE load .env from backend folder
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

HF_TOKEN = os.getenv("HF_TOKEN")
AI_MODEL = os.getenv("AI_DETECTOR_MODEL", "Ateeqq/ai-vs-human-image-detector")
# print("HF TOKEN:", HF_TOKEN)
# print("AI detector model:", AI_MODEL)

from transformers import pipeline
from PIL import Image
import requests
from io import BytesIO

cache = {}

# Load model once
detector = pipeline(
    "image-classification",
    model=AI_MODEL,
    token=HF_TOKEN
)

def is_ai_image_from_url(image_url: str) -> bool:
    if image_url in cache:
        return cache[image_url]

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content)).convert("RGB")
        image = image.resize((512, 512))

        result = detector(image)
        print("MODEL OUTPUT:", result)

        scores = {str(item["label"]).lower(): float(item["score"]) for item in result}
        ai_score = scores.get("ai", scores.get("artificial", 0.0))
        human_score = scores.get("hum", scores.get("human", 0.0))

        # Balanced decision rule using both score values.
        # - Strong AI probability should override human.
        # - If human is clearly stronger, treat as not AI.
        # - When scores are close, require a minimum AI confidence.
        score_diff = ai_score - human_score

        if ai_score >= 0.35 and score_diff > 0.05:
            is_ai = True
        elif human_score >= 0.35 and score_diff < -0.05:
            is_ai = False
        else:
            is_ai = ai_score > human_score and ai_score >= 0.2

        cache[image_url] = is_ai
        return is_ai

    except Exception as e:
        print("ERROR while processing image:", image_url)
        print("ERROR DETAILS:", str(e))
        return None
