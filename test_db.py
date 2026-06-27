import db_operations

def runnable_test():
    print("--- ROZPOCZYNAMY TESTY BAZY ControlCompany ---")
    
    # 1. Inicjalizacja bazy danych
    db_operations.inicjalizuj_baze()
    print("[TEST 1] Inicjalizacja bazy: OK")
    
    # 2. Tworzymy dwa różne sklepy dla Szefa
    sklep1 = db_operations.dodaj_sklep("Sklep Spozywczy u Janka")
    sklep2 = db_operations.dodaj_sklep("Drugi Punkt - Warzywniak")
    
    print(f"[TEST 2] Dodawanie sklepów: {sklep1['status']}, {sklep2['status']}")
    
    # POPRAWKA: Usunięte kropki pomiędzy nawiasami słowników
    id_spozywczy = sklep1["sklep"]["id"] if sklep1["status"] == "sukces" else 1
    id_warzywniak = sklep2["sklep"]["id"] if sklep2["status"] == "sukces" else 2

    # 3. Dodajemy produkt do Sklepu 1 (Mleko za 4.50 zł = 450 groszy)
    prod1 = db_operations.dodaj_produkt(sklep_id=id_spozywczy, nazwa="Mleko 3.2%", cena_grosze=450, ilosc=20)
    # Dodajemy produkt do Sklepu 2 (Marchew za 2.99 zł = 299 groszy)
    prod2 = db_operations.dodaj_produkt(sklep_id=id_warzywniak, nazwa="Marchew luz", cena_grosze=299, ilosc=100)
    
    print(f"[TEST 3] Dodanie produktu do Spozywczego: {prod1['status']}")
    print(f"[TEST 4] Dodanie produktu do Warzywniaka: {prod2['status']}")
    
    # 4. Sprawdzamy, czy magazyny są odizolowane
    magazyn_1 = db_operations.wyswietl_magazyn_sklepu(id_spozywczy)
    print(f"\n[WERYFIKACJA] Stan magazynu 'Spożywczy u Janka' (ID: {id_spozywczy}):")
    for p in magazyn_1.get("produkty", []):
        print(f" -> {p['nazwa']} | Cena: {p['cena_grosze']/100} zł | Ilość: {p['ilosc']} szt.")

if __name__ == "__main__":
    runnable_test()