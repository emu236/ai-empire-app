# pages/5_🎤_Inteligentny_Dyktafon.py

import streamlit as st
import os
import database as db
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# --- KONFIGURACJA ---
load_dotenv()
st.set_page_config(page_title="Inteligentny Dyktafon", page_icon="🎙️", layout="wide")

# ==============================================================================
# 🔒 BRAMKA BEZPIECZEŃSTWA
# ==============================================================================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⛔ Dostęp zablokowany.")
    st.markdown("[Zaloguj się](/Home)")
    st.stop()

USER_TIER = st.session_state.get('user_tier', 'Free')
USERNAME = st.session_state.get('username', '')

# ✅ POPRAWNY KOD:
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("OPENAI_API_KEY")

# ==============================================================================

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Ustawienia")
    try: user_credits = db.get_user_credits(USERNAME)
    except: user_credits = 0
    st.metric("Twoje Kredyty", user_credits)
    
    st.divider()
    st.markdown("### 🧠 Tryb Inteligencji")
    tryb = st.radio(
        "Co mam zrobić z nagraniem?",
        [
            "📝 Transkrypcja (Słowo w słowo)",
            "📋 Lista Zadań (Wyciągnij taski)",
            "📧 Notatka Spotkaniowa (Podsumowanie)",
            "✨ Korekta Językowa (Wygładź styl)"
        ]
    )
    
    jezyk = st.selectbox("Język nagrania:", ["Auto-wykrywanie", "Polski", "Angielski"])

st.title("🎙️ Inteligentny Dyktafon AI")
st.caption("Nagraj swoje myśli, a AI zamieni je w gotowy dokument.")

# --- GŁÓWNY INTERFEJS ---

audio_value = st.audio_input("Naciśnij mikrofon, aby rozpocząć nagrywanie")

if audio_value:
    st.success("Nagranie zarejestrowane!")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Twoje nagranie")
        # st.audio(audio_value) # Opcjonalny odsłuch
        
        # Obliczanie kosztu
        KOSZT = 2 # Podstawa
        if "Transkrypcja (" not in tryb: # Jeśli używamy GPT do analizy
            KOSZT = 3
            
        if st.button(f"🚀 Przetwórz (Koszt: {KOSZT} Kredyty)", type="primary", use_container_width=True):
            
            if not db.deduct_credits(USERNAME, KOSZT):
                st.error("❌ Brak kredytów! Doładuj w Home.")
            else:
                client = OpenAI(api_key=st.session_state.api_key)
                
                with st.spinner("🎧 AI słucha i analizuje..."):
                    try:
                        # 1. Transkrypcja (Whisper)
                        audio_value.name = "voice_memo.wav"
                        transcript_obj = client.audio.transcriptions.create(
                            model="whisper-1", 
                            file=audio_value,
                            response_format="text",
                            language="pl" if jezyk == "Polski" else None
                        )
                        text_raw = transcript_obj # W zależności od wersji biblioteki to może być string lub obiekt
                        
                        st.session_state.dyktafon_raw = text_raw
                        st.session_state.dyktafon_result = ""
                        
                        # 2. Inteligentna Obróbka (GPT-4o)
                        if "Transkrypcja (" not in tryb:
                            system_prompt = "Jesteś asystentem biurowym."
                            user_prompt = ""
                            
                            if "Lista Zadań" in tryb:
                                user_prompt = f"Wyciągnij z poniższego tekstu listę zadań do wykonania (To-Do List). Sformatuj jako listę punktowaną z checkboxami. Tekst: {text_raw}"
                            elif "Notatka" in tryb:
                                user_prompt = f"Zrób profesjonalną notatkę ze spotkania/nagrania. Wypunktuj kluczowe decyzje, daty i osoby. Tekst: {text_raw}"
                            elif "Korekta" in tryb:
                                user_prompt = f"Popraw poniższy tekst, aby brzmiał profesjonalnie, płynnie i był poprawny gramatycznie. Usuń yyy, eee i powtórzenia. Tekst: {text_raw}"
                                
                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ]
                            )
                            st.session_state.dyktafon_result = response.choices[0].message.content
                        else:
                            st.session_state.dyktafon_result = text_raw # Tylko przepisanie
                            
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Błąd: {e}")

    # --- WYNIKI ---
    with col2:
        if 'dyktafon_result' in st.session_state and st.session_state.dyktafon_result:
            st.subheader("📄 Wynik")
            
            # Edytowalny wynik
            final_text = st.text_area("Edytuj przed skopiowaniem:", 
                                      value=st.session_state.dyktafon_result, 
                                      height=400)
            
            # Pobieranie
            c_d1, c_d2 = st.columns(2)
            
            # Pobierz jako TXT
            c_d1.download_button(
                label="📥 Pobierz Notatkę (.txt)",
                data=final_text,
                file_name=f"notatka_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            # Opcja: Wyślij do generatora Ebooków (Cross-selling!)
            if c_d2.button("📚 Użyj jako bazy do E-booka", use_container_width=True):
                st.session_state.temat_roboczy = final_text # Przekazujemy tekst
                st.success("Przeniesiono do Fabryki Contentu! Wejdź w zakładkę po lewej.")
                # Można tu dodać st.switch_page, ale wymaga to importu