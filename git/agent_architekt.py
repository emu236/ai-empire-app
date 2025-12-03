# Agent 2: Architekt Produktu (Multi-Lang v3.2)

from openai import OpenAI
from typing import Optional
import json

# Dodano argument: jezyk_docelowy
def uruchom_agenta_architekta(temat_produktu: str, klucz_api: str, jezyk_docelowy: str = "Polski") -> Optional[str]:
    client = OpenAI(api_key=klucz_api)

    instrukcja_jezykowa = ""
    if jezyk_docelowy != "Polski":
        instrukcja_jezykowa = f"UWAGA: Stwórz CAŁĄ strukturę w języku: {jezyk_docelowy}. Tytuły rozdziałów i opisy muszą być w języku {jezyk_docelowy}."

    prompt_architektury = f"""
    Jesteś doświadczonym Architektem Produktów Cyfrowych. Twoim zadaniem jest stworzenie kompleksowego Prospektu dla e-booka na temat: "{temat_produktu}". 
    
    {instrukcja_jezykowa}
    
    Prospekt musi być w formacie JSON i zawierać następujące klucze:
    1. 'Tytul': Sugestywny i chwytliwy tytuł e-booka (w języku {jezyk_docelowy}).
    2. 'Kluczowa_Obietnica_USP': Unikalna Propozycja Sprzedaży.
    3. 'Segment_Docelowy': Kim jest idealny klient.
    4. 'Cel_Ebooka': Co czytelnik osiągnie po przeczytaniu.
    5. 'Spis_Tresci': Lista modułów/rozdziałów (co najmniej 7, maksimum 9). Format: "Moduł X: [Tytuł w języku {jezyk_docelowy}]".
    6. 'Bonusy': Lista dwóch wartościowych bonusów.

    Nie dodawaj żadnego dodatkowego tekstu ani wyjaśnień poza czystym obiektem JSON.
    """
    
    print(f"  [Agent 2] Tworzę prospekt JSON ({jezyk_docelowy})...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Jesteś Architektem Produktów. Zawsze zwracaj czysty, poprawny obiekt JSON."},
                {"role": "user", "content": prompt_architektury}
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  [Agent 2] Wystąpił błąd: {e}")
        return None