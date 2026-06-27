import sqlite3
from contextlib import contextmanager
from typing import Dict, Any, List, Optional

DB_NAME = "control_company.db"

@contextmanager
def pobierz_polaczenie():
    """Menedżer kontekstu bezpiecznie zarządzający połączeniem z SQLite."""
    conn = sqlite3.connect(DB_NAME, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA synchronous=NORMAL;")
        # Wymuszenie sprawdzania kluczy obcych i kaskadowego usuwania produktów
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        if conn.in_transaction:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def inicjalizuj_baze() -> None:
    """Tworzy schemat bazy danych z relacją Multi-Store i włącza tryb WAL."""
    try:
        with pobierz_polaczenie() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            kursor = conn.cursor()
            
            kursor.execute("""
                CREATE TABLE IF NOT EXISTS sklepy(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazwa TEXT NOT NULL UNIQUE
                )
            """)
            
            kursor.execute("""
                CREATE TABLE IF NOT EXISTS produkty(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sklep_id INTEGER NOT NULL,
                    nazwa TEXT NOT NULL,
                    cena_grosze INTEGER NOT NULL,  
                    ilosc INTEGER NOT NULL,
                    FOREIGN KEY(sklep_id) REFERENCES sklepy(id) ON DELETE CASCADE
                )
            """)
    except Exception as e:
        print(f"[Baza Danych] Krytyczny błąd inicjalizacji: {str(e)}")


def dodaj_sklep(nazwa: str) -> Dict[str, Any]:
    """Tworzy nowy sklep w systemie."""
    if not nazwa or not nazwa.strip():
        return {"status": "blad_walidacji", "komunikat": "Nazwa sklepu nie może być pusta."}
    try:
        with pobierz_polaczenie() as conn:
            kursor = conn.cursor()
            kursor.execute("INSERT INTO sklepy (nazwa) VALUES (?)", (nazwa.strip(),))
            nowe_id = kursor.lastrowid
        return {"status": "sukces", "sklep": {"id": nowe_id, "nazwa": nazwa.strip()}}
    except sqlite3.IntegrityError:
        return {"status": "blad", "komunikat": f"Sklep o nazwie '{nazwa}' już istnieje."}
    except Exception as e:
        return {"status": "blad", "komunikat": str(e)}


def pobierz_wszystkie_sklepy() -> List[Dict[str, Any]]:
    """Zwraca listę wszystkich zarejestrowanych sklepów Szefa dla interfejsu UI."""
    try:
        with pobierz_polaczenie() as conn:
            kursor = conn.cursor()
            kursor.execute("SELECT id, nazwa FROM sklepy")
            return [dict(row) for row in kursor.fetchall()]
    except Exception:
        return []


def dodaj_product(sklep_id: int, nazwa: str, cena_grosze: int, ilosc: int) -> Dict[str, Any]:
    """Aliasing dla kompatybilności z ewentualnymi wahaniami językowymi LLM."""
    return dodaj_produkt(sklep_id, nazwa, cena_grosze, ilosc)


def dodaj_produkt(sklep_id: int, nazwa: str, cena_grosze: int, ilosc: int) -> Dict[str, Any]:
    """Dodaje nowy produkt do magazynu konkretnego sklepu."""
    if not nazwa or not nazwa.strip():
        return {"status": "blad_walidacji", "komunikat": "Nazwa produktu nie może być pusta."}
    if cena_grosze < 0 or ilosc < 0:
        return {"status": "blad_walidacji", "komunikat": "Cena i ilość nie mogą być ujemne."}

    try:
        with pobierz_polaczenie() as conn:
            kursor = conn.cursor()
            kursor.execute("SELECT id FROM sklepy WHERE id = ?", (sklep_id,))
            if not kursor.fetchone():
                return {"status": "nie_znaleziono", "komunikat": f"Sklep o ID {sklep_id} nie istnieje."}

            kursor.execute(
                "INSERT INTO produkty (sklep_id, nazwa, cena_grosze, ilosc) VALUES (?, ?, ?, ?)",
                (sklep_id, nazwa.strip(), cena_grosze, ilosc)
            )
            nowe_id = kursor.lastrowid
            
        return {
            "status": "sukces",
            "produkt": {"id": nowe_id, "sklep_id": sklep_id, "nazwa": nazwa.strip(), "cena_grosze": cena_grosze, "ilosc": ilosc}
        }
    except Exception as e:
        return {"status": "blad", "komunikat": str(e)}


def wyswietl_magazyn_sklepu(sklep_id: int) -> Dict[str, Any]:
    """Pobiera listę wszystkich produktów z wybranego sklepu."""
    try:
        with pobierz_polaczenie() as conn:
            kursor = conn.cursor()
            kursor.execute("SELECT id, nazwa, cena_grosze, ilosc FROM produkty WHERE sklep_id = ?", (sklep_id,))
            rows = kursor.fetchall()
            
        if not rows:
            return {"status": "pusty", "produkty": []}
        return {"status": "sukces", "produkty": [dict(r) for r in rows]}
    except Exception as e:
        return {"status": "blad", "komunikat": str(e)}


def usun_produkt(sklep_id: int, produkt_id: int) -> Dict[str, Any]:
    """Bezpiecznie usuwa produkt z konkretnego sklepu na podstawie ID."""
    try:
        with pobierz_polaczenie() as conn:
            kursor = conn.cursor()
            kursor.execute("SELECT nazwa FROM produkty WHERE id = ? AND sklep_id = ?", (produkt_id, sklep_id))
            row = kursor.fetchone()
            
            if not row:
                return {"status": "nie_znaleziono", "komunikat": f"Brak produktu o ID {produkt_id} w tym sklepie."}
                
            nazwa_produktu = row["nazwa"]
            kursor.execute("DELETE FROM produkty WHERE id = ? AND sklep_id = ?", (produkt_id, sklep_id))
            
        return {"status": "sukces", "operacja": "usuwanie", "id": produkt_id, "nazwa": nazwa_produktu}
    except Exception as e:
        return {"status": "blad", "komunikat": str(e)}


def aktualizuj_produkt(sklep_id: int, produkt_id: int, nowa_cena_grosze: Optional[int] = None, nowa_ilosc: Optional[int] = None) -> Dict[str, Any]:
    """Aktualizuje cenę lub ilość produktu w konkretnym sklepie."""
    if nowa_cena_grosze is None and nowa_ilosc is None:
        return {"status": "brak_zmian", "komunikat": "Nie podano żadnych danych do aktualizacji."}
    if (nowa_cena_grosze is not None and nowa_cena_grosze < 0) or (nowa_ilosc is not None and nowa_ilosc < 0):
        return {"status": "blad_walidacji", "komunikat": "Wartości nie mogą być ujemne."}
        
    try:
        with pobierz_polaczenie() as conn:
            kursor = conn.cursor()
            kursor.execute("SELECT nazwa FROM produkty WHERE id = ? AND sklep_id = ?", (produkt_id, sklep_id))
            row = kursor.fetchone()

            if not row:
                return {"status": "nie_znaleziono", "komunikat": f"Brak produktu o ID {produkt_id} w tym sklepie."}
            
            pola_do_zmiany = []
            argumenty = []

            if nowa_cena_grosze is not None:
                pola_do_zmiany.append("cena_grosze = ?")
                argumenty.append(nowa_cena_grosze)
            if nowa_ilosc is not None:
                pola_do_zmiany.append("ilosc = ?")
                argumenty.append(nowa_ilosc)

            argumenty.extend([produkt_id, sklep_id])
            zapytanie = f"UPDATE produkty SET {', '.join(pola_do_zmiany)} WHERE id = ? AND sklep_id = ?"
            kursor.execute(zapytanie, tuple(argumenty))

        return {
            "status": "sukces",
            "id": produkt_id,
            "nazwa": row["nazwa"],
            "zaktualizowane_pola": {"cena_grosze": nowa_cena_grosze, "ilosc": nowa_ilosc}
        }
    except Exception as e:
        return {"status": "blad", "komunikat": str(e)}


def szukaj_produktu(sklep_id: int, fraza: str) -> Dict[str, Any]:
    """Wyszukuje produkty w obrębie wyłącznie jednego, wybranego sklepu."""
    if not fraza or not fraza.strip():
        return {"status": "blad_walidacji", "komunikat": "Fraza wyszukiwania nie może być pusta."}

    try:
        with pobierz_polaczenie() as conn:
            kursor = conn.cursor()
            kursor.execute(
                "SELECT id, nazwa, cena_grosze, ilosc FROM produkty WHERE sklep_id = ? AND nazwa LIKE ?",
                (sklep_id, f"%{fraza.strip()}%")
            )
            rows = kursor.fetchall()

        if not rows:
            return {"status": "pusty", "wyniki": [], "fraza": fraza}
        
        return {"status": "sukces", "wyniki": [dict(r) for r in rows], "fraza": fraza}
    except Exception as e:
        return {"status": "blad", "komunikat": str(e)}