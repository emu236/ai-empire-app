# Agent 9: Wydawca (Wersja PRO v12.0 - PDF + EPUB)

import os
import logging
import re
import glob
from fpdf import FPDF
from PIL import Image

# Importy do EPUB
from ebooklib import epub
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- KONFIGURACJA PDF (Bez zmian) ---
COLOR_PRIMARY = (33, 37, 41)
COLOR_ACCENT = (0, 123, 255)
COLOR_TEXT = (60, 60, 60)
MARGIN = 25

def to_roman(n):
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ''
    i = 0
    while  n > 0:
        for _ in range(n // val[i]):
            roman_num += syb[i]
            n -= val[i]
        i += 1
    return roman_num

# --- KLASA PDF (Skrócona, bo bez zmian logicznych) ---
class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.toc_pages = {}
        self.use_unicode = False
        self.current_chapter_title = "" 
        self.chapter_counter = 0
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self): pass
    def footer(self):
        self.set_y(-15)
        self.set_font_safe('Arial', '', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'{self.page_no()}', 0, 0, 'C')

    def set_font_safe(self, family, style='', size=0):
        try: self.set_font(family, style, size)
        except: self.set_font('Arial', style, size)
            
    def get_font_name(self): return 'DejaVu' if self.use_unicode else 'Arial'

    def chapter_title(self, label, image_path=None):
        self.chapter_counter += 1
        self.add_page() 
        self.toc_pages[label] = self.page_no()
        self.current_chapter_title = label 
        
        roman_num = to_roman(self.chapter_counter)
        font = self.get_font_name()

        self.set_font(font, 'B', 12)
        self.set_text_color(100, 100, 100) 
        self.ln(5)
        self.cell(0, 10, f"ROZDZIAŁ {roman_num}", 0, 1, 'L')

        self.set_font(font, 'B', 24)
        self.set_text_color(*COLOR_PRIMARY)
        self.multi_cell(0, 10, label, align='L')
        
        if image_path: self.add_hero_image(image_path)

        self.ln(5)
        self.set_fill_color(*COLOR_ACCENT)
        self.cell(20, 1.5, "", 0, 1, 'L', fill=True) 
        self.ln(10)

    def chapter_subtitle(self, label):
        if label.strip() == self.current_chapter_title.strip(): return 
        font = self.get_font_name()
        self.set_font(font, 'B', 15)
        self.set_text_color(*COLOR_PRIMARY)
        self.ln(4)
        self.multi_cell(0, 7, label)
        self.ln(2)

    def parse_markdown_bold(self, text):
        if text.strip() == self.current_chapter_title.strip(): return
        font = self.get_font_name()
        parts = text.split('**')
        self.set_text_color(*COLOR_TEXT)
        self.set_font(font, '', 11)
        if len(parts) == 1: self.multi_cell(0, 6, text)
        else:
            for i, part in enumerate(parts):
                if i % 2 == 0: self.set_font(font, '', 11)
                else: self.set_font(font, 'B', 11)
                self.write(6, part)
            self.ln()
        self.ln(2)

    def print_bullet_point(self, text):
        font = self.get_font_name()
        self.set_font(font, '', 11)
        self.set_text_color(*COLOR_TEXT)
        self.set_x(MARGIN + 5) 
        self.cell(5, 6, chr(149), 0, 0, 'R')
        clean_text = text.lstrip('*- ').strip()
        self.multi_cell(0, 6, clean_text)
        self.ln(1)

    def print_toc(self, chapter_titles):
        self.add_page()
        font = self.get_font_name()
        self.set_font(font, 'B', 22)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 20, "Spis Treści", 0, 1, 'L')
        self.ln(5)
        self.set_font(font, '', 12)
        self.set_text_color(0, 0, 0)
        for i, title in enumerate(chapter_titles):
            roman = to_roman(i+1)
            clean_title = title.split(': ', 1)[-1].strip() if ':' in title else title
            self.cell(0, 10, f"Rozdział {roman}: {clean_title}", 0, 1, 'L')
            self.set_draw_color(230, 230, 230)
            self.line(MARGIN, self.get_y(), 190, self.get_y())

    def add_hero_image(self, image_path):
        if not os.path.exists(image_path): return
        try:
            target_width = 160 
            self.ln(5)
            self.image(image_path, x=MARGIN, w=target_width)
            self.ln(5)
        except Exception as e: logging.error(f"Błąd obrazu: {e}")

