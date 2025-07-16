import streamlit as st
import pathlib
import pandas as pd 
import plotly.express as px #Installiert

from core.calculations import calc_ticket_status_percantage_dynamic, calc_tickets_done_vs_created, calc_average_processing_time,calc_monthly_date_ranges, calc_daily_date_ranges, calc_avg_age

# DONE
# 1. Beim kreisdiagramm müssen die tickets noch nach Stadie von der API abgefragt werden -> nicht möglich keine 
#    dynamische Abfrage
# 2. Bessere Variante zum Abfragen der Stadie finden für die Selectbox -> Bisher noch keine Gefunden
# 3. Im Kreisdiagramm-Dialog Lädt die seite für jeden neu ausgählte Stadie neu 
# 5. Statistik Daten in einer sessionstate variable Speichern


# 7  bei mehreren Tickettypen evtl nur mehrere als auswahl zulassen
# 8. Bearbeitungszeiten nach mehreren Typen berücksichtigt neues Fehler Ticket nicht -> Ticket wird gar nicht erst geladen


st.set_page_config(initial_sidebar_state="expanded")

add_pagelink = (
    st.sidebar.page_link("pages/startpage.py", label = "Startseite"),
    st.sidebar.page_link("pages/myprojects.py", label = "Meine Projekte")
)

#Costum CSS auf die seite Anwenden
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

#Costum CSS laden
css_path = pathlib.Path("assets/styles.css")
load_css(css_path)


# ---Methoden zum erstellen der einzigen Statistiken---
# Decorator zur Datenprüfung
def if_stat_data_available(func):
    def wrapper():
        if st.session_state.statistic_result_df is not None:
            func()
        else:
            st.error("Keine Daten für das Diagramm verfügbar.")
    return wrapper

# Kreisdiagramm: Prozentsätze nach Ticketstatus
@if_stat_data_available
def show_ticket_status_chart():
    df = st.session_state.statistic_result_df
    fig = px.pie(
        df, names="states", values="percentages",
        title="Ticket-Status Verteilung"
    )
    st.plotly_chart(fig)

# Linien-Diagramm: Tickets erstellt vs. erledigt
@if_stat_data_available
def show_ticket_trend_chart():
    df = st.session_state.statistic_result_df
    fig = px.line(
        df,
        x="Datum",
        y=["Erstellt", "Erledigt"],
        markers=True,
        title="📈 Tickets: Erstellt vs. Erledigt",
        color_discrete_map={"Erstellt": "indianred", "Erledigt": "mediumseagreen"}
    )
    st.plotly_chart(fig)


#Balkendiagramm: durchschnittliche Bearbeitungszeit
#Decorator der prüft ob die passenden Daten vorhanden sind
@if_stat_data_available
def show_avg_processing_time_chart():
    #Laden der Statistikdaten in eine lokale variable 
    df = st.session_state.statistic_result_df
    #Erstellung der konkreten Statistik mit passenden Daten
    fig = px.bar(
        df,
        x="Monat",
        y="durchsch. Bearbeitungszeit",
        title="⏱ Durchschnittliche Bearbeitungszeit pro Monat (in Tagen)"
    )
    #Anzeigen der Statisitk
    fig.update_xaxes(tickformat="%b %Y")
    fig.update_layout(xaxis_type='category')
    st.plotly_chart(fig)

# Balkendiagramm: durchschnittliche Bearbeitungszeit nach mehreren Tickettypen
@if_stat_data_available
def show_avg_processing_time_by_type_chart():
    df = pd.concat(st.session_state.statistic_result_df, ignore_index=True)
    df = df.groupby(["Monat", "Kategorie"], as_index=False)["durchsch. Bearbeitungszeit"].sum()
    fig = px.bar(
        df,
        x="Monat",
        y="durchsch. Bearbeitungszeit",
        color="Kategorie",
        barmode="group",
        title="🔍 Bearbeitungszeit nach Tickettyp pro Monat"
    )
    st.plotly_chart(fig)
    st.write(df)

# Balkendiagramm: durchschnittliches Alter von Tickets
@if_stat_data_available
def show_avg_ticket_age_chart():
    df = st.session_state.statistic_result_df
    fig = px.bar(
        df,
        x="Monat",
        y="durchsch. Alter",
        title="📊 Durchschnittliches Ticket-Alter aller noch offenen Tickets pro Monat (in Tagen)"
    )
    fig.update_xaxes(tickformat="%b %Y")
    fig.update_layout(xaxis_type='category')
    st.plotly_chart(fig)
    df

