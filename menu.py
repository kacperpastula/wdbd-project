import os
import setup
import database
import upload
from colorama import Fore, Back, Style, init
#Menu główne
#Wygląd
def main_menu_front(mess = "\n=== Witamy w naszym programie! ==="):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(mess)
    print("\n[1] Konfiguracja programu od 0")
    print("[2] Zmiana parametrów programu")
    print("[3] Obsługa struktury bazy danych")
    print("[4] Pobieranie danych")
    print("[5] Wyświetlenie danych")
    print("[help] Pomoc")
    print("[exit] Wyjście z programu")
    
    menu_output = input("\nWybierz opcję: ").strip().lower() or "help"
    return menu_output
#Praca
def main_menu():
    while True:
        mo = main_menu_front()        
        match mo:
            case "1":
                first_setup()
            case "exit":
                os.system('cls' if os.name == 'nt' else 'clear')
                print("\nDziękujemy za skorzystanie z programu. Do widzenia!")
                break
            case "2":
                change_options()
            case "3":
                db_tables_mng()
            case "4":
                data_menu()
            case "5" |"6" |"7" |"8" |"9" | "help":
                print("\nPrzepraszam, to nie zostało jeszcze zaimplementowane :(")
            case _:
                print("\nNiepoprawny wybór. Spróbuj ponownie.") 


#Konfiguracja programu od 0
def first_setup():
    config = setup.get_user_input()
    
    if setup.test_postgres_connection(config):
        setup.save_to_env(config)
        print("\nGotowe! Możesz teraz przejść do pobierania daych.")
    else:
        print("\nUstawienia nie zostały zapisane z powodu błędu połączenia.")
        retry = input("Czy chcesz zapisać mimo to? (y/N): ").strip().lower()
        if retry == 'y':
            setup.save_to_env(config)


#Menu zmiany parametrów
#Wygląd
def change_menu_front():
    print("\n=== Menu zmiany parametrów ===")
    print("\nParametry dotyczące bazy:")
    print("[1] Host")
    print("[2] Port")
    print("[3] Nazwa bazy danych")
    print("[4] Użytkownik bazy danych")
    print("[5] Hasło bazy danych")
    print("[6] Sprawdzić połączenie z bazą danych")
    print("\nParametry dotyczące API:")
    print("[7] Klucz do API")
    print("[8] Kraje")
    print("[9] Częstotliwość pobierania danych")
    print("[10] Graniczna data aktywności stacji")
    print("[11] Sprawdzić połączenie z API")
    print("\nInne:")
    print("[help] Pomoc")
    print("[exit] Wyjście do głównego menu")
    
    menu_output = input("\nWybierz opcję: ").strip().lower() or "help"
    return menu_output
#Praca
def change_options():
    while True:
        mo = change_menu_front()
        match mo:
            #BD
            case "1":
                db_host = input("Host (np. localhost): ").strip() or "localhost"
                setup.update_env_variable("DB_HOST", db_host)
                print("Host został zaktualizowany. Pamiętaj o przetestowaniu połączenia!")
            case "2":
                db_port = input("Port (np. 5432): ").strip() or "5432"
                setup.update_env_variable("DB_PORT", db_port)
                print("Port został zaktualizowany. Pamiętaj o przetestowaniu połączenia!")
            case "3":
                db_name = input("Nazwa bazy danych: ").strip()
                setup.update_env_variable("DB_NAME", db_name)
                print("Nazwa bazy danych została zaktualizowana. Pamiętaj o przetestowaniu połączenia!")
            case "4":
                db_user = input("Użytkownik bazy danych: ").strip()
                setup.update_env_variable("DB_USER", db_user)
                print("Urzytkownik został zaktualizowany. Pamiętaj o przetestowaniu połączenia!")
            case "5":
                db_password = input("Podaj nowe hasło do bazy danych: ").strip()
                setup.update_env_variable("DB_PASSWORD", db_password)
                print("Hasło do bazy zostało zaktualizowane. Pamiętaj o przetestowaniu połączenia!")
            case "6":
                setup.test_postgres_connection()
            #API
            case "7":
                openaq_key = input("Podaj swój klucz API OpenAQ: ").strip()
                setup.update_env_variable("OPENAQ_API_KEY", openaq_key)
            case "8":
                countries_input = input("Podaj kody krajów po przecinku (np. PL, DE, FR): ").strip()
                countries = ",".join([c.strip().upper() for c in countries_input.split(",") if c.strip()])
                setup.update_env_variable("TARGET_COUNTRIES", countries)
            case "9":
                setup.get_fetch_interval()
            case "10":
                print("\nPodaj graniczną datę aktywności stacji w formacie ISO.")
                print("Stacje, które nie wysłały danych po tej dacie, zostaną oznaczone jako nieaktywne.")
                default_date = "2026-01-30T01:00:00Z"
                last_update_input = input(f"Data aktywności (Enter dla domyślnej: {default_date}): ").strip()
                last_update_activity = last_update_input if last_update_input else default_date
                setup.update_env_variable("LAST_UPDATE_ACTIVITY", last_update_activity)

            case "11":
              setup.test_openaq_connection()  
            #Inne
            case "exit":
                break
            case "help":
                print("\nPrzepraszam, to nie zostało jeszcze zaimplementowane :(")
            case _:
                print("\nNiepoprawny wybór. Spróbuj ponownie.") 

