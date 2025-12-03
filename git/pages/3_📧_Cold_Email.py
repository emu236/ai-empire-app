# pages/4_📧_Cold_Email.py
import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

# --- Konfiguracja ---
load_dotenv()
st.set_page_config(page_title="Generator Cold Email", page_icon="📧", layout="wide")

# Pobieranie klucza API (z sesji lub .env)
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("OPENAI_API_KEY")

st.title("📧 Generator Ofert & Cold Email")
st.markdown("### Zamień swój produkt w sprzedaż. Wygeneruj skuteczne maile B2B.")

# --- Pasek boczny ---
with st.sidebar:
    st.header("⚙️ Konfiguracja")
    
    # Obsługa klucza API spójna z resztą aplikacji
    api_key_input = st.text_input("Klucz OpenAI API", value=st.session_state.api_key if st.session_state.api_key else "", type="password")
    if api_key_input:
        st.session_state.api_key = api_key_input
    
    st.divider()
    framework = st.selectbox("Strategia Copywritingu", 
                             ["AIDA (Uwaga-Zainteresowanie-Pożądanie-Akcja)", 
                              "PAS (Problem-Agitacja-Rozwiązanie)", 
                              "BAB (Before-After-Bridge)",
                              "Bezpośredni i Krótki (Cold Mailing 2.0)"])
    
    tone = st.select_slider("Ton wiadomości", options=["Luźny", "Przyjacielski", "Profesjonalny", "Agresywny sprzedażowo"])

# --- Funkcja Generująca ---
def generate_emails(product_name, audience, problem, solution, framework, tone, key):
    client = OpenAI(api_key=key)
    
    prompt = f"""
    Jesteś światowej klasy copywriterem B2B i ekspertem od Cold Mailingu.
    Twoim zadaniem jest napisanie sekwencji sprzedażowej.
    
    KONTEKST:
    - Produkt/Usługa: {product_name}
    - Klient docelowy (Persona): {audience}
    - Główny ból klienta: {problem}
    - Nasze rozwiązanie: {solution}
    - Wybrany ton: {tone}
    - Framework: {framework}
    
    ZADANIE:
    Napisz sekwencję 3 krótkich, konkretnych maili:
    1. **E-mail 1 (Otwarcie):** Przełamujący lody, krótki, skupiony na problemie klienta (nie na nas). Musi mieć intrygujący temat.
    2. **E-mail 2 (Follow-up - 3 dni później):** Przypomnienie, dodanie "social proof" lub dodatkowej wartości. Krótki.
    3. **E-mail 3 (Break-up - 7 dni później):** "Ostatnia szansa", lekkie wycofanie się, zostawienie otwartej furtki.
    
    FORMATOWANIE:
    Użyj Markdown. Oddziel maile poziomą linią (---). Nie dodawaj zbędnych komentarzy typu "Oto twoje maile", po prostu podaj treść.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Błąd: {e}"

# --- Interfejs Główny ---

if not st.session_state.api_key:
    st.warning("👈 Podaj klucz API w pasku bocznym, aby korzystać z narzędzia.")
    st.stop()

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.subheader("📝 Dane o Ofercie")
    st.caption("Wypełnij to raz, a otrzymasz gotową kampanię.")
    
    product_name = st.text_input("Co sprzedajesz?", placeholder="np. Generator E-booków AI")
    audience = st.text_input("Do kogo?", placeholder="np. Influencerzy z TikToka, którzy nie mają własnych produktów")
    
    problem = st.text_area("Jaki mają problem?", height=100, 
                           placeholder="np. Mają duże zasięgi, ale nie zarabiają na nich pieniędzy, bo nie mają co sprzedawać.")
    
    solution = st.text_area("Jak im pomagasz?", height=100,
                            placeholder="np. Daję gotowe narzędzie, które tworzy e-booka w 5 minut, którego mogą sprzedać fanom.")
    
    st.write("")
    generate_btn = st.button("🚀 Generuj Sekwencję Maili", type="primary", use_container_width=True)

with col2:
    st.subheader("📩 Wynik")
    
    if generate_btn:
        if not problem or not solution:
            st.error("⚠️ Uzupełnij opis problemu i rozwiązania.")
        else:
            with st.spinner("Analizuję psychologię klienta i piszę teksty..."):
                email_content = generate_emails(product_name, audience, problem, solution, framework, tone, st.session_state.api_key)
                
                st.markdown(email_content)
                
                st.download_button(
                    label="📥 Pobierz sekwencję (.txt)",
                    data=email_content,
                    file_name="kampania_cold_email.txt",
                    mime="text/plain"
                )