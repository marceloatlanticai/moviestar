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
            "prompt": f"Professional movie still of a {gender} as a {style}. High-end cinematic lighting, 8k masterpiece.",
            "negative_prompt": "distorted, cartoon, bad face, text, logo, watermark",
            "prompt_strength": 0.45,
            "guidance_scale": 12.0,
            "aspect_ratio": "2:3"
        }
        
        prediction = client.predictions.create(version=model.latest_version, input=inputs)
        
        # Loop de progresso estilo JFM
        progress_bar = st.progress(0, text="Initializing Director's Cut...")
        start_time = time.time()
        phrase_idx = 0
        
        while prediction.status not in ["succeeded", "failed", "canceled"]:
            if time.time() - start_time > 300: break 
            current_phrase = loading_phrases[phrase_idx % len(loading_phrases)]
            progress_bar.progress(60, text=current_phrase)
            phrase_idx += 1
            time.sleep(4)
            prediction.reload()
            
        if prediction.status == "succeeded":
            progress_bar.empty()
            output = prediction.output[0] if isinstance(prediction.output, list) else prediction.output
            return output
        return None
    except Exception as e:
        st.error(f"AI Director Error: {e}")
        return None

# ==========================================
# 5. FLUXO DO APP
# ==========================================
st.markdown("<h1>Hollywood Casting</h1>", unsafe_allow_html=True)

if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state.answers = []

QUIZ_QUESTIONS = [
    {"step": 1, "question": "Choose the world you belong to:", "options": [{"label": "THE FRONTIER", "tag": "Explorer"}, {"label": "THE STREETS", "tag": "Vigilante"}]},
    {"step": 2, "question": "What defines your strategy?", "options": [{"label": "THE ARCHITECT", "tag": "Mastermind"}, {"label": "THE AVENGER", "tag": "Epic"}]},
    {"step": 3, "question": "Pick your visual atmosphere:", "options": [{"label": "NEON DREAMS", "tag": "Cyberpunk"}, {"label": "GOLDEN AGE", "tag": "Classic"}]}
]

if st.session_state.step < len(QUIZ_QUESTIONS):
    q = QUIZ_QUESTIONS[st.session_state.step]
    st.markdown(f"<h3 style='text-align:center;'>{q['question']}</h3>", unsafe_allow_html=True)
    cols = st.columns(2)
    for i, opt in enumerate(q['options']):
        with cols[i]:
            st.markdown(f"<div class='quiz-card'><h4>{opt['label']}</h4></div>", unsafe_allow_html=True)
            if st.button(f"SELECT {opt['label']}", key=f"q{st.session_state.step}{i}"):
                st.session_state.answers.append(opt['tag'])
                st.session_state.step += 1
                st.rerun()

elif st.session_state.step == len(QUIZ_QUESTIONS):
    st.markdown("### 📸 Final Step: Your Headshot")
    gender = st.selectbox("I am an:", ["Actor", "Actress"])
    file = st.file_uploader("Upload your photo", type=["jpg", "png", "jpeg"])
    if file:
        img = ImageOps.exif_transpose(Image.open(file)).convert('RGB')
        st.image(img, width=400)
        if st.button("GENERATE MY MOVIE POSTER"):
            with st.status("🎬 Directing with Gemini 2.5 & Nano Banana...") as status:
                img.save("temp.jpg")
                v = get_casting_verdict(st.session_state.answers, GOOGLE_KEY)
                url = generate_poster_assincrono("temp.jpg", v['archetype'], gender, REPLICATE_KEY)
                if url:
                    st.session_state.url = url
                    st.session_state.v = v
                    st.session_state.step += 1
                    status.update(label="Cut! It's perfect.", state="complete")
                    st.rerun()
else:
    st.balloons()
    st.markdown(f"<h2 style='color:#D4AF37; text-align:center;'>THE {st.session_state.v['archetype'].upper()}</h2>", unsafe_allow_html=True)
    st.image(st.session_state.url, use_container_width=True)
    
    res = requests.get(st.session_state.url)
    st.download_button("DOWNLOAD POSTER", data=res.content, file_name="casting.png", mime="image/png")
    
    if st.button("RESTART AUDITION"):
        st.session_state.step = 0
        st.rerun()
