import os
import sys
import mimetypes
import re
from typing import Dict, Any, List
from google import genai
from google.genai import types
from dotenv import load_dotenv

import db_operations

load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    print("[BŁĄD] Nie znaleziono klucza GEMINI_API_KEY w pliku .env!")
    sys.exit(1)

MAPA_NARZEDZI = {
    "dodaj_produkt": db_operations.dodaj_produkt,
    "wyswietl_magazyn_sklepu": db_operations.wyswietl_magazyn_sklepu,
    "usun_produkt": db_operations.usun_produkt,
    "aktualizuj_produkt": db_operations.aktualizuj_produkt,
    "szukaj_produktu": db_operations.szukaj_produktu
}

def wykonaj_funkcje_bazy(nazwa_funkcji: str, argumenty: Dict[str, Any]) -> Dict[str, Any]:
    """Dynamicznie wykonuje funkcje bazy danych z obronnym parsowaniem typów."""
    if nazwa_funkcji in MAPA_NARZEDZI:
        try:
            # POPRAWKA ARCHITEKTONICZNA: Zabezpieczenie przed przesyłaniem floatów przez LLM dla pól typu INT
            if "cena_grosze" in argumenty and argumenty["cena_grosze"] is not None:
                argumenty["cena_grosze"] = int(round(float(argumenty["cena_grosze"])))
            if "nowa_cena_grosze" in argumenty and argumenty["nowa_cena_grosze"] is not None:
                argumenty["nowa_cena_grosze"] = int(round(float(argumenty["nowa_cena_grosze"])))
            if "ilosc" in argumenty and argumenty["ilosc"] is not None:
                argumenty["ilosc"] = int(round(float(argumenty["ilosc"])))
            if "nowa_ilosc" in argumenty and argumenty["nowa_ilosc"] is not None:
                argumenty["nowa_ilosc"] = int(round(float(argumenty["nowa_ilosc"])))
                
            return MAPA_NARZEDZI[nazwa_funkcji](**argumenty)
        except Exception as e:
            return {"status": "blad_wykonania", "komunikat": str(e)}
    return {"status": "nieobslugiwane_narzedzie", "komunikat": f"Funkcja {nazwa_funkcji} nie exists."}


def uruchom_agenta_ai(aktualny_sklep_id: int, nazwa_sklepu: str):
    print("\n" + "="*50)
    print(f"[AI MENADŻER] Łączenie z asystentem dla: {nazwa_sklepu.upper()}")
    print("[INFO] Wpisz 'menu', aby wrócić do wyboru sklepów.")
    print("="*50)

    client = genai.Client()

    system_instruction = (
        f"Jesteś elitarnym, inteligentnym menadżerem i osobistym doradcą biznesowym dla sklepu o nazwie: '{nazwa_sklepu}'. "
        f"Twoim celem życiowym jest pomaganie Szefowi w zarządzaniu wyłącznie tym konkretnym punktem (ID sklepu w bazie: {aktualny_sklep_id}). "
        f"Do dyspozycji masz zaawansowane narzędzia bazodanowe do zarządzania produktami (dodawanie, usuwanie, aktualizacja, szukanie, wyświetlanie). "
        f"UWAGA NA FINANSE: Ty rozmawiasz z Szefem zawsze w złotówkach (np. 4.50 zł), ale funkcje bazy danych bezwzględnie przyjmują "
        f"parametr 'cena_grosze' jako LICZBĘ CAŁKOWITĄ w groszach (np. 4.50 zł = 450). Zawsze przeliczaj walutę w locie przed wywołaniem narzędzia! "
        f"MULTIMODALNOŚĆ: Szef może przesyłać Ci zdjęcia faktur, paragony lub dokumenty PDF z dostawami. "
        f"Twoim zadaniem jest dokładne przeanalizowanie takiego dokumentu, wyciągnięcie z niego nazw produktów, ich cen oraz ilości, "
        f"a następnie AUTOMATYCZNE WYWOŁANIE narzędzia 'dodaj_produkt' dla każdej pozycji z dokumentu! "
        f"Po wykonaniu narzędzi, podsumuj krótko, profesjonalnie i po polsku, co dokładnie zostało zaimportowane."
    )

    try:
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                tools=list(MAPA_NARZEDZI.values()),
                temperature=0.1,  
                system_instruction=system_instruction
            )
        )
    except Exception as e:
        print(f"[BŁĄD AI]: Nie udało się zainicjalizować sesji: {str(e)}")
        return

    print(f"\n[AI]: Cześć Szefie! Jestem gotowy do pracy w '{nazwa_sklepu}'. Możesz też podać ścieżkę do zdjęcia/PDF faktury!")

    while True:
        polecenie = input(f"({nazwa_sklepu}) > ").strip()
        
        if not polecenie:
            continue
            
        if polecenie.lower() in ["menu", "wyjdz", "exit"]:
            print("[System] Odłączanie asystenta. Wracam do menu głównego.")
            break

        print("[AI] Analizuję...")

        try:
            zawartosc_wiadomosci = [polecenie]
            
            # POPRAWKA: Zaawansowane wyszukiwanie ścieżek z bezwzględnym czyszczeniem cudzysłowów systemowych
            szukane_sciezki = re.findall(r'["\']([^"\']+)["\']', polecenie) + polecenie.split()
            
            for kandydat in szukane_sciezki:
                czysta_sciezka = kandydat.strip(",.?!\"'")
                if os.path.isfile(czysta_sciezka):
                    mime_type, _ = mimetypes.guess_type(czysta_sciezka)
                    if mime_type and (mime_type.startswith("image/") or mime_type == "application/pdf"):
                        print(f"[System] Wykryto dokument: {czysta_sciezka}. Wczytywanie do AI...")
                        with open(czysta_sciezka, "rb") as f:
                            dane_pliku = f.read()
                        
                        zawartosc_wiadomosci.append(
                            types.Part.from_bytes(data=dane_pliku, mime_type=mime_type)
                        )
                        break

            response = chat.send_message(zawartosc_wiadomosci)

            while response.function_calls:
                czesci_odpowiedzi = []
                
                for function_call in response.function_calls:
                    print(f"[System] AI uruchamia akcję: '{function_call.name}'")
                    argumenty = dict(function_call.args)
                    
                    # BEZPIECZEŃSTWO: Wymuszenie id aktualnego sklepu dla WSZYSTKICH operacji
                    argumenty["sklep_id"] = aktualny_sklep_id
                    
                    wynik_z_bazy = wykonaj_funkcje_bazy(function_call.name, argumenty)
                    
                    czesci_odpowiedzi.append(
                        types.Part.from_function_response(
                            name=function_call.name,
                            response=wynik_z_bazy
                        )
                    )
                
                response = chat.send_message(czesci_odpowiedzi)

            if response.text:
                print(f"\n[AI]: {response.text}\n")

        except Exception as e:
            print(f"\n[BŁĄD INTEGRACJI AI]: Wystąpił problem: {str(e)}\n")