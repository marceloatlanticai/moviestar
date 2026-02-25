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

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Hollywood Casting Experience",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 1. CONFIGURAÇÕES E DICIONÁRIOS
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
# 2. UI E CSS (Baseado no seu Blueprint JFM)
# ==========================================

def load_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=Roboto:wght@300;400;700&family=Oswald:wght@700&display=swap');
        
        :root { --primary-gold: #D4AF37; --bg-dark: #0F0F0F; --card-bg: #1A1A1A; }
        
        html, body, .stApp { background-color: var(--bg-dark) !important; color: #FFFFFF !important; font-family: 'Roboto', sans-serif !important; }
        
        h1 { font-family: 'Oswald', sans-serif !important; text-transform: uppercase; color: var(--primary-gold) !important; text-align: center; font-size: 4rem !important; margin-bottom: 0px !important; }
        .subtitle { text-align: center; color: #888; font-style: italic; margin-bottom: 50px; }
        
        /* Quiz Cards */
        .quiz-card { background-color: var(--card-bg); border: 1px solid #333; padding: 25px; border-radius: 10px; transition: 0.3s; height: 100%; }
        .quiz-card:hover { border-color: var(--primary-gold); }
        
        /* Custom Buttons */
        div.stButton > button { width: 100%; background-color: var(--primary-gold) !important; color: black !important; font-weight: bold !important; text-transform: uppercase; border: none !important; padding: 15px !important; }
        
        /* Responsive Image 50% Desktop */
        @media (min-width: 768px) {
            div[data-testid="stImage"] > img { width: 50% !important; margin: 0 auto !important; border-radius: 15px; border: 2px solid var(--primary-gold); }
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC (Gemini & Replicate)
# ==========================================

def get_casting_verdict(answers, api_key):
    client = genai.Client(api_key=api_key)
    prompt = f"Act as a Hollywood Casting Director. User chose: {answers}. Select the best match from {list(CASTING_ARCHETYPES.keys())}. Return ONLY JSON: {{\"archetype\": \"name\", \"reason\": \"short English sentence\"}}"
    response = client.models.generate_content(model='gemini-2.0-flash', contents=[prompt])
    return json.loads(response.text.replace("```json", "").replace("```", "").strip())

def generate_poster(image_path, archetype_key, gender, api_key):
    os.environ["REPLICATE_API_TOKEN"] = api_key
    style_desc = CASTING_ARCHETYPES[archetype_key]
    
    # Trava de segurança para preservação de rosto do seu projeto anterior
    prompt = f"Professional cinematic movie still of a {gender} {style_desc}. CRITICAL: Maintain exact facial features, expression, and mouth position from source image. 8k, masterpiece, highly detailed."
    negative_prompt = "distorted, cartoon, bad face, different hairstyle, changed mouth, invented teeth, bad anatomy, text, watermark."
    
    with open(image_path, "rb") as f:
        img_data = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        
    output = replicate.run(
        "google/nano-banana-pro",
        input={
            "image_input": [img_data],
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "prompt_strength": 0.50,
            "guidance_scale": 12.0,
            "aspect_ratio": "2:3"
        }
    )
    return output[0]

# ==========================================
# 4. MAIN APP FLOW
# ==========================================

load_custom_css()

st.markdown("<h1>Hollywood Casting</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Discover your cinematic destiny.</p>", unsafe_allow_html=True)

# Sidebar para Keys
with st.sidebar:
    st.title("Studio Settings")
    GOOGLE_KEY = st.text_input("Google API Key", type="password")
    REPLICATE_KEY = st.text_input("Replicate Token", type="password")

# Session State Initialization
if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state.answers = []

# Quiz Interface
if st.session_state.step < len(QUIZ_QUESTIONS):
    current = QUIZ_QUESTIONS[st.session_state.step]
    st.markdown(f"### {current['question']}")
    
    col1, col2 = st.columns(2)
    for i, opt in enumerate(current['options']):
        with [col1, col2][i]:
            st.markdown(f"""<div class='quiz-card'><h3>{opt['label']}</h3><p>{opt['brief']}</p></div>""", unsafe_allow_html=True)
            if st.button(f"SELECT {opt['label']}", key=f"btn_{st.session_state.step}_{i}"):
                st.session_state.answers.append(opt['tag'])
                st.session_state.step += 1
                st.rerun()

# Final Stage: Photo & Generation
elif st.session_state.step == len(QUIZ_QUESTIONS):
    st.markdown("### 📸 Final Step: Your Headshot")
    gender = st.selectbox("Identify as:", ["Actor", "Actress"])
    uploaded_file = st.file_uploader("Upload your photo to start casting", type=["jpg", "png", "jpeg"])
    
    if uploaded_file and GOOGLE_KEY and REPLICATE_KEY:
        img = Image.open(uploaded_file)
        st.image(img, caption="Your Source Photo")
        
        if st.button("GENERATE MY MOVIE POSTER"):
            with st.status("🎬 Directing your scene...") as s:
                # 1. Get Archetype
                verdict = get_casting_verdict(st.session_state.answers, GOOGLE_KEY)
                st.write(f"Casting you as: **{verdict['archetype']}**")
                
                # 2. Generate Image
                img.save("temp_actor.jpg")
                poster_url = generate_poster("temp_actor.jpg", verdict['archetype'], gender, REPLICATE_KEY)
                
                st.session_state.final_poster = poster_url
                st.session_state.verdict = verdict
                st.session_state.step += 1
                st.rerun()

# Result Display
else:
    st.balloons()
    st.markdown(f"<h2 style='text-align:center; color:#D4AF37;'>YOU ARE THE {st.session_state.verdict['archetype'].upper()}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'>{st.session_state.verdict['reason']}</p>", unsafe_allow_html=True)
    
    st.image(st.session_state.final_poster, use_container_width=True)
    
    if st.button("RESTART CASTING"):
        del st.session_state.step
        del st.session_state.answers
        st.rerun()
