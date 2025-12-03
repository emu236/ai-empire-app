# pages/8_🎥_Studio_Awatarow.py - WERSJA IMGBB (STABILNA)

import streamlit as st
import os
import database as db
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import time

# --- KONFIGURACJA ---
load_dotenv()
st.set_page_config(page_title="Studio Awatarów AI", page_icon="🎥", layout="wide")

# 🔒 BRAMKA BEZPIECZEŃSTWA
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⛔ Dostęp zablokowany.")
    st.markdown("[Zaloguj się](/Home)")
    st.stop()

USER_TIER = st.session_state.get('user_tier', 'Free')
USERNAME = st.session_state.get('username', '')

# CREDENTIALS
DID_EMAIL = os.getenv("DID_EMAIL")
DID_KEY = os.getenv("DID_KEY")
IMGBB_KEY = os.getenv("IMGBB_KEY") # WYMAGANY KLUCZ IMGBB

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Panel Sterowania")
    try: user_credits = db.get_user_credits(USERNAME)
    except: user_credits = 0
    st.metric("Twoje Kredyty", user_credits)
    
    st.info("💡 Ożyw zdjęcie i stwórz wideo-prezenterkę.")

# --- FUNKCJA UPLOADU (IMGBB - STABILNA) ---
def upload_to_imgbb(file_obj):
    """Wgrywa plik na ImgBB i zwraca bezpośredni URL."""
    if not IMGBB_KEY:
        st.error("Błąd konfiguracji: Brak IMGBB_KEY w pliku .env. Zdobądź go na api.imgbb.com")
        return None
        
    try:
        file_obj.seek(0)
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_KEY,
            "expiration": 600 # Link ważny 10 minut
        }
        files = {
            "image": file_obj
        }
        response = requests.post(url, data=payload, files=files)
        response.raise_for_status()
        
        return response.json()['data']['url']
            
    except Exception as e:
        st.error(f"Błąd hostingu zdjęcia (ImgBB): {e}")
        return None

def create_talk(text, image_url, email, key):
    url = "https://api.d-id.com/talks"
    
    # Używamy głosu Marka (Polski)
    payload = {
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": { "type": "microsoft", "voice_id": "pl-PL-MarekNeural" },
            "input": text
        },
        "config": { "fluent": "false", "pad_audio": "0.0" },
        "source_url": image_url
    }
    
    response = requests.post(url, json=payload, auth=HTTPBasicAuth(email, key))
    return response.json()

def get_talk_status(talk_id, email, key):
    url = f"https://api.d-id.com/talks/{talk_id}"
    response = requests.get(url, auth=HTTPBasicAuth(email, key))
    return response.json()

# ==============================================================================
# GŁÓWNY INTERFEJS
# ==============================================================================
st.title("🎥 Studio Awatarów AI")

if not DID_EMAIL or not DID_KEY:
    st.error("Błąd: Brak kluczy D-ID w .env")
    st.stop()

# --- INPUTY ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Scenariusz")
    default_text = st.session_state.get('temat_roboczy', '') if len(st.session_state.get('temat_roboczy', '')) < 500 else ""
    script_text = st.text_area("Co awatar ma powiedzieć?", height=300, max_chars=500, value=default_text)

with col2:
    st.subheader("2. Wybierz Awatara")
    tab_ready, tab_custom = st.tabs(["🖼️ Gotowe", "📤 Wgraj Własne"])
    
    avatar_url = None 
    
    with tab_ready:
        avatars = {
            "👨‍💼 Marek (Ekspert)": "https://img.freepik.com/free-photo/portrait-successful-man-having-stubble-posing-with-broad-smile-keeping-arms-folded_171337-1267.jpg",
            "🤖 Cyber-Asystent": "https://img.freepik.com/free-photo/view-3d-robot-with-tech-elements_23-2150835659.jpg"
        }
        selected = st.selectbox("Postać:", list(avatars.keys()))
        ready_url = avatars[selected]
        st.image(ready_url, width=150)
            
    with tab_custom:
        st.info("Wgraj zdjęcie (JPG/PNG). Max 5MB.")
        uploaded_file = st.file_uploader("Wybierz plik", type=['jpg', 'png', 'jpeg'])
        custom_url_input = st.text_input("Lub wklej link:")
        if uploaded_file: st.image(uploaded_file, width=150)
        elif custom_url_input: st.image(custom_url_input, width=150)

st.divider()

# --- GENEROWANIE ---
KOSZT_WIDEO = 15
generate_btn = st.button(f"🎬 Generuj Wideo (Koszt: {KOSZT_WIDEO} Kredytów)", type="primary", use_container_width=True)

if generate_btn:
    final_image_url = None
    
    # 1. Upload
    if uploaded_file:
        with st.status("Wysyłanie zdjęcia na serwer ImgBB...", expanded=False):
            temp_link = upload_to_imgbb(uploaded_file)
            if temp_link:
                final_image_url = temp_link
                st.success(f"Zdjęcie wgrane!")
            else:
                st.error("Błąd uploadu.")
                st.stop()
    elif custom_url_input:
        final_image_url = custom_url_input
    else:
        final_image_url = ready_url
    
    # 2. Walidacja
    if not script_text: st.warning("Uzupełnij tekst.")
    elif not final_image_url: st.warning("Brak zdjęcia.")
    elif not db.deduct_credits(USERNAME, KOSZT_WIDEO): st.error(f"❌ Brak kredytów!")
    else:
        # 3. D-ID
        with st.status("🎬 Reżyseria w toku...", expanded=True) as status:
            try:
                status.write("Wysyłanie do D-ID...")
                response = create_talk(script_text, final_image_url, DID_EMAIL, DID_KEY)
                
                # DIAGNOSTYKA BŁĘDÓW
                if response.get("kind") == "error" or "id" not in response:
                    err_msg = response.get('description', response) # Pełna treść błędu
                    st.error(f"Błąd D-ID: {err_msg}")
                    st.code(f"Link zdjęcia: {final_image_url}") 
                    db.deduct_credits(USERNAME, -KOSZT_WIDEO)
                    status.update(label="Błąd API", state="error")
                    st.stop()

                talk_id = response.get("id")
                status.write(f"Generowanie ID: {talk_id}...")
                
                # Pętla oczekiwania
                video_url = None
                for _ in range(24):
                    time.sleep(5)
                    res = get_talk_status(talk_id, DID_EMAIL, DID_KEY)
                    stat = res.get("status")
                    if stat == "done":
                        video_url = res.get("result_url")
                        break
                    elif stat == "error":
                        st.error(f"Błąd generowania: {res}")
                        db.deduct_credits(USERNAME, -KOSZT_WIDEO)
                        break
                        
                if video_url:
                    status.update(label="✅ Gotowe!", state="complete")
                    st.session_state.generated_video_url = video_url
                    st.rerun()
                else:
                    status.update(label="Timeout/Błąd", state="error")

            except Exception as e:
                st.error(f"Wyjątek: {e}")
                db.deduct_credits(USERNAME, -KOSZT_WIDEO)

if 'generated_video_url' in st.session_state:
    st.divider()
    st.video(st.session_state.generated_video_url)