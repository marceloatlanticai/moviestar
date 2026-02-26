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
st.set_page_config(
    page_title="Hollywood Casting Game", 
    page_icon="🎬", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. RELEASES (Safe, English & Oscar Inspired)
# ==========================================
RELEASES = {
    "The Frontier": {
        "desc": "A determined space explorer leading humanity's last hope toward a distant, mysterious star system.",
        "icon": "thefrontier.png"
    },
    "The Bench Storyteller": {
        "desc": "A man with an extraordinary life story sharing his wisdom with strangers on a simple park bench.",
        "icon": "benchstory.png"
    },
    "The Jazz Obsession": {
        "desc": "A young, ambitious prodigy pushing physical and mental limits under a ruthless master's tutelage.",
        "icon": "jazzobs.png"
    },
    "The Digital Heist": {
        "desc": "A skilled specialist who enters people's subconscious to extract secrets through their dreams.",
        "icon": "heist.png"
    },
    "The Silent Star": {
        "desc": "A legendary performer from the golden era of cinema struggling to find their voice in a changing world.",
        "icon": "silentstar.png"
    },
    "The Parasite House": {
        "desc": "A clever strategist infiltrating a high-society household to secure a better future for their family.",
        "icon": "parasite.png"
    }
}

# ==========================================
# 3. UI / CSS (Dark Cinema Style)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=Oswald:wght@700&family=Roboto:wght@400&display=swap');
    :root { --gold: #D4AF37; --bg: #0F0F0F; }
    html, body, .stApp { background-color: var(--bg) !important; color: white !important; font-family: 'Roboto', sans-serif !important; }
    h1 { font-family: 'Oswald' !important; color: var(--gold) !important; text-align: center; text-transform: uppercase; font-size: 3.5rem !important; margin-bottom: 0px !important; }
    .subtitle { text-align: center; color: #888; font-style: italic; margin-bottom: 30px; }
    .quiz-card { background: #1A1A1A; border: 1px solid #333; padding: 25px; border-radius: 10px; text-align: center; min-height: 250px; }
    div.stButton > button { background: var(--gold) !important; color: black !important; font-weight: bold !important; width: 100%; border-radius: 5px; height: 50px; text-transform: uppercase; border: none !important; }
    .icon-circle { width:150px; height:150px; border-radius:50%; background:#333; margin:0 auto; display:flex; align-items:center; justify-content:center; color:white; font-size:40px; border: 2px solid var(--gold); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. INITIALIZATION
# ==========================================
if 'scores' not in st.session_state:
    st.session_state.scores = {k: 0 for k in RELEASES.keys()}
if 'matches' not in st.session_state:
    st.session_state.matches = 0
if 'current_champion' not in st.session_state:
    st.session_state.current_champion = random.choice(list(RELEASES.keys()))

# ==========================================
# 5. CORE AI LOGIC
# ==========================================

def get_personality_profile(scores, api_key):
    try:
        client = genai.Client(api_key=api_key.strip())
        top_roles = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        prompt = f"""
        Act as a top Hollywood Talent Agent. Based on these casting results: {top_roles}, 
        write a sharp, 3-sentence personality profile for this actor. 
        CRITICAL: DO NOT mention real actors or movie titles. 
        Focus on their 'screen presence', 'acting range', and 'vibe'. 
        Be professional and encouraging. Language: English.
        """
        response = client.models.generate_content(model='gemini-2.5-flash', contents=[prompt])
        return response.text.strip()
    except:
        return "You possess a versatile screen presence that blends deep emotional vulnerability with a commanding physical intensity."

def generate_poster_assincrono(image_path, archetype_key, gender, api_key):
    client = replicate.Client(api_token=api_key.strip())
    style_desc = RELEASES[archetype_key]['desc']
    
    with open(image_path, "rb") as f:
        img_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"

    loading_phrases = ["🎬 Setting the stage...", "📽️ Rolling film...", "🎭 Applying character makeup...", "🎞️ Developing negatives...", "✨ Calibrating star aura...", "🌟 Finalizing the scene..."]

    try:
        model = client.models.get("google/nano-banana-pro")
        inputs = {
            "image_input": [img_b64],
            "prompt": f"Professional cinematic movie still, headshot of an {gender} as: {style_desc}. Masterpiece lighting, 8k, realistic movie poster.",
            "negative_prompt": "distorted, cartoon, bad face, text, logo, watermark, blurry",
            "prompt_strength": 0.45,
            "guidance_scale": 12.0,
            "aspect_ratio": "2:3"
        }
        
        prediction = client.predictions.create(version=model.latest_version, input=inputs)
        start_time = time.time()
        phrase_idx = 0
        
        while prediction.status not in ["succeeded", "failed", "canceled"]:
            if time.time() - start_time > 300: break 
            time.sleep(4)
            prediction.reload()
            
        if prediction.status == "succeeded":
            res = prediction.output
            return str(res[0] if isinstance(res, list) else res)
        return None
    except Exception as e:
        st.error(f"AI Director Error: {e}")
        return None

# ==========================================
# 6. APP FLOW
# ==========================================
st.markdown("<h1>Hollywood Casting Tournament</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>The battle for your career's defining role</p>", unsafe_allow_html=True)

if not REPLICATE_KEY or not GOOGLE_KEY:
    st.error("❌ API Keys missing in Secrets. Please check GOOGLE_KEY and REPLICATE_KEY.")
    st.stop()

# TOURNAMENT PHASE
if st.session_state.matches < 5:
    st.markdown(f"<h3 style='text-align:center;'>Match #{st.session_state.matches + 1}</h3>", unsafe_allow_html=True)
    
    challenger = random.choice([k for k in RELEASES.keys() if k != st.session_state.current_champion])
    col1, col2 = st.columns(2)
    
    for i, role in enumerate([st.session_state.current_champion, challenger]):
        with [col1, col2][i]:
            st.markdown("<div class='quiz-card'>", unsafe_allow_html=True)
            # Icon Circle Logic
            try:
                st.image(f"icons/{RELEASES[role]['icon']}", width=150)
            except:
                st.markdown(f"<div class='icon-circle'>{role[:1]}</div>", unsafe_allow_html=True)
            
            st.markdown(f"<h3 style='text-align:center;'>{role.upper()}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; padding:10px;'>{RELEASES[role]['desc']}</p>", unsafe_allow_html=True)
            
            if st.button(f"CAST ME AS {role.upper()}", key=f"btn_{role}_{st.session_state.matches}"):
                st.session_state.scores[role] += 1
                st.session_state.current_champion = role
                st.session_state.matches += 1
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# CASTING PHASE
elif "poster_url" not in st.session_state:
    st.success("Tournament Complete! Your DNA has been synthesized.")
    gender = st.selectbox("Identify your screen presence:", ["Actor", "Actress"])
    file = st.file_uploader("Upload your professional headshot", type=["jpg", "png", "jpeg"])
    
    if file:
        img = ImageOps.exif_transpose(Image.open(file)).convert('RGB')
        st.image(img, width=300, caption="Ready for Production")
        
        if st.button("GENERATE FINAL VERDICT & POSTER", type="primary"):
            with st.status("🎬 Directing the scene...") as status:
                img.save("temp.jpg")
                profile = get_personality_profile(st.session_state.scores, GOOGLE_KEY)
                url = generate_poster_assincrono("temp.jpg", st.session_state.current_champion, gender, REPLICATE_KEY)
                
                if url:
                    st.session_state.poster_url = url
                    st.session_state.profile_text = profile
                    status.update(label="Cut! It's a wrap.", state="complete")
                    st.rerun()

# RESULTS PHASE
else:
    st.balloons()
    st.markdown(f"<h2 style='color:#D4AF37; text-align:center;'>THE {st.session_state.current_champion.upper()}</h2>", unsafe_allow_html=True)
    
    st.markdown("### 🎭 Your Actor Profile")
    st.info(st.session_state.profile_text)
    
    try:
        st.image(st.session_state.poster_url, use_container_width=True)
        img_res = requests.get(st.session_state.poster_url)
        if img_res.status_code == 200:
            st.download_button("DOWNLOAD YOUR POSTER", data=img_res.content, file_name="hollywood_poster.png", mime="image/png")
    except:
        st.error("Error displaying poster. Please check your connection.")

    if st.button("START NEW TOURNAMENT"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
