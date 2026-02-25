import streamlit as st
import streamlit.components.v1 as components
import os
import time
import base64
import json
import requests
from google import genai
import replicate
from PIL import Image, ImageOps
from io import BytesIO

# ==========================================
# 1. CONFIGURAÇÃO DE CHAVES (INSERIR AQUI)
# ==========================================
GOOGLE_KEY = "AIzaSyBAAHn-qD9fCJwWujRI9kHBOx8VOP5im0c"
REPLICATE_KEY = "r8_CTeySjMjSnCMb9AvSOtUjSVSjTTPWND3JMzBh"

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Hollywood Casting Experience",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. DICIONÁRIOS E CONTEÚDO (EM INGLÊS)
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

QUIZ_QUESTIONS = [
    {
        "step": 1,
        "question": "Choose the world you belong to:",
        "options": [
            {"label": "THE FRONTIER", "brief": "A team of explorers travel through a wormhole in space to ensure humanity's survival.", "tag": "Explorer"},
            {"label": "THE STREETS", "brief": "A retired assassin is forced back into the criminal underworld to avenge a personal loss.", "tag": "Vigilante"}
        ]
    },
    {
        "step": 2,
        "question": "What defines your strategy?",
        "options": [
            {"label": "THE ARCHITECT", "brief": "A skilled thief steals secrets through dream-sharing technology and subconscious layers.", "tag": "Mastermind"},
            {"label": "THE AVENGER", "brief": "A former General seeks revenge against a corrupt empire in the grand arenas of history.", "tag": "Epic"}
        ]
    },
    {
        "step": 3,
        "question": "Pick your visual atmosphere:",
        "options": [
            {"label": "NEON DREAMS", "brief": "A detective in a rainy futuristic city hunts down rogue synthetic humans.", "tag": "Cyberpunk"},
            {"label": "GOLDEN AGE", "brief": "A mysterious millionaire throws lavish parties while chasing a dream from the past.", "tag": "Classic"}
        ]
    }
]

# ==========================================
# 3. UI E CSS (ESTILO PREMIUM DARK/GOLD)
# ==========================================

