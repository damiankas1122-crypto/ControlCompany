# ControlCompany v1.0 
### Inteligentny Asystent Magazynowy AI dla Małych i Średnich Przedsiębiorstw

**ControlCompany** to nowoczesna aplikacja wspierająca mikro- oraz małych przedsiębiorców w codziennym zarządzaniu procesami magazynowymi. System działa jako autonomiczny, cyfrowy menadżer oraz doradca biznesowy AI, zdolny do jednoczesnej obsługi wielu odizolowanych punktów handlowych (architektura **Multi-Store / Multi-Tenant**).

---

##  Stos Technologiczny (Core / Backend)
* **Język programowania:** Python 3.10+
* **Baza danych:** SQLite 3 (Optymalizacje Enterprise: tryb WAL, `synchronous=NORMAL`, wymuszone sprawdzanie `FOREIGN KEY` oraz kaskadowe usuwanie relacji).
* **Sztuczna Inteligencja:** Google Gemini 2.5 Flash via najnowsze oficjalne SDK (`google-genai`).
* **Zarządzanie stanem i kontekstem:** Dynamiczne wstrzykiwanie bezpieczeństwa per sklep (Context Injection) oraz natywna pętla obsługi sekwencyjnego *Parallel Function Calling*.

---

##  Struktura Projektu

```text
ControlCompany/
├── .env                  # Prywatny klucz API (Zignorowany w Git)
├── .env.example          # Szablon konfiguracji zmiennych środowiskowych
├── .gitignore            # Definicje plików ignorowanych przez system kontroli wersji
├── README.md             # Dokumentacja główna projektu
├── agent.py              # Orkiestrator sesji AI i parser narzędzi (Function Calling)
├── db_operations.py      # Warstwa dostępu do danych (CRUD Multi-Store)
└── main.py               # Panel sterowania i interfejs użytkownika (CLI)


---

##  Instrukcja Uruchomienia Lokalnego

### 1. Przygotowanie środowiska i zależności
W terminalu VS Code wykonaj:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install google-genai python-dotenv
```_

### 2. Konfiguracja i start
* Stwórz plik `.env` i wklej: `GEMINI_API_KEY=twój_klucz`
* Uruchom aplikację: `python main.py`

---

##  Rozwiązywanie Problemów (Troubleshooting)

### Błąd aktywacji skryptów w systemie Windows (PowerShell)
Jeśli PowerShell zablokuje uruchomienie `Activate.ps1`, wpisz w terminalu:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser