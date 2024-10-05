import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import json

CACHE_FILE = 'data/acl_schedule_cache_1.json'
CACHE_EXPIRY_HOURS = 24


def load_cached_data():
    try:
        if os.path.exists(CACHE_FILE):
            cache_creation_time = os.path.getctime(CACHE_FILE)
            cache_age = datetime.now() - datetime.fromtimestamp(cache_creation_time)
            if cache_age < timedelta(hours=CACHE_EXPIRY_HOURS):
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                return cache.get('data', None)
    except (IOError, json.JSONDecodeError) as e:
        st.write(f"Error loading cached data: {e}")

    return None

def save_cached_data(data):
    cache = {
        'timestamp': datetime.now().isoformat(),
        'data': data
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)


# @st.cache_data(ttl=3600 * 24)
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
        'league': 'ACL',
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


def get_acl_schedule_main():
    url = "https://www.atlantacricketleague.org/Schedule/2024"
    data = fetch_and_parse_data(url)

    if data is None:
        return
    else:
        return data
