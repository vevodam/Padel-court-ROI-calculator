import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
import time


def scrape_all_daily_timeslots():
    # --- 1. SET THE TARGET DATE ---
    # Uses today's date. (If you are testing a specific past/future date,
    # you can change this to: today = datetime(2026, 4, 9) )
    today = datetime.now()
    day = today.day
    month = today.month
    year = today.year
    date_str_iso = today.strftime("%Y-%m-%d")

    # Format to match the <h3> tag exactly (e.g., "9.4.2026")
    czech_date_str = f"{day}.{month}.{year}"

    timestamp_ms = int(time.time() * 1000)
    url = f"https://padelbrno.isportsystem.cz/ajax/ajax.schema.php?day={day}&month={month}&year={year}&id_sport=1&default_view=day&reset_date=0&event=datepicker&id_infotab=0&time=&filterId=false&filterChecked=false&tab_type=normal&display_type=undefined&labels=undefined&lastTimestamp=undefined&timetableWidth=970&schema_fixed_date=&_={timestamp_ms}"

    headers = {
        "accept": "*/*",
        "accept-language": "cs-CZ,cs;q=0.9,en-GB;q=0.8,en;q=0.7",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    print(f"Fetching data for {date_str_iso}...")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return

    # --- 2 & 3. PARSE HTML & IDENTIFY TODAY'S BLOCK ---
    soup = BeautifulSoup(response.text, 'html.parser')
    all_h3_tags = soup.find_all('h3')
    today_container = None

    for h3 in all_h3_tags:
        if czech_date_str in h3.text:
            today_container = h3.find_parent('div', class_='schemaFullContainer')
            break

    if not today_container:
        print(f"Could not find the schedule block for date: {czech_date_str}")
        return

    # --- 4. IDENTIFY THE TWO SEPARATED COURTS ---
    data_wrapper = today_container.find('div', class_='schemaWrapper')

    courts = {
        "Padel kurt 1": data_wrapper.find('tr', class_='trSchemaLane_1'),
        "Padel kurt 2": data_wrapper.find('tr', class_='trSchemaLane_2')
    }

    daily_data = []

    # --- 5. EXTRACT EVERY TIMESLOT FOR BOTH COURTS ---
    for court_name, court_row in courts.items():
        if not court_row:
            continue

        # THE FIX: recursive=False forces BS4 to ignore the broken HTML nesting
        # and only look at the direct table cells (<td>) for this specific row.
        table_cells = court_row.find_all('td', recursive=False)

        for td in table_cells:
            title_text = None

            # Check if the title is directly on the <td> (like "Obsazeno" or "Tento čas...")
            if td.has_attr('title'):
                title_text = td['title']
            else:
                # If not, check if there is an <a> tag inside it with the title (like "Volno")
                a_tag = td.find('a', title=True)
                if a_tag:
                    title_text = a_tag['title']

            # If we found a title, split it into Time and Status
            if title_text and "–" in title_text:
                parts = title_text.split(" - ", 1)  # Split only on the first dash
                if len(parts) >= 1:
                    time_block = parts[0].strip()
                    status = parts[1].strip() if len(parts) > 1 else "Neznámý stav"

                    daily_data.append([date_str_iso, court_name, time_block, status])

    # --- 6. RETURN A CSV FILE ---
    csv_filename = "padel_brno_all_slots.csv"
    file_exists = os.path.isfile(csv_filename)

    with open(csv_filename, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(['Date', 'Court', 'Time Slot', 'Status'])

        writer.writerows(daily_data)

    print(f"Done! Saved {len(daily_data)} total timeslots to {csv_filename}.")


if __name__ == "__main__":
    scrape_all_daily_timeslots()