import os
import psycopg2
import requests
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
            conn.commit()
        print("Baza danych została całkowicie wyczyszczona (tabele usunięte).")
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
    active_sensor_ids = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                active_sensor_ids = [row[0] for row in rows]
        return active_sensor_ids
    except Exception as e:
        print(f"Błąd podczas pobierania aktywnych stacji: {e}")
        return []

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