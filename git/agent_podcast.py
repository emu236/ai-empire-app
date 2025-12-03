# agent_podcast.py - STUDIO NAGRAŃ AI
import os
import time
from openai import OpenAI
from pydub import AudioSegment  # Wymaga: pip install pydub

def generuj_scenariusz_dialogu(client, tekst_wejsciowy):
    """
    Zamienia tekst rozdziału na scenariusz dialogu między Hostem a Ekspertem.
    """
    prompt = f"""
    Jesteś producentem radiowym. Twoim zadaniem jest zamiana podanego tekstu książki na angażujący scenariusz podcastu.
    
    ZASADY:
    1. Format ma być DOKŁADNIE taki:
       HOST: [Krótkie pytanie lub wstęp]
       EKSPERT: [Merytoryczna odpowiedź, wyjaśnienie]
       HOST: [Reakcja i kolejne pytanie]
       EKSPERT: [Dalsze wyjaśnienie]
    2. Używaj prostego, mówionego języka. Ma to brzmieć jak naturalna rozmowa dwóch osób.
    3. Host jest ciekawy i entuzjastyczny. Ekspert jest spokojny i merytoryczny.
    4. Całość ma trwać ok. 2-3 minuty czytania (nie rób tego zbyt długiego).
    
    TEKST ŹRÓDŁOWY:
    {tekst_wejsciowy[:10000]} 
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Błąd generowania scenariusza: {e}")
        return None

def text_to_speech_file(client, text, filepath, voice):
    """Generuje plik audio dla pojedynczej wypowiedzi."""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        response.stream_to_file(filepath)
        return filepath
    except Exception as e:
        print(f"Błąd TTS: {e}")
        return None

def uruchom_agenta_podcastu(api_key, tresc_ksiazki, output_folder, nazwa_pliku="Podcast_AI.mp3"):
    """
    Główna funkcja orkiestrująca cały proces tworzenia podcastu.
    """
    if not tresc_ksiazki:
        return None
        
    client = OpenAI(api_key=api_key)
    full_text = "\n".join(tresc_ksiazki) # Scalamy listę rozdziałów w jeden tekst
    
    # 1. PISANIE SCENARIUSZA
    print("🎙️ Pisanie scenariusza...")
    scenariusz = generuj_scenariusz_dialogu(client, full_text)
    if not scenariusz:
        return None

    # 2. NAGRYWANIE GŁOSÓW (Dubbing)
    print("🎙️ Nagrywanie głosów...")
    combined_audio = AudioSegment.empty()
    lines = scenariusz.split('\n')
    temp_files = []
    
    # Definicja obsady
    GLOS_HOSTA = "alloy"   # Żeński/Neutralny, energiczny
    GLOS_EKSPERTA = "onyx" # Męski, głęboki
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue
        
        # Rozpoznawanie ról
        speaker = None
        text = ""
        voice = ""
        
        if line.upper().startswith("HOST:"):
            speaker = "HOST"
            text = line[5:].strip() # Usuwa "HOST:"
            voice = GLOS_HOSTA
        elif line.upper().startswith("EKSPERT:"):
            speaker = "EKSPERT"
            text = line[8:].strip() # Usuwa "EKSPERT:"
            voice = GLOS_EKSPERTA
            
        if speaker and text:
            temp_filename = os.path.join(output_folder, f"temp_line_{i}.mp3")
            if text_to_speech_file(client, text, temp_filename, voice):
                # Dodajemy ciszę 0.5s między wypowiedziami dla naturalności
                segment = AudioSegment.from_mp3(temp_filename)
                combined_audio += segment + AudioSegment.silent(duration=300) 
                temp_files.append(temp_filename)

    # 3. MONTAŻ I EXPORT
    print("🎚️ Montaż końcowy...")
    final_path = os.path.join(output_folder, nazwa_pliku)
    combined_audio.export(final_path, format="mp3")
    
    # Sprzątanie plików tymczasowych
    for f in temp_files:
        try: os.remove(f)
        except: pass
        
    return final_path