#Menu obsługi bazy danych
#Wygląd
def db_menu_front():
    print("\n=== Menu tworzenia struktury bazy danych ===")
    print("\n[1] Stworzyć tabeli")
    print("[2] Usunąć tabeli (Usuwa tylko tabeli związane z tym programem)")
    print("[help] Pomoc")
    print("[exit] Wyjście do głównego menu")
    
    
    menu_output = input("\nWybierz opcję: ").strip().lower() or "help"
    return menu_output
#Praca
def db_tables_mng():
    while True:
        mo = db_menu_front()
        match mo:
            case "1":
                if database.create_database_tables():
                    database.create_views()
            case "2":
                database.drop_all_tables()
            case "exit":
                break
            case "help":
                print("\nPrzepraszam, to nie zostało jeszcze zaimplementowane :(")
            case _:
                print("\nNiepoprawny wybór. Spróbuj ponownie.") 

#Menu pobierania danych
#wygląd
def data_menu_front():
    print("\n=== Menu pobierania danych ===")
    print("\n[1] Rospocznij pobieranie danych / Zatrzymaj pobieranie danych")
    print("[2] Pobierz nowe dane teraz")
    print("[3] Zaktualizować listę stacji")
    print("[help] Pomoc")
    print("[exit] Wyjście do głównego menu")
    
    menu_output = input("\nWybierz opcję: ").strip().lower() or "help"
    return menu_output

    # Czyści terminal przed pokazaniem menu (działa na Windows i Linux/Mac)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    banner = f"""
{Fore.GREEN}  ___   _               _VE  __  __                 _ _             
{Fore.GREEN} / _ \ | |             / _ \|  \/  |               (_) |            
{Fore.CYAN}| | | || |__    ___   / /_\ \ \  / | ___  _ __  _  _ _| |_ ___  _ __ 
{Fore.CYAN}| | | || '_ \  / _ \  |  _  | |\/| |/ _ \| '_ \| | | | | __/ _ \| '__|
{Fore.BLUE}| |_| || |_) ||  __/  | | | | |  | | (_) | | | | |_| | | || (_) | |   
{Fore.BLUE} \___/ |_.__/  \___|  \_| |_/\_|  |_/\___/|_| |_|\__,_|_|\__\___/|_|   
    """
    print(banner)
    print(Fore.YELLOW + "           System Monitorowania Jakości Powietrza v1.0")
    print(Style.DIM + "        -------------------------------------------------")
#Praca
def data_menu():
    while True:
        mo = data_menu_front()
        match mo:
            case "1":
                res = input("\nJeśli chcesz uruchomić pobieranie wpisz [1], jeąeli zatrzymać - [2]")
                match res:
                    case "1":
                        upload.start_background_fetching()
                    case "2":
                        upload.stop_background_fetching()
                        break
                    case _:
                        print("\nNiepoprawny wybór. Spróbuj ponownie.") 
            case "2":
                upload.fetch_latest_measurements_for_all_active_stations()
            case "3":
                lim = input("\nIle stacji chcesz pobrać z jednego kraju?: ").strip().lower()
                print("To może potrwać, im więcej krajów, tym dłużej")
                upload.get_X_stations(lim)
            case "exit":
                break
            case "help":
                print("\nPrzepraszam, to nie zostało jeszcze zaimplementowane :(")
            case _:
                print("\nNiepoprawny wybór. Spróbuj ponownie.") 
    