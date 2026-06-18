# Monitor Jakości Powietrza 

Projekt służący do automatycznego pobierania, magazynowania w bazie PostgreSQL i interaktywnej wizualizacji danych o zanieczyszczeniu powietrza z API OpenAQ.

## 1. Konfiguracja i instalacja środowiska

Projekt korzysta z narzędzia `uv` do zarządzania zależnościami.

1. Pobierz projekt na swój dysk.
2. Zainstaluj wymagane biblioteki, uruchamiając w terminalu:
   ```bash
   uv sync
3. Otwórz konsolę bazy danych i stwórz pustą bazę pod projekt:
    ```sql
    CREATE DATABASE nowabaza;
## 2. Pierwsze uruchomienie i pobieranie danych

Całym procesem steruję się za pomocą menu w konsoli wybierając odpowiednie opcje, przy pomocy klawiatury.

1. Uruchom główny program, klikając przycis run lub wpisz w terminalu: 
    ```bash
    uv run python main.py
2. Wybierz opcje 1 - Konfiguracja programu od 0. W konsoli pojawi się komunikat proszący o podanie danych do utworzonej bazy, oraz klucza API z OpenAQ. Program podane dane zapisuję w pliku `.env` 
3. Następnie podaj listę krajów, z których mają być zbierane dane(np. PL, DE, FR)
4. Podaj, co ile czasu program ma sprawdzać i pobierać nowe dane.
5. Podaj graniczną datę aktywności stacji w formacie ISO.
Stacje, które nie wysłały danych po tej dacie, zostaną oznaczone jako nieaktywne.
6. Wybierz opcje 3 - Obsługa struktury bazy danych, a następnie stwórz tabelę. Program utworzy 5 widoków.
7. Wybierz opcje 4 - Pobieranie danych. Wybierz opcje [1] Rozpocznij pobieranie danych - rozpoczynający pobieranie danych zgodnie z wytycznymi z punktu 6 lub [2] Pobierz nowe dane teraz - pobierający aktualne dane z API i dodaje je do utworzonej tabeli pomiarów.

## 3. Wizualizacja
1. Po utworzeniu bazy z pomiarami możesz wyświetlić je bezpośrednio w terminalu poprzez wybranie opcji 5 - Wyświetlanie danych. W terminalu aplikacja wypisze 5 widoków SQL
2. Zebrane dane możesz również zwizualizować na wykresach poprzez wybranie opcji 6 - Uruchom Wizualizacje. Aplikacja uruchomi się automatycznie w Twojej domyślnej przeglądarce pod adresem `http://localhost:8501`. 
