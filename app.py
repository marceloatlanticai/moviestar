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
# 2. RELEASES
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
# 3. UI / CSS (LIMPEZA TOTAL DOS RETÂNGULOS)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=Oswald:wght@700&family=Roboto:wght@400&display=swap');
    :root { --gold: #D4AF37; --bg: #0F0F0F; }
    html, body, .stApp { background-color: var(--bg) !important; color: white !important; font-family: 'Roboto', sans-serif !important; }
    h1 { font-family: 'Oswald' !important; color: var(--gold) !important; text-align: center; text-transform: uppercase; font-size: 3.5rem !important; margin-bottom: 0px !important; }
    .subtitle { text-align: center; color: #888; font-style: italic; margin-bottom: 30px; }
    
    /* Card de duelo limpo */
    .quiz-card-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 20px;
        background-color: transparent;
    }

    /* Estilo do Ícone / Círculo */
    .casting-icon {
        width: 150px;
        height: 150px;
        border-radius: 50%;
        border: 2px solid var(--gold);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        background-color: #1A1A1A;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2);
    }
    
    .casting-icon img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .initial-letter {
        font-size: 60px;
        color: white;
        font-family: 'Oswald', sans-serif;
    }

    div.stButton > button { background: var(--gold) !important; color: black !important; font-weight: bold !important; width: 100%; border-radius: 5px; height: 50px; text-transform: uppercase; border: none !important; }
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
        prompt = f"Act as a top Hollywood Talent Agent. Based on these casting results: {top_roles}, write a sharp, 3-sentence personality profile for this actor. English."
        response = client.models.generate_content(model='gemini-2.0-flash', contents=[prompt])
        return response.text.strip()
    except:
        return "You possess a versatile screen presence that blends deep emotional vulnerability with a commanding physical intensity."

def generate_poster_assincrono(image_path, archetype_key, gender, api_key):
    client = replicate.Client(api_token=api_key.strip())
    style_desc = RELEASES[archetype_key]['desc']
    with open(image_path, "rb") as f:
        img_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    try:
        model = client.models.get("google/nano-banana-pro")
        inputs = {
            "image_input": [img_b64],
            "prompt": f"Professional cinematic movie still, headshot of an {gender} as: {style_desc}. Masterpiece lighting, 8k, realistic movie poster.",
            "negative_prompt": "distorted, cartoon, bad face, text, logo, watermark, blurry",
            "prompt_strength": 0.45, "guidance_scale": 12.0, "aspect_ratio": "2:3"
        }
        prediction = client.predictions.create(version=model.latest_version, input=inputs)
        while prediction.status not in ["succeeded", "failed", "canceled"]:
            time.sleep(4)
            prediction.reload()
        if prediction.status == "succeeded":
            return str(prediction.output[0])
        return None
    except Exception as e:
        st.error(f"AI Director Error: {e}")
        return None

# ==========================================
# 6. APP FLOW (TORNEIO SEM RETÂNGULOS)
# ==========================================
st.markdown("<h1>Hollywood Casting Tournament</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>The battle for your career's defining role</p>", unsafe_allow_html=True)

if st.session_state.matches < 5:
    st.markdown(f"<h3 style='text-align:center;'>Match #{st.session_state.matches + 1}</h3>", unsafe_allow_html=True)
    
    challenger = random.choice([k for k in RELEASES.keys() if k != st.session_state.current_champion])
    col1, col2 = st.columns(2)
    
    for i, role in enumerate([st.session_state.current_champion, challenger]):
        with [col1, col2][i]:
            # Criamos o ícone usando HTML direto para evitar o placeholder do st.image
            icon_path = f"icons/{RELEASES[role]['icon']}"
            
            # Se a imagem existe no GitHub/Local, gera a tag <img>, senão gera a Letra
            if os.path.exists(icon_path):
                # Para carregar imagem local no Streamlit via HTML é preciso converter para base64
                with open(icon_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                icon_html = f'<div class="casting-icon"><img src="data:image/png;base64,{data}"></div>'
            else:
                icon_html = f'<div class="casting-icon"><span class="initial-letter">{role[0]}</span></div>'

            # Renderização do Card
            st.markdown(f"""
                <div class="quiz-card-container">
                    {icon_html}
                    <h3 style="font-family:Oswald;">{role.upper()}</h3>
                    <p style="min-height:80px; color:#bbb;">{RELEASES[role]['desc']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"CAST ME AS {role.upper()}", key=f"btn_{role}_{st.session_state.matches}"):
                st.session_state.scores[role] += 1
                st.session_state.current_champion = role
                st.session_state.matches += 1
                st.rerun()

# FASE DE UPLOAD
elif "poster_url" not in st.session_state:
    st.success("Tournament Complete!")
    gender = st.selectbox("Identify your screen presence:", ["Actor", "Actress"])
    file = st.file_uploader("Upload your professional headshot", type=["jpg", "png", "jpeg"])
    
    if file:
        img = ImageOps.exif_transpose(Image.open(file)).convert('RGB')
        st.image(img, width=300)
        if st.button("GENERATE FINAL VERDICT & POSTER", type="primary"):
            with st.status("🎬 Directing...") as status:
                img.save("temp.jpg")
                profile = get_personality_profile(st.session_state.scores, GOOGLE_KEY)
                url = generate_poster_assincrono("temp.jpg", st.session_state.current_champion, gender, REPLICATE_KEY)
                if url:
                    st.session_state.poster_url = url
                    st.session_state.profile_text = profile
                    st.rerun()

# RESULTADO FINAL
else:
    st.balloons()
    st.markdown(f"<h2 style='color:#D4AF37; text-align:center;'>THE {st.session_state.current_champion.upper()}</h2>", unsafe_allow_html=True)
    st.info(st.session_state.profile_text)
    st.image(st.session_state.poster_url, use_container_width=True)
    if st.button("START NEW TOURNAMENT"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