# Funktion zum validieren des user Inputs im Dialog
def validate_positive_int(input_value, field_name="Wert"):
    try:
        value = int(input_value)
        if value <= 0:
            st.error(f"{field_name} muss größer als 0 sein.")
            return None
        return value
    except ValueError:
        st.error(f"{field_name} muss eine gültige Zahl sein.")
        return None


# ---Methoden für die individuellen Dialog-Fenster mit Parameter Übergabe für die einzelnen Statistiken---

# Handler: Kreisdiagramm für Ticket-Status
def handle_status_chart():
    option_months_back = st.text_input("Anzahl der Monate zurück", value = 12)
    months = validate_positive_int(option_months_back, "Monate")

    if months:
        date_range_df = calc_monthly_date_ranges(months)
        tickets = st.session_state.jira_client.load_all_tickets_between_dates_project(
            date_range_df.iloc[-1]["start_date"], 
            date_range_df.iloc[0]["end_date"]
        )

        if not tickets:
            st.error("Keine Tickets gefunden")
            return

        unique_states = sorted({issue.fields.status.name for issue in tickets})
        options_states = st.multiselect("Welche Status anzeigen?", unique_states)

        if st.button("Bericht erstellen"):
            if len(options_states) > 1:
                st.session_state.statistic_result_df = calc_ticket_status_percantage_dynamic(tickets, options_states)
                st.session_state.show_statistic = True
                st.rerun()
            else:
                st.error("Bitte mehrere Status auswählen")


# Handler: Vergleich von Erstellt vs. Erledigt
def handle_ticket_trend_chart():
    days_input = st.text_input("Anzahl der Tage zurück", value=30)
    is_accumulate = st.selectbox("Akkumuliert?", ("Ja", "Nein")) == "Ja"
    days = validate_positive_int(days_input, "Tage")

    if st.button("Bericht erstellen") and days:
        date_range_df = calc_daily_date_ranges(days)
        tickets = st.session_state.jira_client.load_all_tickets_created_and_resolved_between_dates(
            date_range_df.iloc[-1]["Datum"], 
            date_range_df.iloc[0]["Datum"]
        )

        if not tickets:
            st.error("Keine Tickets gefunden")
        else:
            st.session_state.statistic_result_df = calc_tickets_done_vs_created(tickets, date_range_df, is_accumulate)
            st.session_state.show_statistic = True
            st.rerun()


# Handler: Durchschnittliche Bearbeitungszeit 
def handle_avg_processing_time_chart():
    months_input = st.text_input("Anzahl der Monate zurück", value=12)
    filter_by_type = st.selectbox("Nach Tickettypen filtern?", ("Nein", "Ja")) == "Ja"
    months = validate_positive_int(months_input, "Monate")
    selected_type = None

    if filter_by_type:
        issue_types = st.session_state.jira_client.load_all_issuetypes_of_project()
        selected_type = st.selectbox("Tickettyp auswählen", issue_types)

    if st.button("Bericht erstellen") and months:
        date_range_df = calc_monthly_date_ranges(months)

        if selected_type:
            tickets = st.session_state.jira_client.load_all_tickets_type_between_dates(
                date_range_df.iloc[-1]["start_date"],
                date_range_df.iloc[0]["end_date"],
                selected_type
            )
        else:
            tickets = st.session_state.jira_client.load_all_tickets_between_dates_project(
                date_range_df.iloc[-1]["start_date"],
                date_range_df.iloc[0]["end_date"]
            )

        if not tickets:
            st.error("Keine Tickets gefunden")
        else:
            st.session_state.statistic_result_df = calc_average_processing_time(tickets, date_range_df)
            st.session_state.show_statistic = True
            st.rerun()



