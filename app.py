import streamlit as st
import os
import time
import base64
import json
import requests
from google import genai
import replicate
from PIL import Image, ImageOps
import random

# ==========================================
# 1. CONFIGURAÇÃO DE CHAVES
# ==========================================
GOOGLE_KEY = st.secrets.get("GOOGLE_KEY", "")
REPLICATE_KEY = st.secrets.get("REPLICATE_KEY", "")

# ==========================================
# 2. RELEASES (Inspirados no Oscar - 100% Inglês & Seguro)
# ==========================================
# Removidos nomes de filmes/atores para evitar copyright
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

st.set_page_config(page_title="Hollywood Casting Game", page_icon="🎬", layout="wide")

# Inicializa estados do jogo
if 'scores' not in st.session_state:
    st.session_state.scores = {k: 0 for k in RELEASES.keys()}
if 'matches' not in st.session_state:
    st.session_state.matches = 0
if 'current_champion' not in st.session_state:
    st.session_state.current_champion = random.choice(list(RELEASES.keys()))

# ==========================================
# 3. LÓGICA DE IA (Gemini 2.5 Flash)
# ==========================================
def get_personality_profile(scores, api_key):
    try:
        client = genai.Client(api_key=api_key)
        top_roles = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        prompt = f"""
        Act as a top Hollywood Talent Agent. Based on these casting preferences: {top_roles}, 
        write a 3-sentence personality profile for this actor. 
        DO NOT mention real actors or movie titles. 
        Focus on their 'screen presence', 'acting range', and 'vibe'. 
        Be professional and encouraging. Language: English.
        """
        response = client.models.generate_content(model='gemini-2.5-flash', contents=[prompt])
        return response.text.strip()
    except:
        return "You possess a versatile screen presence that blends deep emotional vulnerability with a commanding physical intensity."

# ==========================================
# 4. GERAÇÃO DE IMAGEM (Nano Banana)
# ==========================================
def generate_blended_poster(image_path, scores, gender, api_key):
    client = replicate.Client(api_token=api_key)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top1 = sorted_scores[0][0]
    
    # Prompt focado no vencedor, mas mantendo a essência do duelo
    dna_prompt = f"A professional high-end cinematic movie still of a {gender} in a scene described as: {RELEASES[top1]['desc']}. Masterpiece lighting, 8k, realistic."

    with open(image_path, "rb") as f:
        img_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"

    try:
        model = client.models.get("google/nano-banana-pro")
        output = client.predictions.create(
            version=model.latest_version,
            input={
                "image_input": [img_b64],
                "prompt": dna_prompt,
                "prompt_strength": 0.45,
                "guidance_scale": 12.0,
                "aspect_ratio": "2:3"
            }
        )
        while output.status not in ["succeeded", "failed"]:
            time.sleep(2)
            output.reload()
        return output.output[0]
    except: return None

# ==========================================
# 5. UI PRINCIPAL
# ==========================================
st.markdown("<h1 style='text-align:center; color:#D4AF37;'>HOLLYWOOD CASTING TOURNAMENT</h1>", unsafe_allow_html=True)

# Mecânica de Duelo (Limite de 5 rodadas)
if st.session_state.matches < 5:
    st.markdown(f"<p style='text-align:center;'>Match #{st.session_state.matches + 1}: Which role defines your talent?</p>", unsafe_allow_html=True)
    
    challenger = random.choice([k for k in RELEASES.keys() if k != st.session_state.current_champion])
    col1, col2 = st.columns(2)
    
    for i, role in enumerate([st.session_state.current_champion, challenger]):
        with [col1, col2][i]:
            # Ícones circulares
            try:
                st.image(f"icons/{RELEASES[role]['icon']}", width=150)
            except:
                st.markdown(f"<div style='width:150px; height:150px; border-radius:50%; background:#333; margin:0 auto; display:flex; align-items:center; justify-content:center; color:white; font-size:40px;'>{role[:1]}</div>", unsafe_allow_html=True)
            
            st.markdown(f"<h3 style='text-align:center;'>{role.upper()}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; padding:0 20px;'>{RELEASES[role]['desc']}</p>", unsafe_allow_html=True)
            
            if st.button(f"CAST ME AS {role.upper()}", key=f"btn_{role}_{st.session_state.matches}"):
                st.session_state.scores[role] += 1
                st.session_state.current_champion = role
                st.session_state.matches += 1
                st.rerun()

# Resultado Final
else:
    st.success("Tournament Complete! Analyzing your actor DNA...")
    gender = st.selectbox("Identify your screen presence:", ["Actor", "Actress"])
    file = st.file_uploader("Upload your professional headshot", type=["jpg", "png", "jpeg"])
    
    if file:
        img = Image.open(file)
        if st.button("GENERATE FINAL VERDICT & POSTER", type="primary"):
            with st.status("🎬 Directing your scene...") as status:
                img.save("temp.jpg")
                
                # Gera Perfil de Personalidade
                profile = get_personality_profile(st.session_state.scores, GOOGLE_KEY)
                
                # Gera Imagem
                poster_url = generate_blended_poster("temp.jpg", st.session_state.scores, gender, REPLICATE_KEY)
                
                if poster_url:
                    st.divider()
                    st.markdown(f"### 🎭 What kind of {gender} are you?")
                    st.info(profile)
                    
                    st.image(poster_url, use_container_width=True)
                    
                    # Download
                    res = requests.get(poster_url)
                    st.download_button("DOWNLOAD YOUR POSTER", data=res.content, file_name="hollywood_poster.png", mime="image/png")
                    st.balloons()
                    status.update(label="Cut! It's a wrap.", state="complete")

if st.button("RESTART TOURNAMENT"):
    st.session_state.clear()
    st.rerun()
