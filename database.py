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