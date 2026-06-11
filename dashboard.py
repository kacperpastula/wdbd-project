import streamlit as st
import pandas as pd
import plotly.express as px
import database  

st.set_page_config(page_title="Monitor Jakości Powietrza", layout="wide", page_icon="🌤️")

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

df_trends = load_dashboard_data("v_daily_trends")
df_hourly = load_dashboard_data("v_hourly_pollution_profile")
df_country = load_dashboard_data("v_country_sensor_avg")

if not df_trends.empty:
    df_trends['measurement_date'] = pd.to_datetime(df_trends['measurement_date']).dt.date

st.title("Dashboard Jakości Powietrza")
st.markdown("Wizualizacja danych pomiarowych z systemu bazodanowego OpenAQ.")

if df_trends.empty or df_hourly.empty or df_country.empty:
    st.warning("Brak kompletnych danych w bazie danych. Upewnij się, że tabele oraz widoki zostały utworzone (opcja [3] w menu programu głównego) oraz dane zostały pobrane (opcja [4]).")
else:
    st.sidebar.header("Filtry danych")

    lista_czujnikow = sorted(df_trends['sensor_name'].unique())
    wybrany_czujnik = st.sidebar.selectbox("1. Wybierz zanieczyszczenie:", lista_czujnikow)

    lista_krajow = sorted(df_trends['country_name'].unique())
    wybrane_kraje = st.sidebar.multiselect("2. Wybierz kraje:", lista_krajow, default=lista_krajow)

    df_filtered_by_country = df_trends[df_trends['country_name'].isin(wybrane_kraje)]

    lista_stacji = sorted(df_filtered_by_country['station_name'].unique())
    wybrane_stacje = st.sidebar.multiselect("3. Wybierz stacje pomiarowe:", lista_stacji, default=lista_stacji[:5] if lista_stacji else [])

    min_date = df_trends['measurement_date'].min()
    max_date = df_trends['measurement_date'].max()
    wybrane_daty = st.sidebar.date_input("4. Zakres dat pomiarów:", [min_date, max_date], min_value=min_date, max_value=max_date)

    wybrane_godziny = st.sidebar.slider("5. Zakres godzin (Wykres 3):", 0, 23, (0, 23))

    opcje_agregacji = {"Średnia wartość": "avg_value", "Maksymalna wartość": "max_value", "Minimalna wartość": "min_value"}
    wybrana_agregacja = st.sidebar.radio("6. Statystyka na wykresie trendu:", list(opcje_agregacji.keys()))
    kolumna_agregacji = opcje_agregacji[wybrana_agregacja]

    min_possible = float(df_trends['min_value'].min())
    max_possible = float(df_trends['max_value'].max())
    min_prog = st.sidebar.slider("7. Minimalny próg stężenia:", min_possible, max_possible, min_possible)

    max_prog = st.sidebar.slider("8. Maksymalny próg stężenia:", min_possible, max_possible, max_possible)

    jednostki_dla_czujnika = df_trends[df_trends['sensor_name'] == wybrany_czujnik]['unit'].unique()
    wybrana_jednostka = st.sidebar.selectbox("9. Jednostka miary:", jednostki_dla_czujnika)

    typ_skali = st.sidebar.selectbox("10. Typ skali osi pionowej (Wykres 1):", ["Liniowa", "Logarytmiczna"])
    log_y = True if typ_skali == "Logarytmiczna" else False


    df_trends_filtered = df_trends[
        (df_trends['sensor_name'] == wybrany_czujnik) &
        (df_trends['country_name'].isin(wybrane_kraje)) &
        (df_trends['station_name'].isin(wybrane_stacje)) &
        (df_trends['avg_value'] >= min_prog) &
        (df_trends['avg_value'] <= max_prog)
    ]
    if isinstance(wybrane_daty, (list, tuple)) and len(wybrane_daty) == 2:
        df_trends_filtered = df_trends_filtered[
            (df_trends_filtered['measurement_date'] >= wybrane_daty[0]) &
            (df_trends_filtered['measurement_date'] <= wybrane_daty[1])
        ]

    df_hourly_filtered = df_hourly[
        (df_hourly['sensor_name'] == wybrany_czujnik) &
        (df_hourly['country_name'].isin(wybrane_kraje)) &
        (df_hourly['station_name'].isin(wybrane_stacje)) &
        (df_hourly['hour_of_day'] >= wybrane_godziny[0]) &
        (df_hourly['hour_of_day'] <= wybrane_godziny[1])
    ]

    df_country_filtered = df_country[
        (df_country['sensor_name'] == wybrany_czujnik) &
        (df_country['country_name'].isin(wybrane_kraje))
    ]


    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Historyczny trend zmian zanieczyszczeń")
        if not df_trends_filtered.empty:
            fig_line = px.line(
            df_trends_filtered,
            x="measurement_date",
            y=kolumna_agregacji,
            color="station_name",
                title=f"{wybrana_agregacja} dla: {wybrany_czujnik}",
                labels={"measurement_date": "Data pomiaru", kolumna_agregacji: f"Stężenie ({wybrana_jednostka})", "station_name": "Stacja"},
                log_y=log_y,
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig_line.update_layout(template="plotly_dark")
    
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Brak danych spełniających kryteria filtrów dla wykresu trendu liniowego.")

    with col2:
        st.subheader("2. Średnie zanieczyszczenie według krajów")
        if not df_country_filtered.empty:
            fig_bar = px.bar(
                df_country_filtered,
                x="country_name",
                y="overall_avg_value",
                color="country_name",
                title=f"Ogólne uśrednione stężenie {wybrany_czujnik} dla aktywnych stacji",
                labels={"country_name": "Kraj", "overall_avg_value": f"Średnia ({wybrana_jednostka})"},
                text_auto='.2f'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Brak danych krajowych dla wybranego parametru.")

    st.markdown("---")

    st.subheader("3. Dobowy profil zanieczyszczeń (Heatmapa godzinowa)")
    if not df_hourly_filtered.empty:
        fig_heat = px.density_heatmap(
            df_hourly_filtered,
            x="hour_of_day",
            y="station_name",
            z="avg_hourly_value",
            histfunc="avg",
            color_continuous_scale="plasma",
            title=f"Rozkład stężeń {wybrany_czujnik} w zależności od godziny doby",
            labels={"hour_of_day": "Godzina", "station_name": "Stacja pomiarowa", "avg_hourly_value": wybrana_jednostka}
        )
        fig_heat.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
        fig_heat.update_layout(template="plotly_dark")
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Brak danych godzinowych spełniających kryteria wybranych filtrów.")