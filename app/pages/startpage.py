import streamlit as st
import pathlib
import pandas as pd
from datetime import datetime
import plotly.express as px #Installiert
from core.calculations import calc_average_processing_time, calc_ticket_status_percantage, calc_monthly_date_ranges


st.set_page_config(initial_sidebar_state="expanded")

jira_projects = []

add_pagelin = (
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

# Laden des jira_user aus dem jira_client Objekt
jira_user = st.session_state.jira_client.jira_user


#Laden aller Projekte des users
with st.container(key="startpage-spinner-container"):
    with st.spinner("Daten werden Abgerufen"):
        if st.session_state.jira_projects is None:
            st.session_state.jira_projects = st.session_state.jira_client.load_projects_of_user()

def show_user_avg_processing_time_chart():
    # Berechnen des Zeitraum Dataframes sowie Abfrage der Tickets über den Zeitraum
    date_range_df = calc_monthly_date_ranges(12) 
    tickets = st.session_state.jira_client.load_tickets_between_dates_user(
        date_range_df.iloc[-1]["start_date"],
        date_range_df.iloc[0]["end_date"]
    )
    if not tickets:
        st.error("Keine Tickets für den User gefunden")
    else:
        # Aufruf der Berechnungsmethode
        avg_processing_times_by_month_df = calc_average_processing_time(tickets, date_range_df)
        if not avg_processing_times_by_month_df.empty:
            #Erstellen des Diagramms
            avg_proc_time_chart = px.bar(
                avg_processing_times_by_month_df,
                x="Monat",
                y="durchsch. Bearbeitungszeit",
                title="⏱️ Durchschnittliche Bearbeitungszeit pro Monat (in Tagen)"
            )
            avg_proc_time_chart.update_xaxes(tickformat="%b %Y")
            avg_proc_time_chart.update_layout(xaxis_type='category')
            st.plotly_chart(avg_proc_time_chart)


# Kreisdiagramm: Prozentsätze nach Ticketstatus
def show_user_ticket_status_chart():
    #Zeigt die aktuelle Ticketstatusverteilung des Users in einem Pie Chart

    tickets = st.session_state.jira_client.load_all_tickets_user()

    if not tickets:
        st.error("Keine Tickets für den User gefunden")
    else:
        ticket_status_df = calc_ticket_status_percantage(tickets)
        status_chart_data = {
            "Kategorien": ["Geschlossen", "Neu", "In Bearbeitung"],
            "Werte": [
                ticket_status_df["Fertig"],
                ticket_status_df["Offen"],
                ticket_status_df["In Bearbeitung"]
            ]
        }

        status_pie_chart = px.pie(status_chart_data, names="Kategorien", values="Werte",
                                title="📊 Verteilung der Ticket-Status")
        st.plotly_chart(status_pie_chart)



# Haupt-Cotainer für alle Seiten Inhalte
with st.container(key="main-container"):

    #Container für Header
    with st.container(key="startpage-header-container"):
        st.title("Startseite")
        st.subheader(f"Willkommen auf der Startseite {jira_user}! 🎉")

    # Abmelde Button 
    if st.button("Abmelden", key="startpage-logout-button"):
        st.switch_page("./app.py")

    st.write("Deine Projekte")

    #Container zum Anzeigen der Tickets
    with st.container(border=True, height=200, key="startpage-ticket-container"):

        #Überprüfen ob Tickts vorhanden sind und Anzeigen dieser
        if not st.session_state.jira_projects: 
            st.write(f"Keine Vorhandenen Projekte für diesen User: {jira_user}")
        else:
            for project in st.session_state.jira_projects:
               #Alle vorhandenen Projekte als Button abbilden
               if st.button(f"Projekt: {project.key} - {project.name}", key=f"project{project.key}"):
                   st.session_state.jira_client.jira_project = project
                   st.switch_page("pages/myprojects.py")

    #Container zum Anzeigen der Statistiken
    with st.container(key="statistics-container"):

        #Statistik Ticket-Bearbeitungszeit durschnittlich für die letzten 12 Monate (User)
        with st.container(key="startpage-graph1-container"):
            show_user_avg_processing_time_chart()
            
        ##Statistik Ticket-Bearbeitungszeit durschnittlich für die letzten 12 Monate (User)
        with st.container(key="startpage-graph2-container"): 
            show_user_ticket_status_chart()

           

