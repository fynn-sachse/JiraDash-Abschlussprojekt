import streamlit as st
import sys
import pathlib
import plotly.express as px #Installiert

from core.calculations import calc_ticket_status_percantage_dynamic, calc_tickets_done_vs_created, calc_average_processing_time,calc_monthly_date_ranges, calc_daily_date_ranges

# DOTOS
# 1. Beim kreisdiagramm müssen die tickets noch nach Stadie von der API abgefragt werden
# 2. Bessere Variante zum Abfragen der Stadie finden für die Selectbox
# 3. Im Kreisdiagramm-Dialog Lädt die seite für jeden neu ausgählte Stadie neu -> fixen
# 4. Redundante Varaiblen Name abändern
# 5. Statistik Daten in einer sessionstate variable Speichern
# 6. Spezifischere Namen für die Statistik Methoden
# 7. evtl Laden Symbole einbauen
# 8. #Wahrscheinlich wird bei Alter der Tickets nach Typ 2 mal das selbe Dataframe erstellt


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


# Pie-Chart-Funktion
def load_pie_chart():
    if st.session_state.percentage_result_df is not None:
        pie_chart = px.pie(
            st.session_state.percentage_result_df, 
            names="states", values="percentages", 
            title="Ticket-Status Verteilung"
        )
        st.plotly_chart(pie_chart)
    else:
        st.error("Keine Daten für das Diagramm verfügbar.")


# Line-Chart-Funktion
def load_line_chart():
    if st.session_state.line_chart_df is not None:
        line_chart = px.line(st.session_state.line_chart_df, x = "Datum", y=["Erstellt", "Erledigt"]
                             ,markers=True, title="Tickets: Erstellt vs. Erledigt", 
                             color_discrete_map={"Erstellt": "red", "Erledigt": "green"})
        st.plotly_chart(line_chart)
        st.write(st.session_state.line_chart_df)
    else:
        st.error("keine Daten für das Diagramm verfügbar")


# Bar-Chart-Funktion
def load_bar_chart():
    if st.session_state.avg_monthly_proc_time_df is not None:
         bar_chart = px.bar(st.session_state.avg_monthly_proc_time_df, 
                            x="Monat", 
                            y="dursch. Bearbeitungszeit", 
                            title="Durchschnittliche Bearbeitungszeit pro Monat in Tagen")
         bar_chart.update_xaxes(tickformat="%b %Y")
         bar_chart.update_layout(xaxis_type='category')
         st.plotly_chart(bar_chart)
         st.write(st.session_state.avg_monthly_proc_time_df)
    else:    
        st.error("Fehler beim Kalkulieren der Daten")

#def load_ticket_age_stat ():
    #if st.session_state.avg_monthly_proc_time_df is not None:



