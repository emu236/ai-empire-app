# pages/2_🏭_Fabryka_Contentu.py - WERSJA CZYSTA (BEZ RANDOM I DATAVIZ)

import streamlit as st
import os
import json
import re
import time
import zipfile
# Usunięto 'import random' bo nie jest już potrzebny
from dotenv import load_dotenv
from openai import OpenAI
import sys
import database as db 

# --- KONFIGURACJA ---
load_dotenv()
st.set_page_config(page_title="Fabryka Contentu AI", page_icon="🏭", layout="wide")

# ==============================================================================
# 🔒 BRAMKA BEZPIECZEŃSTWA
# ==============================================================================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⛔ Dostęp zablokowany.")
    st.info("Musisz się zalogować.")
    st.markdown("[Przejdź do logowania](/Home)")
    st.stop()

USER_TIER = st.session_state.get('user_tier', 'Free')
USERNAME = st.session_state.get('username', '')

# ==============================================================================

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- IMPORTY AGENTÓW ---
try:
    from agent_analityk_v2 import uruchom_agenta_analityka
    from agent_architekt import uruchom_agenta_architekta
    from agent_pisarz import uruchom_agenta_pisarza
    from agent_krytyk import uruchom_agenta_krytyka
    from agent_researcher import uruchom_researchera
    from agent_grafik import uruchom_agenta_grafika
    from agent_wydawca import uruchom_wydawce
    from agent_marketer import uruchom_agenta_marketera
    
    # Audio/Podcast zostają
    from agent_audio import generuj_audiobook
    from agent_podcast import uruchom_agenta_podcastu
    # USUNIĘTO: agent_dataviz (żeby nie generował błędów)

except ImportError as e:
    st.error(f"❌ Błąd importu agentów: {e}")
    st.stop()

def parsuj_prospekt_json(json_str):
    try: return json.loads(json_str)
    except: return None

def oczysc_tekst_pisarza(tekst_raw):
    if not tekst_raw: return ""
    t = re.sub(r'^#+\s+.*$', '', tekst_raw, flags=re.MULTILINE)
    t = re.sub(r'\*\*Rozdział.*?\*\*', '', t, flags=re.IGNORECASE)
    return re.sub(r'\n{3,}', '\n\n', t).strip()

# --- STAN APLIKACJI ---
if 'etap' not in st.session_state: st.session_state.etap = 0
if 'projekt_path' not in st.session_state: st.session_state.projekt_path = ""
if 'prospekt_data' not in st.session_state: st.session_state.prospekt_data = {}
if 'ebook_content_main' not in st.session_state: st.session_state.ebook_content_main = [] 
if 'ebook_content_pl' not in st.session_state: st.session_state.ebook_content_pl = []
if 'generation_done' not in st.session_state: st.session_state.generation_done = False
if 'pdfy_gotowe' not in st.session_state: st.session_state.pdfy_gotowe = False
if 'api_key' not in st.session_state: st.session_state.api_key = os.getenv("OPENAI_API_KEY")
if 'jezyk_docelowy' not in st.session_state: st.session_state.jezyk_docelowy = "Polski"
if 'temat_roboczy' not in st.session_state: st.session_state.temat_roboczy = ""

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Panel Sterowania")
    try: user_credits = db.get_user_credits(USERNAME)
    except: user_credits = 0
    st.success(f"👤 {USERNAME}")
    st.metric("Twoje Kredyty", user_credits)
    st.caption(f"💎 Pakiet: {USER_TIER}")
    
    if user_credits < 2: st.error("⚠️ Doładuj konto!")
    
    st.divider()
    
    # HISTORIA PROJEKTÓW
    st.subheader("📂 Twoje Projekty")
    user_projects = db.get_user_projects(USERNAME)
    project_options = ["➕ Rozpocznij Nowy Projekt"] + [f"{p[2]} | {p[0]}" for p in user_projects]
    selected_project_str = st.selectbox("Wybierz z historii:", project_options)
    
    if st.button("Wczytaj Projekt"):
        if selected_project_str == "➕ Rozpocznij Nowy Projekt":
            for k in ['prospekt_data', 'ebook_content_main', 'ebook_content_pl', 'projekt_path', 'generation_done', 'pdfy_gotowe']:
                if k in st.session_state: del st.session_state[k]
            st.session_state.etap = 0
            st.rerun()
        else:
            index = project_options.index(selected_project_str) - 1
            if index >= 0:
                sciezka = user_projects[index][1]
                if os.path.exists(sciezka):
                    st.session_state.projekt_path = sciezka
                    try:
                        with open(os.path.join(sciezka, "prospekt.json"), "r", encoding="utf-8") as f:
                            st.session_state.prospekt_data = json.load(f)
                    except: pass
                    try:
                        with open(os.path.join(sciezka, "tekst_MAIN.txt"), "r", encoding="utf-8") as f:
                            st.session_state.ebook_content_main = f.readlines()
                    except: pass
                    
                    st.session_state.etap = 3
                    st.session_state.generation_done = True
                    st.session_state.pdfy_gotowe = True
                    st.toast(f"Wczytano: {user_projects[index][0]}", icon="📂")
                    time.sleep(1); st.rerun()
                else: st.error("Pliki nie istnieją.")

    st.divider()
    api_key_input = st.text_input("Klucz OpenAI API", value=st.session_state.api_key, type="password")
    if api_key_input: st.session_state.api_key = api_key_input
    
    wyb = st.selectbox("Język produktu:", ["Polski", "Angielski (English)", "Niemiecki (Deutsch)", "Hiszpański (Español)"])
    st.session_state.jezyk_docelowy = wyb.split(" (")[0]

