# pages/3_📄_Polityka_Prywatnosci.py
import streamlit as st

st.set_page_config(page_title="Polityka Prywatności i Regulamin", page_icon="📄", layout="centered")

st.title("Polityka Prywatności i Regulamin")

st.markdown("""
### 1. Kto jest administratorem Twoich danych?
Administratorem danych osobowych jest:  
**[TUTAJ WPISZ: Twoje Imię i Nazwisko / Firma]** E-mail kontaktowy: **[TUTAJ WPISZ: Twój email]**

### 2. Cel przetwarzania danych
Twoje dane (imię, adres e-mail) przetwarzamy w celu:
1.  **Wykonywania umowy** o dostarczenie treści cyfrowych (wysyłka E-booka).
2.  **Świadczenia usługi Newslettera** (informacje handlowe, wiedza, promocje) – na podstawie Twojej dobrowolnej zgody i zamówienia usługi.
3.  **Analizy i statystyki** – uzasadniony interes Administratora.

### 3. Odbiorcy danych
Zaufani partnerzy techniczni: dostawcy hostingu, serwerów (np. Streamlit Cloud) oraz systemów pocztowych (np. Google/Gmail). Nie sprzedajemy Twoich danych nikomu.

### 4. Czas przechowywania
Dane przetwarzamy do momentu wycofania przez Ciebie zgody (wypisania się z newslettera).

### 5. Twoje prawa
Masz prawo do: wglądu w dane, ich poprawiania, usunięcia ("prawo do bycia zapomnianym") oraz wniesienia skargi do Prezesa UODO.

### 6. Pliki Cookies
Strona używa niezbędnych plików cookies do utrzymania sesji technicznej.

---

### 7. Regulamin Newslettera (Świadczenie Usług Drogą Elektroniczną)

**§1. Postanowienia ogólne**
Niniejszy regulamin określa zasady korzystania z usługi Newsletter oraz otrzymywania treści cyfrowych (E-booka).

**§2. Rodzaj i zakres usługi**
Usługa polega na bezpłatnym przesyłaniu na podany adres e-mail wiadomości zawierających treści edukacyjne, marketingowe oraz darmowego E-booka.

**§3. Wymagania techniczne**
Do skorzystania z usługi niezbędne są:
1.  Urządzenie z dostępem do Internetu.
2.  Aktywne konto poczty elektronicznej.
3.  Oprogramowanie umożliwiające otwieranie plików PDF (np. Adobe Reader, przeglądarka internetowa).

**§4. Warunki zawierania i rozwiązywania umowy**
1.  Umowa zostaje zawarta z chwilą wpisania danych w formularzu i kliknięcia przycisku "Odbierz E-booka".
2.  Użytkownik może w każdej chwili zrezygnować z usługi (rozwiązać umowę), klikając w link "Wypisz się" w stopce wiadomości lub wysyłając wiadomość na adres Administratora.

**§5. Reklamacje**
Wszelkie reklamacje dotyczące niedostarczenia E-booka lub problemów technicznych prosimy zgłaszać mailowo. Administrator rozpatrzy reklamację w terminie 14 dni.

---
*Ostatnia aktualizacja: [WPISZ DZISIEJSZĄ DATĘ]*
""")

# Ukrywamy sidebar dla czytelności dokumentu
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
</style>
""", unsafe_allow_html=True)

st.write("")
if st.button("⬅️ Wróć do Formularza"):
    st.switch_page("pages/2_🎁_Odbierz_Prezent.py")