def load_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=Roboto:wght@300;400;700&family=Oswald:wght@700&display=swap');
        :root { --primary-gold: #D4AF37; --bg-dark: #0F0F0F; --card-bg: #1A1A1A; }
        html, body, .stApp { background-color: var(--bg-dark) !important; color: #FFFFFF !important; font-family: 'Roboto', sans-serif !important; }
        h1 { font-family: 'Oswald', sans-serif !important; text-transform: uppercase; color: var(--primary-gold) !important; text-align: center; font-size: 3.5rem !important; margin-bottom: 0px !important; padding-top: 20px;}
        .subtitle { text-align: center; color: #888; font-style: italic; margin-bottom: 40px; }
        .quiz-card { background-color: var(--card-bg); border: 1px solid #333; padding: 25px; border-radius: 10px; transition: 0.3s; min-height: 180px; margin-bottom: 10px; }
        .quiz-card:hover { border-color: var(--primary-gold); }
        div.stButton > button { width: 100%; background-color: var(--primary-gold) !important; color: black !important; font-weight: bold !important; text-transform: uppercase; border: none !important; padding: 12px !important; border-radius: 5px !important; }
        @media (min-width: 768px) { div[data-testid="stImage"] > img { width: 50% !important; margin: 0 auto !important; border-radius: 10px; border: 1px solid var(--primary-gold); } }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 4. CORE LOGIC (GEMINI 2.0 FLASH + REPLICATE)
# ==========================================

def get_casting_verdict(answers, api_key):
    try:
        client = genai.Client(api_key=api_key)
        # Usando modelo 2.0-flash conforme blueprint original
        prompt = f"Act as a Hollywood Casting Director. User choices: {answers}. Select the best match from {list(CASTING_ARCHETYPES.keys())}. Return ONLY a raw JSON: {{\"archetype\": \"name\", \"reason\": \"short sentence\"}}"
        response = client.models.generate_content(model='gemini-2.0-flash', contents=[prompt])
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        import random
        random_archetype = random.choice(list(CASTING_ARCHETYPES.keys()))
        return {"archetype": random_archetype, "reason": "Your screen presence is undeniable and versatile."}

def generate_poster(image_path, archetype_key, gender, api_key):
    os.environ["REPLICATE_API_TOKEN"] = api_key
    style_desc = CASTING_ARCHETYPES[archetype_key]
    
    # Lógica de proteção de identidade (v21.0)
    prompt = f"High-end cinematic movie still of a {gender} {style_desc}. CRITICAL: Keep EXACT facial features, expression and mouth position from source image. 8k, movie poster quality, masterpiece."
    negative_prompt = "distorted, cartoon, bad face, different hairstyle, changed mouth, invented teeth, text, watermark, logo, blurred."
    
    with open(image_path, "rb") as f:
        img_data = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        
    output = replicate.run(
        "google/nano-banana-pro",
        input={
            "image_input": [img_data],
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "prompt_strength": 0.50, # Mantendo equilíbrio entre IA e Foto Real
            "guidance_scale": 12.0,
            "aspect_ratio": "2:3"
        }
    )
    return output[0]

# ==========================================
# 5. APP FLOW
# ==========================================

load_custom_css()
st.markdown("<h1>Hollywood Casting</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Find your role in the next blockbuster.</p>", unsafe_allow_html=True)

if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state.answers = []

# ETAPA: QUIZ
if st.session_state.step < len(QUIZ_QUESTIONS):
    current = QUIZ_QUESTIONS[st.session_state.step]
    st.markdown(f"<h3 style='text-align:center;'>{current['question']}</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    for i, opt in enumerate(current['options']):
        with [col1, col2][i]:
            st.markdown(f"<div class='quiz-card'><h4>{opt['label']}</h4><p style='font-size:0.9rem; color:#bbb;'>{opt['brief']}</p></div>", unsafe_allow_html=True)
            if st.button(f"SELECT {opt['label']}", key=f"btn_{st.session_state.step}_{i}"):
                st.session_state.answers.append(opt['tag'])
                st.session_state.step += 1
                st.rerun()

# ETAPA: UPLOAD E GERAÇÃO
elif st.session_state.step == len(QUIZ_QUESTIONS):
    st.markdown("### 📸 Final Step: Your Headshot")
    gender = st.selectbox("I identify as:", ["Actor", "Actress"])
    uploaded_file = st.file_uploader("Upload a clear photo of your face", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        img = ImageOps.exif_transpose(img) 
        st.image(img, caption="Source Photo")
        
        if st.button("GENERATE MY MOVIE POSTER", type="primary"):
            if GOOGLE_KEY == "SUA_CHAVE_AQUI" or REPLICATE_KEY == "SEU_TOKEN_AQUI":
                st.error("Please insert your API Keys in the app.py file!")
            else:
                with st.status("🎬 Directing your scene...") as s:
                    img.save("temp_actor.jpg")
                    # Chamada Gemini 2.0
                    verdict = get_casting_verdict(st.session_state.answers, GOOGLE_KEY)
                    # Chamada Replicate
                    poster_url = generate_poster("temp_actor.jpg", verdict['archetype'], gender, REPLICATE_KEY)
                    
                    st.session_state.final_poster = poster_url
                    st.session_state.verdict = verdict
                    st.session_state.step += 1
                    st.rerun()

# ETAPA: RESULTADO FINAL
else:
    st.balloons()
    st.markdown(f"<h2 style='text-align:center; color:#D4AF37;'>YOU WERE CAST AS: {st.session_state.verdict['archetype'].upper()}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-style:italic;'>\"{st.session_state.verdict['reason']}\"</p>", unsafe_allow_html=True)
    
    st.image(st.session_state.final_poster, use_container_width=True)
    
    # Download
    try:
        response = requests.get(st.session_state.final_poster)
        st.download_button("DOWNLOAD YOUR POSTER", data=response.content, file_name="my_hollywood_casting.png", mime="image/png")
    except:
        st.info("Poster ready for download.")
    
    if st.button("AUDITION AGAIN"):
        st.session_state.step = 0
        st.session_state.answers = []
        if 'final_poster' in st.session_state: del st.session_state.final_poster
        st.rerun()
