import requests
import re
import time
import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from datetime import datetime

API_URL = "https://clinicaltrials.gov/api/v2/studies/"

def fetch_trial_data(nct_number):
    """Fetches clinical trial metadata from ClinicalTrials.gov API."""
    url = f"{API_URL}{nct_number}?format=json"
    
    response = requests.get(url, headers={"Accept": "application/json"})

    if response.status_code != 200:
        return None

    data = response.json()

    try:
        protocol_section = data.get("protocolSection", {})
        id_module = protocol_section.get("identificationModule", {})
        status_module = protocol_section.get("statusModule", {})

        title = id_module.get("briefTitle", "Unknown Title")
        last_update_date = status_module.get("lastUpdatePostDateStruct", {}).get("date", "Unknown Date")

        return {
            "nct": nct_number,
            "title": f"{title}. ClinicalTrials.gov Identifier: {nct_number}",
            "last_update": last_update_date,
            "url": f"https://clinicaltrials.gov/ct2/show/{nct_number}"
        }

    except Exception:
        return None

def format_bibtex_entry(trial_data):
    """Generates a BibTeX entry for a clinical trial."""
    retrieved_date = datetime.today().strftime("%Y-%m-%d")

    try:
        update_datetime = datetime.strptime(trial_data['last_update'], "%Y-%m-%d")
        year = update_datetime.year
        month = update_datetime.strftime("%B")
        day = update_datetime.day
    except ValueError:
        year, month, day = "Unknown", "Unknown", "Unknown"

    return f"""@article{{{trial_data['nct']},
  title = {{{trial_data['title']}}},
  year = {{{year}}},
  month = {{{month}}},
  day = {{{day}}},
  note = {{Retrieved on {retrieved_date}}},
  url = {{{trial_data['url']}}}
}}
"""

def format_ris_entry(trial_data):
    """Generates an RIS entry for a clinical trial."""
    retrieved_date = datetime.today().strftime("%Y-%m-%d")

    try:
        update_datetime = datetime.strptime(trial_data['last_update'], "%Y-%m-%d")
        update_date_formatted = update_datetime.strftime("%Y/%m/%d")
    except ValueError:
        update_date_formatted = "Unknown"

    return f"""TY  - JOUR
TI  - {trial_data['title']}
DA  - {update_date_formatted}
UR  - {trial_data['url']}
PY  - {update_date_formatted.split('/')[0]}
RD  - {retrieved_date}
ER  -
"""

def extract_nct_numbers(filepath):
    """Extracts all NCT numbers from a given CSV or TXT file."""
    nct_numbers = set()

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                matches = re.findall(r"NCT\d{8}", line, re.IGNORECASE)
                nct_numbers.update(matches)
    except Exception as e:
        messagebox.showerror("Error", f"Could not read file: {e}")
        return []

    return list(nct_numbers)

def process_trials():
    """Handles file selection, data fetching, and exporting citations."""
    file_path = filedialog.askopenfilename(
        title="Select a CSV or TXT file containing NCT numbers",
        filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not file_path:
        return

    progress_text.insert(tk.END, f"📄 Processing file: {file_path}\n")
    root.update()

    nct_list = extract_nct_numbers(file_path)

    if not nct_list:
        progress_text.insert(tk.END, "❌ No valid NCT numbers found.\n")
        return

    output_bib = "citations.bib"
    output_ris = "citations.ris"
    bib_entries = []
    ris_entries = []

    progress_text.insert(tk.END, f"🔎 Found {len(nct_list)} NCT numbers. Fetching data...\n")
    root.update()

    for i, nct in enumerate(nct_list, 1):
        progress_text.insert(tk.END, f"📡 [{i}/{len(nct_list)}] Fetching {nct}...\n")
        root.update()
        
        trial = fetch_trial_data(nct)
        if trial:
            bib_entries.append(format_bibtex_entry(trial))
            ris_entries.append(format_ris_entry(trial))
            progress_text.insert(tk.END, "✅ Success\n")
        else:
            progress_text.insert(tk.END, "❌ Failed\n")
        time.sleep(0.5)

    if bib_entries:
        with open(output_bib, "w", encoding="utf-8") as f:
            f.writelines(bib_entries)

    if ris_entries:
        with open(output_ris, "w", encoding="utf-8") as f:
            f.writelines(ris_entries)

    progress_text.insert(tk.END, "\n🎉 Done! Citations saved.\n")
    messagebox.showinfo("Success", "Citations saved as 'citations.bib' and 'citations.ris'.")
    root.update()

# Create GUI Window
root = tk.Tk()
root.title("ClinicalTrials.gov Citation Generator")
root.geometry("500x400")

# Title Label
title_label = tk.Label(root, text="Generate BibTeX and RIS Citations from ClinicalTrials.gov NCT Identifiers", font=("Arial", 14, "bold"))
title_label.pack(pady=10)

# Select File Button
select_button = tk.Button(root, text="Select CSV or TXT File", command=process_trials, font=("Arial", 12))
select_button.pack(pady=5)

# Progress Display
progress_text = scrolledtext.ScrolledText(root, height=15, width=60)
progress_text.pack(pady=10)

# Run the application
root.mainloop()