st.title(f"🏭 Fabryka Contentu ({st.session_state.jezyk_docelowy})")

if not st.session_state.api_key: st.info("👈 Podaj klucz API."); st.stop()

# ==============================================================================
# ETAP 0: START
# ==============================================================================
if st.session_state.etap == 0:
    st.markdown("### 💰 Cennik Generowania")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📖 Tekst", "2 Kredyty")
    c2.metric("🎨 Okładka", "1 Kredyt")
    c3.metric("🎧 Audiobook", "6 Kredytów")
    c4.metric("🎙️ Podcast", "3 Kredyty")
    st.divider()

    st.subheader("Krok 1: Wybierz Temat")
    tryb = st.radio("Jak chcesz wybrać temat?", ["💡 Własny pomysł", "🏆 Wybierz z Top 10 Kategorii"])
    if tryb == "💡 Własny pomysł":
        st.session_state.temat_roboczy = st.text_input("Wpisz temat:", value=st.session_state.temat_roboczy)
    else:
        kategorie_top10 = ["Rozwój Osobisty", "Finanse", "Zdrowie", "AI", "Marketing", "Psychologia", "Programowanie", "Gotowanie", "Podróże", "Rodzicielstwo"]
        wybrana_kat = st.selectbox("Wybierz niszę:", kategorie_top10)
        st.session_state.temat_roboczy = st.text_input("Doprecyzuj temat:", value=wybrana_kat)

    st.write("")
    with st.form("start_form"):
        if st.form_submit_button("🚀 Generuj Strukturę (Gratis)", type="primary"):
            if len(st.session_state.temat_roboczy) < 3: st.error("Wpisz temat.")
            else:
                for k in ['prospekt_data', 'ebook_content_main', 'ebook_content_pl', 'projekt_path', 'generation_done', 'pdfy_gotowe']:
                    if k in st.session_state: del st.session_state[k]
                st.session_state.temat = st.session_state.temat_roboczy
                st.session_state.etap = 1
                st.rerun()

# ==============================================================================
# ETAP 1: PLANOWANIE
# ==============================================================================
elif st.session_state.etap == 1:
    st.subheader("Krok 2: Plan (JSON)")
    if not st.session_state.prospekt_data:
        with st.status("🏗️ Architekt projektuje...", expanded=True):
            p_json = uruchom_agenta_architekta(st.session_state.temat, st.session_state.api_key, st.session_state.jezyk_docelowy)
            dane = parsuj_prospekt_json(p_json)
            if dane: st.session_state.prospekt_data = dane; st.rerun()
            else: st.error("Błąd JSON."); st.stop()
    
    with st.form("edycja_planu"):
        t = st.text_input("Tytuł", st.session_state.prospekt_data.get('Tytul',''))
        u = st.text_input("USP", st.session_state.prospekt_data.get('Kluczowa_Obietnica_USP',''))
        r_ed = st.text_area("Rozdziały", "\n".join(st.session_state.prospekt_data.get('Spis_Tresci', [])), height=300)
        
        c1, c2 = st.columns([1, 5])
        with c1:
            if st.form_submit_button("🔙 Wróć"): st.session_state.etap = 0; st.rerun()
        with c2:
            if st.form_submit_button("✅ Zatwierdź Plan", type="primary"):
                st.session_state.prospekt_data.update({'Tytul': t, 'Kluczowa_Obietnica_USP': u})
                st.session_state.prospekt_data['Spis_Tresci'] = [x.strip() for x in r_ed.split('\n') if x.strip()]
                safe = re.sub(r'[^a-zA-Z0-9]', '', t)[:20]
                folder = f"{time.strftime('%Y%m%d')}_{safe}"
                os.makedirs(folder, exist_ok=True)
                st.session_state.projekt_path = folder
                with open(os.path.join(folder, "prospekt.json"), "w", encoding="utf-8") as f: json.dump(st.session_state.prospekt_data, f, ensure_ascii=False)
                st.session_state.etap = 2
                st.rerun()

