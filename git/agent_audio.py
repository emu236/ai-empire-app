# agent_audio.py - Moduł generowania dźwięku
import os
from openai import OpenAI
from pydub import AudioSegment # Wymaga: pip install pydub

def text_to_speech(client, text, filename, voice="alloy"):
    """Generuje plik MP3 z podanego tekstu."""
    try:
        response = client.audio.speech.create(
            model="tts-1-hd", # Model wysokiej jakości
            voice=voice,
            input=text[:4096] # Limit OpenAI to 4096 znaków na żądanie
        )
        response.stream_to_file(filename)
        return filename
    except Exception as e:
        print(f"Błąd TTS: {e}")
        return None

def generuj_audiobook(api_key, text_content, output_folder, voice="onyx"):
    """
    Tworzy audiobooka: jeden plik MP3 na jeden rozdział.
    text_content: lista stringów (rozdziałów)
    """
    client = OpenAI(api_key=api_key)
    files = []
    
    for i, chapter_text in enumerate(text_content):
        # Usuwanie nagłówków Markdown (## Tytuł) dla lektora, żeby nie czytał "Hash hash Tytuł"
        clean_text = chapter_text.replace("#", "").strip()
        
        filename = os.path.join(output_folder, f"Rozdzial_{i+1}.mp3")
        print(f"Generuję audio: {filename}...")
        
        saved_file = text_to_speech(client, clean_text, filename, voice)
        if saved_file:
            files.append(saved_file)
            
    return files

def generuj_podcast_dialog(api_key, full_text, output_path):
    """
    1. Przerabia treść na scenariusz podcastu.
    2. Generuje audio z podziałem na role.
    """
    client = OpenAI(api_key=api_key)
    
    # KROK A: Tworzenie scenariusza
    prompt = f"""
    Na podstawie poniższej treści książki, stwórz krótki, dynamiczny scenariusz podcastu (ok. 3-5 minut rozmowy).
    Występują: 
    - HOST (Entuzjasta, zadaje pytania)
    - EKSPERT (Autor książki, odpowiada merytorycznie).
    
    Format wyjściowy musi być dokładnie taki:
    HOST: [Tekst]
    EKSPERT: [Tekst]
    
    TREŚĆ KSIĄŻKI:
    {full_text[:15000]} 
    """
    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    script = completion.choices[0].message.content
    
    # KROK B: Generowanie audio
    combined_audio = AudioSegment.empty()
    
    lines = script.split('\n')
    temp_files = []
    
    for idx, line in enumerate(lines):
        if line.startswith("HOST:"):
            txt = line.replace("HOST:", "").strip()
            fname = f"temp_{idx}.mp3"
            text_to_speech(client, txt, fname, voice="alloy") # Głos Hosta
            if os.path.exists(fname):
                combined_audio += AudioSegment.from_mp3(fname)
                temp_files.append(fname)
                
        elif line.startswith("EKSPERT:"):
            txt = line.replace("EKSPERT:", "").strip()
            fname = f"temp_{idx}.mp3"
            text_to_speech(client, txt, fname, voice="onyx") # Głos Eksperta
            if os.path.exists(fname):
                combined_audio += AudioSegment.from_mp3(fname)
                temp_files.append(fname)
    
    # Eksport całości
    final_path = os.path.join(output_path, "Podcast_AI.mp3")
    combined_audio.export(final_path, format="mp3")
    
    # Sprzątanie plików tymczasowych
    for f in temp_files:
        if os.path.exists(f): os.remove(f)
        
    return final_path