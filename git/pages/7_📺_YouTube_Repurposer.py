# pages/7_📺_YouTube_Repurposer.py - WERSJA SAAS (KREDYTY + INTEGRACJA EBOOK)

import streamlit as st
import os
import database as db
from dotenv import load_dotenv
import sys

# --- KONFIGURACJA ---
load_dotenv()
st.set_page_config(page_title="YouTube Repurposer", page_icon="📺", layout="wide")

# ==============================================================================
# 🔒 BRAMKA BEZPIECZEŃSTWA
# ==============================================================================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⛔ Dostęp zablokowany.")
    st.markdown("[Zaloguj się](/Home)")
    st.stop()

USER_TIER = st.session_state.get('user_tier', 'Free')
USERNAME = st.session_state.get('username', '')

# Bezpieczna inicjalizacja API Key
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("OPENAI_API_KEY")

# Inicjalizacja zmiennych sesji dla tego modułu
if 'transkrypcja' not in st.session_state: st.session_state.transkrypcja = ""
if 'yt_url' not in st.session_state: st.session_state.yt_url = ""

# ==============================================================================

# Dodajemy ścieżkę do agentów
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importujemy agenta YouTube (zakładam, że masz ten plik, jak nie - daj znać)
try:
    from agent_youtube import pobierz_transkrypcje, repurpose_content
except ImportError:
    # Fallback - prosta funkcja mockupowa, jeśli nie masz pliku agent_youtube.py
    def pobierz_transkrypcje(url): return "To jest przykładowa transkrypcja wideo...", None
    def repurpose_content(text, format_type, key): return f"Przykładowy {format_type} na podstawie tekstu."
    st.warning("⚠️ Brak pliku agent_youtube.py - działam w trybie demo.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Panel Sterowania")
    try: user_credits = db.get_user_credits(USERNAME)
    except: user_credits = 0
    st.metric("Twoje Kredyty", user_credits)
    
    st.info("💡 Zamień wideo w treść. Pobranie transkrypcji: 1 Kredyt.")

# --- GŁÓWNY EKRAN ---
st.title("📺 YouTube Content Repurposer")
st.markdown("Wklej link do filmu, pobierz treść i zamień ją w posty lub całego E-booka.")

url = st.text_input("Link do wideo na YouTube:", placeholder="https://www.youtube.com/watch?v=...", value=st.session_state.yt_url)

# Przycisk Pobierania
if st.button("📥 Pobierz treść (Koszt: 1 Kredyt)", type="primary"):
    if not url:
        st.warning("Wklej link!")
    elif not db.deduct_credits(USERNAME, 1):
        st.error("❌ Brak kredytów! Doładuj w Home.")
    else:
        with st.spinner("Pobieranie napisów i przetwarzanie..."):
            tekst, blad = pobierz_transkrypcje(url)
            
            if blad:
                st.error(f"Błąd: {blad}")
                # Opcjonalnie: zwrot kredytu w przypadku błędu technicznego
                db.deduct_credits(USERNAME, -1) 
            else:
                st.session_state.transkrypcja = tekst
                st.session_state.yt_url = url
                st.success(f"Sukces! Pobrano {len(tekst)} znaków.")
                st.rerun()

# --- PANEL PRACY Z TREŚCIĄ ---
if st.session_state.transkrypcja:
    with st.expander("📄 Pokaż surową transkrypcję", expanded=False):
        st.text_area("Treść wideo:", st.session_state.transkrypcja, height=200)

    st.divider()
    st.subheader("♻️ Co chcesz stworzyć?")
    
    # Dzielimy na dwie główne ścieżki: Social Media vs PRODUKT CYFROWY
    
    tab_social, tab_product = st.tabs(["📢 Social Media & Blog", "📚 Stwórz E-booka / Produkt"])
    
    # ZAKŁADKA 1: SOCIAL MEDIA
    with tab_social:
        st.caption("Szybki content marketing (Koszt: 1 Kredyt za generację)")
        col1, col2, col3, col4 = st.columns(4)
        
        wybrany_format = None
        
        with col1: 
            if st.button("📝 Artykuł Blogowy"): wybrany_format = "Blog"
        with col2:
            if st.button("🐦 Wątek Twitter"): wybrany_format = "Twitter"
        with col3:
            if st.button("💼 Post LinkedIn"): wybrany_format = "LinkedIn"
        with col4:
            if st.button("📧 Newsletter"): wybrany_format = "Newsletter"
            
        if wybrany_format:
            if not db.deduct_credits(USERNAME, 1):
                st.error("Brak kredytów.")
            else:
                with st.spinner(f"Piszę {wybrany_format}..."):
                    wynik = repurpose_content(st.session_state.transkrypcja, wybrany_format, st.session_state.api_key)
                    st.markdown("---")
                    st.subheader(f"Wynik: {wybrany_format}")
                    st.markdown(wynik)
                    st.download_button("Pobierz .txt", wynik, f"{wybrany_format}.txt")

    # ZAKŁADKA 2: E-BOOK (CROSS-SELLING)
    with tab_product:
        st.info("🚀 Zamień wiedzę z tego filmu w pełnopłatny produkt cyfrowy.")
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("""
            **Co się stanie?**
            1. Prześlemy treść filmu do **Fabryki Contentu**.
            2. Architekt AI stworzy na jej podstawie **spis treści**.
            3. Będziesz mógł wygenerować E-booka, Audiobooka i Podcast.
            """)
        with c2:
            st.write("")
            # PRZYCISK PRZEKIEROWANIA
            if st.button("🏭 Prześlij do Fabryki Contentu", type="primary", use_container_width=True):
                # Przygotowujemy dane dla Fabryki
                # Ograniczamy nieco długość promptu, żeby nie zapchać context window na starcie, 
                # ale dajemy wystarczająco dużo, by Architekt zrozumiał kontekst.
                base_text = st.session_state.transkrypcja[:15000] 
                
                prompt_temat = f"E-book na podstawie wideo YouTube: {st.session_state.yt_url}\n\nGŁÓWNE TEZY I TREŚĆ:\n{base_text}..."
                
                # Zapisujemy w sesji
                st.session_state.temat_roboczy = prompt_temat
                st.session_state.etap = 0 # Resetujemy fabrykę do startu
                
                # Przekierowanie
                try:
                    st.switch_page("pages/2_🏭_Fabryka_Contentu.py")
                except Exception as e:
                    st.error("Nie udało się przekierować automatycznie. Kliknij 'Fabryka Contentu' w menu.")