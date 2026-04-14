import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
import time


def scrape_and_calculate():
    today = datetime.now()
    day = today.day
    month = today.month
    year = today.year
    date_str_iso = today.strftime("%Y-%m-%d")
    czech_date_str = f"{day}.{month}.{year}"

    timestamp_ms = int(time.time() * 1000)
    url = f"https://padelbrno.isportsystem.cz/ajax/ajax.schema.php?day={day}&month={month}&year={year}&id_sport=1&default_view=day&reset_date=0&event=datepicker&id_infotab=0&time=&filterId=false&filterChecked=false&tab_type=normal&display_type=undefined&labels=undefined&lastTimestamp=undefined&timetableWidth=970&schema_fixed_date=&_={timestamp_ms}"

    headers = {
        "accept": "*/*",
        "accept-language": "cs-CZ,cs;q=0.9,en-GB;q=0.8,en;q=0.7",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    today_container = None

    for h3 in soup.find_all('h3'):
        if czech_date_str in h3.text:
            today_container = h3.find_parent('div', class_='schemaFullContainer')
            break

    if not today_container:
        print(f"Could not find the schedule block for date: {czech_date_str}")
        return

    data_wrapper = today_container.find('div', class_='schemaWrapper')
    courts = {
        "Padel kurt 1": data_wrapper.find('tr', class_='trSchemaLane_1'),
        "Padel kurt 2": data_wrapper.find('tr', class_='trSchemaLane_2')
    }

    daily_data = []

    # Counters for our math
    total_slots = 0
    booked_slots = 0

    for court_name, court_row in courts.items():
        if not court_row:
            continue

        table_cells = court_row.find_all('td', recursive=False)

        for td in table_cells:
            title_text = None
            if td.has_attr('title'):
                title_text = td['title']
            else:
                a_tag = td.find('a', title=True)
                if a_tag:
                    title_text = a_tag['title']

            if title_text and "–" in title_text:
                parts = title_text.split(" - ", 1)
                if len(parts) >= 1:
                    time_block = parts[0].strip()
                    status = parts[1].strip() if len(parts) > 1 else "Neznámý stav"

                    daily_data.append([date_str_iso, court_name, time_block, status])

                    # Update our counters
                    total_slots += 1
                    if status == "Obsazeno":
                        booked_slots += 1

    # --- SAVE RAW DATA ---
    raw_csv = "padel_brno_all_slots.csv"
    raw_exists = os.path.isfile(raw_csv)
    with open(raw_csv, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        if not raw_exists:
            writer.writerow(['Date', 'Court', 'Time Slot', 'Status'])
        writer.writerows(daily_data)

    # --- DO THE MATH & SAVE SUMMARY ---
    occupancy_rate = 0
    if total_slots > 0:
        occupancy_rate = round((booked_slots / total_slots) * 100, 2)

    print(f"[{date_str_iso}] Occupancy: {occupancy_rate}% ({booked_slots}/{total_slots} slots booked)")

    summary_csv = "padel_brno_daily_summary.csv"
    summary_exists = os.path.isfile(summary_csv)
    with open(summary_csv, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        if not summary_exists:
            writer.writerow(['Date', 'Total Slots', 'Booked Slots', 'Occupancy Rate (%)'])
        writer.writerow([date_str_iso, total_slots, booked_slots, occupancy_rate])


if __name__ == "__main__":
    scrape_and_calculate()