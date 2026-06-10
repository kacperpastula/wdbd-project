import requests
import os
from datetime import datetime
import database
from dotenv import load_dotenv
from openaq import OpenAQ
import threading

bg_thread = None
stop_event = threading.Event()

def get_X_stations(limit=50):
    start_time = datetime.now()
    log_id = database.add_import_log_start('STATIONS_LIST', start_time)

    load_dotenv(override=True)
    url = "https://api.openaq.org/v3/locations"
    
    countries_env = os.getenv("TARGET_COUNTRIES")
    countries_list = [c.strip().upper() for c in countries_env.split(",") if c.strip()]
    
    if not countries_list:
        database.update_import_log_finish(log_id, 4, 0, "Brak zdefiniowanych krajów w TARGET_COUNTRIES.")
        return {"error": "No target countries configured"}
    
    headers = {
        "X-API-Key": os.getenv("OPENAQ_API_KEY"),
        "Accept": "application/json"
    }

    records_processed = 0
    errors_occurred = False
    
    for country_iso in countries_list:
        params = {
            "iso": country_iso,
            "limit": limit
        }

        last_update_env = os.getenv("LAST_UPDATE_ACTIVITY") or "2026-01-30T01:00:00Z"
        dt_wzorzec = datetime.fromisoformat(last_update_env.replace('Z', '+00:00'))

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            for station in data["results"]:
                station_id = station["id"]
                station_name = station["name"]
                lat = station["coordinates"]["latitude"]
                lon = station["coordinates"]["longitude"]
                
                country_id = station["country"]["id"]
                country_name = station["country"]["name"]
                
                #Wyliczenie czy stacja jest aktywna 
                datetimeLast_obj = station.get("datetimeLast")
                is_active = False
                if datetimeLast_obj is not None:
                    datetimeLast_utc_tekst = datetimeLast_obj.get("utc")
                    if datetimeLast_utc_tekst:
                        dt_last = datetime.fromisoformat(datetimeLast_utc_tekst.replace('Z', '+00:00'))
                        is_active = dt_last > dt_wzorzec

                database.add_to_tab_country(country_id, country_name)
                database.add_to_tab_station(station_id, station_name, country_id, lat, lon, is_active)
                records_processed += 1
                
                for sensor in station["sensors"]:
                    sensor_id = sensor["id"]
                    sensor_name = sensor["parameter"]["name"]
                    unit = sensor["parameter"]["units"]
                    database.add_to_tab_sensor(sensor_id, sensor_name, unit)
        except requests.exceptions.RequestException as e:
            errors_occurred = True
            print(f"Błąd podczas pobierania stacji dla kraju {country_iso}: {e}")
            continue

    if errors_occurred and records_processed > 0:
        database.update_import_log_finish(log_id, 3, records_processed, "Pobrano stacje częściowo z błędami.")
    elif records_processed > 0:
        database.update_import_log_finish(log_id, 2, records_processed, "Pomyślnie zaimportowano listę stacji.")
    else:
        database.update_import_log_finish(log_id, 4, 0, "Nie udało się zaimportować żadnej stacji pomiarowej.")

    return {"status": "success", "processed": records_processed}


def fetch_latest_measurements_for_all_active_stations():
    start_time = datetime.now()
    log_id = database.add_import_log_start('LATEST_MEASUREMENTS', start_time)
    
    load_dotenv(override=True)
    api_key = os.getenv("OPENAQ_API_KEY")
    
    active_station_ids = database.get_active_station_ids()
    
    if not active_station_ids:
        print("Brak aktywnych stacji w bazie danych. Najpierw zaimportuj stacje.")
        return {"error": "No active stations found"}
    

    print("Inicjalizacja klienta OpenAQ...")
    client = OpenAQ(api_key=api_key)

    records_processed = 0
    errors_occurred = False

    for station_id in active_station_ids:
        print(f"Pobieranie pomiarów ze stacji {station_id}")
        try:
            latest_response = client.locations.latest(locations_id=station_id)
            
            if latest_response.results:
                for item in latest_response.results:
                    value = item.value
                    time_text = item.datetime.utc
                    sensor_id = item.sensors_id
                    if value is None or sensor_id is None or not time_text:
                        continue
                    timestamp = datetime.fromisoformat(time_text.replace('Z', '+00:00'))   
                    database.add_to_tab_measurement(station_id, sensor_id, value, timestamp)
                    records_processed += 1
            else:
                print(f"API nie zwróciło wyników dla stacji {station_id} (brak danych w systemie).")

        except Exception as e:
            errors_occurred = True
            print(f"Wystąpił błąd podczas korzystania z biblioteki OpenAQ dla stacji {station_id}: {e}")
            continue
    
    if errors_occurred and records_processed > 0:
        database.update_import_log_finish(log_id, 3, records_processed, "Pomiary pobrane częściowo z błędami.")
    elif records_processed > 0:
        database.update_import_log_finish(log_id, 2, records_processed, "Pomyślnie zapisano najnowsze pomiary smogu.")
    else:
        database.update_import_log_finish(log_id, 4, 0, "Wystąpił błąd. Nie zapisano żadnego nowego pomiaru z API.")

    return {"status": "success", "processed": records_processed}



def background_worker(stop_event):
    while True:
        load_dotenv(override=True)
        interval_min = int(os.getenv("FETCH_INTERVAL_MINUTES") or 60)
        
        print(f"\n[Wątek w tle] Rozpoczynam automatyczny pobór danych z OpenAQ...")
        try:
            fetch_latest_measurements_for_all_active_stations()
            print(f"[Wątek w tle] Pobieranie zakończone. Kolejne za {interval_min} min.")
        except Exception as e:
            print(f"[Wątek w tle] Błąd podczas automatycznego pobierania: {e}")
            
        if stop_event.wait(timeout=interval_min * 60):
            break

def start_background_fetching():
    global bg_thread, stop_event
    if bg_thread and bg_thread.is_alive():
        print(f"\nPobieranie w tle już działa!")
        return

    stop_event.clear()
    bg_thread = threading.Thread(target=background_worker, args=(stop_event,))
    bg_thread.daemon = True
    bg_thread.start()
    print(f"Automatyczne pobieranie w tle zostało URUCHOMIONE.")

def stop_background_fetching():
    global bg_thread, stop_event
    if not bg_thread or not bg_thread.is_alive():
        print(f"Pobieranie w tle nie jest teraz uruchomione.")
        return

    print(f"Zatrzymywanie wątku w tle... Proszę czekać.")
    stop_event.set()
    bg_thread.join()
    print(f"Automatyczne pobieranie w tle zostało ZATRZYMANE.")
