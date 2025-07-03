from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz
import pandas as pd

# ---DOTOS---
# Tickets direkt nach Erstellt oder erledigt von der API Abfragen -> Perfomanter (Erstellt VS Erledigt u. processing_time)
# Bei Alter und Bearbeitungszeit nicht immer über jeden Monat iterrieren und Sekunden aussrechnen -> Sekunden vorher ausrechnen

# ---Info--- 
# 1. Durschnittliche Bearbeitungszeiten werden zu dem Monat zugeordnet in dem die Tickets geschlossen worden sind
# 2. alc_ticket_processing_time berechnet die Bearbeitungszeit ab dem ein Ticket erstellt wurde nicht ab dem es auf In Bearbeitung gesgetzt wird
# Passt so Begründung


# Die Bearbeitungszeit eines Tickets Berechnen
def calc_ticket_age(issue):
    created_date = issue.fields.created  # Erstellungsdatum des Tickets
    created_date = pd.to_datetime(created_date)  # In Datetime umwandeln
    today = pd.to_datetime(datetime.now(pytz.utc))  # Aktuelles Datum

    ticket_age_seconds = (today - created_date).total_seconds()  # Differenz in Tagen berechnen
    return ticket_age_seconds
    
def calc_ticket_proc_time(issue):

    resolved = issue.fields.resolutiondate

    if hasattr(issue, 'changelog') and resolved:    
        first_change = None  

        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == "status":
                    first_change = history.created  # Erstes Änderungsdatum zurückgeben
                    break
            
            if first_change:
                break

        first_change_date = pd.to_datetime(first_change)
        resolved_date = pd.to_datetime(resolved)
        processing_time_seconds = (resolved_date - first_change_date).total_seconds()
        return processing_time_seconds  
    
   

def calc_daily_date_ranges(days_back):
    today = datetime.today()
    dates = [today - timedelta(days=i) for i in range(days_back)]
    df = pd.DataFrame(dates, columns=["Datum"])
    df["Datum"] = df["Datum"].dt.strftime("%Y-%m-%d")

    return df

def calc_monthly_date_ranges(months_back):

    today = datetime.today().replace(day=1)  # Ersten Tag des aktuellen Monats setzen
    monthly_date_ranges = []

    for i in range(months_back):
        start_date = today - relativedelta(months=i)  # Erster Tag des Monats
        end_date = start_date + relativedelta(months=1) - relativedelta(days=1)  # Letzter Tag des Monats

        monthly_date_ranges.append({"Monat": start_date.strftime("%Y-%m"), "start_date": start_date.date(), "end_date": end_date.date()})

    
    return pd.DataFrame(monthly_date_ranges)

def calc_avg_age(tickets, date_ranges_df):
    
    preprocessed = [
        {
            "created": pd.to_datetime(issue.fields.created).date(),
            "age_days": calc_ticket_age(issue) / 86400,  # Sekunden in Tage
        }
        for issue in tickets
        if calc_ticket_age(issue) is not None and issue.fields.resolutiondate == None
        
    ]

    for index, row in date_ranges_df.iterrows():
        filtered = [issue for issue in preprocessed 
                    if row["start_date"] <= issue["created"] <= row["end_date"]]
                   
        if filtered:
            avg_age = sum(issue["age_days"] for issue in filtered) / len(filtered)
            date_ranges_df.at[index, "durchsch. Alter"] = avg_age
        else:
            date_ranges_df.at[index, "durchsch. Alter"] = None
            
    date_ranges_df["Monat"] = pd.to_datetime(date_ranges_df["Monat"]).dt.strftime('%b %Y')
    return date_ranges_df


def calc_average_processing_time(tickets, date_ranges_df):

    preprocessed = [
        {
            "created": pd.to_datetime(issue.fields.created).date(),
            "proc_time_days": calc_ticket_proc_time(issue) / 86400,
        }

        for issue in tickets
        if calc_ticket_proc_time(issue) is not None and issue.fields.resolutiondate is not None 
    ]   

    for index, row in date_ranges_df.iterrows():
        filtered = [issue for issue in preprocessed 
                    if row["start_date"] <= issue["created"] <= row["end_date"]]
        
        if filtered:
            avg_proc_time = sum(issue["proc_time_days"] for issue in filtered) / len(filtered)
            date_ranges_df.at[index, "durchsch. Bearbeitungszeit"] = avg_proc_time
        else:
            date_ranges_df.at[index, "durchsch. Bearbeitungszeit"] = None
            
    date_ranges_df["Monat"] = pd.to_datetime(date_ranges_df["Monat"]).dt.strftime('%b %Y')
    return date_ranges_df


