# Agent 4: Pisarz (Multi-Lang v4.0 - Fix Tytułów PL)

from openai import OpenAI

def uruchom_agenta_pisarza(prospekt_produktu: str, tytul_rozdzialu: str, dane_z_researchu: str, klucz_api: str, feedback_korekta: str, jezyk_docelowy: str = "Polski") -> str:
    client = OpenAI(api_key=klucz_api)
    
    kontekst_korekty = ""
    if feedback_korekta and "Brak" not in feedback_korekta:
        kontekst_korekty = f"--- INSTRUKCJA KOREKTY: {feedback_korekta} ---"
        
    # Logika Językowa
    if jezyk_docelowy == "Polski":
        instrukcja_jezykowa = "Napisz rozdział w języku Polskim."
    else:
        instrukcja_jezykowa = f"""
        WAŻNE WYMAGANIE DWUJĘZYCZNE:
        1. Napisz CAŁY rozdział w języku: {jezyk_docelowy}.
        2. Następnie wstaw dokładnie ten separator: [---TLUMACZENIE---]
        3. Następnie napisz TŁUMACZENIE całego rozdziału na język Polski.
        
        BARDZO WAŻNE DLA POLSKIEJ CZĘŚCI:
        Pierwszą linią po separatorze [---TLUMACZENIE---] MUSI BYĆ przetłumaczony tytuł rozdziału z nagłówkiem Markdown ##.
        Przykład:
        [---TLUMACZENIE---]
        ## Wstęp do Programowania (to jest przetłumaczony tytuł)
        Tutaj treść rozdziału po polsku...
        """

    prompt_pisarski = f"""
    Jesteś utalentowanym autorem. Napisz treść rozdziału: "{tytul_rozdzialu}".
    
    {instrukcja_jezykowa}

    --- PROSPEKT ---
    {prospekt_produktu}
    --- RESEARCH ---
    {dane_z_researchu}
    
    {kontekst_korekty}

    Tekst powinien być merytoryczny i podzielony na akapity. Używaj nagłówków ##.
    """
    
    print(f"  [Agent 4] Piszę treść rozdziału '{tytul_rozdzialu}' ({jezyk_docelowy})...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Jesteś autorem e-booków."},
                {"role": "user", "content": prompt_pisarski}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  [Agent 4] Błąd: {e}")
        return None