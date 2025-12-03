# agent_researcher.py - WERSJA Z WERYFIKACJĄ ŹRÓDEŁ (FACT-CHECKING)

from openai import OpenAI
from duckduckgo_search import DDGS
import json

def search_web(query, max_results=10):
    """Przeszukuje internet w poszukiwaniu aktualnych informacji."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        print(f"Błąd wyszukiwania: {e}")
        return []

def weryfikuj_zrodla(client, topic, search_results):
    """
    Kluczowa funkcja: FILTR JAKOŚCI.
    Analizuje znalezione linki i wybiera tylko te wiarygodne.
    """
    if not search_results:
        return []

    # Przygotowujemy listę dla AI do oceny
    sources_text = "\n".join([f"ID: {i} | URL: {r['href']} | Tytuł: {r['title']} | Fragment: {r['body']}" for i, r in enumerate(search_results)])

    prompt = f"""
    Jesteś surowym Weryfikatorem Źródeł (Fact-Checker).
    Temat badania: "{topic}".
    
    Twoim zadaniem jest ocenić poniższą listę znalezionych w sieci źródeł i wybrać TYLKO te wiarygodne i merytoryczne.
    
    KRYTERIA ODRZUCENIA (BLACKLISTA):
    - Fora internetowe (Reddit, Quora - chyba że temat dotyczy opinii społecznej).
    - Strony z dużą ilością reklam, clickbaitowe tytuły.
    - Nieznane, podejrzane domeny.
    - Treści, które wyglądają na spam SEO.
    
    KRYTERIA AKCEPTACJI (WHITELISTA):
    - Oficjalne dokumentacje, strony rządowe (.gov), edukacyjne (.edu).
    - Renomowane portale branżowe i newsowe.
    - Blogi ekspertów z udokumentowanym autorytetem.
    
    Zwróć TYLKO listę ID najlepszych źródeł (maksymalnie 5) w formacie JSON:
    {{ "selected_ids": [0, 2, 5] }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        selected_ids = data.get("selected_ids", [])
        
        # Zwracamy pełne obiekty wybranych źródeł
        verified_sources = [search_results[i] for i in selected_ids if i < len(search_results)]
        return verified_sources
        
    except Exception as e:
        print(f"Błąd weryfikacji: {e}")
        return search_results[:3] # Fallback: weź pierwsze 3 jak AI zawiedzie

def uruchom_researchera(temat, api_key):
    """
    Główna funkcja orkiestrująca: Szukaj -> Weryfikuj -> Notuj.
    """
    client = OpenAI(api_key=api_key)
    
    print(f"🔍 [Researcher] Szukam informacji o: {temat}")
    
    # 1. Wyszukiwanie (Live Web)
    raw_results = search_web(temat)
    
    # 2. Filtracja (Fact-Checking)
    print("🛡️ [Researcher] Weryfikuję wiarygodność źródeł...")
    verified_sources = weryfikuj_zrodla(client, temat, raw_results)
    
    # Przygotowanie kontekstu dla pisarza
    if verified_sources:
        context_text = "\n\n".join([f"ŹRÓDŁO ({s['title']}): {s['body']} [Link: {s['href']}]" for s in verified_sources])
    else:
        context_text = "Brak wiarygodnych źródeł online. Opieram się na wiedzy ogólnej."

    # 3. Synteza (Tworzenie notatki)
    print("📝 [Researcher] Tworzę notatkę merytoryczną...")
    prompt = f"""
    Jesteś asystentem ds. researchu (Researcherem).
    Temat rozdziału: "{temat}".
    
    Oto zweryfikowane, wiarygodne informacje znalezione w sieci:
    {context_text}
    
    Zadanie:
    Stwórz szczegółową, merytoryczną notatkę dla Pisarza.
    1. Wyciągnij najważniejsze fakty, liczby, definicje i przykłady.
    2. Jeśli źródła podają sprzeczne informacje, zaznacz to.
    3. Ignoruj informacje reklamowe.
    4. Skup się na "mięsie" - konkretnej wiedzy, którą można użyć w e-booku.
    5. Jeśli temat dotyczy kodowania/technologii, poszukaj przykładów w źródłach.
    
    Notatka ma być zwięzła, ale gęsta od informacji.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Błąd generowania notatki: {e}"