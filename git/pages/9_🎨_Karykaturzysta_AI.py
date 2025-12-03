# pages/9_🎨_Karykaturzysta_AI.py - WERSJA SZKIC OŁÓWKIEM (PENCIL SKETCH STYLE)

import streamlit as st
import os
import database as db
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from openai import OpenAI
import random
import time
import base64
import io
from PIL import Image

# --- KONFIGURACJA ---
load_dotenv()
st.set_page_config(page_title="Karykaturzysta AI", page_icon="🎨", layout="wide")

# 🔒 BRAMKA BEZPIECZEŃSTWA
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⛔ Dostęp zablokowany."); st.stop()

USER_TIER = st.session_state.get('user_tier', 'Free')
USERNAME = st.session_state.get('username', '')

# KLUCZE
DID_EMAIL = os.getenv("DID_EMAIL")
DID_KEY = os.getenv("DID_KEY")
IMGBB_KEY = os.getenv("IMGBB_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STABILITY_KEY = os.getenv("STABILITY_KEY")

if not OPENAI_API_KEY: st.session_state.api_key = OPENAI_API_KEY

# ==============================================================================
# FUNKCJE POMOCNICZE
# ==============================================================================

def upload_file_to_imgbb(file_obj):
    """Wgrywa plik (bytes) na ImgBB."""
    try:
        if hasattr(file_obj, 'seek'): file_obj.seek(0)
        url = "https://api.imgbb.com/1/upload"
        payload = { "key": IMGBB_KEY, "expiration": 600 }
        files = { "image": file_obj }
        response = requests.post(url, data=payload, files=files)
        response.raise_for_status()
        return response.json()['data']['url']
    except Exception as e:
        st.error(f"Błąd uploadu: {e}")
        return None

def upload_url_to_imgbb(image_url):
    try:
        img_data = requests.get(image_url).content
        return upload_file_to_imgbb(io.BytesIO(img_data))
    except Exception as e:
        return None

# --- DALL-E (Dla generowania od zera - też zmieniamy na szkic) ---
def generuj_prompty_karykatury(opis_pl):
    client = OpenAI(api_key=st.session_state.api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Translate description to English prompt for DALL-E 2."},
                # Zmiana stylu na szkic ołówkiem
                {"role": "user", "content": f"Opis: '{opis_pl}'. Styl: 'Black and white pencil sketch caricature on paper, hand-drawn, cross-hatching, highly detailed portrait, white background'. Return ONLY prompt."}
            ]
        )
        return response.choices[0].message.content
    except: return None

def generuj_3_warianty(prompt):
    client = OpenAI(api_key=st.session_state.api_key)
    try:
        response = client.images.generate(model="dall-e-2", prompt=prompt, n=3, size="512x512")
        return [img.url for img in response.data]
    except Exception as e:
        st.error(f"Błąd DALL-E: {e}"); return []

# --- STYLIZACJA (STABILITY AI - NOWA LOGIKA SZKICU) ---
def stylizuj_zdjecie(image_file):
    """Zamienia zdjęcie w karykaturę w stylu szkicu ołówkiem."""
    if not STABILITY_KEY:
        st.error("Brak klucza STABILITY_KEY w .env")
        return None

    try:
        image = Image.open(image_file).convert("RGB").resize((1024, 1024))
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {STABILITY_KEY}"
            },
            files={ "init_image": img_byte_arr },
            data={
                "init_image_mode": "IMAGE_STRENGTH",
                "image_strength": 0.35, # Niska wartość = duża zmiana w stronę rysunku
                # Usunęliśmy "style_preset": "comic-book"

                # Pozytywny Prompt (Nowy styl szkicu ołówkiem)
                "text_prompts[0][text]": "black and white pencil sketch caricature, hand drawn, cross-hatching, graphite on paper texture, highly detailed, realistic shading, portrait",
                "text_prompts[0][weight]": 1,
                
                # Negatywny Prompt (Czego ma NIE być - koloru i cyfrowego wyglądu)
                "text_prompts[1][text]": "color, photograph, 3d render, digital art, smooth, flat, simple drawing, vector art",
                "text_prompts[1][weight]": -1,
                
                "cfg_scale": 9, 
                "samples": 1,
                "steps": 40,
            }
        )

        if response.status_code != 200:
            st.error(f"Błąd Stability AI: {response.text}")
            return None

        data = response.json()
        for i, image in enumerate(data["artifacts"]):
            return base64.b64decode(image["base64"])
            
    except Exception as e:
        st.error(f"Błąd stylizacji: {e}")
        return None

# --- D-ID ---
def create_talk(text, image_url, email, key):
    url = "https://api.d-id.com/talks"
    payload = {
        "script": { "type": "text", "provider": { "type": "microsoft", "voice_id": "pl-PL-MarekNeural" }, "input": text },
        "config": { "fluent": "false", "pad_audio": "0.0", "stitch": "true" },
        "source_url": image_url
    }
    return requests.post(url, json=payload, auth=HTTPBasicAuth(email, key)).json()

def get_talk_status(talk_id, email, key):
    return requests.get(f"https://api.d-id.com/talks/{talk_id}", auth=HTTPBasicAuth(email, key)).json()

# ==============================================================================
# INTERFEJS
# ==============================================================================

with st.sidebar:
    st.header("⚙️ Panel")
    try: user_credits = db.get_user_credits(USERNAME)
    except: user_credits = 0
    st.metric("Kredyty", user_credits)
    st.info("Krok 1: Stwórz postać.\nKrok 2: Ożyw ją (15 Kredytów).")

