# Dokumentacja projektu: Monitor Jakości Powietrza

## Opis projektu

Aplikacja służy do monitorowania jakości powietrza z wykorzystaniem danych z API OpenAQ.
Dane są zapisywane w bazie PostgreSQL, a następnie prezentowane w konsoli oraz na dashboardzie Streamlit.

Główne funkcje:
- pobieranie listy stacji i czujników z OpenAQ,
- zapisywanie informacji o stacjach, sensorach i pomiarach do bazy danych,
- tworzenie struktury bazy danych (tabele i widoki),
- automatyczne pobieranie pomiarów w tle,
- podgląd danych w konsoli i wizualizacja w przeglądarce.

## Wymagania

- Python 3.12 lub nowszy
- PostgreSQL
- aktywne połączenie internetowe
- klucz API OpenAQ

## Instalacja

1. Sklonuj repozytorium lub skopiuj pliki do lokalnego katalogu.
2. Przejdź do katalogu projektu
3. Zainstaluj zależności:

   - jeśli używasz `uv`:
     ```bash
     uv sync
     ```

   - jeśli nie korzystasz z `uv`:
     ```bash
     python -m pip install --upgrade pip
     python -m pip install colorama python-dotenv openaq pandas psycopg2 requests tabulate textual streamlit plotly
     ```

4. Utwórz bazę PostgreSQL, np.:

   ```sql
   CREATE DATABASE nowabaza;
   ```

5. Upewnij się, że masz dostęp do bazy i że użytkownik ma uprawnienia do tworzenia tabel.

> W przypadku problemów z instalacją `psycopg2`, użyj `psycopg2-binary`.

## Konfiguracja

Aplikacja zapisuje ustawienia w pliku `.env`.
Aby skonfigurować projekt, uruchom program i wybierz opcję `1` w menu głównym.

Podczas konfiguracji podaj:
- `DB_HOST` — host bazy danych (np. `localhost`),
- `DB_PORT` — port PostgreSQL (np. `5432`),
- `DB_NAME` — nazwa bazy danych,
- `DB_USER` — użytkownik bazy danych,
- `DB_PASSWORD` — hasło do bazy danych,
- `OPENAQ_API_KEY` — klucz API OpenAQ,
- `TARGET_COUNTRIES` — lista kodów krajów oddzielona przecinkami (np. `PL,DE,FR`),
- `FETCH_INTERVAL_MINUTES` — interwał pobierania danych w minutach,
- `LAST_UPDATE_ACTIVITY` — graniczna data aktywności stacji w formacie ISO.

Przykład wartości w `.env`:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nowabaza
DB_USER=postgres
DB_PASSWORD=haslo
OPENAQ_API_KEY=twój_klucz_api
TARGET_COUNTRIES=PL,DE,FR
FETCH_INTERVAL_MINUTES=60
LAST_UPDATE_ACTIVITY=2026-01-30T01:00:00Z
```

## Struktura bazy danych

Program tworzy następujące tabele:

- `country` — dane krajów,
- `station` — stacje pomiarowe,
- `sensor` — sensory i jednostki pomiarowe,
- `measurement` — pomiary z czujników,
- `import_status` — statusy operacji importu,
- `import_log` — logi importu danych.

Dodatkowo tworzy widoki SQL:

- `v_full_measurements` — wszystkie pomiary w jednej płaskiej strukturze,
- `v_daily_trends` — dzienne statystyki pomiarów,
- `v_latest_measurements` — najnowsze pomiary dla czujników,
- `v_country_sensor_avg` — średnie zanieczyszczeń według kraju,
- `v_hourly_pollution_profile` — dobowy profil stężeń według godziny.

## Uruchamianie programu

Uruchom program główny:

```bash
uv run python main.py
```

lub bez `uv`:

```bash
python main.py
```

## Obsługa programu

Po starcie programu dostępne jest menu z opcjami:

1. `Konfiguracja programu od 0`
   - wprowadza dane połączeniowe do bazy i klucz API,
   - zapisuje je w pliku `.env`,
   - testuje połączenie z bazą.

2. `Zmiana parametrów programu`
   - edycja ustawień bazy danych,
   - edycja klucza API i listy krajów,
   - zmiana częstotliwości pobierania danych,
   - test połączenia z OpenAQ.

3. `Obsługa struktury bazy danych`
   - `Stworzyć tabelę` — tworzy tabele oraz zapisuje statusy importu,
   - `Usunąć tabelę` — kasuje tabele i widoki utworzone przez aplikację.

4. `Pobieranie danych`
   - `Rozpocznij pobieranie danych / Zatrzymaj pobieranie danych` — uruchamia lub zatrzymuje automatyczny proces pobierania w tle,
   - `Pobierz nowe dane teraz` — aktualizuje bazę o najnowsze pomiary z aktywnych stacji,
   - `Zaktualizować listę stacji` — pobiera informacje o stacjach z OpenAQ.

5. `Wyświetlenie danych`
   - wyświetla listę dostępnych widoków i pozwala przeglądać wyniki w terminalu.

6. `Uruchom Wizualizację`
   - uruchamia dashboard Streamlit w przeglądarce na `http://localhost:8501`.

## Dashboard Streamlit

Dashboard wykorzystuje widoki:
- `v_full_measurements`,
- `v_hourly_pollution_profile`,
- `v_country_sensor_avg`.

Dostępne filtry:
- zanieczyszczenie,
- kraje,
- aktywne stacje,
- stacje pomiarowe,
- zakres dat,
- zakres godzin,
- minimalny i maksymalny próg stężenia,
- typ wykresu i skala osi Y,
- grupowanie linii (stacje lub kraje).

## Główne pliki projektu

- `main.py` — uruchamianie aplikacji,
- `menu.py` — menu konsolowe i obsługa wyborów,
- `setup.py` — konfiguracja i operacje `.env`, testy połączeń,
- `database.py` — definicja bazy danych, tabele, widoki, wyświetlanie danych,
- `upload.py` — pobieranie danych z OpenAQ i mechanizm tła,
- `dashboard.py` — aplikacja Streamlit do wizualizacji,
- `pyproject.toml` — metadane i zależności projektu.

## Uwagi i wskazówki

- Plik `.env` zawiera dane uwierzytelniające, nie umieszczaj go w repozytorium publicznym.
- Przed uruchomieniem dashboardu upewnij się, że baza ma dane oraz że widoki zostały utworzone.
- Możesz zmienić listę krajów w opcji `Zmiana parametrów programu`.
- Jeżeli widzisz problemy z `psycopg2`, spróbuj zainstalować `psycopg2-binary`.
