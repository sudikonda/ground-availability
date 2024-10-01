import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import json

CACHE_FILE = 'data/acl_schedule_cache.json'
CACHE_EXPIRY_HOURS = 24


def load_cached_data():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        if datetime.now() - datetime.fromisoformat(cache['timestamp']) < timedelta(hours=CACHE_EXPIRY_HOURS):
            return cache['data']
    return None


def save_cached_data(data):
    cache = {
        'timestamp': datetime.now().isoformat(),
        'data': data
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)


@st.cache_data(ttl=3600 * 24)
def fetch_and_parse_data(url):
    cached_data = load_cached_data()
    if cached_data:
        return cached_data

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        parsed_data = parse_schedule_data(soup)
        save_cached_data(parsed_data)
        return parsed_data
    except requests.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return None


def parse_schedule_data(soup):
    all_grounds = set()
    matches = []
    for match in soup.find_all('div', {'matchno': True}):
        match_info = extract_match_info(match)
        matches.append(match_info)
        all_grounds.add(match_info['ground_name'])
    return {'all_grounds': list(all_grounds), 'matches': matches}


def extract_match_info(match):
    match_no = match.get('matchno')
    home_team_id = match.get('htid')
    visiting_team_id = match.get('vtid')
    umpire_team_id = match.get('utid')
    teams = match.find_all('a', class_=['text-primary', 'text-dark'])
    home_team = match.find("a", href=lambda href: href and str(home_team_id) in href)
    visiting_team = match.find("a", href=lambda href: href and str(visiting_team_id) in href)
    ground = match.find('a', title="Ground Directions")
    date_time = match.find_all('div', class_='text-nowrap')

    return {
        'match_no': match_no,
        'home_team_id': home_team_id,
        'visiting_team_id': visiting_team_id,
        'umpire_team_id': umpire_team_id,
        'home_team_name': home_team.get_text(strip=True) if teams else "N/A",
        'visiting_team_name': visiting_team.get_text(strip=True) if teams else "N/A",
        'ground_name': ground.get_text(strip=True) if ground else "N/A",
        'match_time': date_time[0].get_text(strip=True) if date_time else "N/A",
        'match_date': date_time[1].get_text(strip=True) if date_time else "N/A"
    }


def main():
    st.set_page_config(page_title="Ground Availability and Matches Schedule", page_icon="🏏")
    st.title("🏃🏼Ground Availability and Matches Schedule 🏏️")

    selected_date = st.date_input("Select a date", datetime.today())
    date_str = selected_date.strftime('%b %d')

    url = "https://www.atlantacricketleague.org/Schedule/2024"
    data = fetch_and_parse_data(url)

    if data is None:
        return

    all_grounds = data['all_grounds']
    matches = data['matches']

    matches_today = [match for match in matches if date_str in match['match_date']]
    grounds_in_use_today = set(match['ground_name'] for match in matches_today)
    available_grounds = [ground for ground in all_grounds if ground not in grounds_in_use_today]

    st.subheader(f"Matches scheduled for {date_str} by Ground:")
    if matches_today:
        for ground in grounds_in_use_today:
            with st.expander(f"Ground: {ground}"):
                ground_matches = [match for match in matches_today if match['ground_name'] == ground]
                df = pd.DataFrame(ground_matches)
                st.table(df[['home_team_name', 'visiting_team_name', 'match_time', 'match_date']])
    else:
        st.write(f"No matches scheduled for {date_str}.")

    st.subheader(f"Available Grounds for {date_str}:")
    if available_grounds:
        with st.expander("Click to view available grounds"):
            df_available = pd.DataFrame({"Available Grounds": available_grounds})
            st.table(df_available)
    else:
        st.write("No available grounds for the selected date.")


if __name__ == "__main__":
    main()