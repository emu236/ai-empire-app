# pages/6_🕵️_Lowca_Nisz.py - WERSJA LIVE RESEARCH (OPARTA NA FAKTACH)

import streamlit as st
import os
import database as db
from openai import OpenAI
from dotenv import load_dotenv
import json
import re
from duckduckgo_search import DDGS # <--- KLUCZOWY IMPORT

# --- KONFIGURACJA ---
load_dotenv()
st.set_page_config(page_title="Łowca Nisz AI (Live)", page_icon="🕵️", layout="wide")

# ==============================================================================
# 🔒 BRAMKA BEZPIECZEŃSTWA
# ==============================================================================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⛔ Dostęp zablokowany.")
    st.markdown("[Zaloguj się](/Home)")
    st.stop()

USER_TIER = st.session_state.get('user_tier', 'Free')
USERNAME = st.session_state.get('username', '')

if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("OPENAI_API_KEY")

# ==============================================================================

# --- FUNKCJE POMOCNICZE (RESEARCH) ---
def search_trends(topic):
    """Przeszukuje internet w poszukiwaniu problemów i trendów w danej niszy."""
    try:
        # Szukamy bolączek i trendów na bieżący rok
        query = f"trending problems and popular topics in {topic} 2024 2025 reddit quora blog"
        with DDGS() as ddgs:
            # Pobieramy 5 najlepszych wyników
            results = list(ddgs.text(query, max_results=5))
        
        # Formatujemy to w zwięzły tekst dla GPT
        context = "\n".join([f"- Tytuł: {r['title']}\n  Treść: {r['body']}" for r in results])
        return context
    except Exception as e:
        print(f"Błąd wyszukiwania: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Ustawienia")
    try: user_credits = db.get_user_credits(USERNAME)
    except: user_credits = 0
    st.metric("Twoje Kredyty", user_credits)
    
    st.info("💡 **Tryb LIVE:** AI najpierw przeszukuje Internet, aby znaleźć realne problemy ludzi, a dopiero potem generuje pomysły.")

st.title("🕵️ Łowca Nisz (Live Research)")
st.markdown("Wpisz branżę. Agent sprawdzi, **czego ludzie szukają w Internecie** i zaproponuje dochodowe e-booki.")

# --- INPUT ---
col1, col2 = st.columns([2, 1])
with col1:
    kategoria = st.text_input("Twoja branża / Zainteresowanie:", placeholder="np. Fotografia ślubna, AI w marketingu, Bieganie...")

with col2:
    st.write("") 
    st.write("")
    # Koszt jest wyższy (2 kredyty), bo robimy live research
    analyze_btn = st.button("🚀 Analizuj Rynek (Koszt: 2 Kredyty)", type="primary", use_container_width=True)

# --- LOGIKA ANALIZY ---
if analyze_btn:
    if not kategoria:
        st.error("Wpisz kategorię!")
    elif not db.deduct_credits(USERNAME, 2):
        st.error("❌ Brak kredytów! (Wymagane: 2)")
    else:
        if not st.session_state.api_key:
             st.error("Brak klucza API.")
             st.stop()

        client = OpenAI(api_key=st.session_state.api_key)
        
        with st.status("🕵️‍♂️ Rozpoczynam śledztwo...", expanded=True) as status:
            
            # KROK 1: LIVE SEARCH
            status.write(f"🌍 Przeszukuję Internet pod kątem trendów w '{kategoria}'...")
            market_data = search_trends(kategoria)
            
            if not market_data:
                status.write("⚠️ Nie udało się pobrać danych z sieci. Bazuję na wiedzy ogólnej.")
                market_data = "Brak danych live. Użyj wiedzy ogólnej."
            else:
                status.write("✅ Znaleziono aktualne sygnały rynkowe.")
            
            # KROK 2: ANALIZA GPT
            status.write("🧠 Analizuję zebrane dane i generuję pomysły...")
            
            try:
                prompt = f"""
                Działasz jako Analityk Rynku Wydawniczego.
                
                KATEGORIA: "{kategoria}"
                
                DANE Z INTERNETU (TRENDY/PROBLEMY):
                {market_data}
                
                Na podstawie powyższych danych z sieci (oraz własnej wiedzy), wymyśl 3 KONKRETNE i DOCHODOWE tematy na e-booka typu "How-To".
                
                ZASADY:
                1. Tematy muszą odpowiadać na realne problemy znalezione w danych.
                2. Tytuły muszą być chwytliwe (Bestsellerowe).
                3. Ignoruj tematy zbyt ogólne.
                
                Zwróć JSON w formacie:
                {{
                    "propozycje": [
                        {{
                            "tytul": "Tytuł",
                            "podtytul": "Obietnica/Korzyść",
                            "dla_kogo": "Precyzyjna grupa",
                            "problem_rynkowy": "Jaki konkretny problem z danych rozwiązuje?",
                            "zarys": "3-4 główne punkty"
                        }},
                        ...
                    ]
                }}
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                
                content = response.choices[0].message.content
                content_clean = content.replace("```json", "").replace("```", "").strip()
                
                data = json.loads(content_clean)
                
                # Inteligentne szukanie listy
                propozycje = []
                if isinstance(data, dict):
                    if "propozycje" in data: propozycje = data["propozycje"]
                    else:
                        for v in data.values():
                            if isinstance(v, list): propozycje = v; break
                elif isinstance(data, list): propozycje = data
                
                if not propozycje: raise ValueError("Pusta lista.")
                
                st.session_state.znalezione_nisze = propozycje
                status.update(label="✅ Gotowe! Oto wyniki:", state="complete")
                
            except Exception as e:
                st.error(f"Błąd analizy: {e}")
                db.deduct_credits(USERNAME, -2) # Zwrot
                status.update(label="Błąd", state="error")

# --- WYNIKI ---
if 'znalezione_nisze' in st.session_state:
    st.divider()
    
    nisze = st.session_state.znalezione_nisze
    if not isinstance(nisze, list):
        st.error("Błąd formatu.")
    else:
        for i, nisza in enumerate(nisze):
            tytul = nisza.get('tytul', 'Bez tytułu')
            podtytul = nisza.get('podtytul', '')
            dla_kogo = nisza.get('dla_kogo', '')
            problem = nisza.get('problem_rynkowy', '...') # Nowe pole!
            zarys = nisza.get('zarys', '')

            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                
                with c1:
                    st.markdown(f"### 📘 {tytul}")
                    if podtytul: st.markdown(f"_{podtytul}_")
                    st.info(f"🔍 **Problem rynkowy:** {problem}")
                    st.markdown(f"🎯 **Dla kogo:** {dla_kogo}")
                    if zarys:
                        with st.expander("👀 Zobacz plan"):
                            st.write(zarys)
                
                with c2:
                    st.write("")
                    st.write("")
                    st.write("")
                    if st.button(f"🛠️ Produkuj to!", key=f"btn_prod_{i}", use_container_width=True, type="primary"):
                        full_prompt = f"Temat: {tytul}\nPodtytuł: {podtytul}\nGrupa: {dla_kogo}\nProblem do rozwiązania: {problem}\nPlan: {zarys}"
                        st.session_state.temat_roboczy = full_prompt
                        st.session_state.etap = 0
                        try: st.switch_page("pages/2_🏭_Fabryka_Contentu.py")
                        except: st.error("Przejdź do Fabryki ręcznie.")