# ==============================================================================
# ETAP 2: PISANIE (CZYSTE, BEZ BŁĘDÓW)
# ==============================================================================
elif st.session_state.etap == 2:
    if not st.session_state.generation_done:
        st.subheader("Krok 3: Generowanie Treści")
        st.info(f"Projekt: **{st.session_state.prospekt_data.get('Tytul')}**")
        
        KOSZT_TEKSTU = 2
        if st.button(f"🚀 Rozpocznij Pisanie (Koszt: {KOSZT_TEKSTU} Kredyty)"):
            if not db.deduct_credits(USERNAME, KOSZT_TEKSTU):
                st.error(f"❌ Masz za mało kredytów! Potrzebujesz: {KOSZT_TEKSTU}")
            else:
                p_str = json.dumps(st.session_state.prospekt_data)
                rozdz = st.session_state.prospekt_data['Spis_Tresci']
                prog = st.progress(0); main_content = []; log = st.container()

                for i, r_raw in enumerate(rozdz):
                    prog.progress(int((i/len(rozdz))*100))
                    tit = r_raw.split(': ', 1)[-1].strip() if ':' in r_raw else r_raw
                    
                    with log.status(f"Rozdział {i+1}: {tit}...", expanded=False) as status:
                        status.write("🔍 Research..."); notatki = uruchom_researchera(tit, st.session_state.api_key)
                        status.write("✍️ Pisanie..."); raw_text = uruchom_agenta_pisarza(p_str, tit, notatki, st.session_state.api_key, "Brak", st.session_state.jezyk_docelowy)
                        if raw_text is None: raw_text = "⚠️ Błąd."

                        # --- GENEROWANIE CZYSTEJ ILUSTRACJI ---
                        status.write("🎨 Generowanie ilustracji...")
                        prompt_graficzny = f"Illustration for chapter '{tit}'. Abstract business style. NO TEXT."
                        img_path = uruchom_agenta_grafika(prompt_graficzny, "Ilustracja", st.session_state.api_key, st.session_state.projekt_path, f"img_{i}", st.session_state.jezyk_docelowy)
                        
                        img_tag = ""
                        if img_path:
                            fname = os.path.basename(str(img_path))
                            # Czysty Markdown (bezpieczny)
                            img_tag = f"![Ilustracja]({fname})\n\n"

                        part_main = raw_text
                        if "[---TLUMACZENIE---]" in raw_text:
                            part_main = raw_text.split("[---TLUMACZENIE---]")[0]

                        # Składanie
                        main_content.append(f"## {tit}\n\n{img_tag}{oczysc_tekst_pisarza(part_main)}\n\n")
                        status.update(label=f"✅ Rozdział {i+1} gotowy", state="complete")

                prog.progress(100)
                st.session_state.ebook_content_main = main_content
                st.session_state.ebook_content_pl = main_content 
                st.session_state.generation_done = True
                st.rerun()
    else:
        st.subheader("✅ Treść wygenerowana"); st.success("Rozdziały gotowe.")
        if st.button("Zapisz Projekt i Przejdź Dalej"):
            with open(os.path.join(st.session_state.projekt_path, "tekst_MAIN.txt"), "w", encoding="utf-8") as f: f.writelines(st.session_state.ebook_content_main)
            with open(os.path.join(st.session_state.projekt_path, "tekst_PL.txt"), "w", encoding="utf-8") as f: f.writelines(st.session_state.ebook_content_pl)
            db.save_project(USERNAME, st.session_state.prospekt_data.get('Tytul'), st.session_state.projekt_path)
            st.toast("Zapisano w historii!", icon="💾")
            st.session_state.etap = 3
            st.rerun()

