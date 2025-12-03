# agent_grafik.py - WERSJA Z POPRAWIONYM TŁEM DLA DŁUGICH TYTUŁÓW
from openai import OpenAI
import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

# Funkcja pomocnicza do dzielenia tekstu na linie, żeby mieścił się w obrazku
def zawijaj_tekst(text, font, max_width, draw_interface):
    lines = []
    # Jeśli brak tekstu, zwróć pustą listę
    if not text:
        return lines
        
    words = text.split()
    current_line = words[0]
    
    for word in words[1:]:
        # Sprawdzamy, czy dodanie kolejnego słowa przekroczy szerokość
        # Używamy textbbox (nowsza metoda PIL) do pomiaru
        bbox = draw_interface.textbbox((0, 0), current_line + " " + word, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

def uruchom_agenta_grafika(prompt_user, usp_text, api_key, output_folder, filename_base, jezyk="Polski"):
    client = OpenAI(api_key=api_key)
    os.makedirs(output_folder, exist_ok=True)

    # 1. Tłumaczenie prompta (DALL-E działa najlepiej po angielsku)
    prompt_trans = prompt_user
    if jezyk != "Angielski":
        try:
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Translate to English. Just the translation."},
                          {"role": "user", "content": prompt_user}]
            )
            prompt_trans = resp.choices[0].message.content
        except: pass

    # 2. Generowanie obrazu w DALL-E 3
    # Wymuszamy pionowy format dla okładki
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"{prompt_trans}. Vertical book cover design, high resolution, detailed, cinematic lighting.",
            size="1024x1792", # Format pionowy
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        image_data = requests.get(image_url).content
        img = Image.open(io.BytesIO(image_data))

        # Jeśli to nie okładka, tylko ilustracja do rozdziału, zapisz i wyjdź
        if filename_base != "okladka":
            filepath = os.path.join(output_folder, f"{filename_base}.png")
            img.save(filepath)
            return filepath
            
    except Exception as e:
        print(f"Błąd DALL-E: {e}")
        return None

    # ==========================================================================
    # 3. SKŁADANIE OKŁADKI (ZAAWANSOWANE NAKŁADANIE TEKSTU)
    # ==========================================================================
    try:
        # Konwertujemy na RGBA, żeby móc używać przezroczystości
        img = img.convert("RGBA")
        width, height = img.size
        
        # Warstwa na półprzezroczyste tło (overlay)
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        overlay_draw = ImageDraw.Draw(overlay)
        draw = ImageDraw.Draw(img)

        # --- Ładowanie czcionek (z fallbackiem do domyślnej) ---
        try:
            # Próba załadowania ładnej czcionki systemowej (Windows)
            font_title = ImageFont.truetype("arialbd.ttf", 90) # Arial Bold, duża
            font_usp = ImageFont.truetype("arial.ttf", 50)    # Arial zwykła, mniejsza
        except IOError:
            # Fallback jeśli nie ma Arial
            font_title = ImageFont.load_default()
            font_usp = ImageFont.load_default()
            print("Nie znaleziono Arial. Używam czcionki domyślnej.")

        # --- Przygotowanie tekstu (Tytuł z prompta) ---
        # Wyciągamy tytuł z prompta użytkownika (zakładamy, że jest w '...')
        import re
        match = re.search(r"theme: '([^']*)'", prompt_user)
        title_text = match.group(1) if match else "Tytuł E-booka"
        
        # --- KONFIGURACJA UKŁADU ---
        margin_x = 80 # Marginesy boczne
        max_text_width = width - (2 * margin_x)
        
        # 1. Zawijamy tekst na linie
        wrapped_title = zawijaj_tekst(title_text, font_title, max_text_width, draw)
        
        # 2. Obliczamy wysokość bloku tekstu
        # Pobieramy metryki czcionki (odstęp między liniami)
        try:
            ascent, descent = font_title.getmetrics()
            line_spacing = ascent + descent + 20 # Dodatkowy odstęp
        except:
             line_spacing = 100 # Wartość domyślna dla starych wersji PIL

        total_title_height = len(wrapped_title) * line_spacing

        # 3. Rysujemy dynamiczne tło pod tytuł
        start_y_title = 200 # Gdzie zaczyna się blok tytułu
        padding_box = 40    # Margines wewnątrz białego pudełka
        
        box_x1 = margin_x - padding_box
        box_y1 = start_y_title - padding_box
        box_x2 = width - margin_x + padding_box
        # Wysokość pudełka zależy od liczby linii tekstu
        box_y2 = start_y_title + total_title_height + padding_box

        # Rysujemy półprzezroczysty biały prostokąt na warstwie overlay
        overlay_draw.rectangle(
            [(box_x1, box_y1), (box_x2, box_y2)],
            fill=(255, 255, 255, 200) # Biały z przezroczystością (alpha=200/255)
        )
        
        # Łączymy obraz z warstwą tła
        img = Image.alpha_composite(img, overlay)
        # Odświeżamy obiekt rysowania po scaleniu
        draw = ImageDraw.Draw(img)

        # 4. Rysujemy tytuł linia po linii
        current_y = start_y_title
        for line in wrapped_title:
            # Centrowanie poziome każdej linii
            bbox = draw.textbbox((0, 0), line, font=font_title)
            line_width = bbox[2] - bbox[0]
            text_x = (width - line_width) / 2
            
            # Rysowanie tekstu (ciemny szary dla kontrastu)
            draw.text((text_x, current_y), line, font=font_title, fill=(40, 40, 40))
            current_y += line_spacing

        # --- Rysowanie USP (Podtytułu) na dole ---
        if usp_text and len(usp_text) > 3:
            usp_start_y = height - 300
            wrapped_usp = zawijaj_tekst(usp_text, font_usp, max_text_width, draw)
            
            current_y_usp = usp_start_y
            for line in wrapped_usp:
                bbox = draw.textbbox((0, 0), line, font=font_usp)
                line_width = bbox[2] - bbox[0]
                text_x = (width - line_width) / 2
                
                # Dodajemy lekki cień pod USP dla czytelności
                draw.text((text_x+2, current_y_usp+2), line, font=font_usp, fill=(0,0,0,180))
                # Tekst właściwy (biały)
                draw.text((text_x, current_y_usp), line, font=font_usp, fill=(255, 255, 255))
                current_y_usp += 60 # Mniejszy odstęp dla USP

        # Zapisujemy wynik (konwertujemy z powrotem do RGB, bo PNG nie musi mieć alphy)
        filepath = os.path.join(output_folder, f"{filename_base}.png")
        img.convert("RGB").save(filepath)
        return filepath

    except Exception as e:
        print(f"Błąd podczas składania okładki (PIL): {e}")
        # W razie błędu grafiki, zwracamy czysty obraz z DALL-E
        filepath = os.path.join(output_folder, f"{filename_base}_raw.png")
        img.convert("RGB").save(filepath)
        return filepath