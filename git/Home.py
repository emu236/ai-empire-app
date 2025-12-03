# Home.py - WERSJA Z PROFILEM I SKLEPEM KREDYTÓW

import streamlit as st
import database as db
import stripe_agent
import time
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# --- KONFIGURACJA ---
load_dotenv()
st.set_page_config(page_title="AI Empire", page_icon="👑", layout="wide")

# Ścieżki
PATH_TO_PDF = "public/prezent.pdf" 
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Baza
db.init_db()

# --- STAN APLIKACJI ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user_tier' not in st.session_state: st.session_state.user_tier = "Free"
if 'username' not in st.session_state: st.session_state.username = ""
if 'email' not in st.session_state: st.session_state.email = ""
if 'credits' not in st.session_state: st.session_state.credits = 0
if 'is_admin' not in st.session_state: st.session_state.is_admin = False

# ==============================================================================
# 🎨 CUSTOM CSS
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 3rem; padding-bottom: 5rem; }
    
    .metric-card {
        background-color: #262730;
        border: 1px solid #444;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .hero-title {
        background: linear-gradient(90deg, #FF4B4B 0%, #7038FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
    }
    .price-card {
        background-color: #121212; padding: 20px; border-radius: 15px; border: 1px solid #444; text-align: center;
    }
    .price-card.highlight { border: 2px solid #FFD700; box-shadow: 0 0 15px rgba(255, 215, 0, 0.2); }
    .price-big { font-size: 2rem; font-weight: bold; color: #FFF; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# --- FUNKCJE LOGICZNE ---
def perform_login(user, tier, admin_status, email, credits):
    st.session_state.authenticated = True
    st.session_state.username = user
    st.session_state.user_tier = tier
    st.session_state.is_admin = bool(admin_status)
    st.session_state.email = email
    st.session_state.credits = credits

def send_lead_magnet(receiver_email, name):
    if not os.path.exists(PATH_TO_PDF): return False, "Brak PDF."
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = receiver_email
        msg['Subject'] = f"🎁 {name}, Twój Plan AI"
        msg.attach(MIMEText(f"Cześć {name}!\n\nOto Twój e-book.", 'plain'))
        with open(PATH_TO_PDF, "rb") as f:
            part = MIMEApplication(f.read(), Name="Poradnik.pdf")
        part['Content-Disposition'] = 'attachment; filename="Poradnik.pdf"'
        msg.attach(part)
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True, "Wysłano"
    except Exception as e: return False, str(e)

# ==============================================================================
# 🚨 LOGIKA POWROTU ZE STRIPE (OBSŁUGA SUBSKRYPCJI I KREDYTÓW)
# ==============================================================================
query_params = st.query_params
if "session_id" in query_params:
    session_id = query_params["session_id"]
    st.query_params.clear()
    
    with st.spinner("Przetwarzanie transakcji..."):
        result = stripe_agent.verify_payment(session_id)
        
        if result["verified"]:
            user = result["username"]
            
            # SCENARIUSZ A: ZMIANA PAKIETU
            if result["type"] == "subscription":
                new_tier = result["value"]
                db.update_user_tier(user, new_tier)
                st.balloons()
                st.success(f"🎉 Sukces! Twój nowy plan to: {new_tier}")
                
            # SCENARIUSZ B: DOŁADOWANIE KREDYTÓW
            elif result["type"] == "credits":
                amount = int(result["value"])
                db.add_user_credits(user, amount) # Funkcja dodająca (nie resetująca)
                st.balloons()
                st.success(f"🎉 Doładowano {amount} kredytów!")

            # AUTO-LOGIN po transakcji
            u_data = db.get_user_details(user)
            if u_data:
                perform_login(user, u_data['tier'], u_data['is_admin'], u_data['email'], u_data['credits'])
                time.sleep(3)
                st.rerun()
        else:
            st.error("Płatność nie została zweryfikowana.")
            time.sleep(3)
            st.rerun()

# ==============================================================================
# WIDOK 1: ZALOGOWANY (NOWY LAYOUT)
# ==============================================================================
if st.session_state.authenticated:
    
    # Header z powitaniem
    c1, c2 = st.columns([3, 1])
    with c1: st.title(f"Cześć, {st.session_state.username} 👋")
    with c2: 
        # Odświeżenie kredytów
        current_credits = db.get_user_credits(st.session_state.username)
        st.session_state.credits = current_credits
        st.metric("Twoje Saldo", f"{current_credits} ⚡")

    # --- ZAKŁADKI GŁÓWNE ---
    tab_home, tab_shop, tab_profile = st.tabs(["🚀 Centrum Dowodzenia", "⚡ Doładuj Kredyty", "👤 Mój Profil"])

    # --- TAB 1: NARZĘDZIA ---
    with tab_home:
        if st.session_state.user_tier == "Premium":
            st.markdown("### Dostępne Narzędzia")
            row1 = st.columns(3)
            with row1[0]:
                if st.button("📚 Fabryka Ebooków", use_container_width=True): st.switch_page("pages/2_🏭_Fabryka_Contentu.py")
            with row1[1]:
                if st.button("🎥 Studio Awatarów", use_container_width=True): st.switch_page("pages/8_🎥_Studio_Awatarow.py")
            with row1[2]:
                if st.button("🎙️ Inteligentny Dyktafon", use_container_width=True): st.switch_page("pages/5_🎤_Inteligentny_Dyktafon.py")
            
            st.write("")
            row2 = st.columns(3)
            with row2[0]:
                if st.button("🕵️ Łowca Nisz", use_container_width=True): st.switch_page("pages/6_🕵️_Lowca_Nisz.py")
            with row2[1]:
                if st.button("📧 Cold Email B2B", use_container_width=True): st.switch_page("pages/3_📧_Cold_Email.py")
            with row2[2]:
                if st.button("📺 YouTube Repurposer", use_container_width=True): st.switch_page("pages/7_📺_YouTube_Repurposer.py")
        else:
            st.warning("Twój pakiet (Free/Basic/Standard) ogranicza dostęp do narzędzi. Przejdź do zakładki Profil, aby ulepszyć plan.")
            # Tutaj można dać ograniczone przyciski dla niższych pakietów

    # --- TAB 2: SKLEP Z KREDYTAMI (NOWOŚĆ) ---
    with tab_shop:
        st.subheader("Brakuje mocy? Dokup kredyty bez zmiany planu.")
        
        c_s1, c_s2, c_s3 = st.columns(3)
        
        # PAKIET MAŁY
        with c_s1:
            st.markdown('<div class="price-card"><h4>Starter Pack</h4><div class="price-big">29 zł</div><p>50 Kredytów</p></div>', unsafe_allow_html=True)
            url = stripe_agent.create_checkout_session("Small", "credits", st.session_state.email, st.session_state.username)
            if url: st.link_button("Kup 50 ⚡", url, use_container_width=True)

        # PAKIET ŚREDNI
        with c_s2:
            st.markdown('<div class="price-card highlight"><h4>Power Pack</h4><div class="price-big">99 zł</div><p>200 Kredytów</p></div>', unsafe_allow_html=True)
            url = stripe_agent.create_checkout_session("Medium", "credits", st.session_state.email, st.session_state.username)
            if url: st.link_button("Kup 200 ⚡", url, type="primary", use_container_width=True)

        # PAKIET DUŻY
        with c_s3:
            st.markdown('<div class="price-card"><h4>Tycoon Pack</h4><div class="price-big">399 zł</div><p>1000 Kredytów</p></div>', unsafe_allow_html=True)
            url = stripe_agent.create_checkout_session("Large", "credits", st.session_state.email, st.session_state.username)
            if url: st.link_button("Kup 1000 ⚡", url, use_container_width=True)

    # --- TAB 3: PROFIL (NOWOŚĆ) ---
    with tab_profile:
        col_p1, col_p2 = st.columns([1, 2])
        
        with col_p1:
            st.markdown("### Twoje Dane")
            st.text_input("Login", value=st.session_state.username, disabled=True)
            st.text_input("Email", value=st.session_state.email, disabled=True)
            st.text_input("Aktywny Plan", value=st.session_state.user_tier, disabled=True)
            
            st.markdown("---")
            if st.button("Wyloguj się z konta", type="secondary"):
                st.session_state.authenticated = False
                st.rerun()

        with col_p2:
            st.markdown("### Zarządzaj Subskrypcją")
            st.info("Tutaj możesz zmienić swój miesięczny plan. Zmiana planu zresetuje Twoje kredyty do wartości domyślnej dla nowego planu.")
            
            cp1, cp2, cp3 = st.columns(3)
            with cp1:
                st.caption("Basic (10 Kredytów)")
                if st.session_state.user_tier == "Basic": st.button("Obecny", disabled=True, key="p_b")
                else:
                    u = stripe_agent.create_checkout_session("Basic", "subscription", st.session_state.email, st.session_state.username)
                    if u: st.link_button("Zmień na Basic (49zł)", u)
            
            with cp2:
                st.caption("Standard (30 Kredytów)")
                if st.session_state.user_tier == "Standard": st.button("Obecny", disabled=True, key="p_s")
                else:
                    u = stripe_agent.create_checkout_session("Standard", "subscription", st.session_state.email, st.session_state.username)
                    if u: st.link_button("Zmień na Standard (99zł)", u)

            with cp3:
                st.caption("Premium (100 Kredytów)")
                if st.session_state.user_tier == "Premium": st.button("Obecny", disabled=True, key="p_p")
                else:
                    u = stripe_agent.create_checkout_session("Premium", "subscription", st.session_state.email, st.session_state.username)
                    if u: st.link_button("Zmień na Premium (199zł)", u)

# ==============================================================================
# WIDOK 2: LANDING PAGE (DLA GOŚCI) - BEZ ZMIAN WIZUALNYCH
# ==============================================================================
else:
    # ... (Tutaj wklej dokładnie tę samą sekcję Landing Page co w poprzednim kodzie) ...
    # Dla oszczędności miejsca w odpowiedzi, zakładam że sekcja 'else' zostaje taka jak była.
    # Jeśli potrzebujesz jej pełnego kodu, daj znać!
    
    # Skrócona wersja Landing Page (żeby kod się zmieścił):
    st.markdown('<div class="hero-title">Zbuduj Imperium Contentu z AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Zaloguj się, aby zarządzać.</div>', unsafe_allow_html=True)
    
    tab_login, tab_reg = st.tabs(["Logowanie", "Rejestracja"])
    with tab_login:
        with st.form("login_main"):
            l_user = st.text_input("Login")
            l_pass = st.text_input("Hasło", type="password")
            if st.form_submit_button("Zaloguj się", type="primary"):
                s, t, a, e, c = db.check_login(l_user, l_pass)
                if s: perform_login(l_user, t, a, e, c); st.rerun()
                else: st.error("Błąd.")
                
    with tab_reg:
        # ... formularz rejestracji ...
        with st.form("register_main"):
            new_user = st.text_input("Login")
            new_email = st.text_input("Email")
            new_pass = st.text_input("Hasło", type="password")
            zgoda = st.checkbox("Regulamin")
            if st.form_submit_button("Załóż konto"):
                ok, msg = db.create_user(new_user, new_email, new_pass)
                if ok: st.success("Gotowe!");
                else: st.error(msg)