# Dialog-Funktion für Statistikeinstellungen
@st.dialog(f"Statistik Einstellungen für {st.session_state.jira_client.jira_project}")
def show_dialog():
    
    match option_statistic:

        # --- Ticket Status Dialog und Daten laden ---
        case "Kreisdiagramm nach Ticket Status":

            #Status-Optionen aus Tickets extrahieren
            tickets = st.session_state.jira_client.load_all_tickets_of_project(100)
        
            unique_states = sorted({issue.fields.status.name for issue in tickets})

            options_states = st.multiselect("Welche Stadien sollen angezeigt werden?", unique_states)

            if st.button("Bericht erstellen"):
                if options_states:
                    st.session_state.percentage_result_df = calc_ticket_status_percantage_dynamic(tickets, options_states)
                    st.session_state.show_statistic = True
                    st.rerun()
                else:
                    st.error("Bitte Stadie auswählen")

        # --- Ticket Erstell Vs Erledigt Dialog und Daten Laden --- 
        case "Tickets Erstellt Vs Erledigt":
            
            option_days_back = st.text_input("Anzahl der Tage Zuvor Angeben", value=30)
            option_acumulate = st.selectbox("Akumulative Summen?", ("Ja", "Nein"))

            is_acumulate = {"Ja": True, "Nein": False}[option_acumulate]

            try:
                option_days_back = int(option_days_back)
            except ValueError:
                st.error("Bitte Korrekte Zahl eingeben")
                option_days_back = None  

            if st.button("Bericht erstellen"):
                if option_days_back and option_acumulate:

                    date_range_df = calc_daily_date_ranges(option_days_back)
                    tickets = st.session_state.jira_client.load_all_tickets_created_and_resolved_between_dates(date_range_df.iloc[-1]["Datum"], date_range_df.iloc[0]["Datum"])
                    
                    if not tickets:
                        st.error("Keine Tickets für die ausgwählten Filter oder das Porjekt vorhanden")
                    else:
                        st.session_state.line_chart_df = calc_tickets_done_vs_created(tickets, date_range_df, is_acumulate)
                        st.session_state.show_statistic = True
                        st.rerun()
                else:
                    st.error("Beide alle optionen wählen")

        # --- Durchschnittliche Bearbeitungszeiten Dialog und Daten Laden ---
        case "Durschnittliche Bearbeitungszeit":
            
            option_month_back = st.text_input("Anzahl der Monate Zuvor Angeben", value=12)
            option_filter_issue_type = st.selectbox("Nach Ticket Typen Filtern?", ("Nein", "Ja"))

            try:
                option_month_back = int(option_month_back)
            except ValueError:
                st.error("Bitte Korrekte Zahl eingeben")
                option_month_back = None

            if option_filter_issue_type == "Ja":

                issue_types = st.session_state.jira_client.load_all_issuetypes_of_project()
                option_issue_types = st.selectbox("Tickettyp auswählen", issue_types)

            else: 
                option_issue_types = None


            if st.button("Bericht erstellen"):
                if option_month_back:

                    date_range_df = calc_monthly_date_ranges(option_month_back)

                    if option_issue_types:
                        tickets = st.session_state.jira_client.load_all_tickets_type_between_dates(date_range_df.iloc[-1]["start_date"], 
                                                                                                   date_range_df.iloc[0]["end_date"],
                                                                                                   option_issue_types)
                    else:   
                        tickets = st.session_state.jira_client.load_all_tickets_between_dates_project(date_range_df.iloc[-1]["start_date"], 
                                                                                                      date_range_df.iloc[0]["end_date"])
                    if not tickets:
                        st.error("Keine Tickets für die ausgwählten Filter oder das Porjekt vorhanden")
                    else:
                        st.session_state.avg_monthly_proc_time_df = calc_average_processing_time(tickets, date_range_df)
                        st.session_state.show_statistic = True
                        st.rerun()
                        
                else:
                    st.error("Bitte eine Zahl angeben")

         # --- Durchschnittliche Ticket Alter Dialog und Daten Laden ---
        case "Durschnitts Alter eines Tickettyps":

            issue_types = st.session_state.jira_client.load_all_issuetypes_of_project()

            results_list = []
            option_month_back = st.text_input("Anzahl der Monate Zuvor Angeben", value=12)
            option_issue_types = st.multiselect("Tickettyp auswählen", issue_types)

            try:
                option_month_back = int(option_month_back)
            except ValueError:
                st.error("Bitte Korrekte Zahl eingeben")
                option_month_back = None

            if st.button("Bericht erstellen"):
                if option_month_back and option_issue_types:

                    date_range_df = calc_monthly_date_ranges(option_month_back)
                    
                    
                    for issue_type in option_issue_types:
                        tickets = st.session_state.jira_client.load_all_tickets_type_between_dates(date_range_df.iloc[-1]["start_date"], 
                                                                                                    date_range_df.iloc[0]["end_date"],
                                                                                                    issue_type)
                        
                        avg_monthly_proc_time_df = calc_average_processing_time(tickets, date_range_df)
                        print(avg_monthly_proc_time_df)
                        results_list.append(avg_monthly_proc_time_df)
                    
                    st.write(results_list)
                        
                    for i in range(len(results_list)):
                        results_list[i].rename(columns={"dursch. Bearbeitungszeit": f"dursch. Bearbeitungszeit {option_issue_types[i]}"}, inplace=True)
                        
                    
                    st.session_state.avg_monthly_proc_time_df = results_list
                    st.session_state.show_statistic = True
                    #st.rerun()
                    
                else: st.error("Bitte Bitte einen Tickettyp und eine Monatsanzahl angeben")


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
         "Durschnitts Alter eines Tickettyps")
    )

    
    if st.button("Okay"):

        if option_project and option_statistic:
    
            show_dialog()
           
        else:
            st.error("Bitte ein Projekt und eine Statistik auswählen")


if st.session_state.show_statistic: 
    match option_statistic:
        case "Kreisdiagramm nach Ticket Status": 
            load_pie_chart()
            st.session_state.show_statistic = False
        case "Tickets Erstellt Vs Erledigt":
            load_line_chart()
            st.session_state.show_statistic = False
        case "Durschnittliche Bearbeitungszeit":
            load_bar_chart()
            st.session_state.show_statistic = False
        case "Durschnitts Alter eines Tickettyps":
            st.write(st.session_state.avg_monthly_proc_time_df)