def clean_text_fallback(text):
    replacements = {'ą':'a', 'ć':'c', 'ę':'e', 'ł':'l', 'ń':'n', 'ó':'o', 'ś':'s', 'ź':'z', 'ż':'z', 'Ą':'A', 'Ć':'C', 'Ę':'E', 'Ł':'L', 'Ń':'N', 'Ó':'O', 'Ś':'S', 'Ź':'Z', 'Ż':'Z', '”':'"', '„':'"', '…':'...', '–':'-'}
    for k, v in replacements.items(): text = text.replace(k, v)
    return text

# --- NOWA FUNKCJA: GENERATOR EPUB ---
def generuj_epub(nazwa_projektu, lista_rozdzialow, tytul, usp, input_file, output_filename, images_map):
    logging.info(f"  [Wydawca] Generowanie EPUB: {output_filename}")
    
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(tytul)
    book.set_language('pl')
    book.add_author('AI Author')
    
    # Dodaj okładkę
    cover_path = os.path.join(nazwa_projektu, "okladka.png")
    if os.path.exists(cover_path):
        # EPUB wymaga otwarcia obrazu
        with open(cover_path, 'rb') as f:
            book.set_cover("cover.png", f.read())

    # CSS dla EPUB (Stylizacja)
    style = '''
        body { font-family: serif; margin: 5%; text-align: justify; }
        h1 { text-align: center; color: #2c3e50; margin-bottom: 0.5em; }
        h2 { color: #2980b9; border-bottom: 1px solid #eee; padding-bottom: 0.3em; margin-top: 1.5em; }
        p { margin-bottom: 1em; line-height: 1.6; }
        img { max-width: 100%; height: auto; display: block; margin: 20px auto; }
        .chapter-num { font-size: 0.8em; color: #7f8c8d; text-transform: uppercase; text-align: center; margin-top: 2em; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Tworzenie rozdziałów
    chapters_epub = []
    current_chapter = None
    chapter_counter = 0
    
    sciezka_txt = os.path.join(nazwa_projektu, input_file)
    
    with open(sciezka_txt, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Parsowanie tekstu do HTML (dla EPUB)
    content_buffer = []
    
    def flush_chapter():
        nonlocal current_chapter, content_buffer
        if current_chapter:
            html_body = "".join(content_buffer)
            current_chapter.content = html_body
            book.add_item(current_chapter)
            chapters_epub.append(current_chapter)
            content_buffer = []

    for line in lines:
        line = line.strip()
        if not line: continue

        if line.startswith("## ") and "---" not in line:
            flush_chapter() # Zapisz poprzedni
            
            chapter_counter += 1
            title = line.replace("## ", "").strip()
            roman = to_roman(chapter_counter)
            file_name = f'chap_{chapter_counter}.xhtml'
            
            current_chapter = epub.EpubHtml(title=title, file_name=file_name, lang='pl')
            current_chapter.add_item(nav_css)
            
            # Nagłówek rozdziału
            content_buffer.append(f'<div class="chapter-num">Rozdział {roman}</div>')
            content_buffer.append(f'<h1>{title}</h1>')
            
            # Obrazek
            img_path = images_map.get(chapter_counter)
            if img_path and os.path.exists(img_path):
                # Dodajemy obraz do EPUB
                img_name = os.path.basename(img_path)
                with open(img_path, 'rb') as f_img:
                    epub_img = epub.EpubItem(uid=f"img_{chapter_counter}", file_name=f"images/{img_name}", media_type="image/png", content=f_img.read())
                    book.add_item(epub_img)
                    content_buffer.append(f'<img src="images/{img_name}" alt="{title}" />')

        elif line.startswith("# ") and "---" not in line:
            clean = line.replace("# ", "").strip()
            content_buffer.append(f'<h2>{clean}</h2>')
            
        elif line.startswith("- ") or line.startswith("* "):
            clean = line.lstrip('*- ').strip()
            content_buffer.append(f'<ul><li>{clean}</li></ul>')
            
        else:
            # Markdown bold na HTML bold
            html_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            content_buffer.append(f'<p>{html_line}</p>')

    flush_chapter() # Zapisz ostatni

    # Spis treści i nawigacja
    book.toc = tuple(chapters_epub)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Zapis pliku
    sciezka_epub = os.path.join(nazwa_projektu, output_filename)
    epub.write_epub(sciezka_epub, book, {})
    logging.info(f"  [Wydawca] SUKCES: {sciezka_epub}")


# --- GŁÓWNA FUNKCJA WYDAWCY ---
def uruchom_wydawce(nazwa_projektu: str, lista_rozdzialow: list, tytul_ebooka: str, usp_ebooka: str, input_file: str = "wynik_CALY_EBOOK.txt", output_filename: str = "EBOOK_FINALNY.pdf"):
    
    # 1. GENEROWANIE PDF (tak jak było)
    sciezka_txt = os.path.join(nazwa_projektu, input_file)
    if not os.path.exists(sciezka_txt): return

    images_map = {}
    all_images = sorted(glob.glob(os.path.join(nazwa_projektu, "img_*.png")))
    for i, img_path in enumerate(all_images):
        if i < len(lista_rozdzialow):
            images_map[i+1] = img_path

    sciezka_pdf = os.path.join(nazwa_projektu, output_filename)
    
    # PDF LOGIC (Skrócona tutaj, ale w pliku powinna być pełna - wklejam tylko wywołanie metody)
    # ... (Tutaj jest kod klasy PDF i generowania, który już masz wyżej w klasie PDF) ...
    # Aby nie powtarzać kodu PDF, po prostu uruchamiamy logikę z klasy PDF:
    
    pdf = PDF()
    font_path = "DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font('DejaVu', '', font_path)
        pdf.add_font('DejaVu', 'B', font_path)
        pdf.use_unicode = True
    
    # Okładka PDF
    pdf.add_page()
    sciezka_okladki = os.path.join(nazwa_projektu, "okladka.png")
    if os.path.exists(sciezka_okladki):
        try:
            img = Image.open(sciezka_okladki)
            if img.mode != 'RGB': img = img.convert('RGB')
            temp_cover = os.path.join(nazwa_projektu, "temp.jpg")
            img.save(temp_cover)
            pdf.image(temp_cover, x=0, y=0, w=210, h=297)
            os.remove(temp_cover)
        except: pass
    
    # Tekst na okładce PDF
    pdf.set_y(100) 
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 90, 210, 80, 'F')
    pdf.set_y(105)
    font = pdf.get_font_name()
    pdf.set_font(font, 'B', 32)
    pdf.set_text_color(0, 0, 0)
    safe_title = tytul_ebooka if pdf.use_unicode else clean_text_fallback(tytul_ebooka)
    pdf.multi_cell(0, 14, safe_title, align='C')
    if usp_ebooka:
        pdf.ln(5)
        pdf.set_font(font, '', 16)
        pdf.set_text_color(80, 80, 80)
        safe_usp = usp_ebooka if pdf.use_unicode else clean_text_fallback(usp_ebooka)
        pdf.multi_cell(0, 8, safe_usp, align='C')

    pdf.print_toc(lista_rozdzialow)
    pdf.chapter_counter = 0 
    
    try:
        with open(sciezka_txt, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line:
                pdf.ln(3); continue
            if not pdf.use_unicode: line = clean_text_fallback(line)
            if line.startswith("!["): continue 
            if line.startswith("## ") and "---" not in line:
                clean = line.replace("## ", "").strip()
                next_chap_num = pdf.chapter_counter + 1
                img_for_chapter = images_map.get(next_chap_num)
                pdf.chapter_title(clean, img_for_chapter)
            elif line.startswith("# ") and "---" not in line:
                pdf.chapter_subtitle(line.replace("# ", "").strip())
            elif line.startswith("---"): pass 
            elif line.startswith("- ") or line.startswith("* "): pdf.print_bullet_point(line)
            else: pdf.parse_markdown_bold(line)
        pdf.output(sciezka_pdf)
        logging.info(f"SUKCES PDF: {sciezka_pdf}")
    except Exception as e:
        logging.error(f"Błąd PDF: {e}")

    # 2. GENEROWANIE EPUB (NOWOŚĆ)
    try:
        epub_filename = output_filename.replace(".pdf", ".epub")
        generuj_epub(nazwa_projektu, lista_rozdzialow, tytul_ebooka, usp_ebooka, input_file, epub_filename, images_map)
    except Exception as e:
        logging.error(f"Błąd EPUB: {e}")

if __name__ == '__main__':
    pass