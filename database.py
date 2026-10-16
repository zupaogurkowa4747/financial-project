import sqlite3
from contextlib import contextmanager
DB_NAME = "database.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise 
    finally:
        conn.close()

def init_db():
    with get_db() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transakcje (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                kwota REAL NOT NULL,
                typ TEXT NOT NULL) ''')
        
    with get_db() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wydatki (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                kwota REAL NOT NULL,
                kategoria TEXT NOT NULL,
                opis TEXT NOT NULL
                )''')


def pobierz_wszystkie_transakcje():
    with get_db() as cursor:
        cursor.execute("SELECT data, kwota, typ, id FROM transakcje ORDER BY id DESC")
        return cursor.fetchall()


def dodaj_transakcje(data, kwota, typ):
    with get_db() as cursor:
        cursor.execute("INSERT INTO transakcje (data, kwota, typ) VALUES (?, ?, ?)", (data, kwota, typ))

def pobierz_sume():
    with get_db() as cursor:
        cursor.execute("SELECT SUM(kwota) FROM transakcje")
        wynik = cursor.fetchone()[0]
        return wynik if wynik is not None else 0

def pobierz_wplaty():
    with get_db() as cursor:
        cursor.execute("SELECT SUM(kwota) FROM transakcje WHERE kwota > 0")
        wynik = cursor.fetchone()[0]
        return wynik if wynik is not None else 0

def pobierz_wyplaty():
    with get_db() as cursor:
        cursor.execute("SELECT SUM(kwota) FROM transakcje WHERE kwota < 0")
        wynik = cursor.fetchone()[0]
        return abs(wynik) if wynik is not None else 0

def usun_transakcje(id):
    with get_db() as cursor:
        cursor.execute("DELETE FROM transakcje WHERE id = ?", (id,))

def dodaj_wydatek(data, kwota, kategoria, opis):
    with get_db() as cursor:
        cursor.execute("INSERT INTO wydatki (data, kwota, kategoria, opis) VALUES (?, ?, ?, ?)", (data, kwota, kategoria, opis))

def pobierz_wydatki():
    with get_db() as cursor:
        cursor.execute("SELECT data, kwota, kategoria, opis, id FROM wydatki ORDER BY id DESC")
        return cursor.fetchall()

def pobierz_wydatki_wg_kategorii():
    with get_db() as cursor:
        cursor.execute("SELECT kategoria, SUM(kwota) FROM wydatki GROUP BY kategoria ORDER BY SUM(kwota) DESC")
        return cursor.fetchall()

def pobierz_sume_wydatkow():
        with get_db() as cursor:
            cursor.execute("SELECT SUM(kwota) FROM wydatki")
            wynik = cursor.fetchone()[0]
            return wynik if wynik is not None else 0