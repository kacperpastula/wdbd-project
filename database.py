import os
import psycopg2
import requests
import pandas as pd
from dotenv import load_dotenv

def get_db_connection():
    load_dotenv(override=True)
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5
    )

def create_database_tables():
    print("\n[Baza Danych] Tworzenie struktury tabel...")
    
    load_dotenv(override=True)
    
    if not os.getenv("DB_NAME"):
        print("Błąd: Brak konfiguracji bazy danych w pliku .env.")
        return False

    sql_queries = [
        # 1. Tabela Country
        """
        CREATE TABLE IF NOT EXISTS country (
            country_id INT PRIMARY KEY,
            country_name VARCHAR(255) NOT NULL
        );
        """,
        # 2. Tabela Station
        """
        CREATE TABLE IF NOT EXISTS station (
            station_id INT PRIMARY KEY,
            country_id INT REFERENCES country(country_id) ON DELETE SET NULL,
            station_name VARCHAR(255),
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            is_active boolean NOT NULL
        );
        """,
        # 3. Tabela Sensor
        """
        CREATE TABLE IF NOT EXISTS sensor (
            sensor_id INT PRIMARY KEY,
            sensor_name VARCHAR(255) NOT NULL,
            unit VARCHAR(50) NOT NULL
        );
        """,
        # 4. Tabela Measurement
        """
        CREATE TABLE IF NOT EXISTS measurement (
            measurement_id SERIAL PRIMARY KEY,
            sensor_id INT REFERENCES sensor(sensor_id) ON DELETE CASCADE,
            station_id INT REFERENCES station(station_id) ON DELETE CASCADE,
            value FLOAT NOT NULL,
            time TIMESTAMP NOT NULL,
            UNIQUE (sensor_id, time)
        );
        """
    ]

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                for query in sql_queries:
                    cursor.execute(query)
        connection.commit()
        
        print("Struktura bazy danych została pomyślnie utworzona!")
        print("Utworzone tabele: country, sensor, station, measurement")
        return True

    except Exception as e:
        print(f"Wystąpił błąd podczas tworzenia tabel: {e}")
        return False

def drop_all_tables():
    print("\n[Baza Danych] Rozpoczynam usuwanie wszystkich tabel...")
    
    load_dotenv(override=True)
    
    if not os.getenv("DB_NAME"):
        print("Błąd: Brak konfiguracji bazy danych w pliku .env.")
        return False
    
    tables = ["measurement", "station", "sensor", "country"]

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                for table in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                    cursor.execute(f"DROP VIEW IF EXISTS v_full_measurements, v_daily_trends, v_latest_measurements, v_country_sensor_avg, v_hourly_pollution_profile;")
            conn.commit()
        print("Baza danych została całkowicie wyczyszczona (tabele i widoki usunięte).")
        return True
        
    except Exception as e:
        print(f"Wystąpił błąd podczas czyszczenia bazy: {e}")
        return False

def add_to_tab_country(country_id, country_name):
    query = """
    INSERT INTO country (country_id, country_name)
    VALUES (%s, %s)
    ON CONFLICT (country_id) 
    DO UPDATE SET country_name = EXCLUDED.country_name;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (country_id, country_name))
            conn.commit()
    except Exception as e:
        print(f"Błąd podczas dodawania kraju {country_name}: {e}")

def add_to_tab_sensor(sensor_id, sensor_name, unit):
    """Wstawia czujnik/parametr do tabeli sensor. Jeśli istnieje, aktualizuje dane."""
    query = """
    INSERT INTO sensor (sensor_id, sensor_name, unit)
    VALUES (%s, %s, %s)
    ON CONFLICT (sensor_id) 
    DO UPDATE SET sensor_name = EXCLUDED.sensor_name, unit = EXCLUDED.unit;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (sensor_id, sensor_name, unit))
            conn.commit()
    except Exception as e:
        print(f"Błąd podczas dodawania sensora {sensor_name}: {e}")

