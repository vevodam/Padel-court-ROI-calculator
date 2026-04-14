import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
import time

# --- CONFIGURATION: DEFINE YOUR LOCATIONS HERE ---
LOCATIONS = [
    {
        "name": "Za Lužánkami (Outdoor)",
        "id_sport": 1,
        "lanes": {
            "Padel kurt 1": "trSchemaLane_1",
            "Padel kurt 2": "trSchemaLane_2"
        },
        "raw_csv": "padel_brno_luzanky_all_slots.csv",
        "summary_csv": "padel_brno_luzanky_daily_summary.csv"
    },
    {
        "name": "Brno Jehnice (Indoor)",
        "id_sport": 12,
        "lanes": {
            "Padel Indoor": "trSchemaLane_68"  # Assumes the single court uses Lane 1
        },
        "raw_csv": "padel_brno_jehnice_all_slots.csv",
        "summary_csv": "padel_brno_jehnice_daily_summary.csv"
    }
]


def scrape_and_calculate_all_locations():
    today = datetime.now()
    day = today.day
    month = today.month
    year = today.year
    date_str_iso = today.strftime("%Y-%m-%d")
    czech_date_str = f"{day}.{month}.{year}"

    timestamp_ms = int(time.time() * 1000)

    # Base headers remain the same
    headers = {
        "accept": "*/*",
        "accept-language": "cs-CZ,cs;q=0.9,en-GB;q=0.8,en;q=0.7",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    # Loop through each location in our config
    for loc in LOCATIONS:
        print(f"\n--- Processing {loc['name']} ---")

        # Inject the correct id_sport into the URL
        url = f"https://padelbrno.isportsystem.cz/ajax/ajax.schema.php?day={day}&month={month}&year={year}&id_sport={loc['id_sport']}&default_view=day&reset_date=0&event=datepicker&id_infotab=0&time=&filterId=false&filterChecked=false&tab_type=normal&display_type=undefined&labels=undefined&lastTimestamp=undefined&timetableWidth=970&schema_fixed_date=&_={timestamp_ms}"

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch data for {loc['name']}. Status: {response.status_code}")
            continue  # Skip to the next location if this one fails

        soup = BeautifulSoup(response.text, 'html.parser')
        today_container = None

        for h3 in soup.find_all('h3'):
            if czech_date_str in h3.text:
                today_container = h3.find_parent('div', class_='schemaFullContainer')
                break

        if not today_container:
            print(f"Could not find the schedule block for {loc['name']} on {czech_date_str}")
            continue

        data_wrapper = today_container.find('div', class_='schemaWrapper')
        if not data_wrapper:
            print(f"Could not find the data grid for {loc['name']}.")
            continue

        daily_data = []
        total_slots = 0
        booked_slots = 0

        # Dynamically search for the courts defined in the config for THIS location
        for court_name, row_class in loc["lanes"].items():
            court_row = data_wrapper.find('tr', class_=row_class)

            if not court_row:
                print(f"  Warning: Could not find row for {court_name}")
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

                        # --- THE FIX ---
                        # If the word "Kroužek" is anywhere in the status, force it to say "Obsazeno"
                        if "Neznámý stav" in status:
                            status = "Obsazeno"

                        daily_data.append([date_str_iso, court_name, time_block, status])

                        total_slots += 1
                        if status == "Obsazeno":
                            booked_slots += 1

        # --- SAVE RAW DATA (Using specific filename for this location) ---
        if daily_data:
            raw_exists = os.path.isfile(loc["raw_csv"])
            with open(loc["raw_csv"], mode='a', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                if not raw_exists:
                    writer.writerow(['Date', 'Court', 'Time Slot', 'Status'])
                writer.writerows(daily_data)

            # --- DO THE MATH & SAVE SUMMARY ---
            occupancy_rate = round((booked_slots / total_slots) * 100, 2) if total_slots > 0 else 0

            print(f"  Occupancy: {occupancy_rate}% ({booked_slots}/{total_slots} slots booked)")

            summary_exists = os.path.isfile(loc["summary_csv"])
            with open(loc["summary_csv"], mode='a', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                if not summary_exists:
                    writer.writerow(['Date', 'Total Slots', 'Booked Slots', 'Occupancy Rate (%)'])
                writer.writerow([date_str_iso, total_slots, booked_slots, occupancy_rate])

            print(f"  Saved to {loc['raw_csv']} and {loc['summary_csv']}")


if __name__ == "__main__":
    scrape_and_calculate_all_locations()