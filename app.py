import streamlit as st
import os
import time
import base64
import json
import requests
from google import genai
import replicate
from PIL import Image, ImageOps
from io import BytesIO
import random

# ==========================================
# 1. CONFIGURAÇÃO DE CHAVES (VIA SECRETS)
# ==========================================
GOOGLE_KEY = st.secrets.get("GOOGLE_KEY", "")
REPLICATE_KEY = st.secrets.get("REPLICATE_KEY", st.secrets.get("REPLICATE_TOKEN", ""))

if REPLICATE_KEY:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_KEY

# --- PAGE CONFIG ---
st.set_page_config(page_title="Hollywood Casting", page_icon="🎬", layout="wide")

# ==========================================
# 2. ARQUÉTIPOS CINEMATOGRÁFICOS
# ==========================================
CASTING_ARCHETYPES = {
    "Resistance Leader": "Post-apocalyptic survivor, tactical gear, war paint, fierce gaze, desert ruins background, high contrast, gritty texture.",
    "Noir Mastermind": "Classic Film Noir style, dramatic chiaroscuro lighting, sharp suit or trench coat, mysterious atmosphere, detective office shadows.",
    "Frontier Explorer": "Sci-fi astronaut, high-tech space suit, bioluminescent details, alien planet landscape, cinematic lighting, epic scale.",
    "Lone Justiciar": "Modern Western vigilante, leather jacket, silhouette against sunset, dusty atmosphere, intense cinematic gaze.",
    "Epic Divinity": "High fantasy hero, ornate light armor, ethereal glowing elements, ancient forest background, magical atmosphere.",
    "Elite Disciplinarian": "Intense dramatic portrait, sweat and grit, professional training environment, focused expression, cinematic backlight.",
    "Classic Icon": "1920s high society glamour, luxury ballroom, velvet textures, classic Hollywood lighting, elegant stance.",
    "Cyberpunk Vigilante": "Cybernetic enhancements, neon-lit rainy street, tech-wear, futuristic city, vibrant teal and orange lighting.",
    "Zen Master": "Traditional martial arts attire, flowing fabric, serene temple or bamboo forest, perfect balance, soft morning mist.",
    "Arcane Investigator": "Supernatural detective, ancient library, floating books, mystical artifacts, warm candlelight vs cold shadows."
}

# ==========================================
# 3. UI / CSS (ESTILO DARK CINEMA)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=Oswald:wght@700&display=swap');
    :root { --gold: #D4AF37; --bg: #0F0F0F; }
    html, body, .stApp { background-color: var(--bg) !important; color: white !important; }
    h1 { font-family: 'Oswald' !important; color: var(--gold) !important; text-align: center; text-transform: uppercase; font-size: 3.5rem !important; }
    .quiz-card { background: #1A1A1A; border: 1px solid #333; padding: 25px; border-radius: 10px; text-align: center; }
    div.stButton > button { background: var(--gold) !important; color: black !important; font-weight: bold !important; width: 100%; border-radius: 5px; height: 50px; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. LÓGICA DE IA (ESTILO JFM)
# ==========================================

def get_casting_verdict(answers, api_key):
    try:
        client = genai.Client(api_key=api_key.strip())
        prompt = f"Casting Director: User likes {answers}. Match one from {list(CASTING_ARCHETYPES.keys())}. Return ONLY JSON: {{\"archetype\": \"name\", \"reason\": \"short sentence\"}}"
        # Usando a versão solicitada no blueprint
        response = client.models.generate_content(model='gemini-2.5-flash', contents=[prompt])
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        return {"archetype": random.choice(list(CASTING_ARCHETYPES.keys())), "reason": "Your screen presence is undeniable."}

def generate_poster_assincrono(image_path, archetype_key, gender, api_key):
    client = replicate.Client(api_token=api_key.strip())
    style = CASTING_ARCHETYPES[archetype_key]
    
    # Codificação idêntica ao JFM
    with open(image_path, "rb") as f:
        img_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"

    # Frases de carregamento estilo Cinema
    loading_phrases = ["🎬 Setting up the lights...", "📽️ Loading 35mm film...", "🎭 Applying cinematic makeup...", "🎞️ Developing the negatives...", "✨ Calibrating star power...", "🌟 Casting the spell..."]

    try:
        # A MÁGICA: Pega a versão exata do modelo (Fix 422)
        model = client.models.get("google/nano-banana-pro")
        inputs = {
            "image_input": [img_b64],
            "prompt
