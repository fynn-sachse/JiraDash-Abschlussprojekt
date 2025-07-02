import truststore as ts
ts.inject_into_ssl()

from jira import JIRA
import os
from dotenv import load_dotenv

load_dotenv()

#DOTO
# 1. Methodenname kürzen

class JiraClient:

    
   
    def __init__(self, jira_user, jira_password, jira_project):
        self.server_url = os.getenv("JIRA_SERVER_URL")
        self.jira_auth = self.auth_jira_server(jira_user, jira_password)
        self.jira_user = jira_user
        self.jira_project = jira_project

       
    
    def auth_jira_server(self, username, password):
        try:
            return JIRA(server=self.server_url, basic_auth=(username, password))
        except Exception as e:
            print(f"Fehler bei der Authentifizierung: {e}")
            return None


    # Funktion zum laden aller Tickets des Jira Nutzers  
    # DOTO lädt nicht alle Tickets sondern nur die ersten 50 stand jetzt
    def load_all_tickets_user(self):
        #Lädt alle Tickets eines Jira-Users
        jql_query = (f'assignee = "{self.jira_user}"')

        try:
            return self.jira_auth.search_issues(jql_query)
        except Exception as e:
            print(f"Fehler beim Laden der Tickets: {e}")
            return None

    def load_tickets_between_dates_user(self, start_date, end_date):
        #Lädt alle Tickets des Jira-Users zwischen zwei Datumsgrenzen.
        jql_query =(f'assignee = "{self.jira_user}" '
                    f'AND created >= "{start_date}" '
                    f'AND created <= "{end_date}" '
                    f'ORDER BY created DESC')
        try:
            return self.jira_auth.search_issues(jql_query, expand="changelog")
        except Exception as e:
            print(f"Fehler beim Laden der Tickets: {e}")
            return None


    # Funktion zum laden aller Projekte des Jira Nutzers  
    def load_projects_of_user(self):
        #Lädt alle Projekte, auf die der Benutzer Zugriff hat.
        accessible_projects = []
        try:
            for project in self.jira_auth.projects():
                permissions = self.jira_auth.my_permissions(projectKey=project.key)
                if permissions["permissions"]["BROWSE_PROJECTS"]["havePermission"]:
                    accessible_projects.append(project)
            return accessible_projects
        
        except Exception as e:
            print(f"Fehler beim Laden der Projekte: {e}")
            return None
        

    def load_all_tickets_of_project(self, max_tickets):
        #Lädt alle Tickets eines Projekts mit einer maximalen Anzahl
        start_at = 0
        max_results = max_tickets
        all_tickets = []
        
        try:
            while len(all_tickets) < max_tickets:
                tickets = self.jira_auth.search_issues(
                    f'project={self.jira_project}', startAt=start_at, maxResults=max_results)

                if not tickets:
                    break

                all_tickets.extend(tickets)
                start_at += max_results

            print(all_tickets)
            return all_tickets
            
        except Exception as e:
            print(f"Fehler beim Laden der Projekttickets: {e}")
            return None
        

    def load_all_tickets_between_dates_project(self, start_date, end_date):
        jql_query = (
            f'project = {self.jira_project} AND created >= "{start_date}" '
            f'AND created <= "{end_date}" ORDER BY created ASC'
        )
        return self._load_tickets_with_query(jql_query)
    

    def load_all_tickets_between_dates_user(self, start_date, end_date):

        #Lädt alle Tickets des Jira-Users zwischen zwei Datumsgrenzen.
        jql_query = (
            f'assignee = "{self.jira_user}" AND created >= "{start_date}" '
            f'AND created <= "{end_date}" ORDER BY created ASC'
        )
        return self._load_tickets_with_query(jql_query)
    

    def load_all_tickets_created_and_resolved_between_dates(self, start_date, end_date):

        #Lädt alle Tickets des Jira-Projekts zwischen zwei Datumsgrenzen.
        jql_query = (
            f'project = "{self.jira_project}" AND '
            f'((created >= "{start_date}" AND created <= "{end_date}") '
            f'OR (resolutiondate >= "{start_date}" AND resolutiondate <= "{end_date}"))'
            f'ORDER BY created ASC'
        )
        return self._load_tickets_with_query(jql_query)
    

    def load_all_tickets_type_between_dates(self, start_date, end_date, issuetype):
        
        
        #Lädt alle Tickets des Jira_Projekts nach Ticket Typ zwischen zwei Datumsgrenzen 
        jql_query = (
            f'project = "{self.jira_project}" AND '
            f'((created >= "{start_date}" AND created <= "{end_date}") '
            f'AND issuetype = "{issuetype}")'
            f'ORDER BY created ASC'
        )
        return self._load_tickets_with_query(jql_query)
    
    def load_all_tickets_in_progress_between_dates(self, start_date, end_date):

        #Lädt alle erledigten Tickets des Jira_Projekts zwischen zwei Datumsgrenzen 
        jql_query = (f'project =  "{self.jira_project}" AND'
                     f'((created >= "{start_date}" AND created <= "{end_date}")'
                     f'AND resolution = EMPTY)'
                     f'ORDER BY created DESC')

        return self._load_tickets_with_query(jql_query)

    def _load_tickets_with_query(self, jql_query):
        #Hilfsmethode zum Laden von Tickets basierend auf einer JQL-Abfrage.
        start_at = 0
        max_results = 100
        all_tickets = []

        try:
            while True:
                tickets = self.jira_auth.search_issues(jql_query, startAt=start_at, maxResults=max_results, expand='changelog')

                if not tickets:
                    break

                all_tickets.extend(tickets)
                start_at += max_results
            
            print(len(all_tickets))
            return all_tickets
        except Exception as e:
            print(f"Fehler beim Laden der Tickets mit JQL '{jql_query}': {e}")
            return None
        

    def load_all_issuetypes_of_project(self):

        #Lädt alle alle Ticket Typen eines Projekts
        issue_types = []
        meta = self.jira_auth.createmeta(projectKeys=self.jira_project, expand="projects.issuetypes")
       
        if "projects" in meta:
            for project in meta["projects"]:
                if project["key"] == self.jira_project.key:
                    for issue_type in project["issuetypes"]:
                        issue_types.append(issue_type["name"]) # Hier evtl. nach orgininal name oä.
         
        return issue_types
    
    