st.title("🎨 Karykaturzysta AI (Styl Szkicu)")

if not DID_EMAIL or not IMGBB_KEY: st.error("Brak kluczy API."); st.stop()

# --- KROK 1 ---
st.subheader("1. Źródło Postaci")
tab_gen, tab_upload = st.tabs(["🎨 Generuj od zera", "📤 Wgraj Swoje Zdjęcie"])

# GENEROWANIE
with tab_gen:
    col_g1, col_g2 = st.columns([3, 1])
    with col_g1:
        opis_user = st.text_input("Opis postaci:", placeholder="np. Szef kuchni, gruby, wesoły...")
    with col_g2:
        st.write(""); st.write("")
        if st.button("Rysuj (2 Kredyty)", type="primary"):
            if db.deduct_credits(USERNAME, 2):
                with st.spinner("Rysowanie..."):
                    p = generuj_prompty_karykatury(opis_user)
                    st.session_state.karykatury_urls = generuj_3_warianty(p)
            else: st.error("Brak kredytów")

    if 'karykatury_urls' in st.session_state:
        cols = st.columns(3)
        for i, url in enumerate(st.session_state.karykatury_urls):
            with cols[i]:
                st.image(url)
                if st.button(f"Wybierz #{i+1}", key=f"sel_{i}"):
                    with st.spinner("Przetwarzanie..."):
                        link = upload_url_to_imgbb(url)
                        if link: st.session_state.final_avatar_url = link; st.success("Wybrano!")

# UPLOAD I STYLIZACJA (IMG2IMG)
with tab_upload:
    st.info("Wgraj zdjęcie twarzy. Zamienimy je w ręczny szkic ołówkiem.")
    
    uploaded_file = st.file_uploader("Wybierz plik", type=['jpg', 'png', 'jpeg'], key="uploader_karykatura")
    
    if uploaded_file:
        # LOGIKA RESETU PO ZMIANIE ZDJĘCIA
        if 'last_uploaded_name' not in st.session_state or st.session_state.last_uploaded_name != uploaded_file.name:
            st.session_state.stylized_image_bytes = None
            st.session_state.final_avatar_url = None
            st.session_state.last_uploaded_name = uploaded_file.name
            st.rerun()
            
        c_u1, c_u2 = st.columns(2)
        with c_u1:
            st.image(uploaded_file, caption="Oryginał", width=200)
            if st.button("✅ Użyj Oryginału (Realizm)", use_container_width=True):
                with st.spinner("Wysyłanie..."):
                    link = upload_file_to_imgbb(uploaded_file)
                    if link: st.session_state.final_avatar_url = link; st.success("Gotowe!")

        with c_u2:
            if st.session_state.get('stylized_image_bytes'):
                st.image(st.session_state.stylized_image_bytes, caption="Szkic Ołówkiem", width=200)
                
                if st.button("✅ Użyj Szkicu", type="primary", use_container_width=True):
                    with st.spinner("Wysyłanie na serwer..."):
                        f_obj = io.BytesIO(st.session_state.stylized_image_bytes)
                        link = upload_file_to_imgbb(f_obj)
                        if link: st.session_state.final_avatar_url = link; st.success("Gotowe!")
                
                if st.button("🔄 Spróbuj ponownie"):
                    st.session_state.stylized_image_bytes = None
                    st.rerun()
            else:
                st.info("Styl Artystyczny")
                if st.button("🎨 Zmień w Szkic (2 Kredyty)", type="secondary", use_container_width=True):
                    if db.deduct_credits(USERNAME, 2):
                        with st.spinner("Rysowanie (Stability AI)..."):
                            uploaded_file.seek(0)
                            img_bytes = stylizuj_zdjecie(uploaded_file)
                            if img_bytes:
                                st.session_state.stylized_image_bytes = img_bytes
                                st.rerun()
                    else: st.error("Brak kredytów")

# --- KROK 2 ---
if 'final_avatar_url' in st.session_state:
    st.divider()
    st.subheader("2. Stwórz Wideo")
    c_v1, c_v2 = st.columns([1, 2])
    with c_v1: st.image(st.session_state.final_avatar_url, width=200, caption="Wybrana postać")
    with c_v2:
        tekst = st.text_area("Tekst:", height=150)
        if st.button("🎬 Generuj (15 Kredytów)", type="primary"):
            if db.deduct_credits(USERNAME, 15):
                with st.status("Produkcja...") as status:
                    try:
                        r = create_talk(tekst, st.session_state.final_avatar_url, DID_EMAIL, DID_KEY)
                        tid = r.get('id')
                        if not tid: st.error(f"Błąd D-ID: {r}"); db.deduct_credits(USERNAME, -15); st.stop()
                        
                        vid_url = None
                        for _ in range(24):
                            time.sleep(5)
                            res = get_talk_status(tid, DID_EMAIL, DID_KEY)
                            if res.get('status') == 'done': vid_url = res.get('result_url'); break
                            if res.get('status') == 'error': break
                        
                        if vid_url:
                            status.update(label="Gotowe!", state="complete")
                            st.session_state.karykatura_video = vid_url
                            st.rerun()
                        else:
                            status.update(label="Błąd", state="error")
                            db.deduct_credits(USERNAME, -15)
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                        db.deduct_credits(USERNAME, -15)
            else: st.error("Brak kredytów")

if 'karykatura_video' in st.session_state:
    st.success("Gotowe!")
    st.video(st.session_state.karykatura_video)