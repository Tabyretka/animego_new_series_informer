import sqlite3
from config import db_name


def start_base():
    db = sqlite3.connect(f'{db_name}')
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER, url TEXT)")
    db.commit()
    db.close()


def create_profile(user_id):
    db = sqlite3.connect(f'{db_name}')
    cursor = db.cursor()
    data = cursor.execute(f'SELECT user_id FROM users WHERE user_id=={user_id}').fetchone()
    if data is None:
        cursor.execute(f"INSERT INTO users VALUES(?, ?);", [user_id, ''])
    else:
        url = cursor.execute(f"SELECT url FROM users WHERE user_id=={user_id}").fetchone()
        return url
    db.commit()
    db.close()
    return None


def get_all_data():
    db = sqlite3.connect(f'{db_name}')
    cursor = db.cursor()
    data = cursor.execute("SELECT * FROM users WHERE url!=''").fetchall()
    db.commit()
    db.close()
    return [i for i in data]


def get_url(user_id):
    db = sqlite3.connect(f'{db_name}')
    cursor = db.cursor()
    url = cursor.execute(f"SELECT url FROM users WHERE user_id=={user_id}").fetchone()
    db.close()
    return url


def edit_url(user_id, url):
    db = sqlite3.connect(f'{db_name}')
    cursor = db.cursor()
    cursor.execute(f"UPDATE users SET url='{url}' WHERE user_id={user_id}")
    db.commit()
    db.close()