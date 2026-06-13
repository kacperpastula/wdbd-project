import streamlit as st
import pandas as pd
import plotly.express as px
import database  

st.set_page_config(page_title="Monitor Jakości Powietrza", layout="wide")

# --- Funkcja ładowania danych z bazy ---
@st.cache_data
def load_dashboard_data(view_name):
    try:
        conn = database.get_db_connection()
        query = f"SELECT * FROM {view_name};"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Błąd ładowania danych z widoku {view_name}: {e}")
        return pd.DataFrame()

# Naprawa okienek ostrzegawczych w ciemnym motywie
st.markdown("""
        <style>
        [data-testid="stAlert"] {
            background-color: rgba(255, 255, 255, 0.1) !important; 
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        [data-testid="stAlert"] p {
            color: #FAFAFA !important; 
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)

# Pobranie danych ze wszystkich 3 potrzebnych widoków
df_full = load_dashboard_data("v_full_measurements") 
df_hourly = load_dashboard_data("v_hourly_pollution_profile")
df_country = load_dashboard_data("v_country_sensor_avg")

if not df_full.empty:
    df_full['measurement_time'] = pd.to_datetime(df_full['measurement_time'])

st.title("Dashboard Jakości Powietrza")
st.markdown("Wizualizacja danych pomiarowych z systemu bazodanowego OpenAQ.")

if df_full.empty or df_hourly.empty or df_country.empty:
    st.warning("Brak kompletnych danych w bazie danych. Upewnij się, że dane zostały pobrane (opcja [4] w main.py).")
else:

    st.sidebar.header("Filtry danych")
    
    if st.sidebar.button("Odśwież dane z bazy"):
        st.cache_data.clear()
        st.rerun()

    # 1. Zanieczyszczenie
    lista_czujnikow = sorted(df_full['sensor_name'].unique())
    wybrany_czujnik = st.sidebar.selectbox("1. Wybierz zanieczyszczenie:", lista_czujnikow)
    jednostka = df_full[df_full['sensor_name'] == wybrany_czujnik]['unit'].iloc[0]

    # 2. Kraj
    lista_krajow = sorted(df_full['country_name'].unique())
    wybrane_kraje = st.sidebar.multiselect("2. Wybierz kraje:", lista_krajow, default=lista_krajow)
    df_filtered_by_country = df_full[df_full['country_name'].isin(wybrane_kraje)]

    # 3. Stacja
    lista_stacji = sorted(df_filtered_by_country['station_name'].unique())
    wybrane_stacje = st.sidebar.multiselect("3. Wybierz stacje pomiarowe:", lista_stacji, default=lista_stacji[:5] if lista_stacji else [])

    # 4. Zakres dat pomiarów
    min_date = df_full['measurement_time'].min().date()
    max_date = df_full['measurement_time'].max().date()
    wybrane_daty = st.sidebar.date_input("4. Zakres dat pomiarów:", [min_date, max_date], min_value=min_date, max_value=max_date)

    # 5. Zakres godzin (Dla Heatmapy)
    wybrane_godziny = st.sidebar.slider("5. Zakres godzin (Wykres 3):", 0, 23, (0, 23))

    # Dynamiczne wyciąganie min i max dla suwaków
    df_sensor_only = df_full[df_full['sensor_name'] == wybrany_czujnik]
    min_possible = float(df_sensor_only['value'].min())
    max_possible = float(df_sensor_only['value'].max())

    # 6. Min próg
    min_prog = st.sidebar.slider("6. Minimalny próg stężenia:", min_possible, max_possible, min_possible)

    # 7. Max próg
    max_prog = st.sidebar.slider("7. Maksymalny próg stężenia:", min_possible, max_possible, max_possible)

    # 8. Rozdzielczość danych
    rozdzielczosc = st.sidebar.radio("8. Rozdzielczość Wykresu 1:", ["Szczegółowa (godzinowa)", "Uśredniona (dzienna)"])

    # 9. Tryb rysowania wykresu
    tryb_rysowania = st.sidebar.selectbox("9. Wygląd trendu (Wykres 1):", ["Linie i punkty", "Tylko linie", "Tylko punkty (Scatter)"])

    # 10. Typ skali 
    typ_skali = st.sidebar.selectbox("10. Typ skali osi Y (Wykres 1):", ["Liniowa", "Logarytmiczna"])
    log_y = True if typ_skali == "Logarytmiczna" else False
    
    # 11. NOWOŚĆ: Grupowanie osi Y
    grupowanie_linii = st.sidebar.radio("11. Grupuj linie (Wykres 1) według:", ["Stacji", "Krajów (Średnia)"])


    # Filtrowanie głównych danych dla Wykresu 1
    df_w1 = df_full[
        (df_full['sensor_name'] == wybrany_czujnik) &
        (df_full['country_name'].isin(wybrane_kraje)) &
        (df_full['station_name'].isin(wybrane_stacje)) &
        (df_full['value'] >= min_prog) &
        (df_full['value'] <= max_prog)
    ].copy() 

    if isinstance(wybrane_daty, (list, tuple)) and len(wybrane_daty) == 2:
        df_w1 = df_w1[
            (df_w1['measurement_time'].dt.date >= wybrane_daty[0]) &
            (df_w1['measurement_time'].dt.date <= wybrane_daty[1])
        ]
        
    # LOGIKA GRUPOWANIA (KRAJE LUB STACJE + GODZINY LUB DNI)
    if not df_w1.empty:
        if rozdzielczosc == "Uśredniona (dzienna)":
            df_w1['time_col'] = df_w1['measurement_time'].dt.date
        else:
            # Zaokrąglamy czas do pełnych godzin, żeby ładnie narysować profil dobowy
            df_w1['time_col'] = df_w1['measurement_time'].dt.floor('h')

        # Decydujemy, co ma być osobną linią na wykresie
        group_col = 'station_name' if grupowanie_linii == "Stacji" else 'country_name'

        # Zwijamy dane i wyciągamy średnią
        df_w1 = df_w1.groupby(['time_col', group_col])['value'].mean().reset_index()
        df_w1.rename(columns={'time_col': 'measurement_time'}, inplace=True)

    # Filtrowanie danych dla Wykresu 2 (Heatmapa)
    df_hourly_filtered = df_hourly[
        (df_hourly['sensor_name'] == wybrany_czujnik) &
        (df_hourly['country_name'].isin(wybrane_kraje)) &
        (df_hourly['station_name'].isin(wybrane_stacje)) &
        (df_hourly['hour_of_day'] >= wybrane_godziny[0]) &
        (df_hourly['hour_of_day'] <= wybrane_godziny[1])
    ]

    # Filtrowanie danych dla Wykresu 3 (Słupki Krajów)
    df_country_filtered = df_country[
        (df_country['sensor_name'] == wybrany_czujnik) &
        (df_country['country_name'].isin(wybrane_kraje))
    ]

    # ==========================================
    # WIZUALIZACJE
    # ==========================================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Trend zanieczyszczeń w czasie")
        if not df_w1.empty:
            fig_line = px.line(
                df_w1,
                x="measurement_time",
                y="value",
                color=group_col,  # Dynamiczny kolor zależnie od wybranego grupowania
                title=f"Trend {wybrany_czujnik.upper()} ({rozdzielczosc}) - wg {grupowanie_linii}",
                labels={"measurement_time": "Czas pomiaru", "value": f"Stężenie ({jednostka})", group_col: grupowanie_linii},
                log_y=log_y,
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            
            mode_map = {"Linie i punkty": "lines+markers", "Tylko linie": "lines", "Tylko punkty (Scatter)": "markers"}
            fig_line.update_traces(mode=mode_map[tryb_rysowania])
            
            fig_line.update_layout(template="plotly_dark")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Brak danych spełniających kryteria filtrów dla wykresu liniowego.")

    with col2:
        st.subheader("2. Średnie stężenie według krajów")
        if not df_country_filtered.empty:
            fig_bar = px.bar(
                df_country_filtered,
                x="country_name",
                y="overall_avg_value",
                color="country_name",
                title=f"Ogólne stężenie {wybrany_czujnik.upper()} dla aktywnych stacji",
                labels={"country_name": "Kraj", "overall_avg_value": f"Średnia ({jednostka})"},
                text_auto='.2f'
            )
            fig_bar.update_layout(template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Brak danych krajowych dla wybranego parametru.")

    st.markdown("---")

    st.subheader("3. Dobowy profil (Heatmapa godzinowa)")
    if not df_hourly_filtered.empty:
        fig_heat = px.density_heatmap(
            df_hourly_filtered,
            x="hour_of_day",
            y="station_name",
            z="avg_hourly_value",
            histfunc="avg",
            color_continuous_scale="plasma",
            title=f"Rozkład stężeń {wybrany_czujnik.upper()} w zależności od godziny",
            labels={"hour_of_day": "Godzina", "station_name": "Stacja", "avg_hourly_value": jednostka}
        )
        fig_heat.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
        fig_heat.update_layout(template="plotly_dark")
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Brak danych godzinowych spełniających kryteria wybranych filtrów.")