# ==============================================================================
# ETAP 3: PRODUKCJA
# ==============================================================================
elif st.session_state.etap == 3:
    st.subheader(f"Zarządzanie Projektem: {st.session_state.prospekt_data.get('Tytul', 'Bez tytułu')}")
    
    col_cover, col_pdf, col_audio = st.columns(3)
    
    with col_cover:
        st.markdown("### 1. Grafika")
        KOSZT_OKLADKI = 1
        if st.button(f"🎨 Generuj Okładkę (-{KOSZT_OKLADKI} Kredyt)"):
            if not db.deduct_credits(USERNAME, KOSZT_OKLADKI): st.error("❌ Brak kredytów!")
            else:
                with st.status("Generowanie...", expanded=True):
                    t = st.session_state.prospekt_data['Tytul']; u = st.session_state.prospekt_data.get('Kluczowa_Obietnica_USP','')
                    prompt = f"A full page vertical A4 abstract background texture, theme: '{t}'. Visual art only. CRITICAL EXCLUSION: NO text, NO letters."
                    p = uruchom_agenta_grafika(prompt, u, st.session_state.api_key, st.session_state.projekt_path, "okladka", st.session_state.jezyk_docelowy)
                    if p: st.image(str(p)); st.success("Gotowe.")

    with col_pdf:
        st.markdown("### 2. E-book")
        if st.button("📄 Złóż Pliki (Gratis)"):
            with st.status("Składanie...", expanded=True):
                r = st.session_state.prospekt_data.get('Spis_Tresci', []); t = st.session_state.prospekt_data.get('Tytul', ''); u = st.session_state.prospekt_data.get('Kluczowa_Obietnica_USP','')
                uruchom_wydawce(st.session_state.projekt_path, r, t, u, "tekst_MAIN.txt", f"Ebook_{st.session_state.jezyk_docelowy}.pdf")
                uruchom_wydawce(st.session_state.projekt_path, r, t, u, "tekst_MAIN.txt", f"Ebook_{st.session_state.jezyk_docelowy}.epub")
                st.session_state.pdfy_gotowe = True
                st.rerun()

    with col_audio:
        st.markdown("### 3. Audio Studio")
        if USER_TIER in ["Standard", "Premium"]:
            glosy = {"Onyx (Męski)": "onyx", "Nova (Żeński)": "nova", "Alloy (Uniw)": "alloy", "Echo (Męski)": "echo"}
            wybrany = st.selectbox("Lektor:", list(glosy.keys()), index=0)
            kod = glosy[wybrany]

            KOSZT_AUDIO = 6
            if st.button(f"🎧 Audiobook (-{KOSZT_AUDIO} Kredytów)"):
                if not st.session_state.ebook_content_main: st.error("Brak tekstu!")
                elif not db.deduct_credits(USERNAME, KOSZT_AUDIO): st.error("❌ Brak kredytów!")
                else:
                    with st.status("Nagrywanie...", expanded=True):
                        generuj_audiobook(st.session_state.api_key, st.session_state.ebook_content_main, st.session_state.projekt_path, voice=kod)
                        st.session_state.pdfy_gotowe = True; st.rerun()
            
            st.divider()
            
            if USER_TIER == "Premium":
                KOSZT_PODCAST = 3
                if st.button(f"🎙️ Podcast AI (-{KOSZT_PODCAST} Kredyty)"):
                    if not st.session_state.ebook_content_main: st.error("Brak tekstu.")
                    elif not db.deduct_credits(USERNAME, KOSZT_PODCAST): st.error("❌ Brak kredytów!")
                    else:
                         with st.status("Produkcja...", expanded=True):
                            try:
                                path = uruchom_agenta_podcastu(st.session_state.api_key, st.session_state.ebook_content_main, st.session_state.projekt_path)
                                if path: st.success("Gotowe!"); st.audio(path); st.session_state.pdfy_gotowe = True; st.rerun()
                                else: st.error("Błąd.")
                            except Exception as e: st.error(f"Błąd: {e}")
            else: st.info("Podcast w PREMIUM.")
        else: st.error("Zablokowane w BASIC.")

    st.divider()
    
    if st.session_state.pdfy_gotowe:
        st.success("📁 Pliki Projektu")
        c1, c2, c3 = st.columns(3)
        path = os.path.join(st.session_state.projekt_path, f"Ebook_{st.session_state.jezyk_docelowy}")
        
        with c1:
            if os.path.exists(path+".pdf"):
                with open(path+".pdf", "rb") as f: st.download_button("📥 PDF", f, "ebook.pdf", "application/pdf")
            if os.path.exists(path+".epub"):
                with open(path+".epub", "rb") as f: st.download_button("📥 EPUB", f, "ebook.epub", "application/epub+zip")
        with c2:
            p_path = os.path.join(st.session_state.projekt_path, "Podcast_AI.mp3")
            if os.path.exists(p_path):
                with open(p_path, "rb") as f: st.download_button("🎙️ Podcast", f, "podcast.mp3", "audio/mpeg")
        with c3:
            mp3s = [f for f in os.listdir(st.session_state.projekt_path) if f.startswith("Rozdzial_") and f.endswith(".mp3")]
            if mp3s:
                zip_path = os.path.join(st.session_state.projekt_path, "Audiobook.zip")
                with zipfile.ZipFile(zip_path, 'w') as z:
                    for m in mp3s: z.write(os.path.join(st.session_state.projekt_path, m), m)
                with open(zip_path, "rb") as f: st.download_button("📦 Audiobook ZIP", f, "audiobook.zip", "application/zip")

    st.write(""); st.write("")
    if st.button("🔄 Reset / Nowy Projekt"):
        for k in ['prospekt_data', 'ebook_content_main', 'ebook_content_pl', 'projekt_path', 'generation_done', 'pdfy_gotowe']:
            if k in st.session_state: del st.session_state[k]
        st.session_state.etap = 0
        st.rerun()