"""
def calc_average_processing_time(tickets, date_ranges_df):

    date_ranges_df["durchsch. Bearbeitungszeit"] = 0

    for index, row in date_ranges_df.iterrows():

        total_time = timedelta()
        processed_issues = 0

        for issue in tickets:
            processing_time_seconds = calc_ticket_proc_time(issue)
            

            # Abschlussdatum aus Jira Ticket holen
            if issue.fields.resolutiondate: 
                completion_date = pd.to_datetime(issue.fields.resolutiondate, utc=True)

                 # Nur Tickets zählen, die in dem Monat abgeschlossen wurden
                if row["start_date"] <= completion_date.date() <= row["end_date"] and processing_time_seconds is not None:
                    total_time += timedelta(seconds=processing_time_seconds)
                    processed_issues += 1
        
        if processed_issues > 0: 
            avg_time = (total_time.total_seconds() / processed_issues / 86400) # Umrechnung Sekunden zu Tagen      
            date_ranges_df.at[index, "durchsch. Bearbeitungszeit"] = avg_time
        else:
            date_ranges_df.at[index, "durchsch. Bearbeitungszeit"] = None
    
    date_ranges_df["Monat"] = pd.to_datetime(date_ranges_df["Monat"]).dt.strftime('%b %Y')

    

    return(date_ranges_df)
"""   
       

    
# Prozent Satz der Tickets eines User nach Status Berechnen 
def calc_ticket_status_percantage(tickets):
    status_count = {"done": 0, "to do": 0, "in progress": 0}
    total_issues = len(tickets)

    # Über alle issues in den Übergeben Tickets iterieren
    for issue in tickets:
        status = issue.fields.status.statusCategory.name.lower() if hasattr (issue.fields.status, "statusCategory") else "unknown"

        # Counter jeweils nach Stadien der Tickets erhöhen
        if status in ["done", "fertig"]:
            status_count["done"] += 1
        elif status in ["to do", "aufgaben"]:
            status_count["to do"] += 1
        elif status in ["in progress", "in arbeit"]:
            status_count["in progress"] += 1


    return {
        "Fertig": (status_count["done"] / total_issues) * 100 if total_issues > 0 else 0,
        "Offen": (status_count["to do"] / total_issues) * 100 if total_issues > 0 else 0,
        "In Bearbeitung": (status_count["in progress"] / total_issues) * 100 if total_issues > 0 else 0
    }

def calc_ticket_status_percantage_dynamic(tickets, states):
    status_count = {status: 0 for status in states}
    total_issues = len(tickets)
    for issue in tickets:
        status = issue.fields.status.name  
        if status in status_count:
            status_count[status] += 1

    percentage_results = {
        status: (count / total_issues) * 100 if total_issues > 0 else 0
        for status, count in status_count.items()
    }

    df_percentage_results = pd.DataFrame({
        "states" : percentage_results.keys(),
        "percentages" : percentage_results.values()

    })
    return df_percentage_results

def calc_tickets_done_vs_created(tickets, date_range_df, cumulation):
    date_range_df["Datum"] = pd.to_datetime(date_range_df["Datum"])
    created_dates = []
    resolved_dates = []

    #Tickets nach Erstellungs- und Erledigungsdatum sammeln
    for issue in tickets:
        created_date = pd.to_datetime(issue.fields.created).date()
        created_dates.append(created_date)

        if hasattr(issue.fields, "resolutiondate") and issue.fields.resolutiondate:
            resolved_date = pd.to_datetime(issue.fields.resolutiondate).date()
            resolved_dates.append(resolved_date)

    # Erstellte & erledigte Tickets zählen
    created_counts = pd.Series(created_dates).value_counts().rename("Erstellt")
    resolved_counts = pd.Series(resolved_dates).value_counts().rename("Erledigt")
    # Stelle sicher, dass Index auch datetime64[ns] ist
    created_counts.index = pd.to_datetime(created_counts.index)
    resolved_counts.index = pd.to_datetime(resolved_counts.index)
    # Zählungen in den DataFrame integrieren
    date_range_df = date_range_df.merge(created_counts, left_on="Datum", right_index=True, how="left")
    date_range_df = date_range_df.merge(resolved_counts, left_on="Datum", right_index=True, how="left")
    # Fehlende Werte (NaN) mit 0 ersetzen
    date_range_df.fillna(0, inplace=True)

    if cumulation:
        date_range_df = date_range_df = date_range_df.iloc[::-1].reset_index(drop=True)
        date_range_df["Erstellt"] = date_range_df["Erstellt"].cumsum()
        date_range_df["Erledigt"] = date_range_df["Erledigt"].cumsum()
        return date_range_df 
    
    else:
        return date_range_df

    


    