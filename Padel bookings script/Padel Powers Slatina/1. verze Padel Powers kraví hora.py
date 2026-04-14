import requests
from datetime import datetime, timedelta
import csv
import os


def scrape_padel_powers():
    # Target tomorrow to avoid past-time logic
    target_date = datetime.now() + timedelta(days=0)
    date_str_iso = target_date.strftime("%Y-%m-%d")
    api_date = f"{date_str_iso}T00:00"

    print(f"Fetching data for Brno Slatina on {date_str_iso}...")

    url = "https://api.foys.io/court-booking/public/api/v1/locations/search"

    params = (
        ('reservationTypeId', '85'),
        ('locationId', 'b267cf7e-706a-4a21-a8fb-5399e5309da8'),
        ('playingTimes[]', '60'),
        ('playingTimes[]', '90'),
        ('playingTimes[]', '120'),
        ('date', api_date)
    )

    import requests

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'cs-CZ,cs;q=0.9,en-GB;q=0.8,en;q=0.7,nl-NL;q=0.6,nl;q=0.5,de;q=0.4',
        'content-type': 'application/json',
        'origin': 'https://www.padelpowers.com',
        'priority': 'u=1, i',
        'referer': 'https://www.padelpowers.com/rezervace/court-booking/reservation/?location=Brno%20Slatina&date=2026-04-09',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'x-federationid': '30c6ef06-0a88-4ed7-a0ba-23352869c8a1',
        'x-organisationid': '48c8d621-a469-4645-17ee-08db9da35083',
    }

    response = requests.get(
        'https://api.foys.io/court-booking/public/api/v1/locations/search?reservationTypeId=85&locationId=832af7ca-3661-4d34-94ba-50068de855c0&playingTimes[]=60&playingTimes[]=90&playingTimes[]=120&date=2026-04-09T00:00:00.000Z',
        headers=headers,
    )

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return

    json_data = response.json()

    if not json_data:
        print(f"Error: The API returned an empty response.")
        return

    if isinstance(json_data, list) and len(json_data) > 0:
        location_data = json_data[0]
    elif isinstance(json_data, dict):
        location_data = json_data
    else:
        print(f"Error: Unrecognized JSON structure.")
        return

    courts_list = location_data.get('inventoryItemsTimeSlots', [])

    if not courts_list:
        print("Error: Could not find the courts list in the data.")
        return

    daily_data = []
    global_total_slots = 0
    global_booked_slots = 0

    for court in courts_list:
        court_name = court.get('name', 'Neznámý kurt')

        court_schedule = {}
        curr_time = datetime.strptime("07:00", "%H:%M")
        end_time = datetime.strptime("22:00", "%H:%M")

        while curr_time < end_time:
            next_time = curr_time + timedelta(minutes=30)
            slot_str = f"{curr_time.strftime('%H:%M')}–{next_time.strftime('%H:%M')}"
            court_schedule[slot_str] = "Obsazeno"
            curr_time = next_time

        timeslots = court.get('timeSlots', [])
        for slot in timeslots:
            if slot.get('isAvailable') == True:
                st_raw = slot.get('startTime').split('T')[1][:5]
                et_raw = slot.get('endTime').split('T')[1][:5]

                s_dt = datetime.strptime(st_raw, "%H:%M")
                e_dt = datetime.strptime(et_raw, "%H:%M")

                c_dt = s_dt
                while c_dt < e_dt:
                    n_dt = c_dt + timedelta(minutes=30)
                    block_str = f"{c_dt.strftime('%H:%M')}–{n_dt.strftime('%H:%M')}"

                    if block_str in court_schedule:
                        court_schedule[block_str] = "Volno"

                    c_dt = n_dt

        for time_block, status in court_schedule.items():
            daily_data.append([date_str_iso, court_name, time_block, status])

            global_total_slots += 1
            if status == "Obsazeno":
                global_booked_slots += 1

    # --- SAVE RAW DATA ---
    raw_csv = "padel_powers_slatina_all_slots.csv"
    raw_exists = os.path.isfile(raw_csv)

    with open(raw_csv, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        if not raw_exists:
            writer.writerow(['Date', 'Court', 'Time Slot', 'Status'])
        writer.writerows(daily_data)

    # --- DO THE MATH & SAVE SUMMARY ---
    occupancy_rate = 0
    if global_total_slots > 0:
        occupancy_rate = round((global_booked_slots / global_total_slots) * 100, 2)

    print(
        f"[{date_str_iso}] Slatina Occupancy: {occupancy_rate}% ({global_booked_slots}/{global_total_slots} slots booked)")

    # THE RESTORED CODE: Writing the summary to the second CSV file
    summary_csv = "padel_powers_slatina_summary.csv"
    summary_exists = os.path.isfile(summary_csv)

    with open(summary_csv, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        if not summary_exists:
            writer.writerow(['Date', 'Total Slots', 'Booked Slots', 'Occupancy Rate (%)'])
        writer.writerow([date_str_iso, global_total_slots, global_booked_slots, occupancy_rate])

    print(f"Successfully saved summary to {summary_csv}")


if __name__ == "__main__":
    scrape_padel_powers()