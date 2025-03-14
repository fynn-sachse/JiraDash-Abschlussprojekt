import streamlit as st
from services.JiraClient import JiraClient

# Initialisiere Session-State-Variablen, falls sie nicht existieren
for key, default_value in {
    "jira_projects": None,
    "jira_tickets": None,
    "show_statistic": False,
    "percentage_result_df": None,
    "line_chart_df" : None,
    "avg_monthly_proc_time_df" : None,
    "selected_jira_project" : None,
    "jira_client" : None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default_value




#Form zum Eintragen der Anmelde Daten
with st.form("auth-form"):
    st.write("Bitte geb deinen Jira Nutzernamen und dein Passwort ein")
    username = st.text_input("Benutzername", placeholder="Dein Benutzername")
    password = st.text_input("Passwort", type="password", placeholder="Dein Passwort")
    submit_button = st.form_submit_button("Anmelden")

#Nach klicken des Anmelde Buttons Prüfen ob alle Daten Angegeben wurden
if submit_button:
    if not username or not password:
        st.error("Bitte fülle alle Felder aus")
    else:
        #User Authentifizieren
        jira_client = JiraClient(username, password, None)
        
        if jira_client.jira_auth == None:
            st.error("Die Kombination aus Benutzername und Passwort ist falsch")
        else:
            st.session_state.jira_client = jira_client
            st.switch_page("pages/startpage.py")
                

#DOTO 
# Logout option in die Navigation
# Beim Aufrufen der Startseite Checken ob der user Authentifiziert ist
# Session Variablen in Lokale Laden (Startseite)