def add_to_tab_station(station_id, station_name, country_id, lat, lon, is_active):
    """Wstawia stację do tabeli station. Jeśli istnieje, aktualizuje jej status i współrzędne."""
    query = """
    INSERT INTO station (station_id, country_id, station_name, latitude, longitude, is_active)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (station_id) 
    DO UPDATE SET 
        station_name = EXCLUDED.station_name,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        is_active = EXCLUDED.is_active;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (station_id, country_id, station_name, lat, lon, is_active))
            conn.commit()
    except Exception as e:
        print(f"Błąd podczas dodawania stacji {station_name}: {e}")

def add_to_tab_measurement(station_id, sensor_id, value, timestamp, measurement_id=None):
    """
    Wstawia pomiar do tabeli measurement.
    Wymaga podania station_id, sensor_id, value oraz timestamp.
    """
    if measurement_id is not None:
        query = """
        INSERT INTO measurement (measurement_id, station_id, sensor_id, value, time)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (measurement_id) DO NOTHING;
        """
        params = (measurement_id, station_id, sensor_id, value, timestamp)
    else:
        query = """
        INSERT INTO measurement (station_id, sensor_id, value, time)
        VALUES (%s, %s, %s, %s)

        ON CONFLICT (sensor_id, time) DO NOTHING;
        """
        params = (station_id, sensor_id, value, timestamp)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
            conn.commit()
    except Exception as e:
        print(f"Błąd podczas dodawania pomiaru (stacja: {station_id}, sensor: {sensor_id}): {e}")

def get_active_station_ids():
    query = """
    SELECT station_id 
    FROM station 
    WHERE is_active = true;
    """
    active_station_ids = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                active_station_ids = [row[0] for row in rows]
        return active_station_ids
    except Exception as e:
        print(f"Błąd podczas pobierania aktywnych stacji: {e}")
        return []
    
def get_active_sensor_ids():
    query = """
    SELECT sensor_id 
    FROM sensor 
    WHERE station_id IN (
        SELECT station_id 
        FROM station 
        WHERE is_active = true
    );
    """
    active_sensor_ids = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                active_sensor_ids = [row[0] for row in rows]
        return active_sensor_ids
    except Exception as e:
        print(f"Błąd podczas pobierania sensorów aktywnych stacji: {e}")
        return []

def create_views():
    print("\n[Baza Danych] Tworzenie widoków...")
    
    load_dotenv(override=True)
    if not os.getenv("DB_NAME"):
        print("Błąd: Brak konfiguracji bazy danych w pliku .env.")
        return False
    
    views = [
            # Widok 1. Płaskie dane
            # Ten widok łączy wszystkie tabele w jedną płaską strukturę.
            """--sql
            CREATE OR REPLACE VIEW v_full_measurements AS
            SELECT 
                m.measurement_id,
                m.time AS measurement_time,
                m.value,
                s.sensor_name,
                s.unit,
                st.station_name,
                st.latitude,
                st.longitude,
                st.is_active,
                c.country_name
            FROM public.measurement m
            JOIN public.sensor s ON m.sensor_id = s.sensor_id
            JOIN public.station st ON m.station_id = st.station_id
            JOIN public.country c ON st.country_id = c.country_id;
            """,
            # Widok 2. Agregacja trendów dziennych 
            # Ten widok grupuje dane do poziomu dnia, wyciągając najważniejsze statystyki.
            # Sprawdzi się do analizy historycznych trendów i wykresów liniowych.
            """--sql
            CREATE OR REPLACE VIEW v_daily_trends AS
            SELECT 
                DATE(m.time) AS measurement_date,
                st.station_name,
                c.country_name,
                s.sensor_name,
                s.unit,
                COUNT(m.measurement_id) AS measurement_count,
                MIN(m.value) AS min_value,
                MAX(m.value) AS max_value,
                AVG(m.value) AS avg_value
            FROM public.measurement m
            JOIN public.sensor s ON m.sensor_id = s.sensor_id
            JOIN public.station st ON m.station_id = st.station_id
            JOIN public.country c ON st.country_id = c.country_id
            GROUP BY 
                DATE(m.time),
                st.station_name,
                c.country_name,
                s.sensor_name,
                s.unit;
            """,
            # Widok 3. Najnowsze pomiary
            # Jeden, najświeższy pomiar dla każdego czujnika na każdej ze stacji
            """--sql
            CREATE OR REPLACE VIEW v_latest_measurements AS
            WITH RankedMeasurements AS (
                SELECT 
                    station_id,
                    sensor_id,
                    value,
                    time,
                    ROW_NUMBER() OVER (PARTITION BY station_id, sensor_id ORDER BY time DESC) as rn
                FROM public.measurement
            )
            SELECT 
                st.station_name,
                s.sensor_name,
                rm.value AS latest_value,
                s.unit,
                rm.time AS last_measurement_time,
                st.is_active
            FROM RankedMeasurements rm
            JOIN public.station st ON rm.station_id = st.station_id
            JOIN public.sensor s ON rm.sensor_id = s.sensor_id
            WHERE rm.rn = 1;
            """,
            # Widok 4. Analiza zanieczyszczeń według kraju
            # Pozwala na szybkie porównanie ogólnych uśrednionych wartości z konkretnych 
            # typów czujników pomiędzy poszczególnymi państwami. Wyklucza stacje, które zostały oznaczone jako nieaktywne
            """--sql
            CREATE OR REPLACE VIEW v_country_sensor_avg AS
            SELECT 
                c.country_name,
                s.sensor_name,
                s.unit,
                COUNT(DISTINCT st.station_id) AS active_stations_count,
                AVG(m.value) AS overall_avg_value
            FROM public.measurement m
            JOIN public.sensor s ON m.sensor_id = s.sensor_id
            JOIN public.station st ON m.station_id = st.station_id
            JOIN public.country c ON st.country_id = c.country_id
            WHERE st.is_active = TRUE
            GROUP BY 
                c.country_name,
                s.sensor_name,
                s.unit;
            """,
            # Widok 5. Dobowy profil zanieczyszczeń
            # Mówi jakie są średnie wartości z poszczególnych czujników w zależności od godziny, na każdej ze stacji
            """--sql
            CREATE OR REPLACE VIEW v_hourly_pollution_profile AS
            SELECT 
                EXTRACT(HOUR FROM m.time) AS hour_of_day,
                s.sensor_name,
                st.station_name,
                c.country_name,
                ROUND(CAST(AVG(m.value) AS NUMERIC), 2) AS avg_hourly_value
            FROM measurement m
            JOIN sensor s ON m.sensor_id = s.sensor_id
            JOIN station st ON m.station_id = st.station_id
            JOIN country c ON st.country_id = c.country_id
            GROUP BY EXTRACT(HOUR FROM m.time), s.sensor_name, st.station_name, c.country_name;
            """]
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            connect_timeout=5
        )
        
        cursor = connection.cursor()
        
        for query in views:
            cursor.execute(query)
            
        connection.commit()
        
        print("Pomyślnie dodano 5 widoków!")
        print("Utworzone widoki:")
        print(" - v_full_measurements (Płaskie dane)")
        print(" - v_daily_trends (Dzienne trendy)")
        print(" - v_latest_measurements (Najnowsze pomiary)")
        print(" - v_country_sensor_avg (Analiza zanieczyszczeń według kraju)")
        print(" - v_hourly_pollution_profile (Dobowy profil)")
        
        return True

    except psycopg2.Error as e:
        print(f"\nBłąd bazy danych podczas tworzenia widoków: {e}")
        if connection:
            connection.rollback() # Cofa zmiany jeśli coś pękło w połowie
        return False
        
    except Exception as e:
        print(f"\nWystąpił nieoczekiwany błąd: {e}")
        return False
    
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    
def list_database_views():
    """Pobiera i wyświetla listę wszystkich widoków w schemacie publicznym."""
    print("\n[Baza Danych] Pobieranie listy dostępnych widoków...")
    
    
    query = """
    SELECT table_name 
    FROM information_schema.views 
    WHERE table_schema = 'public';
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
               
                views = [row[0] for row in rows]
                
                if not views:
                    print("Brak widoków do wyświetlenia. Baza jest pusta.")
                    return []
                
                print(f"Znaleziono {len(views)} widoków:")
                for idx, view_name in enumerate(views, start=1):
                    print(f" {idx}. {view_name}")
                    
                return views

    except Exception as e:
        print(f"Wystąpił błąd podczas pobierania listy widoków: {e}")
        return []

def display_view_data(view_name):
    """Pobiera dane z podanego widoku i wyświetla je w terminalu jako DataFrame."""
    print(f"\n[Trwa pobieranie danych z widoku: {view_name} ...]")
    
    
    query = f"SELECT * FROM {view_name};" 
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                if not rows:
                    print("\nWidok jest pusty (brak danych).")
                    return
                
                colnames = [desc[0] for desc in cursor.description]
                
                
                df = pd.DataFrame(rows, columns=colnames)
                
                
                pd.set_option('display.max_rows', 100)
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', 200)
                
                print(f"\n--- Dane dla: {view_name} ---")
                
                
                try:
                    print(df.to_markdown(index=False)) 
                except ImportError:
                    # Fallback na wypadek braku zainstalowanego 'tabulate'
                    print(df)
                    
    except Exception as e:
        print(f"Błąd podczas pobierania danych z widoku: {e}")