import os
import psycopg2
import requests
from dotenv import load_dotenv

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
        # 2. Tabela Sensor
        """
        CREATE TABLE IF NOT EXISTS sensor (
            sensor_id INT PRIMARY KEY,
            sensor_name VARCHAR(255) NOT NULL,
            unit VARCHAR(50) NOT NULL,
            is_active boolean NOT NULL
        );
        """,
        # 3. Tabela Location
        """
        CREATE TABLE IF NOT EXISTS location (
            location_id INT PRIMARY KEY,
            country_id INT REFERENCES country(country_id) ON DELETE SET NULL,
            location_name VARCHAR(255),
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION
        );
        """,
        # 4. Tabela Measurement
        """
        CREATE TABLE IF NOT EXISTS measurement (
            measurement_id SERIAL PRIMARY KEY,
            sensor_id INT REFERENCES sensor(sensor_id) ON DELETE CASCADE,
            location_id INT REFERENCES location(location_id) ON DELETE CASCADE,
            value FLOAT NOT NULL,
            time TIMESTAMP NOT NULL
        );
        """
    ]

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
        
        for query in sql_queries:
            cursor.execute(query)
            
        connection.commit()
        
        print("Struktura bazy danych została pomyślnie utworzona!")
        print("Utworzone tabele: country, city, sensor, location, measurement")
        
        cursor.close()
        connection.close()
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
    
    tables = ["measurement", "location", "sensor", "country"]

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
        
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            
        connection.commit()
        print("Baza danych została całkowicie wyczyszczona (tabele usunięte).")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"Wystąpił błąd podczas czyszczenia bazy: {e}")
        return False
    
def create_views():
    print("\n[Baza Danych] Tworzenie widoków...")
    
    load_dotenv(override=True)
    if not os.getenv("DB_NAME"):
        print("Błąd: Brak konfiguracji bazy danych w pliku .env.")
        return False
    
    views = [
            # Widok 1. Płaskie dane
            """--sql
            CREATE OR REPLACE VIEW v_full_measurements AS
            SELECT 
                m.measurement_id,
                m.time AS measurement_time,
                m.value,
                s.sensor_name,
                s.unit,
                l.location_name,
                l.latitude,
                l.longitude,
                c.country_name
            FROM measurement m
            JOIN sensor s ON m.sensor_id = s.sensor_id
            JOIN location l ON m.location_id = l.location_id
            JOIN country c ON l.country_id = c.country_id;
            """,
            # Widok 2. Agregacja trendów dziennych 
            """--sql
            CREATE OR REPLACE VIEW v_daily_trends AS
            SELECT 
                DATE_TRUNC('day', m.time) AS measurement_date,
                c.country_name,
                l.location_name,
                s.sensor_name,
                s.unit,
                ROUND(CAST(AVG(m.value) AS NUMERIC), 2) AS avg_value,
                MIN(m.value) AS min_value,
                MAX(m.value) AS max_value,
                COUNT(m.measurement_id) AS readings_count
            FROM measurement m
            JOIN sensor s ON m.sensor_id = s.sensor_id
            JOIN location l ON m.location_id = l.location_id
            JOIN country c ON l.country_id = c.country_id
            GROUP BY DATE_TRUNC('day', m.time), c.country_name, l.location_name, s.sensor_name, s.unit;
            """,
            # Widok 3. Najnowsze pomiary
            """--sql
            CREATE OR REPLACE VIEW v_latest_measurements AS
            WITH RankedMeasurements AS (
            SELECT 
                m.measurement_id,
                m.location_id,
                m.sensor_id,
                m.value,
                m.time,
                ROW_NUMBER() OVER(PARTITION BY m.location_id, m.sensor_id ORDER BY m.time DESC) as rn
            FROM measurement m
            )
            SELECT 
                rm.time AS latest_time,
                c.country_name,
                l.location_name,
                l.latitude,
                l.longitude,
                s.sensor_name,
                rm.value,
                s.unit
            FROM RankedMeasurements rm
            JOIN sensor s ON rm.sensor_id = s.sensor_id
            JOIN location l ON rm.location_id = l.location_id
            JOIN country c ON l.country_id = c.country_id
            WHERE rm.rn = 1;
            """,
            # Widok 4. Ranking zanieczyszczeń w każdym kraju
            """--sql
            CREATE OR REPLACE VIEW v_location_pollution_ranking AS
            SELECT 
                c.country_name,
                l.location_name,
                s.sensor_name,
                ROUND(CAST(AVG(m.value) AS NUMERIC), 2) AS overall_avg_value,
                DENSE_RANK() OVER (PARTITION BY c.country_name, s.sensor_name ORDER BY AVG(m.value) DESC) AS pollution_rank
            FROM measurement m
            JOIN sensor s ON m.sensor_id = s.sensor_id
            JOIN location l ON m.location_id = l.location_id
            JOIN country c ON l.country_id = c.country_id
            GROUP BY c.country_name, l.location_name, s.sensor_name;
            """,
            # Widok 5. Dobowy profil zanieczyszczeń
            """--sql
            CREATE OR REPLACE VIEW v_hourly_pollution_profile AS
            SELECT 
                EXTRACT(HOUR FROM m.time) AS hour_of_day,
                s.sensor_name,
                l.location_name,
                c.country_name,
                ROUND(CAST(AVG(m.value) AS NUMERIC), 2) AS avg_hourly_value
            FROM measurement m
            JOIN sensor s ON m.sensor_id = s.sensor_id
            JOIN location l ON m.location_id = l.location_id
            JOIN country c ON l.country_id = c.country_id
            GROUP BY EXTRACT(HOUR FROM m.time), s.sensor_name, l.location_name, c.country_name;
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
        print(" - v_location_pollution_ranking (Ranking zanieczyszczeń)")
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