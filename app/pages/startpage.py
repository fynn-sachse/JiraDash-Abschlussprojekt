import streamlit as st
import pathlib
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px #Installiert
from core.calculations import calc_average_processing_time, calc_ticket_status_percantage, calc_monthly_date_ranges

# DOTO:
# übersichtlich machen wie viele Tickets schon geladen haben

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


#Laden aller Tickets und Projekte des Users
with st.container(key="startpage-spinner-container"):
    with st.spinner("Daten werden Abgerufen"):
        if st.session_state.jira_projects == None:
            st.session_state.jira_projects = st.session_state.jira_client.load_projects_of_user()


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
    with st.container(border=True, height=300, key="startpage-ticket-container"):
        #Überprüfen ob Tickts vorhanden sind und Anzeigen dieser
        if not st.session_state.jira_projects: 
            st.write(f"Keine Vorhandenen Projekte für diesen User: {jira_user}")
        else:
            for project in st.session_state.jira_projects:
               if st.button(f"Projekt: {project.key} - {project.name}", key=f"project{project.key}"):
                   st.session_state.jira_client.jira_project = project
                   st.switch_page("pages/myprojects.py")

    with st.container(key="statistics-container"):
        #Statistik Ticket-Bearbeitungszeit durschnittlich für die letzten 12 Monate (User)
        with st.container(key="startpage-graph1-container"):
            
            date_range_df = calc_monthly_date_ranges(12) 
            tickets = st.session_state.jira_client.load_tickets_between_dates_user(date_range_df.iloc[-1]["start_date"], 
                                                                                        date_range_df.iloc[0]["end_date"],)
            avg_monthly_proc_time_df = calc_average_processing_time(tickets, date_range_df)

            if not avg_monthly_proc_time_df.empty:
                bar_chart = px.bar(avg_monthly_proc_time_df, 
                                    x="Monat", 
                                    y="dursch. Bearbeitungszeit", 
                                    title="Durchschnittliche Bearbeitungszeit pro Monat in Tagen")
                    
                bar_chart.update_xaxes(tickformat="%b %Y")
                bar_chart.update_layout(xaxis_type='category')
                st.plotly_chart(bar_chart)
                


        #Statistik Spalte 2
        with st.container(key="startpage-graph2-container"): 
            
            #Tickets von der API Laden
            tickets = st.session_state.jira_client.load_all_tickets_user()

            #Funktion um die Prozentwerte auszurechnen
            status_percantage = calc_ticket_status_percantage(tickets)

            #Daten Objekt für das Kreisdiagramm erstellen
            piechart_data = {
                "Kategorien" : ["Geschlossen", "Neu", "In Bearbeitung"],
                "Werte" : [status_percantage["Fertig"], status_percantage["Offen"], status_percantage["In Bearbeitung"]]
            }

            #Piechart Konfigurieren
            piechart = px.pie(piechart_data, names="Kategorien", values="Werte") 
            st.plotly_chart(piechart)

           
