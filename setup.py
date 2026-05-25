import os
import psycopg2
import requests
from dotenv import load_dotenv

def get_user_input():
    print("=== KONFIGURACJA MONITORA JAKOŚCI POWIETRZA (OpenAQ -> Postgres) ===")
    
    # 1. Parametry dotyczące bazy PostgreSQL
    print("\n[1/3] Dane połączenia z bazą PostgreSQL")
    db_host = input("Host (np. localhost): ").strip() or "localhost"
    db_port = input("Port (np. 5432): ").strip() or "5432"
    db_name = input("Nazwa bazy danych: ").strip()
    db_user = input("Użytkownik bazy danych: ").strip()
    db_password = input("Hasło bazy danych: ").strip()
    
    # 2. Pobieranie klucza do API
    print("\n[2/3] Autoryzacja OpenAQ API")
    openaq_key = input("Podaj swój klucz API OpenAQ: ").strip()
    
    # 3. Pobieranie kodów krajów i częstotliwości pobierania danych
    print("\n[3/3] Filtrowanie danych")
    countries_input = input("Podaj kody krajów po przecinku (np. PL, DE, FR): ").strip()
    # Czyszczenie spacji i konwersja na wielkie litery
    countries = ",".join([c.strip().upper() for c in countries_input.split(",") if c.strip()])
    print("Podaj, co ile czasu program ma sprawdzać i pobierać nowe dane.")
    try:
        hours_in = input("Godziny (np. 1, zostaw puste jeśli 0): ").strip()
        hours = int(hours_in) if hours_in else 0
        
        minutes_in = input("Minuty (np. 30, zostaw puste jeśli 0): ").strip()
        minutes = int(minutes_in) if minutes_in else 0
        
        total_minutes = (hours * 60) + minutes
        
        if total_minutes <= 0:
            print("Czas musi być dłuższy niż 0 minut! Ustawiam domyślnie 15 minut.")
            total_minutes = 15
    except ValueError:
        print("Błąd: Podano nieprawidłową liczbę. Spróbuj ponownie.")
        return None

    return {
        "DB_HOST": db_host,
        "DB_PORT": db_port,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
        "OPENAQ_API_KEY": openaq_key,
        "TARGET_COUNTRIES": countries,
        "FETCH_INTERVAL_MINUTES": total_minutes
    }

def test_postgres_connection(config=None):
    print("\n[Sprawdzanie] Testowanie połączenia z bazą PostgreSQL...")
    if config is None:
        
        load_dotenv(override=True)
        config = {
            "DB_HOST": os.getenv("DB_HOST"),
            "DB_PORT": os.getenv("DB_PORT"),
            "DB_NAME": os.getenv("DB_NAME"),
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD")
        }
        if not config["DB_NAME"] or not config["DB_USER"]:
            print("Brak poprawnej konfiguracji bazy danych w pliku .env!")
            return False

    try:
        connection = psycopg2.connect(
            host=config["DB_HOST"],
            port=config["DB_PORT"],
            database=config["DB_NAME"],
            user=config["DB_USER"],
            password=config["DB_PASSWORD"],
            connect_timeout=5  # limit czasu na połączenie w sekundach
        )
        connection.close()
        print("Połączenie z bazą danych zakończone sukcesem!")
        return True
    except Exception as e:
        print(f"Błąd połączenia z bazą danych: {e}")
        return False

def save_to_env(config):
    env_lines = [
        f"DB_HOST={config['DB_HOST']}",
        f"DB_PORT={config['DB_PORT']}",
        f"DB_NAME={config['DB_NAME']}",
        f"DB_USER={config['DB_USER']}",
        f"DB_PASSWORD={config['DB_PASSWORD']}",
        f"OPENAQ_API_KEY={config['OPENAQ_API_KEY']}",
        f"TARGET_COUNTRIES={config['TARGET_COUNTRIES']}",
        f"FETCH_INTERVAL_MINUTES={config['FETCH_INTERVAL_MINUTES']}"
    ]
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write("\n".join(env_lines) + "\n")
        print("Konfiguracja została zapisana do pliku .env")
    except TypeError:
        print("Podano niepoprawny typ danych, konfiguracja nie została zapisana")

def update_env_variable(key, new_value):
    env_file = ".env"
    lines = []
    key_found = False

    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={new_value}\n"
            key_found = True
            break

    if not key_found:
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.append(f"{key}={new_value}\n")

    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

def test_openaq_connection(api_key=None):
    """
    Testuje połączenie z OpenAQ API v3.
    Jeśli parametr api_key nie zostanie podany, funkcja pobierze go automatycznie z pliku .env.
    """
    print("\n[Sprawdzanie] Testowanie połączenia z API OpenAQ v3...")
    
    if api_key is None:
        load_dotenv(override=True)
        api_key = os.getenv("OPENAQ_API_KEY")
        
    if not api_key:
        print("Błąd: Brak klucza API OpenAQ! Skonfiguruj go najpierw.")
        return False

    url = "https://api.openaq.org/v3/parameters"
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }

    try:
        # Wysłanie zapytania z limitem czasu 5 sekund
        response = requests.get(url, headers=headers, timeout=5)
        
        # Sprawdzamy status odpowiedzi HTTP
        if response.status_code == 200:
            print("Połączenie z API OpenAQ zakończone sukcesem! Klucz jest poprawny.")
            return True
        elif response.status_code == 401:
            print("Błąd API (401 Unauthorized): Podany klucz API OpenAQ jest nieprawidłowy!")
            return False
        else:
            print(f"Błąd API ({response.status_code}): Serwer zwrócił nieoczekiwany status.")
            return False
            
    except requests.exceptions.Timeout:
        print("Błąd połączenia: Przekroczono limit czasu żądania (Timeout). Check internet connection.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Wystąpił błąd podczas połączenia z API: {e}")
        return False

def get_fetch_interval():
    print("Podaj, jak często program ma sprawdzać i pobierać nowe dane.")
    try:
        hours_in = input("Godziny (np. 1, zostaw puste jeśli 0): ").strip()
        hours = int(hours_in) if hours_in else 0
        
        minutes_in = input("Minuty (np. 30, zostaw puste jeśli 0): ").strip()
        minutes = int(minutes_in) if minutes_in else 0
        
        total_minutes = (hours * 60) + minutes
        
        if total_minutes <= 0:
            print("Czas musi być dłuższy niż 0 minut! Ustawiam domyślnie 15 minut.")
            total_minutes = 15
        
        update_env_variable("FETCH_INTERVAL_MINUTES", str(total_minutes))
        print(f"Częstotliwość ustawiona! Dane będą pobierane co {total_minutes} min ({hours}h {minutes}m).")
        return total_minutes
        
    except ValueError:
        print("Błąd: Podano nieprawidłową liczbę. Spróbuj ponownie.")
        return None