# Handler: Durchschnittliche Bearbeitungszeit pro Typ 
def handle_avg_processing_time_by_type_chart():
    months_input = st.text_input("Anzahl der Monate zurück", value=12)
    issue_types = st.session_state.jira_client.load_all_issuetypes_of_project()
    selected_types = st.multiselect("Tickettypen auswählen", issue_types)
    months = validate_positive_int(months_input, "Monate")
    results = []

    if st.button("Bericht erstellen") and months and selected_types:
        date_range_df = calc_monthly_date_ranges(months)

        for issue_type in selected_types:
            tickets = st.session_state.jira_client.load_all_tickets_type_between_dates(
                date_range_df.iloc[-1]["start_date"],
                date_range_df.iloc[0]["end_date"],
                issue_type
            )
            avg_df = calc_average_processing_time(tickets, date_range_df)
            avg_df["Kategorie"] = issue_type
            results.append(avg_df.copy())

        st.session_state.statistic_result_df = results
        st.session_state.show_statistic = True
        st.rerun()



# Handler: Durchschnittliches Alter offener Tickets 
def handle_avg_ticket_age_chart():
    months_input = st.text_input("Anzahl der Monate zurück", value=12)
    months = validate_positive_int(months_input, "Monate")

    if st.button("Bericht erstellen") and months:
        # Laden der Zeiträume nach Nutzereingabe (Monate)
        date_range_df = calc_monthly_date_ranges(months)
        date_range_df
        # Abfrage der Tickets über alle im DataFrame enthaltene Monate
        tickets = st.session_state.jira_client.load_all_tickets_in_progress_between_dates(
            date_range_df.iloc[-1]["start_date"], 
            date_range_df.iloc[0]["end_date"]
        )
        # Aufrufen der Kalkulationsmethode mit Tickets und Zeiräumen als Parameter
        result_df = calc_avg_age(tickets, date_range_df)
        # Ergebniss in SessionState speichert
        st.session_state.statistic_result_df = result_df
        # Statstic-Flag auf True setzten
        st.session_state.show_statistic = True
        #Seite neu Laden
        st.rerun()

 
# Dialog-Funktion für Statistikeinstellungen
@st.dialog(f"Statistik Einstellungen für {st.session_state.jira_client.jira_project}")
def show_dialog():   
    match option_statistic:
        case "Kreisdiagramm nach Ticket Status": 
            handle_status_chart()
        case "Tickets Erstellt Vs Erledigt":
            handle_ticket_trend_chart()
        case "Durschnittliche Bearbeitungszeit":
            handle_avg_processing_time_chart()
        case "Durchschnittliche Bearbeitungszeit nach mehreren Tickettypen":
            handle_avg_processing_time_by_type_chart()
        case "Durchschnittliches Ticketalter":
            handle_avg_ticket_age_chart()
            
        
# Anwendungscontainer
with st.container(key="main-container"):

    st.title(f"Projekt: {st.session_state.jira_client.jira_project}")

    option_project = st.selectbox(
        "Wähle ein Projekt",
        st.session_state.jira_projects,
        index = st.session_state.jira_projects.index(st.session_state.jira_client.jira_project) if st.session_state.jira_client.jira_project in st.session_state.jira_projects else 0
    )

    if st.session_state.jira_client.jira_project != option_project:
        st.session_state.jira_client.jira_project = option_project
        st.rerun()


    option_statistic = st.selectbox(
        "Wähle eine Statistik",
        ("Kreisdiagramm nach Ticket Status", 
         "Tickets Erstellt Vs Erledigt",
         "Durschnittliche Bearbeitungszeit",
         "Durchschnittliche Bearbeitungszeit nach mehreren Tickettypen",
         "Durchschnittliches Ticketalter"))

    
    if st.button("Okay"):

        if option_project and option_statistic:
    
            show_dialog()
           
        else:
            st.error("Bitte ein Projekt und eine Statistik auswählen")


# Einzelne Statistiken Methoden nach auswahl aufrufen
if st.session_state.show_statistic: 
    match option_statistic:
        case "Kreisdiagramm nach Ticket Status": 
            show_ticket_status_chart()
            st.session_state.show_statistic = False
        case "Tickets Erstellt Vs Erledigt":
            show_ticket_trend_chart()
            st.session_state.show_statistic = False
        case "Durschnittliche Bearbeitungszeit":
            show_avg_processing_time_chart()
            st.session_state.show_statistic = False
        case "Durchschnittliche Bearbeitungszeit nach mehreren Tickettypen":
            show_avg_processing_time_by_type_chart()
            st.session_state.show_statistic = False
        case "Durchschnittliches Ticketalter":
            show_avg_ticket_age_chart()
            st.session_state.show_statistic = False
