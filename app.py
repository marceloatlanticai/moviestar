import streamlit as st
import os
import base64
import json
import requests
from google import genai
import replicate
from PIL import Image, ImageOps
from io import BytesIO

# ==========================================
# 1. CONFIGURAÇÃO DE CHAVES (VIA SECRETS)
# ==========================================
GOOGLE_KEY = st.secrets.get("GOOGLE_KEY", "")
REPLICATE_KEY = st.secrets.get("REPLICATE_KEY", st.secrets.get("REPLICATE_API_TOKEN", ""))

if REPLICATE_KEY:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_KEY

# --- PAGE CONFIG ---
st.set_page_config(page_title="Hollywood Casting", page_icon="🎬", layout="wide")

# ==========================================
# 2. CONTEÚDO
# ==========================================
CASTING_ARCHETYPES = {
    "Resistance Leader": "Post-apocalyptic survivor, tactical gear, war paint, fierce gaze, desert ruins, cinematic lighting, gritty.",
    "Noir Mastermind": "Film Noir style, chiaroscuro lighting, suit and fedora, mysterious, detective office shadows, 1940s.",
    "Frontier Explorer": "Sci-fi astronaut, high-tech suit, bioluminescent details, alien planet, epic cinematic scale.",
    "Lone Justiciar": "Modern Western vigilante, leather jacket, silhouette against sunset, dusty, intense gaze.",
    "Epic Divinity": "High fantasy hero, ornate armor, ethereal glowing elements, ancient forest, magical atmosphere.",
    "Elite Disciplinarian": "Intense dramatic portrait, sweat and grit, focused expression, cinematic backlight.",
    "Classic Icon": "1920s high society glamour, luxury ballroom, velvet textures, classic Hollywood lighting.",
    "Cyberpunk Vigilante": "Cybernetic enhancements, neon-lit rainy street, tech-wear, futuristic city, teal and orange lighting.",
    "Zen Master": "Martial arts attire, flowing fabric, serene temple, bamboo forest, soft mist, cinematic.",
    "Arcane Investigator": "Supernatural detective, ancient library, floating books, mystical artifacts, warm candlelight."
}

QUIZ_QUESTIONS = [
    {"step": 1, "question": "Choose the world you belong to:", "options": [{"label": "THE FRONTIER", "tag": "Explorer"}, {"label": "THE STREETS", "tag": "Vigilante"}]},
    {"step": 2, "question": "What defines your strategy?", "options": [{"label": "THE ARCHITECT", "tag": "Mastermind"}, {"label": "THE AVENGER", "tag": "Epic"}]},
    {"step": 3, "question": "Pick your visual atmosphere:", "options": [{"label": "NEON DREAMS", "tag": "Cyberpunk"}, {"label": "GOLDEN AGE", "tag": "Classic"}]}
]

# ==========================================
# 3. UI / CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@700&family=Roboto:wght@400&display=swap');
    :root { --gold: #D4AF37; --bg: #0F0F0F; }
    html, body, .stApp { background-color: var(--bg) !important; color: white !important; font-family: 'Roboto', sans-serif !important; }
    h1 { font-family: 'Oswald' !important; color: var(--gold) !important; text-align: center; text-transform: uppercase; font-size: 3.5rem !important; }
    .quiz-card { background: #1A1A1A; border: 1px solid #333; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 10px; }
    div.stButton > button { background: var(--gold) !important; color: black !important; font-weight: bold !important; width: 100%; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. LÓGICA
# ==========================================
def get_casting_verdict(answers, api_key):
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"Casting Director: User likes {answers}. Match one from {list(CASTING_ARCHETYPES.keys())}. Return JSON: {{\"archetype\": \"name\", \"reason\": \"short sentence\"}}"
        response = client.models.generate_content(model='gemini-2.0-flash', contents=[prompt])
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        return {"archetype": "Classic Icon", "reason": "You have a timeless screen presence."}

def generate_poster(image_path, archetype_key, gender, api_key):
    client = replicate.Client(api_token=api_key)
    style = CASTING_ARCHETYPES[archetype_key]
    
    with open(image_path, "rb") as f:
        img_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"

    # Mudando para o modelo SDXL FaceID ou Realistic para garantir que funcione
    try:
        output = client.run(
            "tencentarc/photomaker:ddfc2b6a45641951921a882ee57bd56130286cd9ad95130daef6795f63d50839",
            input={
                "input_image": img_b64,
                "prompt": f"A photo of a {gender} as a {style}, cinematic movie poster, high quality",
                "negative_prompt": "ugly, distorted, low quality, wedding, text",
                "num_steps": 30,
                "style_name": "Photographic",
                "guidence_scale": 5
            }
        )
        return output[0]
    except Exception as e:
        st.error(f"Replicate Error: {e}")
        return None

# ==========================================
# 5. FLOW
# ==========================================
st.markdown("<h1>Hollywood Casting</h1>", unsafe_allow_html=True)

if not REPLICATE_KEY:
    st.error("❌ REPLICATE_KEY is missing in Secrets.")
    st.stop()

if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state.answers = []

if st.session_state.step < len(QUIZ_QUESTIONS):
    q = QUIZ_QUESTIONS[st.session_state.step]
    st.markdown(f"### {q['question']}")
    cols = st.columns(2)
    for i, opt in enumerate(q['options']):
        with cols[i]:
            st.markdown(f"<div class='quiz-card'><h4>{opt['label']}</h4></div>", unsafe_allow_html=True)
            if st.button(f"CHOOSE {opt['label']}", key=f"q{st.session_state.step}{i}"):
                st.session_state.answers.append(opt['tag'])
                st.session_state.step += 1
                st.rerun()

elif st.session_state.step == len(QUIZ_QUESTIONS):
    gender = st.selectbox("I am an:", ["Actor", "Actress"])
    file = st.file_uploader("Your Headshot", type=["jpg", "png", "jpeg"])
    if file:
        img = Image.open(file)
        st.image(img, width=300)
        if st.button("CAST ME!"):
            with st.status("🎬 Directing..."):
                img.save("temp.jpg")
                v = get_casting_verdict(st.session_state.answers, GOOGLE_KEY)
                url = generate_poster("temp.jpg", v['archetype'], gender, REPLICATE_KEY)
                if url:
                    st.session_state.url = url
                    st.session_state.v = v
                    st.session_state.step += 1
                    st.rerun()
else:
    st.balloons()
    st.markdown(f"<h2 style='color:#D4AF37; text-align:center;'>{st.session_state.v['archetype'].upper()}</h2>", unsafe_allow_html=True)
    st.image(st.session_state.url, use_container_width=True)
    if st.button("RESTART"):
        st.session_state.step = 0
        st.rerun()
