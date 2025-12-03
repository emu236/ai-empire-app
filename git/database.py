# database.py - WERSJA Z HISTORIĄ PROJEKTÓW
import sqlite3
import bcrypt
import os
import datetime

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela Użytkowników
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT,
            password_hash BLOB,
            tier TEXT DEFAULT 'Free',
            is_admin INTEGER DEFAULT 0,
            credits INTEGER DEFAULT 3
        )
    ''')
    
    # NOWOŚĆ: Tabela Projektów
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            project_name TEXT,
            folder_path TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# --- FUNKCJE UŻYTKOWNIKA (Bez zmian) ---
def create_user(username, email, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    initial_tier, is_admin, initial_credits = "Free", 0, 3
    if username == "admin": 
        initial_tier, is_admin, initial_credits = "Premium", 1, 999999

    try:
        c.execute('INSERT INTO users (username, email, password_hash, tier, is_admin, credits) VALUES (?, ?, ?, ?, ?, ?)', 
                  (username, email, hashed, initial_tier, is_admin, initial_credits))
        conn.commit()
        return True, "Konto utworzone."
    except sqlite3.IntegrityError:
        return False, "Login zajęty."
    finally:
        conn.close()

def check_login(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT password_hash, tier, is_admin, email, credits FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[0]):
        return True, user[1], user[2], user[3], user[4]
    return False, None, None, None, 0

def update_user_tier(username, new_tier):
    credits_map = {"Basic": 10, "Standard": 30, "Premium": 100}
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET tier = ?, credits = ? WHERE username = ?', (new_tier, credits_map.get(new_tier, 5), username))
    conn.commit()
    conn.close()

def update_tier_by_email(email, new_tier):
    credits_map = {"Basic": 10, "Standard": 30, "Premium": 100}
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET tier = ?, credits = ? WHERE email = ?', (new_tier, credits_map.get(new_tier, 5), email))
    conn.commit()
    conn.close()

def deduct_credits(username, amount=1):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT credits, is_admin FROM users WHERE username = ?', (username,))
    res = c.fetchone()
    if not res: return False
    
    current, is_admin = res[0], res[1]
    if is_admin == 1: return True
    
    if current >= amount:
        c.execute('UPDATE users SET credits = credits - ? WHERE username = ?', (amount, username))
        conn.commit(); conn.close()
        return True
    return False

def get_user_credits(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT credits FROM users WHERE username = ?', (username,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

def get_user_details(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT tier, is_admin, email, credits FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user: return {"tier": user[0], "is_admin": user[1], "email": user[2], "credits": user[3]}
    return None

# --- NOWE FUNKCJE PROJEKTÓW ---

def save_project(username, project_name, folder_path):
    """Zapisuje nowy projekt w historii użytkownika."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # Sprawdź czy już nie istnieje (żeby nie dublować przy odświeżaniu)
    c.execute('SELECT id FROM projects WHERE folder_path = ?', (folder_path,))
    if not c.fetchone():
        c.execute('INSERT INTO projects (username, project_name, folder_path, created_at) VALUES (?, ?, ?, ?)',
                  (username, project_name, folder_path, date_str))
        conn.commit()
    conn.close()

def get_user_projects(username):
    """Pobiera listę projektów użytkownika (najnowsze na górze)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT project_name, folder_path, created_at FROM projects WHERE username = ? ORDER BY id DESC', (username,))
    projects = c.fetchall()
    conn.close()
    return projects

if not os.path.exists(DB_NAME):
    init_db()
def add_user_credits(username, amount):
    """Dodaje określoną liczbę kredytów do konta użytkownika."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Używamy składni: credits = credits + ?
    c.execute('UPDATE users SET credits = credits + ? WHERE username = ?', (amount, username))
    conn.commit()
    conn.close()