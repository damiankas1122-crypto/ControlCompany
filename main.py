import db_operations
import agent

def aplikacja_control_company():
    # Zapewnienie prawidłowej struktury bazy danych na starcie
    db_operations.inicjalizuj_baze()
    
    while True:
        print("\n" + "="*50)
        print("    CONTROLCOMPANY v1.0 - PANEL ZARZĄDZANIA SZEFA")
        print("="*50)
        print("1. Wybierz sklep i uruchom Asystenta AI")
        print("2. Stwórz / Zarejestruj nowy sklep")
        print("3. Zamknij aplikację")
        print("="*50)
        
        wybor = input("Wybierz opcję (1-3): ").strip()
        
        if wybor == "1":
            sklepy = db_operations.pobierz_wszystkie_sklepy()
                
            if not sklepy:
                print("\n[System] Nie masz jeszcze żadnego sklepu! Stwórz go najpierw (Opcja 2).")
                continue
                
            print("\nTWOJE AKTYWNE SKLEPY:")
            for s in sklepy:
                print(f"ID: {s['id']} | Nazwa: {s['nazwa']}")
                
            try:
                wybrane_id = int(input("\nWpisz ID sklepu, do którego chcesz wejść: ").strip())
                sklep = next((s for s in sklepy if s["id"] == wybrane_id), None)
                
                if sklep:
                    agent.uruchom_agenta_ai(sklep["id"], sklep["nazwa"])
                else:
                    print("\n[Błąd] Nie ma sklepu o takim ID!")
            except ValueError:
                print("\n[Błąd] Musisz podać poprawną liczbę jako ID!")
                
        elif wybor == "2":
            nazwa_nowego_sklepu = input("\nWpisz nazwę dla nowego punktu (np. Sklep Spożywczy u Janka): ").strip()
            wynik = db_operations.dodaj_sklep(nazwa_nowego_sklepu)
            if wynik["status"] == "sukces":
                print(f"\n[Sukces] Zarejestrowano sklep '{nazwa_nowego_sklepu}' z ID: {wynik['sklep']['id']}")
            else:
                print(f"\n[Błąd] {wynik['komunikat']}")
                
        elif wybor == "3":
            print("\nZamykanie ControlCompany. Do widzenia Szefie!")
            break
        else:
            print("\nNiepoprawna opcja! Wybierz 1, 2 lub 3.")

if __name__ == "__main__":
    aplikacja_control_company()