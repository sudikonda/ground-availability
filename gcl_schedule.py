import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, date
import os

CACHE_FILE = 'data/gcl_schedule_cache_1.json'
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
        soup = BeautifulSoup(response.content, "html.parser")
        parsed_data = parse_schedule_data(soup)
        save_cached_data(parsed_data)
        return parsed_data
    except requests.RequestException as e:
        st.write(f"Error fetching data: {str(e)}")
        return None


def get_match_info(match_div):
    if not match_div:
        return None

    # Extract date and time
    date_div = match_div.find('div', class_='sch-time')
    day = date_div.find('h4').text
    date = date_div.find('h2').text
    month_year = date_div.find('h5').text
    time = date_div.find_all('h5')[-1].text
    match_date = f"{day}, {month_year} {date}"

    # Extract team names and IDs
    schedule_text = match_div.find('div', class_='schedule-text')
    team_links = schedule_text.find_all('a', href=lambda x: x and 'viewTeam.do' in x)
    home_team_name = team_links[0].text.strip()
    visiting_team_name = team_links[1].text.strip()
    home_team_id = team_links[0]['href'].split('teamId=')[1].split('&')[0]
    visiting_team_id = team_links[1]['href'].split('teamId=')[1].split('&')[0]

    # Extract ground name
    ground_link = match_div.find('a', href=lambda x: x and 'viewGround.do' in x)
    ground_name = ground_link.text.strip() if ground_link else None

    # Extract umpire info
    umpire_link = match_div.find('a', href=lambda x: x and 'viewUmpire.do' in x)
    umpire_id = umpire_link['href'].split('umpireUId=')[1].split('&')[0] if umpire_link else "N/A"

    # Find the scorecard link and extract the match number
    scorecard_link = match_div.find('a', href=lambda x: x and 'viewScorecard.do' in x)
    roster_link = schedule_text.find_all('a', href=lambda x: x and 'teamRoster.do' in x)
    match_number = scorecard_link['href'].split('matchId=')[1].split('&')[0] if scorecard_link else \
        roster_link[0]['href'].split('fixtureId=')[1].split('&')[0]

    # Create JSON object
    match_info = {
        "league": "GCL",
        "match_no": match_number,
        "home_team_id": home_team_id,
        "visiting_team_id": visiting_team_id,
        "umpire_team_id": umpire_id,
        "home_team_name": home_team_name,
        "visiting_team_name": visiting_team_name,
        "ground_name": ground_name,
        "match_time": time,
        "match_date": match_date
    }

    return match_info


def get_all_grounds(soup):
    grounds = set()
    grounds_div = soup.find('div', attrs={'title': 'Change Ground'})
    ground_links = grounds_div.find_all('li')
    for ground_link in ground_links:
        if ground_link:
            ground_name = ground_link.text.strip()
            grounds.add(ground_name)

    return list(grounds)


def parse_schedule_data(soup):
    # Find all divs with class 'schedule-all'
    match_divs = soup.find_all('div', class_='schedule-all')
    # Process each match
    all_matches = []
    for match_div in match_divs:
        match_info = get_match_info(match_div)
        if match_info:
            all_matches.append(match_info)

    all_grounds = get_all_grounds(soup)
    return {"all_grounds": all_grounds, "matches": all_matches}


def get_gcl_schedule_main():
    today = date.today()
    formatted_today = today.strftime("%m/%d/%Y")

    url = f"https://www.cricclubs.com/GeorgiaCricketLeague/fixtures.do?league=All&teamId=null&internalClubId=null&groundId=null&year=null&clubId=7109&fromDate={formatted_today}&toDate="
    data = fetch_and_parse_data(url)

    if data is None:
        return
    else:
        return data
